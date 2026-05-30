from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import PyPDF2
from pydantic import BaseModel

from app.agents.rps_agent import build_curriculum_graph
from app.core.database import get_session
from app.core.rps_constants import (
    UAS_MODULE,
    UAS_TITLE,
    UTS_MODULE,
    UTS_TITLE,
    is_exam_week,
)
from app.core.rps_coerce import (
    coerce_bahan_kajian,
    coerce_cpmk_number,
    coerce_reference_indices,
)
from app.core.sndikti_catalog import run_catalog
from app.models.rps import RPS
from app.models.course import Course
from app.models.rps_meeting import RPSMeeting

router = APIRouter()


class RPSPayload(BaseModel):
    """Shared payload for both manual create and edit.

    Course-related fields are optional on edit (the course is already linked).

    Each entry in `meetings` may carry both legacy keys
    (`topic`, `cpmk`, `references`) and institutional keys
    (`bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`,
    `cpmk_number`, `reference_indices`). The institutional keys take
    precedence; legacy keys are accepted as fallback to keep older
    clients working during the transition.
    """

    course_name: Optional[str] = ""
    course_code: Optional[str] = ""
    sks: Optional[int] = 3
    semester: Optional[int] = 1
    program_study: Optional[str] = ""
    cpl_list: List[str] = []
    cpmk_list: List[str] = []
    references_list: List[str] = []
    bahan_kajian: List[str] = []
    learning_methods: List[str] = []
    learning_modality: Optional[str] = ""
    meetings: List[Dict[str, Any]] = []


def _save_meetings(
    db: Session,
    rps_id: str,
    meetings: List[Dict[str, Any]],
    *,
    bahan_kajian_options: List[str] | None = None,
    cpmk_list_len: int = 0,
    references_list_len: int = 0,
    fallback_method: str = "",
):
    """Replace meetings for an RPS with the supplied list.

    Each incoming dict may use the institutional keys
    (`bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`,
    `cpmk_number`, `reference_indices`) and/or the legacy keys
    (`topic`, `cpmk`, `references`). Both are persisted: the institutional
    columns drive the new UI, the legacy strings stay populated as a
    fallback so older readers keep working.

    Exam weeks (Modul 8 / 16) are forced to the canonical UTS/UAS values.
    """
    bahan_kajian_options = bahan_kajian_options or []
    db.query(RPSMeeting).filter(RPSMeeting.rps_id == rps_id).delete()

    for m in meetings:
        try:
            week = int(m.get("week", 1))
        except (TypeError, ValueError):
            week = 1

        if is_exam_week(week):
            title = UTS_TITLE if week == UTS_MODULE else UAS_TITLE
            sub_title = title
            sub_desc = ""
            bahan_topik = ""
            cpmk_num = None
            ref_indices: list[int] = []
            legacy_topic = title
            legacy_cpmk = ""
            legacy_refs = ""
            method = ""
            evaluation = ""
        else:
            sub_title = str(m.get("sub_topic_title") or "").strip()
            sub_desc = str(m.get("sub_topic_description") or "").strip()

            # If only the legacy `topic` field is provided, split it on the
            # first colon so the institutional fields stay populated.
            if not sub_title and m.get("topic"):
                from app.core.rps_migration import _split_legacy_topic

                sub_title, sub_desc = _split_legacy_topic(str(m.get("topic")))

            bahan_topik = coerce_bahan_kajian(
                m.get("bahan_kajian_topik", ""), bahan_kajian_options
            )

            cpmk_num = coerce_cpmk_number(
                m.get("cpmk_number", m.get("cpmk")), cpmk_list_len
            )

            ref_indices, _ = coerce_reference_indices(
                m.get("reference_indices", m.get("references")),
                references_list_len,
            )

            # Legacy strings — keep them populated so older readers (and
            # debug screens) still render something useful.
            legacy_topic = (
                f"{sub_title}: {sub_desc}".strip(": ") if sub_desc else sub_title
            )
            legacy_cpmk = f"CPMK-{cpmk_num}" if cpmk_num else ""
            legacy_refs = ", ".join(str(i) for i in ref_indices)

            method = str(m.get("method") or fallback_method or "")[:255]
            evaluation = str(m.get("evaluation") or "")[:255]

        rm = RPSMeeting(
            id=f"rm-{uuid4().hex[:8]}",
            rps_id=rps_id,
            week_number=week,
            bahan_kajian_topik=bahan_topik or "",
            sub_topic_title=sub_title[:500],
            sub_topic_description=sub_desc,
            cpmk_number=cpmk_num,
            reference_indices=ref_indices,
            topic=legacy_topic[:500],
            cpmk=legacy_cpmk[:50],
            references=legacy_refs[:255],
            learning_method=method,
            evaluation_method=evaluation,
            status="ok",
            status_text="OK",
        )
        db.add(rm)


def _validate_meetings(
    meetings: List[Dict[str, Any]],
    *,
    bahan_kajian_options: List[str],
    cpmk_list_len: int,
    references_list_len: int,
) -> None:
    """Raise HTTPException(400) if any meeting violates the institutional rules.

    The error message lists every offending week so the dosen can fix the
    form in one round-trip.
    """
    bk_lookup = {b.strip().lower(): b for b in bahan_kajian_options if b}
    issues: list[str] = []

    for m in meetings:
        try:
            week = int(m.get("week", 0))
        except (TypeError, ValueError):
            issues.append(f"Minggu '{m.get('week')}' bukan angka valid.")
            continue

        bk = str(m.get("bahan_kajian_topik") or "").strip()
        cpmk_num = m.get("cpmk_number")
        ref_indices = m.get("reference_indices") or []

        if is_exam_week(week):
            if bk:
                issues.append(
                    f"Minggu {week}: Bahan Kajian harus kosong (modul ujian)."
                )
            if cpmk_num not in (None, "", 0):
                issues.append(
                    f"Minggu {week}: CPMK harus kosong (modul ujian)."
                )
            if ref_indices:
                issues.append(
                    f"Minggu {week}: Referensi harus kosong (modul ujian)."
                )
            continue

        if bk and bk.lower() not in bk_lookup:
            issues.append(
                f"Minggu {week}: Bahan Kajian '{bk}' tidak ada di daftar RPS."
            )

        if cpmk_num is not None and cpmk_num != "":
            try:
                n = int(cpmk_num)
            except (TypeError, ValueError):
                issues.append(f"Minggu {week}: CPMK '{cpmk_num}' bukan angka.")
            else:
                if cpmk_list_len <= 0 or not (1 <= n <= cpmk_list_len):
                    issues.append(
                        f"Minggu {week}: CPMK {n} di luar rentang 1..{cpmk_list_len}."
                    )

        if ref_indices:
            for raw in ref_indices:
                try:
                    n = int(raw)
                except (TypeError, ValueError):
                    issues.append(
                        f"Minggu {week}: Referensi '{raw}' bukan angka."
                    )
                    continue
                if references_list_len <= 0 or not (1 <= n <= references_list_len):
                    issues.append(
                        f"Minggu {week}: Referensi {n} di luar rentang 1..{references_list_len}."
                    )

    if issues:
        raise HTTPException(status_code=400, detail="; ".join(issues))


