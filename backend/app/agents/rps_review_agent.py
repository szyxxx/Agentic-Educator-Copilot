"""Read-only review agent for RPS drafts.

Builds a list of structured Findings about an RPS without mutating any
database row. Findings drive the FindingsPanel UI; the dosen decides what
to apply, dismiss, or ignore.

Lenses:
    - sndikti_compliance: deterministic catalog from `app.core.sndikti_catalog`.
    - cpmk_alignment / cpl_alignment: LLM evaluates whether each meeting's
      `cpmk_number` is the most appropriate among the available CPMKs and
      whether any CPL is orphaned.
    - content_quality: deterministic blacklist + length checks; LLM
      drafts candidate `sub_topic_description` text when descriptions are
      blank or too short.
    - continuity: single LLM call over the whole 16-meeting sequence to
      catch abrupt jumps and missing scaffolding.
"""

from __future__ import annotations

import hashlib
import json
import logging
import operator
import re
from typing import Annotated, Any, List, TypedDict
from uuid import uuid4

from langgraph.graph import END, StateGraph

from app.core.llm import get_llm
from app.core.rps_constants import is_exam_week
from app.core.sndikti_catalog import run_catalog

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class ReviewState(TypedDict, total=False):
    rps: Any                # ORM row, attribute-accessed only
    course: Any             # ORM row, used by sndikti node
    meetings: list          # list of ORM rows, ordered by week_number
    findings: Annotated[list, operator.add]
    messages: Annotated[list, operator.add]


