from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_session
from app.models.course import Course
from app.models.material import Material
from app.models.rps import RPS
from app.models.rps_meeting import RPSMeeting

router = APIRouter()


def _ref_id(ref: str) -> str:
    """Stable id for a reference string."""
    import hashlib

    return "ref-" + hashlib.md5(ref.encode("utf-8")).hexdigest()[:8]


@router.get("/graph")
def knowledge_graph(course_id: Optional[str] = None, db: Session = Depends(get_session)):
    """Return nodes and edges for the knowledge network visualization.

    Layers (left → right):
        course → cpl → cpmk → week → reference / material
    """
    courses_q = db.query(Course)
    if course_id:
        courses_q = courses_q.filter(Course.id == course_id)
    courses = courses_q.all()

    nodes: list[dict] = []
    edges: list[dict] = []
    seen_ids: set[str] = set()

    def add_node(node: dict):
        if node["id"] in seen_ids:
            return
        seen_ids.add(node["id"])
        nodes.append(node)

    def add_edge(src: str, tgt: str, kind: str = "link"):
        edges.append({"source": src, "target": tgt, "kind": kind})

    for course in courses:
        course_node_id = f"course-{course.id}"
        add_node(
            {
                "id": course_node_id,
                "label": course.name,
                "type": "course",
                "meta": {"code": course.code, "sks": course.sks},
            }
        )

        rps_list = db.query(RPS).filter(RPS.course_id == course.id).all()
        for rps in rps_list:
            cpl_ids: list[str] = []
            for idx, cpl in enumerate(rps.cpl_list or []):
                cpl_id = f"cpl-{rps.id}-{idx}"
                add_node(
                    {
                        "id": cpl_id,
                        "label": f"CPL-{idx + 1}",
                        "type": "cpl",
                        "meta": {"text": cpl, "rps_id": rps.id},
                    }
                )
                add_edge(course_node_id, cpl_id, "has_cpl")
                cpl_ids.append(cpl_id)

            cpmk_ids_by_label: dict[str, str] = {}
            for idx, cpmk in enumerate(rps.cpmk_list or []):
                label = f"CPMK-{idx + 1}"
                cpmk_id = f"cpmk-{rps.id}-{idx}"
                add_node(
                    {
                        "id": cpmk_id,
                        "label": label,
                        "type": "cpmk",
                        "meta": {"text": cpmk, "rps_id": rps.id},
                    }
                )
                # Connect each CPMK to all CPLs of the same RPS (best-effort linkage)
                for cpl_id in cpl_ids:
                    add_edge(cpl_id, cpmk_id, "derives")
                cpmk_ids_by_label[label] = cpmk_id

            # References (RPS-level)
            for ref in rps.references_list or []:
                ref = (ref or "").strip()
                if not ref:
                    continue
                rid = _ref_id(ref)
                add_node(
                    {
                        "id": rid,
                        "label": ref[:80] + ("…" if len(ref) > 80 else ""),
                        "type": "reference",
                        "meta": {"text": ref, "is_url": ref.startswith("http")},
                    }
                )
                add_edge(course_node_id, rid, "references")

            # Meetings → Week nodes
            meetings = (
                db.query(RPSMeeting)
                .filter(RPSMeeting.rps_id == rps.id)
                .order_by(RPSMeeting.week_number)
                .all()
            )
            for m in meetings:
                week_id = f"week-{rps.id}-{m.week_number}"
                # Prefer the institutional sub_topic_title; fall back to legacy topic.
                title = (m.sub_topic_title or m.topic or "").strip()
                desc = (m.sub_topic_description or "").strip()
                topic_blurb = f"{title}: {desc}" if title and desc else title
                add_node(
                    {
                        "id": week_id,
                        "label": f"W{m.week_number}",
                        "type": "week",
                        "meta": {
                            "topic": topic_blurb,
                            "bahan_kajian_topik": m.bahan_kajian_topik or "",
                            "cpmk_number": m.cpmk_number,
                            "reference_indices": m.reference_indices or [],
                            "method": m.learning_method,
                            "evaluation": m.evaluation_method,
                            "rps_id": rps.id,
                        },
                    }
                )
                add_edge(course_node_id, week_id, "has_week")

                # Connect CPMK referenced by this week. The institutional schema
                # uses a single `cpmk_number`; legacy data may still carry a
                # comma-separated string in `m.cpmk`. Walk both.
                cpmk_tokens: list[str] = []
                if m.cpmk_number:
                    cpmk_tokens.append(f"CPMK-{m.cpmk_number}")
                for token in (m.cpmk or "").split(","):
                    token = token.strip()
                    if token:
                        cpmk_tokens.append(token)
                for token in cpmk_tokens:
                    if token in cpmk_ids_by_label:
                        add_edge(cpmk_ids_by_label[token], week_id, "covers")

                # Connect to the canonical numbered references via the
                # institutional `reference_indices` field. The legacy
                # `m.references` string is intentionally NOT used — it would
                # create duplicate reference nodes like "1, 2", "3, 5", etc.
                for idx in m.reference_indices or []:
                    try:
                        i = int(idx)
                    except (TypeError, ValueError):
                        continue
                    if not (1 <= i <= len(rps.references_list or [])):
                        continue
                    ref_text = (rps.references_list or [])[i - 1]
                    if not ref_text:
                        continue
                    rid = _ref_id(ref_text)
                    if rid in seen_ids:
                        add_edge(week_id, rid, "uses")

        # Materials attached to this course (and possibly to specific weeks)
        materials = db.query(Material).filter(Material.course_id == course.id).all()
        # Build a lookup so we can connect materials to the meeting's CPMK/topic
        meetings_by_week: dict[int, "RPSMeeting"] = {}
        for rps in rps_list:
            for m in (
                db.query(RPSMeeting)
                .filter(RPSMeeting.rps_id == rps.id)
                .all()
            ):
                meetings_by_week[m.week_number] = m

        for mat in materials:
            mat_id = f"mat-{mat.id}"
            is_auto = (mat.material_type or "").upper() == "AUTO" or (mat.status_text or "") == "Auto-Generated"
            add_node(
                {
                    "id": mat_id,
                    "label": mat.title,
                    "type": "material",
                    "meta": {
                        "type": mat.material_type,
                        "url": mat.url,
                        "week": mat.week,
                        "indexed": bool(mat.content_text),
                        "auto_generated": is_auto,
                        "status": mat.status_text,
                        "size": mat.size,
                    },
                }
            )

            # Edge 1 → the week node (when the material is attached to a week
            # of an RPS we're rendering).
            week_node = (
                f"week-{mat.rps_id}-{mat.week}"
                if mat.rps_id and mat.week
                else None
            )
            if week_node and week_node in seen_ids:
                add_edge(week_node, mat_id, "auto_material" if is_auto else "uploaded")
            else:
                # Material exists for this course but isn't bound to a specific
                # week (or its week is outside the rendered RPS). Hang it off
                # the course so it's still visible.
                add_edge(course_node_id, mat_id, "uploaded")

            # Edge 2 → the CPMK the meeting maps to. This is the most useful
            # link: "what does this PDF actually teach?" If the meeting has
            # multiple CPMK tokens we connect to all of them.
            mat_meeting = meetings_by_week.get(mat.week or 0) if mat.week else None
            if mat_meeting:
                cpmk_tokens: list[str] = []
                if mat_meeting.cpmk_number:
                    cpmk_tokens.append(f"CPMK-{mat_meeting.cpmk_number}")
                for token in (mat_meeting.cpmk or "").split(","):
                    token = token.strip()
                    if token:
                        cpmk_tokens.append(token)
                for token in cpmk_tokens:
                    cpmk_node = cpmk_ids_by_label.get(token)
                    if cpmk_node:
                        add_edge(cpmk_node, mat_id, "supports")

    return {"nodes": nodes, "edges": edges}


class RagQuery(BaseModel):
    query: str
    course_id: Optional[str] = None
    k: int = 4


@router.post("/query")
def rag_query(payload: RagQuery, db: Session = Depends(get_session)):
    """Retrieval-augmented search over indexed materials."""
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query tidak boleh kosong.")
    try:
        from app.core.rag import retrieve_materials

        results = retrieve_materials(
            payload.query,
            course_id=payload.course_id,
            k=max(1, min(payload.k, 10)),
        )
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"RAG retrieval gagal: {e}")

    out = []
    for doc in results:
        meta = getattr(doc, "metadata", {}) or {}
        out.append(
            {
                "snippet": doc.page_content[:600],
                "title": meta.get("title", "(tanpa judul)"),
                "material_id": meta.get("material_id"),
                "course_id": meta.get("course_id"),
                "rps_id": meta.get("rps_id"),
                "week": meta.get("week"),
                "type": meta.get("type"),
            }
        )
    return {"query": payload.query, "results": out}