def _refresh_compliance(db: Session, rps: RPS) -> int:
    """Recompute the catalog-driven compliance score for an RPS and persist it.

    Called after meetings have been written so the catalog sees the real
    ORM rows. Returns the integer score for the caller's convenience.
    """
    course = db.query(Course).filter(Course.id == rps.course_id).first()
    meetings = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps.id)
        .order_by(RPSMeeting.week_number)
        .all()
    )
    report = run_catalog(rps, meetings, course=course)
    rps.compliance_score = float(report.score)
    return report.score


def _get_or_create_course(db: Session, name: str, code: str, sks: int, semester: int, program_study: str) -> Course:
    course = None
    if code:
        course = db.query(Course).filter(Course.code == code).first()
    if not course:
        course = Course(
            id=f"c-{uuid4().hex[:8]}",
            name=name or "Mata Kuliah Baru",
            code=code or f"NEW-{uuid4().hex[:4].upper()}",
            sks=sks or 3,
            semester=semester or 1,
            program_study=program_study or "",
            status="ok",
            status_text="On Track",
        )
        db.add(course)
        db.commit()
        db.refresh(course)
    return course


@router.post("/generate")
async def generate_rps(
    course_name: str = Form("Mata Kuliah Baru"),
    course_code: str = Form("NEW"),
    sks: int = Form(3),
    program_study: str = Form(""),
    semester: int = Form(1),
    description: str = Form(""),
    learning_method_preference: str = Form("sinkron"),
    bahan_kajian: str = Form(""),
    learning_methods: str = Form(""),
    learning_modality: str = Form(""),
    links: str = Form(""),
    # User-typed lists from the manual form. We treat these as authoritative
    # and only ask the AI to fill in the blanks.
    cpl_list: str = Form(""),
    cpmk_list: str = Form(""),
    references_list: str = Form(""),
    pdf_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_session),
):
    # Parse user-provided links into both a raw text blob (for the AI) and a clean list (for DB)
    references_text = ""
    user_links_list: List[str] = []

    if links:
        try:
            for link in json.loads(links):
                link = link.strip()
                if link:
                    user_links_list.append(link)
                    references_text += link + "\n"
        except Exception:
            pass

    # Parse the JSON-encoded list inputs from the form
    def _parse_list(raw: str) -> List[str]:
        if not raw:
            return []
        try:
            decoded = json.loads(raw)
            if isinstance(decoded, list):
                return [str(v).strip() for v in decoded if str(v).strip()]
        except Exception:
            pass
        return []

    bahan_kajian_list = _parse_list(bahan_kajian)
    learning_methods_list = _parse_list(learning_methods)
    learning_modality_value = (learning_modality or "").strip()
    user_cpl_list = _parse_list(cpl_list)
    user_cpmk_list = _parse_list(cpmk_list)
    user_references_list = _parse_list(references_list)

    # Combined references = user-typed list + raw links (deduped)
    combined_references: List[str] = list(user_references_list)
    for link in user_links_list:
        if link not in combined_references:
            combined_references.append(link)

    if pdf_file:
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file.file)
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += (page.extract_text() or "") + "\n"
            references_text += "\n--- Konten PDF ---\n" + pdf_text[:5000]
        except Exception as e:
            print(f"Failed to parse PDF: {e}")

    # Description is now passed separately as a primary directive — keep the
    # references blob clean of user prose so the LLM doesn't conflate them.

    graph = build_curriculum_graph()
    initial_state = {
        "course_name": course_name,
        "course_code": course_code,
        "sks": sks,
        "program_study": program_study,
        "semester": semester,
        "cpl_list": [],
        "sndikti_rules": "",
        "trend_data": "",
        "references": references_text,
        "bahan_kajian": bahan_kajian_list,
        "learning_methods": learning_methods_list,
        "learning_modality": learning_modality_value,
        "description": description or "",
        "user_cpl": user_cpl_list,
        "user_cpmk": user_cpmk_list,
        "user_references": combined_references,
        "draft_rps": "",
        "validated_rps": "",
        "meetings_list": [],
        "messages": [],
    }

    try:
        result = graph.invoke(initial_state)
        validated_rps = result.get("validated_rps")
        cpl_list_raw = result.get("cpl_list") or []
        trend_data = result.get("trend_data")

        # Pick up bahan_kajian — the agent may have synthesized one if the
        # dosen left the form's bahan_kajian list empty.
        final_bahan_kajian = (
            bahan_kajian_list
            if bahan_kajian_list
            else (result.get("bahan_kajian") or [])
        )

        # Pick up references — same idea: agent may have synthesized a
        # numbered bibliography when the dosen left it empty.
        agent_synthesized_refs = result.get("user_references") or []
        if combined_references:
            base_references = combined_references
        else:
            base_references = list(agent_synthesized_refs)

        course = _get_or_create_course(db, course_name, course_code, sks, semester, program_study)

        # Parse CPL and CPMK from agent output (which already merges user input)
        NOISE_PHRASES = [
            "capaian pembelajaran lulusan",
            "capaian pembelajaran mata kuliah",
            "cpl dan cpmk",
            "berikut adalah",
            "berikut ini",
            "output:",
        ]

        def is_noise(line: str) -> bool:
            lower = line.lower()
            return any(phrase in lower for phrase in NOISE_PHRASES)

        parsed_cpl, parsed_cpmk = [], []
        for item in cpl_list_raw:
            item = item.strip()
            if not item or is_noise(item):
                continue
            if item.startswith("CPL:"):
                parsed_cpl.append(item[4:].strip())
            elif item.startswith("CPMK:"):
                parsed_cpmk.append(item[5:].strip())
            elif "CPMK" in item and not item.startswith("CPL"):
                parsed_cpmk.append(item)
            else:
                parsed_cpl.append(item)

        # Build references list. Authoritative source = whatever the dosen
        # already typed (or whatever the agent synthesized when the dosen
        # left the field empty); we then append agent-suggested references
        # that appeared in meetings as legacy `references` strings.
        agent_refs: List[str] = []
        meetings_list = result.get("meetings_list", [])
        generic_phrases = ["materi", "minggu", "topik", "sesuai", "seluruh", "panduan", "buku utama"]
        for m in meetings_list:
            ref = (m.get("references", "") or "").strip()
            if ref and ref not in base_references and ref not in agent_refs:
                if not any(p in ref.lower() for p in generic_phrases) and len(ref) > 10:
                    agent_refs.append(ref)
        final_references_list = base_references + agent_refs

        # One RPS per course
        rps_obj = db.query(RPS).filter(RPS.course_id == course.id).first()
        if rps_obj:
            rps_obj.status = "draft"
            rps_obj.draft_content = validated_rps
            rps_obj.cpl_list = parsed_cpl
            rps_obj.cpmk_list = parsed_cpmk
            rps_obj.references_list = final_references_list
            rps_obj.bahan_kajian = final_bahan_kajian
            rps_obj.learning_methods = learning_methods_list
            rps_obj.learning_modality = learning_modality_value
            rps_obj.cpmk_count = len(parsed_cpmk)
            rps_obj.references_count = len(final_references_list)
            rps_obj.updated_at = datetime.now().strftime("%b %Y")
        else:
            rps_obj = RPS(
                id=f"rps-{uuid4().hex[:8]}",
                course_id=course.id,
                status="draft",
                draft_content=validated_rps,
                cpl_list=parsed_cpl,
                cpmk_list=parsed_cpmk,
                references_list=final_references_list,
                bahan_kajian=final_bahan_kajian,
                learning_methods=learning_methods_list,
                learning_modality=learning_modality_value,
                cpmk_count=len(parsed_cpmk),
                references_count=len(final_references_list),
                updated_at=datetime.now().strftime("%b %Y"),
            )
            db.add(rps_obj)
            db.flush()

        # Persist meetings (using the shared helper that uses correct column names)
        primary_ref = user_references_list[0] if user_references_list else ""
        normalized = []
        for m in meetings_list:
            normalized.append(
                {
                    "week": m.get("week", 1),
                    "topic": m.get("topic", "Topik Belum Ditetapkan"),
                    "sub_topic_title": m.get("sub_topic_title", ""),
                    "sub_topic_description": m.get("sub_topic_description", ""),
                    "bahan_kajian_topik": m.get("bahan_kajian_topik", ""),
                    "cpmk": m.get("cpmk", ""),
                    "cpmk_number": m.get("cpmk_number"),
                    "reference_indices": m.get("reference_indices", []),
                    "method": m.get("method", learning_method_preference),
                    "references": (m.get("references") or primary_ref or "Lihat Referensi & Pustaka"),
                    "evaluation": m.get("evaluation", "Tanya Jawab"),
                }
            )
        _save_meetings(
            db,
            rps_obj.id,
            normalized,
            bahan_kajian_options=final_bahan_kajian,
            cpmk_list_len=len(parsed_cpmk),
            references_list_len=len(final_references_list),
            fallback_method=", ".join(learning_methods_list) or learning_method_preference,
        )

        db.commit()
        db.refresh(rps_obj)
        _refresh_compliance(db, rps_obj)
        db.commit()

        return {
            "status": "success",
            "message": "RPS generation completed successfully and saved to DB.",
            "data": {
                "rps_id": rps_obj.id,
                "validated_rps": validated_rps,
                "cpl_list": cpl_list_raw,
                "trend_data": trend_data,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_manual_rps(data: RPSPayload, db: Session = Depends(get_session)):
    course = _get_or_create_course(
        db,
        data.course_name or "",
        data.course_code or "",
        data.sks or 3,
        data.semester or 1,
        data.program_study or "",
    )

    _validate_meetings(
        data.meetings,
        bahan_kajian_options=data.bahan_kajian or [],
        cpmk_list_len=len(data.cpmk_list or []),
        references_list_len=len(data.references_list or []),
    )

    rps_obj = db.query(RPS).filter(RPS.course_id == course.id).first()
    if rps_obj:
        rps_obj.status = "draft"
        rps_obj.cpl_list = data.cpl_list
        rps_obj.cpmk_list = data.cpmk_list
        rps_obj.references_list = data.references_list
        rps_obj.bahan_kajian = data.bahan_kajian
        rps_obj.learning_methods = data.learning_methods
        rps_obj.learning_modality = data.learning_modality or ""
        rps_obj.cpmk_count = len(data.cpmk_list)
        rps_obj.references_count = len(data.references_list)
        rps_obj.updated_at = datetime.now().strftime("%b %Y")
    else:
        rps_obj = RPS(
            id=f"rps-{uuid4().hex[:8]}",
            course_id=course.id,
            status="draft",
            cpl_list=data.cpl_list,
            cpmk_list=data.cpmk_list,
            references_list=data.references_list,
            bahan_kajian=data.bahan_kajian,
            learning_methods=data.learning_methods,
            learning_modality=data.learning_modality or "",
            cpmk_count=len(data.cpmk_list),
            references_count=len(data.references_list),
            updated_at=datetime.now().strftime("%b %Y"),
        )
        db.add(rps_obj)
        db.flush()

    fallback_method = ", ".join(data.learning_methods or []) or ""
    _save_meetings(
        db,
        rps_obj.id,
        data.meetings,
        bahan_kajian_options=data.bahan_kajian or [],
        cpmk_list_len=len(data.cpmk_list or []),
        references_list_len=len(data.references_list or []),
        fallback_method=fallback_method,
    )
    db.commit()
    _refresh_compliance(db, rps_obj)
    db.commit()
    return {"status": "success", "rps_id": rps_obj.id}


@router.put("/{rps_id}")
def update_rps(rps_id: str, data: RPSPayload, db: Session = Depends(get_session)):
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")

    _validate_meetings(
        data.meetings,
        bahan_kajian_options=data.bahan_kajian or [],
        cpmk_list_len=len(data.cpmk_list or []),
        references_list_len=len(data.references_list or []),
    )

    rps.cpl_list = data.cpl_list
    rps.cpmk_list = data.cpmk_list
    rps.references_list = data.references_list
    rps.bahan_kajian = data.bahan_kajian
    rps.learning_methods = data.learning_methods
    rps.learning_modality = data.learning_modality or ""
    rps.cpmk_count = len(data.cpmk_list)
    rps.references_count = len(data.references_list)
    rps.updated_at = datetime.now().strftime("%b %Y")

    fallback_method = ", ".join(data.learning_methods or []) or ""
    _save_meetings(
        db,
        rps.id,
        data.meetings,
        bahan_kajian_options=data.bahan_kajian or [],
        cpmk_list_len=len(data.cpmk_list or []),
        references_list_len=len(data.references_list or []),
        fallback_method=fallback_method,
    )
    db.commit()
    _refresh_compliance(db, rps)
    db.commit()
    return {"status": "success"}


@router.post("/{rps_id}/approve")
def approve_rps(rps_id: str, db: Session = Depends(get_session)):
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    rps.status = "validated"
    rps.compliance_score = 100.0
    rps.issues_count = 0
    db.commit()
    return {"status": "success"}


@router.delete("/{rps_id}")
def delete_rps(rps_id: str, db: Session = Depends(get_session)):
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    db.query(RPSMeeting).filter(RPSMeeting.rps_id == rps.id).delete()
    db.delete(rps)
    db.commit()
    return {"status": "success", "message": "RPS deleted successfully"}


# ---------------------------------------------------------------------------
# Feedback / Regeneration endpoints
# ---------------------------------------------------------------------------


class FeedbackPayload(BaseModel):
    feedback: str = ""


# ---------------------------------------------------------------------------
# Deterministic SN-DIKTI compliance report
# ---------------------------------------------------------------------------


_COMPLIANCE_CACHE: dict[str, tuple[float, str | None, dict]] = {}
_COMPLIANCE_TTL_SECONDS = 60.0


def _compliance_cache_lookup(rps_id: str, updated_at: str | None) -> dict | None:
    import time

    entry = _COMPLIANCE_CACHE.get(rps_id)
    if not entry:
        return None
    cached_at, cached_updated_at, payload = entry
    if cached_updated_at != updated_at:
        return None
    if time.time() - cached_at > _COMPLIANCE_TTL_SECONDS:
        return None
    return payload


def _compliance_cache_store(rps_id: str, updated_at: str | None, payload: dict) -> None:
    import time

    _COMPLIANCE_CACHE[rps_id] = (time.time(), updated_at, payload)


def _criterion_row_dict(row) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "regulation_ref": row.regulation_ref,
        "severity": row.severity,
        "scope": row.scope,
        "weight": row.weight,
        "contributed_weight": row.contributed_weight,
        "passed": row.passed,
        "detail": row.detail,
        "field": row.field,
        "group": row.group,
        "target_week": row.target_week,
        "suggested_value": row.suggested_value,
    }


def _group_dict(group) -> dict:
    return {
        "group": group.group,
        "passed": group.passed,
        "total": group.total,
        "earned_weight": group.earned_weight,
        "total_weight": group.total_weight,
    }


@router.get("/{rps_id}/compliance")
def get_compliance(rps_id: str, db: Session = Depends(get_session)):
    """Deterministic SN-DIKTI compliance report.

    Pure execution of the catalog in `app.core.sndikti_catalog` — no LLM
    calls. Cached in-process for 60s per `(rps_id, rps.updated_at)`.
    """
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")

    cached = _compliance_cache_lookup(rps_id, rps.updated_at)
    if cached is not None:
        return cached

    course = db.query(Course).filter(Course.id == rps.course_id).first()
    meetings = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps.id)
        .order_by(RPSMeeting.week_number)
        .all()
    )
    report = run_catalog(rps, meetings, course=course)
    payload = {
        "score": report.score,
        "total_weight": report.total_weight,
        "earned_weight": report.earned_weight,
        "regulation_summary": report.regulation_summary,
        "criteria": [_criterion_row_dict(r) for r in report.criteria],
        "groups": [_group_dict(g) for g in report.groups],
    }
    _compliance_cache_store(rps_id, rps.updated_at, payload)
    return payload