# Severity is assigned in code, not by the LLM.
PLACEHOLDER_PATTERNS = [
    "topik belum ditetapkan",
    "tbd",
    "to be determined",
    "materi minggu",
    "lihat slide",
    "lihat materi",
    "akan ditentukan",
    "n/a",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_for_hash(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _issue_hash(scope: str, target_week, field: str | None, category: str, issue: str) -> str:
    raw = f"{scope}|{target_week or ''}|{field or ''}|{category}|{_normalize_for_hash(issue)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _make_finding(
    *,
    severity: str,
    scope: str,
    category: str,
    issue: str,
    target_week: int | None = None,
    field: str | None = None,
    suggested_fix: str | None = None,
    suggested_value: Any = None,
    regulation_ref: str | None = None,
    criterion_id: str | None = None,
) -> dict:
    return {
        "id": f"rf-{uuid4().hex[:10]}",
        "severity": severity,
        "scope": scope,
        "category": category,
        "issue": issue,
        "target_week": target_week,
        "field": field,
        "suggested_fix": suggested_fix,
        "suggested_value": suggested_value,
        "regulation_ref": regulation_ref,
        "criterion_id": criterion_id,
        "issue_hash": _issue_hash(scope, target_week, field, category, issue),
    }


def _safe_llm_json(prompt: str, *, expect: str = "array") -> Any:
    """Invoke the configured LLM and parse the first JSON object/array we find.

    `expect` is `"array"` or `"object"`. Returns `None` on failure so the
    caller can fall back gracefully — the review agent never blocks on a
    single node failing.
    """
    try:
        llm = get_llm("complex")
        resp = llm.invoke(prompt)
        text = (getattr(resp, "content", "") or "").replace("```json", "").replace("```", "").strip()
        if expect == "array":
            start = text.find("[")
            end = text.rfind("]") + 1
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
        if start < 0 or end <= start:
            return None
        return json.loads(text[start:end])
    except Exception as e:  # pragma: no cover
        log.warning("[review] LLM JSON parse failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def sndikti_compliance_node(state: ReviewState):
    """Re-run the catalog and convert each FAILED criterion into a Finding."""
    rps = state["rps"]
    meetings = state.get("meetings") or []
    course = state.get("course")
    report = run_catalog(rps, meetings, course=course)

    findings: list[dict] = []
    for row in report.criteria:
        if row.passed:
            continue
        findings.append(
            _make_finding(
                severity=row.severity,
                scope="per_week" if row.scope == "per_week" else "cross_cutting",
                category="sndikti_compliance",
                issue=f"{row.title}: {row.detail}" if row.detail else row.title,
                target_week=row.target_week,
                field=row.field,
                suggested_value=row.suggested_value,
                regulation_ref=row.regulation_ref,
                criterion_id=row.id,
            )
        )
    return {"findings": findings}


def content_quality_node(state: ReviewState):
    """Flag vague titles and blank descriptions; ask LLM for candidate descriptions."""
    rps = state["rps"]
    meetings = [m for m in (state.get("meetings") or []) if not is_exam_week(m.week_number)]

    findings: list[dict] = []

    # Deterministic title checks
    for m in meetings:
        title = (m.sub_topic_title or "").strip()
        title_lower = title.lower()
        is_blank = not title
        too_short = bool(title) and len(title.split()) < 4
        is_placeholder = any(p in title_lower for p in PLACEHOLDER_PATTERNS)
        if is_blank or too_short or is_placeholder:
            reason = (
                "kosong"
                if is_blank
                else "terlalu pendek (< 4 kata)"
                if too_short
                else "berisi placeholder"
            )
            findings.append(
                _make_finding(
                    severity="warning",
                    scope="per_week",
                    category="content_quality",
                    issue=f"Judul Sub-Topik {reason} di Modul {m.week_number}.",
                    target_week=m.week_number,
                    field="sub_topic_title",
                    suggested_fix="Tulis judul yang ringkas tapi spesifik (4–10 kata).",
                )
            )

    # Description checks — collect blanks and ask LLM in one batch for candidates
    blank_desc_meetings: list[dict] = []
    for m in meetings:
        desc = (m.sub_topic_description or "").strip()
        if not desc or len(desc.split()) < 10:
            blank_desc_meetings.append(
                {
                    "week": m.week_number,
                    "title": m.sub_topic_title or "",
                    "bahan_kajian_topik": m.bahan_kajian_topik or "",
                    "cpmk_number": m.cpmk_number,
                    "current_description": desc,
                }
            )

    if blank_desc_meetings:
        cpmk_brief = "\n".join(
            f"{i + 1}. {c[:160]}" for i, c in enumerate(rps.cpmk_list or [])
        ) or "(belum ada)"
        prompt = f"""
        Anda asisten kurikulum. Untuk tiap pertemuan berikut, draf satu paragraf deskripsi
        Sub-Topik (40–80 kata, bahasa Indonesia formal) yang selaras dengan judulnya, Bahan Kajian,
        dan CPMK terkait. Ringkas, konkret, hindari frasa generik.

        Daftar CPMK (rujukan ANGKA):
        {cpmk_brief}

        Pertemuan:
        {json.dumps(blank_desc_meetings, ensure_ascii=False)}

        Output JSON array PERSIS bentuk:
        [{{"week": 1, "description": "..."}}]
        Hanya JSON array.
        """
        parsed = _safe_llm_json(prompt, expect="array") or []
        suggestions = {
            int(item.get("week", 0)): str(item.get("description", "")).strip()
            for item in parsed
            if isinstance(item, dict) and item.get("week")
        }
        for entry in blank_desc_meetings:
            week = entry["week"]
            suggestion = suggestions.get(week, "")
            findings.append(
                _make_finding(
                    severity="info",
                    scope="per_week",
                    category="content_quality",
                    issue=f"Deskripsi Sub-Topik tipis di Modul {week}.",
                    target_week=week,
                    field="sub_topic_description",
                    suggested_fix=(
                        "AI menyarankan paragraf di samping. Sesuaikan sebelum menerapkan."
                    ),
                    suggested_value=suggestion or None,
                )
            )
    return {"findings": findings}


def cpl_cpmk_alignment_node(state: ReviewState):
    """LLM check: is each meeting's cpmk_number the best fit, and any orphan CPL?"""
    rps = state["rps"]
    cpl = [c for c in (rps.cpl_list or []) if (c or "").strip()]
    cpmk = [c for c in (rps.cpmk_list or []) if (c or "").strip()]
    if not cpl or not cpmk:
        return {"findings": []}

    meetings = [
        {
            "week": m.week_number,
            "title": (m.sub_topic_title or "").strip(),
            "description": (m.sub_topic_description or "").strip()[:400],
            "cpmk_number": m.cpmk_number,
        }
        for m in (state.get("meetings") or [])
        if not is_exam_week(m.week_number)
        and (m.sub_topic_title or "").strip()
        and m.cpmk_number is not None
    ]
    if not meetings:
        return {"findings": []}

    cpl_text = "\n".join(f"- CPL-{i + 1}: {c[:200]}" for i, c in enumerate(cpl))
    cpmk_text = "\n".join(f"- {i + 1}: {c[:200]}" for i, c in enumerate(cpmk))

    prompt = f"""
    Tinjau pemetaan CPMK pada tiap pertemuan RPS berikut. Untuk setiap pertemuan,
    putuskan apakah CPMK yang dipilih adalah yang PALING tepat di antara daftar CPMK
    yang tersedia (atau hanya cocok marginal). Juga catat CPL yang tidak ditutupi
    oleh CPMK manapun di sepanjang 16 minggu.

    CPL:
    {cpl_text}

    CPMK (gunakan ANGKA):
    {cpmk_text}

    Pertemuan:
    {json.dumps(meetings, ensure_ascii=False)}

    Output JSON object PERSIS:
    {{
      "mismatches": [{{"week": 3, "current": 1, "suggested": 2, "reason": "..."}}],
      "orphan_cpl_indices": [4]
    }}
    `mismatches` hanya berisi entri di mana CPMK saat ini SECARA JELAS tidak optimal.
    Hanya keluarkan JSON.
    """
    parsed = _safe_llm_json(prompt, expect="object") or {}

    findings: list[dict] = []
    for item in parsed.get("mismatches") or []:
        try:
            week = int(item.get("week"))
            suggested = int(item.get("suggested"))
        except (TypeError, ValueError):
            continue
        if not (1 <= suggested <= len(cpmk)):
            continue
        reason = str(item.get("reason") or "")[:280]
        findings.append(
            _make_finding(
                severity="warning",
                scope="per_week",
                category="cpmk_alignment",
                issue=(
                    f"Modul {week}: CPMK saat ini mungkin kurang tepat. "
                    f"Saran ganti ke CPMK-{suggested}. "
                    + (f"Alasan: {reason}" if reason else "")
                ).strip(),
                target_week=week,
                field="cpmk_number",
                suggested_value=suggested,
                suggested_fix=reason or None,
            )
        )

    for idx in parsed.get("orphan_cpl_indices") or []:
        try:
            i = int(idx)
        except (TypeError, ValueError):
            continue
        if not (1 <= i <= len(cpl)):
            continue
        findings.append(
            _make_finding(
                severity="info",
                scope="cross_cutting",
                category="cpl_alignment",
                issue=(
                    f"CPL-{i} tidak ditutupi oleh CPMK manapun. "
                    "Tambahkan CPMK turunan atau hubungkan ke CPMK yang sudah ada."
                ),
                field="cpl_list",
            )
        )
    return {"findings": findings}


def continuity_node(state: ReviewState):
    """Single batched LLM call over the 16-meeting sequence."""
    meetings_serialized = [
        {
            "week": m.week_number,
            "bahan_kajian_topik": m.bahan_kajian_topik or "",
            "title": m.sub_topic_title or "",
            "description": (m.sub_topic_description or "")[:300],
            "cpmk_number": m.cpmk_number,
        }
        for m in (state.get("meetings") or [])
    ]
    if not meetings_serialized:
        return {"findings": []}

    prompt = f"""
    Tinjau urutan 16 pertemuan RPS berikut sebagai satu perjalanan belajar. Identifikasi
    transisi yang janggal: lompatan tingkat kesulitan, topik tak nyambung, atau scaffolding
    yang hilang antar minggu. Lewati pasangan yang masuk akal — laporkan hanya yang BERMASALAH.

    Format JSON ARRAY:
    [
      {{
        "from_week": 3,
        "to_week": 4,
        "severity": "warning",
        "issue": "Lompatan dari pengantar ML ke implementasi LLM tanpa fondasi backprop.",
        "suggested_fix": "Sisipkan minggu khusus jaringan saraf dasar, atau pindahkan implementasi LLM ke setelah Modul 6."
      }}
    ]

    `severity` HARUS salah satu dari "info" atau "warning" (jangan "critical").
    Maksimal 5 entri prioritas tertinggi.

    Pertemuan:
    {json.dumps(meetings_serialized, ensure_ascii=False)}

    Hanya outputkan JSON array.
    """
    parsed = _safe_llm_json(prompt, expect="array") or []

    findings: list[dict] = []
    for item in parsed[:5]:
        if not isinstance(item, dict):
            continue
        try:
            fw = int(item.get("from_week"))
            tw = int(item.get("to_week"))
        except (TypeError, ValueError):
            continue
        sev_raw = str(item.get("severity") or "info").lower()
        severity = "warning" if sev_raw == "warning" else "info"
        issue_text = str(item.get("issue") or "")[:300]
        suggested_fix = str(item.get("suggested_fix") or "")[:300] or None
        if not issue_text:
            continue
        findings.append(
            _make_finding(
                severity=severity,
                scope="cross_cutting",
                category="continuity",
                issue=f"M{fw} → M{tw}: {issue_text}",
                suggested_fix=suggested_fix,
                # No `suggested_value` — continuity fixes need dosen judgement.
            )
        )
    return {"findings": findings}


def aggregate_node(state: ReviewState):
    """Dedupe by issue_hash, then sort by severity then category."""
    sev_rank = {"critical": 0, "warning": 1, "info": 2}
    seen: dict[str, dict] = {}
    for f in state.get("findings") or []:
        h = f["issue_hash"]
        if h not in seen:
            seen[h] = f

    out = sorted(
        seen.values(),
        key=lambda f: (sev_rank.get(f["severity"], 99), f["category"], f.get("target_week") or 0),
    )
    return {"findings": out}


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def build_review_graph():
    graph = StateGraph(ReviewState)

    graph.add_node("sndikti", sndikti_compliance_node)
    graph.add_node("content_quality", content_quality_node)
    graph.add_node("cpmk_alignment", cpl_cpmk_alignment_node)
    graph.add_node("continuity", continuity_node)
    graph.add_node("aggregate", aggregate_node)

    # Fan out: each lens reads from initial state, contributes to findings.
    graph.set_entry_point("sndikti")
    graph.add_edge("sndikti", "content_quality")
    graph.add_edge("content_quality", "cpmk_alignment")
    graph.add_edge("cpmk_alignment", "continuity")
    graph.add_edge("continuity", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()