# ---------------------------------------------------------------------------
# Review agent: review run + findings list + apply / dismiss / reopen
# ---------------------------------------------------------------------------


import threading
import time

from app.agents.rps_review_agent import build_review_graph
from app.models.rps_finding import RPSFinding


_REVIEW_LOCKS: dict[str, threading.Lock] = {}
_REVIEW_LAST_RUN: dict[str, float] = {}
_REVIEW_COOLDOWN_SECONDS = 30.0


def _get_review_lock(rps_id: str) -> threading.Lock:
    lock = _REVIEW_LOCKS.get(rps_id)
    if lock is None:
        lock = threading.Lock()
        _REVIEW_LOCKS[rps_id] = lock
    return lock


def _finding_to_dict(f: RPSFinding) -> dict:
    return {
        "id": f.id,
        "rps_id": f.rps_id,
        "severity": f.severity,
        "scope": f.scope,
        "target_week": f.target_week,
        "category": f.category,
        "field": f.field,
        "issue": f.issue,
        "suggested_fix": f.suggested_fix,
        "suggested_value": f.suggested_value,
        "regulation_ref": f.regulation_ref,
        "criterion_id": f.criterion_id,
        "dismissed": f.dismissed,
        "applied": f.applied,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "last_seen_at": f.last_seen_at.isoformat() if f.last_seen_at else None,
    }


def _summary_counts(findings: list[RPSFinding]) -> dict:
    severity_counts = {"critical": 0, "warning": 0, "info": 0}
    category_counts: dict[str, int] = {}
    for f in findings:
        if f.dismissed or f.applied:
            continue
        severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
        category_counts[f.category] = category_counts.get(f.category, 0) + 1
    return {"severity": severity_counts, "category": category_counts}


@router.post("/{rps_id}/review")
def run_review(rps_id: str, db: Session = Depends(get_session)):
    """Run the read-only review agent and persist the resulting Findings.

    Cooldown: 30 seconds per RPS (in-process).
    Concurrency: a second concurrent call for the same RPS gets HTTP 409.
    """
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")

    now = time.time()
    last = _REVIEW_LAST_RUN.get(rps_id, 0.0)
    if now - last < _REVIEW_COOLDOWN_SECONDS:
        retry_in = int(_REVIEW_COOLDOWN_SECONDS - (now - last)) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Tunggu {retry_in}s sebelum menjalankan review ulang.",
        )

    lock = _get_review_lock(rps_id)
    if not lock.acquire(blocking=False):
        raise HTTPException(
            status_code=409, detail="Review sudah berjalan untuk RPS ini."
        )

    try:
        course = db.query(Course).filter(Course.id == rps.course_id).first()
        meetings = (
            db.query(RPSMeeting)
            .filter(RPSMeeting.rps_id == rps.id)
            .order_by(RPSMeeting.week_number)
            .all()
        )

        graph = build_review_graph()
        try:
            result = graph.invoke(
                {
                    "rps": rps,
                    "course": course,
                    "meetings": meetings,
                    "findings": [],
                    "messages": [],
                }
            )
        except Exception as e:  # pragma: no cover
            log.exception("[review] agent failed: %s", e)
            raise HTTPException(status_code=503, detail=f"LLM provider tidak tersedia: {e}")

        new_findings = result.get("findings") or []
        new_by_hash = {f["issue_hash"]: f for f in new_findings}

        # Upsert: existing rows that match a new hash get last_seen_at bumped;
        # active rows whose hash didn't reappear get pruned; dismissed rows
        # are preserved across runs (matched ones bump last_seen_at).
        existing = (
            db.query(RPSFinding).filter(RPSFinding.rps_id == rps_id).all()
        )
        existing_by_hash = {e.issue_hash: e for e in existing}

        from datetime import datetime

        kept_hashes: set[str] = set()
        for hash_, payload in new_by_hash.items():
            row = existing_by_hash.get(hash_)
            if row:
                row.last_seen_at = datetime.utcnow()
                # Refresh fields the agent may have re-described
                row.issue = payload["issue"]
                row.suggested_fix = payload.get("suggested_fix")
                row.suggested_value = payload.get("suggested_value")
                row.severity = payload["severity"]
                row.regulation_ref = payload.get("regulation_ref")
                row.criterion_id = payload.get("criterion_id")
            else:
                row = RPSFinding(
                    id=payload["id"],
                    rps_id=rps_id,
                    severity=payload["severity"],
                    scope=payload["scope"],
                    target_week=payload.get("target_week"),
                    category=payload["category"],
                    field=payload.get("field"),
                    issue=payload["issue"],
                    suggested_fix=payload.get("suggested_fix"),
                    suggested_value=payload.get("suggested_value"),
                    issue_hash=hash_,
                    regulation_ref=payload.get("regulation_ref"),
                    criterion_id=payload.get("criterion_id"),
                    dismissed=False,
                    applied=False,
                )
                db.add(row)
            kept_hashes.add(hash_)

        # Prune old active findings that no longer apply
        for row in existing:
            if row.issue_hash in kept_hashes:
                continue
            if row.dismissed or row.applied:
                continue
            db.delete(row)

        db.commit()
        _REVIEW_LAST_RUN[rps_id] = time.time()

        active_rows = (
            db.query(RPSFinding)
            .filter(RPSFinding.rps_id == rps_id, RPSFinding.dismissed.is_(False))
            .order_by(RPSFinding.severity.asc(), RPSFinding.category.asc())
            .all()
        )

        return {
            "status": "success",
            "last_reviewed_at": datetime.utcnow().isoformat(),
            "summary_counts": _summary_counts(active_rows),
            "findings": [_finding_to_dict(r) for r in active_rows],
        }
    finally:
        lock.release()


@router.get("/{rps_id}/findings")
def list_findings(
    rps_id: str,
    include_dismissed: bool = False,
    db: Session = Depends(get_session),
):
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    q = db.query(RPSFinding).filter(RPSFinding.rps_id == rps_id)
    if not include_dismissed:
        q = q.filter(RPSFinding.dismissed.is_(False))
    rows = q.order_by(
        RPSFinding.severity.asc(),
        RPSFinding.category.asc(),
        RPSFinding.last_seen_at.desc(),
    ).all()
    last_review = max((r.last_seen_at for r in rows), default=None)
    return {
        "findings": [_finding_to_dict(r) for r in rows],
        "summary_counts": _summary_counts(
            [r for r in rows if not r.dismissed]
        ),
        "last_reviewed_at": last_review.isoformat() if last_review else None,
    }


@router.post("/{rps_id}/findings/{finding_id}/apply")
def apply_finding(
    rps_id: str, finding_id: str, db: Session = Depends(get_session)
):
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    finding = (
        db.query(RPSFinding)
        .filter(RPSFinding.id == finding_id, RPSFinding.rps_id == rps_id)
        .first()
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    if finding.dismissed:
        raise HTTPException(status_code=400, detail="Finding sudah ditutup; buka kembali sebelum menerapkan.")
    if finding.applied:
        raise HTTPException(status_code=400, detail="Finding sudah diterapkan sebelumnya.")
    if finding.suggested_value is None:
        raise HTTPException(
            status_code=400,
            detail="Saran ini tidak punya nilai siap-pakai; silakan terapkan manual.",
        )

    field = finding.field or ""
    suggested_value = finding.suggested_value

    try:
        if finding.scope == "per_week":
            if finding.target_week is None:
                raise HTTPException(status_code=400, detail="Finding per_week tanpa target_week.")
            meeting = (
                db.query(RPSMeeting)
                .filter(
                    RPSMeeting.rps_id == rps_id,
                    RPSMeeting.week_number == finding.target_week,
                )
                .first()
            )
            if not meeting:
                raise HTTPException(status_code=404, detail="Meeting target tidak ditemukan.")
            # Map catalog field names back to ORM columns. The catalog uses
            # `meetings.X` convention; strip the prefix.
            column = field.split(".", 1)[1] if field.startswith("meetings.") else field
            if not hasattr(meeting, column):
                raise HTTPException(status_code=400, detail=f"Field '{column}' tidak dikenal di RPSMeeting.")
            setattr(meeting, column, suggested_value)
        else:
            # cross_cutting → write to the RPS-level field
            column = field
            if not hasattr(rps, column):
                raise HTTPException(status_code=400, detail=f"Field '{column}' tidak dikenal di RPS.")
            setattr(rps, column, suggested_value)

        finding.applied = True
        db.commit()
        # Recompute compliance after the mutation
        _refresh_compliance(db, rps)
        db.commit()
        return {
            "status": "success",
            "finding": _finding_to_dict(finding),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{rps_id}/findings/{finding_id}/dismiss")
def dismiss_finding(
    rps_id: str, finding_id: str, db: Session = Depends(get_session)
):
    finding = (
        db.query(RPSFinding)
        .filter(RPSFinding.id == finding_id, RPSFinding.rps_id == rps_id)
        .first()
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.dismissed = True
    db.commit()
    return {"status": "success", "finding": _finding_to_dict(finding)}


@router.post("/{rps_id}/findings/{finding_id}/reopen")
def reopen_finding(
    rps_id: str, finding_id: str, db: Session = Depends(get_session)
):
    finding = (
        db.query(RPSFinding)
        .filter(RPSFinding.id == finding_id, RPSFinding.rps_id == rps_id)
        .first()
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.dismissed = False
    db.commit()
    return {"status": "success", "finding": _finding_to_dict(finding)}


# ---------------------------------------------------------------------------
# Fill Missing — patch only blank fields, never overwrite the dosen's input
# ---------------------------------------------------------------------------


_FILL_TRACKED_FIELDS = (
    "bahan_kajian_topik",
    "sub_topic_title",
    "sub_topic_description",
    "cpmk_number",
    "reference_indices",
    "learning_method",
    "evaluation_method",
)


def _is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return False


@router.post("/{rps_id}/fill-missing")
def fill_missing(rps_id: str, db: Session = Depends(get_session)):
    """Run a focused agent pass that fills ONLY blank meeting fields.

    Different from `regenerate_*` endpoints which overwrite content. This
    one is non-destructive: every field the dosen has typed is preserved
    verbatim. Skips exam weeks (Modul 8 and 16).
    """
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    if rps.status == "validated":
        raise HTTPException(status_code=400, detail="RPS sudah disetujui, tidak bisa diisi otomatis.")

    course = db.query(Course).filter(Course.id == rps.course_id).first()
    meetings = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps.id)
        .order_by(RPSMeeting.week_number)
        .all()
    )

    # Build the blanks map: per non-exam meeting, which tracked fields are blank.
    blanks_per_meeting: dict[int, list[str]] = {}
    for m in meetings:
        if is_exam_week(m.week_number):
            continue
        blanks: list[str] = []
        for field_name in _FILL_TRACKED_FIELDS:
            if _is_blank(getattr(m, field_name, None)):
                blanks.append(field_name)
        if blanks:
            blanks_per_meeting[m.week_number] = blanks

    if not blanks_per_meeting:
        return {"status": "success", "patched": [], "message": "Tidak ada field kosong."}

    # Compose the prompt. Give the LLM the full RPS context plus a precise
    # list of which fields per meeting are missing — and a strict rule never
    # to fill anything else.
    bahan_kajian_text = "\n".join(f"- {b}" for b in (rps.bahan_kajian or [])) or "(kosong)"
    cpmk_text = "\n".join(
        f"{i + 1}. {c[:200]}" for i, c in enumerate(rps.cpmk_list or [])
    ) or "(kosong)"
    refs_text = "\n".join(
        f"{i + 1}. {r[:200]}" for i, r in enumerate(rps.references_list or [])
    ) or "(kosong)"

    methods_pool = ", ".join(rps.learning_methods or []) or "Ceramah & Diskusi"

    meetings_brief = []
    for m in meetings:
        if is_exam_week(m.week_number):
            continue
        meetings_brief.append(
            {
                "week": m.week_number,
                "current": {
                    "bahan_kajian_topik": m.bahan_kajian_topik or "",
                    "sub_topic_title": m.sub_topic_title or "",
                    "sub_topic_description": m.sub_topic_description or "",
                    "cpmk_number": m.cpmk_number,
                    "reference_indices": m.reference_indices or [],
                    "learning_method": m.learning_method or "",
                    "evaluation_method": m.evaluation_method or "",
                },
                "missing_fields": blanks_per_meeting.get(m.week_number, []),
            }
        )

    prompt = f"""
    Anda asisten kurikulum. Tugas Anda HANYA mengisi field yang kosong pada
    pertemuan RPS — JANGAN ubah field yang sudah berisi nilai.

    Mata Kuliah: {course.name if course else '-'} ({course.sks if course else 3} SKS)

    Bahan Kajian (HARUS dipakai verbatim untuk `bahan_kajian_topik`):
    {bahan_kajian_text}

    Daftar CPMK (gunakan ANGKA untuk `cpmk_number`):
    {cpmk_text}

    Daftar Referensi bernomor (gunakan ANGKA dalam `reference_indices`):
    {refs_text}

    Metode pembelajaran yang dipilih dosen (pakai kombinasi dari daftar ini): {methods_pool}

    Untuk setiap pertemuan di bawah, isi HANYA field yang ada di `missing_fields`.
    JANGAN sertakan field yang sudah terisi.

    Pertemuan:
    {json.dumps(meetings_brief, ensure_ascii=False)}

    Output JSON ARRAY PERSIS:
    [
      {{
        "week": 1,
        "fills": {{ "<field>": <value>, ... }}
      }}
    ]
    Hanya outputkan JSON array.
    """

    try:
        from app.core.llm import get_llm

        llm = get_llm("complex")
        resp = llm.invoke(prompt)
        text = (getattr(resp, "content", "") or "").replace("```json", "").replace("```", "").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start < 0 or end <= start:
            raise ValueError("LLM tidak mengembalikan JSON array.")
        parsed = json.loads(text[start:end])
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM gagal: {e}")

    cpmk_len = len(rps.cpmk_list or [])
    refs_len = len(rps.references_list or [])
    bahan_kajian_options = list(rps.bahan_kajian or [])

    patched: list[dict] = []
    by_week = {m.week_number: m for m in meetings}

    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        try:
            week = int(entry.get("week"))
        except (TypeError, ValueError):
            continue
        if week not in blanks_per_meeting:
            continue  # the dosen had nothing blank here
        meeting = by_week.get(week)
        if not meeting:
            continue
        allowed_fields = set(blanks_per_meeting[week])
        fills = entry.get("fills") or {}

        for field_name, raw_value in fills.items():
            if field_name not in allowed_fields:
                continue  # skip any field that was already filled

            if field_name == "bahan_kajian_topik":
                value = coerce_bahan_kajian(raw_value, bahan_kajian_options)
                if not value:
                    continue
            elif field_name == "cpmk_number":
                value = coerce_cpmk_number(raw_value, cpmk_len)
                if value is None:
                    continue
            elif field_name == "reference_indices":
                indices, _ = coerce_reference_indices(raw_value, refs_len)
                if not indices:
                    continue
                value = indices
            else:
                value = (str(raw_value or "")).strip()
                if not value:
                    continue

            setattr(meeting, field_name, value)
            patched.append({"week": week, "field": field_name, "value": value})

    db.commit()
    _refresh_compliance(db, rps)
    db.commit()

    return {"status": "success", "patched": patched}


@router.post("/{rps_id}/feedback")
def save_rps_feedback(
    rps_id: str,
    payload: FeedbackPayload,
    db: Session = Depends(get_session),
):
    """Persist overall feedback without regenerating."""
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    rps.feedback = payload.feedback
    db.commit()
    return {"status": "success"}


@router.post("/{rps_id}/regenerate")
def regenerate_rps(
    rps_id: str,
    payload: FeedbackPayload,
    db: Session = Depends(get_session),
):
    """Re-run the RPS generator on an existing draft, biased by the user's feedback."""
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    if rps.status == "validated":
        raise HTTPException(status_code=400, detail="RPS sudah disetujui, tidak bisa diregenerasi.")

    course = db.query(Course).filter(Course.id == rps.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found for this RPS")

    feedback = (payload.feedback or "").strip()
    references_text = "\n".join(rps.references_list or [])
    if feedback:
        references_text += "\n--- Catatan Revisi dari Dosen ---\n" + feedback

    graph = build_curriculum_graph()
    initial_state = {
        "course_name": course.name,
        "course_code": course.code,
        "sks": course.sks,
        "program_study": course.program_study or "",
        "semester": course.semester,
        "cpl_list": [],
        "sndikti_rules": "",
        "trend_data": "",
        "references": references_text,
        "bahan_kajian": rps.bahan_kajian or [],
        "learning_methods": rps.learning_methods or [],
        "learning_modality": rps.learning_modality or "",
        "draft_rps": "",
        "validated_rps": "",
        "meetings_list": [],
        "messages": [],
    }

    try:
        result = graph.invoke(initial_state)

        # Reuse the same parsing logic as /generate
        cpl_raw = result.get("cpl_list") or []
        parsed_cpl, parsed_cpmk = [], []
        for item in cpl_raw:
            item = (item or "").strip()
            if not item:
                continue
            if item.startswith("CPL:"):
                parsed_cpl.append(item[4:].strip())
            elif item.startswith("CPMK:"):
                parsed_cpmk.append(item[5:].strip())
            else:
                parsed_cpl.append(item)

        meetings_list = result.get("meetings_list", [])

        # Update RPS with the new draft. Existing references stay untouched.
        rps.cpl_list = parsed_cpl or rps.cpl_list
        rps.cpmk_list = parsed_cpmk or rps.cpmk_list
        rps.cpmk_count = len(rps.cpmk_list or [])
        rps.references_count = len(rps.references_list or [])
        rps.feedback = feedback  # Keep the latest feedback alongside the new draft
        rps.status = "draft"
        rps.updated_at = datetime.now().strftime("%b %Y")

        primary_ref = (rps.references_list or [""])[0]
        normalized = []
        for m in meetings_list:
            normalized.append(
                {
                    "week": m.get("week", 1),
                    "topic": m.get("topic", "Topik Belum Ditetapkan"),
                    "sub_topic_title": m.get("sub_topic_title", ""),
                    "sub_topic_description": m.get("sub_topic_description", ""),
                    "bahan_kajian_topik": m.get("bahan_kajian_topik", ""),
                    "cpmk": m.get("cpmk", ""),
                    "cpmk_number": m.get("cpmk_number"),
                    "reference_indices": m.get("reference_indices", []),
                    "method": m.get("method", "Ceramah & Diskusi"),
                    "references": (m.get("references") or primary_ref or "Lihat Referensi & Pustaka"),
                    "evaluation": m.get("evaluation", "Tanya Jawab"),
                }
            )
        if normalized:
            _save_meetings(
                db,
                rps.id,
                normalized,
                bahan_kajian_options=rps.bahan_kajian or [],
                cpmk_list_len=len(rps.cpmk_list or []),
                references_list_len=len(rps.references_list or []),
                fallback_method=", ".join(rps.learning_methods or []) or "Ceramah & Diskusi",
            )
        db.commit()
        _refresh_compliance(db, rps)
        db.commit()
        return {"status": "success", "rps_id": rps.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class WeekFeedbackPayload(BaseModel):
    feedback: str = ""


@router.post("/{rps_id}/meetings/{week}/feedback")
def save_week_feedback(
    rps_id: str,
    week: int,
    payload: WeekFeedbackPayload,
    db: Session = Depends(get_session),
):
    meeting = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps_id, RPSMeeting.week_number == week)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting.feedback = payload.feedback
    db.commit()
    return {"status": "success"}


@router.post("/{rps_id}/meetings/{week}/regenerate")
def regenerate_week(
    rps_id: str,
    week: int,
    payload: WeekFeedbackPayload,
    db: Session = Depends(get_session),
):
    """Regenerate a single meeting using the LLM, biased by user feedback."""
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")
    if rps.status == "validated":
        raise HTTPException(status_code=400, detail="RPS sudah disetujui, tidak bisa diregenerasi.")

    course = db.query(Course).filter(Course.id == rps.course_id).first()
    meeting = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps_id, RPSMeeting.week_number == week)
        .first()
    )
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    feedback = (payload.feedback or "").strip()

    # Build a focused prompt using the surrounding context for continuity
    prev_meetings = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps_id, RPSMeeting.week_number != week)
        .order_by(RPSMeeting.week_number)
        .all()
    )
    context_lines = "\n".join(
        f"- Minggu {m.week_number}: {(m.sub_topic_title or m.topic or '').strip()}"
        f" (CPMK: {m.cpmk_number if m.cpmk_number is not None else '-'},"
        f" Bahan: {m.bahan_kajian_topik or '-'})"
        for m in prev_meetings
    )

    cpmk_text = "\n".join(
        [f"{i + 1}. {c}" for i, c in enumerate(rps.cpmk_list or [])]
    )

    references_text = "\n".join(
        f"{i + 1}. {r}" for i, r in enumerate(rps.references_list or [])
    )

    bahan_kajian_text = (
        "\n".join(f'- "{b}"' for b in (rps.bahan_kajian or []))
        or "(belum ditentukan)"
    )

    prompt = f"""
    Anda adalah asisten kurikulum. Revisi 1 pertemuan RPS berdasarkan feedback dosen.
    Gunakan format institusi: dua kolom topik (Bahan Kajian/Topik tingkat tinggi
    + Sub-Topik spesifik per minggu), satu nomor CPMK, dan kutipan referensi
    sebagai daftar angka.

    Mata Kuliah: {course.name if course else ''} ({course.code if course else ''})
    SKS: {course.sks if course else 3}

    CPMK yang tersedia (gunakan ANGKA untuk merujuk):
    {cpmk_text}

    Bahan Kajian/Topik yang tersedia (HARUS dipakai verbatim):
    {bahan_kajian_text}

    Daftar Referensi bernomor (kutip dengan ANGKA):
    {references_text}

    Pertemuan lain (untuk konteks, JANGAN duplikasi topiknya):
    {context_lines}

    Konten pertemuan minggu {week} saat ini:
    - Bahan Kajian/Topik: {meeting.bahan_kajian_topik or '(kosong)'}
    - Sub-Topik: {meeting.sub_topic_title or '(kosong)'}: {meeting.sub_topic_description or ''}
    - CPMK: {meeting.cpmk_number if meeting.cpmk_number is not None else '(kosong)'}
    - Referensi: {meeting.reference_indices or '(kosong)'}
    - Metode: {meeting.learning_method}
    - Evaluasi: {meeting.evaluation_method}

    Feedback dari dosen yang harus diterapkan:
    \"\"\"{feedback or 'Perbaiki kualitas konten agar lebih sesuai SN-DIKTI dan sejalan dengan CPMK.'}\"\"\"

    Output HARUS JSON murni dengan struktur:
    {{
        "week": {week},
        "bahan_kajian_topik": "...",
        "sub_topic_title": "...",
        "sub_topic_description": "...",
        "cpmk_number": 1,
        "reference_indices": [1, 3],
        "method": "...",
        "evaluation": "..."
    }}

    Hanya outputkan JSON, tanpa markdown.
    """

    try:
        from app.core.llm import get_llm

        llm = get_llm("complex")
        response = llm.invoke(prompt)
        text = (response.content or "").replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start < 0 or end <= start:
            raise ValueError("LLM tidak mengembalikan JSON yang valid.")
        new_meeting = json.loads(text[start:end])

        bahan_topik = coerce_bahan_kajian(
            new_meeting.get("bahan_kajian_topik", ""), rps.bahan_kajian or []
        )
        cpmk_num = coerce_cpmk_number(
            new_meeting.get("cpmk_number"), len(rps.cpmk_list or [])
        )
        ref_indices, had_invalid = coerce_reference_indices(
            new_meeting.get("reference_indices"), len(rps.references_list or [])
        )

        meeting.bahan_kajian_topik = bahan_topik
        meeting.sub_topic_title = str(
            new_meeting.get("sub_topic_title", meeting.sub_topic_title or "")
        )[:500]
        meeting.sub_topic_description = str(
            new_meeting.get("sub_topic_description", meeting.sub_topic_description or "")
        )
        meeting.cpmk_number = cpmk_num
        meeting.reference_indices = ref_indices

        # Update legacy strings as fallback
        legacy_topic = (
            f"{meeting.sub_topic_title}: {meeting.sub_topic_description}".strip(": ")
            if meeting.sub_topic_description
            else (meeting.sub_topic_title or "")
        )
        meeting.topic = legacy_topic[:500]
        meeting.cpmk = f"CPMK-{cpmk_num}" if cpmk_num else ""
        meeting.references = ", ".join(str(i) for i in ref_indices)[:255]

        meeting.learning_method = str(
            new_meeting.get("method", meeting.learning_method)
        )[:255]
        meeting.evaluation_method = str(
            new_meeting.get("evaluation", meeting.evaluation_method)
        )[:255]
        meeting.feedback = feedback
        if had_invalid or (cpmk_num is None and (rps.cpmk_list or [])):
            meeting.status = "needs_review"
            meeting.status_text = "Perlu Review"
        rps.updated_at = datetime.now().strftime("%b %Y")
        db.commit()
        return {"status": "success", "meeting": new_meeting}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
