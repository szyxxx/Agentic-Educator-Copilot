"""Deterministic SN-DIKTI compliance catalog.

This module is the single source of truth for what counts as "compliant"
under SN-DIKTI / Permendikbudristek No. 53 Tahun 2023. Both the deterministic
Compliance Report (`/api/rps/{id}/compliance`) and the LLM-driven Review
Agent's SN-DIKTI node read from the same `SNDIKTI_CATALOG` list.

Each `SNDIKTI_Criterion` declares:
    - id: stable slug like "SND-001"
    - title: human display text
    - regulation_ref: which article / pasal of the regulation it cites
    - severity: critical | warning | info
    - weight: positive int (points contributed when the criterion passes)
    - scope: rps_level (one row in the report) or per_week (one row per
      affected week, weighted per pass)
    - field: the data column / list the criterion is about, used by the UI
      to deep-link and by Apply_Action to know what to patch
    - group: section header for the UI (e.g. "Identitas")
    - validator: pure function (rps, meetings) -> CriterionResult OR
      (for per_week criteria) (rps, meeting) -> CriterionResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Literal

from app.core.rps_constants import UAS_MODULE, UTS_MODULE, is_exam_week


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Severity = Literal["critical", "warning", "info"]
Scope = Literal["rps_level", "per_week"]


@dataclass
class CriterionResult:
    """One run of one validator against one (rps[, meeting]) pair.

    `applicable=False` is the sentinel for "this criterion does not apply to
    this meeting at all" (e.g. UTS-label criterion evaluated on Modul 5, or
    a per-week field criterion evaluated on Modul 8 which is exam-locked).
    The runner skips inapplicable rows entirely — they don't add to the
    score's denominator.
    """

    passed: bool
    detail: str = ""
    suggested_value: Any = None
    target_week: int | None = None
    applicable: bool = True


@dataclass
class SNDIKTI_Criterion:
    id: str
    title: str
    regulation_ref: str
    severity: Severity
    weight: int
    scope: Scope
    field: str
    group: str
    validator: Callable[..., CriterionResult]


@dataclass
class CriterionRow:
    """Flattened row in the Compliance Report. For per_week criteria the
    catalog produces one row per affected meeting, each carrying its own
    pass/fail and weight contribution."""

    id: str
    title: str
    regulation_ref: str
    severity: Severity
    scope: Scope
    weight: int
    contributed_weight: int
    passed: bool
    detail: str
    field: str
    group: str
    target_week: int | None
    suggested_value: Any


@dataclass
class ComplianceGroup:
    group: str
    passed: int
    total: int
    earned_weight: int
    total_weight: int


@dataclass
class ComplianceReport:
    score: int
    total_weight: int
    earned_weight: int
    regulation_summary: str
    criteria: list[CriterionRow] = field(default_factory=list)
    groups: list[ComplianceGroup] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _non_empty_str(value: Any) -> bool:
    return bool(value and str(value).strip())


def _non_exam_meetings(meetings: Iterable[Any]) -> list[Any]:
    return [m for m in meetings if not is_exam_week(getattr(m, "week_number", None))]


# ---------------------------------------------------------------------------
# rps_level validators
# ---------------------------------------------------------------------------

# --- Identitas ------------------------------------------------------------


def _v_course_name(rps, _meetings):
    val = (getattr(getattr(rps, "_course", None), "name", "") or "").strip()
    if val:
        return CriterionResult(True, f"Nama mata kuliah: {val}")
    return CriterionResult(False, "Nama mata kuliah belum diisi.", suggested_value=None)


def _v_course_code(rps, _meetings):
    val = (getattr(getattr(rps, "_course", None), "code", "") or "").strip()
    if val:
        return CriterionResult(True, f"Kode mata kuliah: {val}")
    return CriterionResult(False, "Kode mata kuliah belum diisi.")


def _v_sks(rps, _meetings):
    sks = getattr(getattr(rps, "_course", None), "sks", None)
    if sks and 1 <= int(sks) <= 6:
        return CriterionResult(True, f"SKS: {sks}")
    return CriterionResult(False, f"SKS tidak valid (saat ini: {sks!r}). Harus 1–6.")


def _v_semester(rps, _meetings):
    sem = getattr(getattr(rps, "_course", None), "semester", None)
    if sem and 1 <= int(sem) <= 14:
        return CriterionResult(True, f"Semester: {sem}")
    return CriterionResult(False, f"Semester tidak valid (saat ini: {sem!r}). Harus 1–14.")


def _v_program_study(rps, _meetings):
    val = (getattr(getattr(rps, "_course", None), "program_study", "") or "").strip()
    if val:
        return CriterionResult(True, f"Program studi: {val}")
    return CriterionResult(False, "Program studi belum diisi.")


# --- Capaian Pembelajaran -------------------------------------------------


def _v_cpl_present(rps, _meetings):
    cpl = [c for c in (rps.cpl_list or []) if _non_empty_str(c)]
    if cpl:
        return CriterionResult(True, f"{len(cpl)} CPL terdaftar.")
    return CriterionResult(False, "Belum ada CPL terdaftar.")


def _v_cpmk_minimum(rps, _meetings):
    cpmk = [c for c in (rps.cpmk_list or []) if _non_empty_str(c)]
    if len(cpmk) >= 3:
        return CriterionResult(True, f"{len(cpmk)} CPMK terdaftar.")
    return CriterionResult(
        False,
        f"Hanya {len(cpmk)} CPMK terdaftar; minimal 3 disarankan untuk cakupan yang memadai.",
    )


def _v_cpmk_used(rps, meetings):
    cpmk_count = len(rps.cpmk_list or [])
    if cpmk_count == 0:
        return CriterionResult(False, "Tidak ada CPMK untuk dievaluasi.")
    used: set[int] = set()
    for m in _non_exam_meetings(meetings):
        if m.cpmk_number is not None:
            used.add(int(m.cpmk_number))
    orphans = [n for n in range(1, cpmk_count + 1) if n not in used]
    if not orphans:
        return CriterionResult(True, "Setiap CPMK dipakai oleh minimal satu pertemuan.")
    return CriterionResult(
        False,
        f"CPMK yang belum dipakai pertemuan apa pun: {', '.join(f'CPMK-{n}' for n in orphans)}.",
    )


def _v_cpl_covered(rps, _meetings):
    """Approx coverage check: every CPL should have at least one CPMK
    referencing it. We don't have explicit CPL→CPMK links, so we treat the
    catalog as "every CPL needs a CPMK" — i.e., #CPMK >= #CPL.
    """
    cpl = len([c for c in (rps.cpl_list or []) if _non_empty_str(c)])
    cpmk = len([c for c in (rps.cpmk_list or []) if _non_empty_str(c)])
    if cpl == 0:
        return CriterionResult(False, "Tidak ada CPL untuk dievaluasi.")
    if cpmk >= cpl:
        return CriterionResult(True, f"{cpmk} CPMK menutupi {cpl} CPL.")
    return CriterionResult(
        False,
        f"Hanya {cpmk} CPMK untuk {cpl} CPL — minimal satu CPMK per CPL.",
    )


# --- Bahan Kajian ---------------------------------------------------------


def _v_bahan_kajian_count(rps, _meetings):
    bk = [b for b in (rps.bahan_kajian or []) if _non_empty_str(b)]
    if len(bk) >= 3:
        return CriterionResult(True, f"{len(bk)} Bahan Kajian terdaftar.")
    return CriterionResult(False, f"Hanya {len(bk)} Bahan Kajian — minimal 3.")


def _v_bahan_kajian_used(rps, meetings):
    bk = [b for b in (rps.bahan_kajian or []) if _non_empty_str(b)]
    if not bk:
        return CriterionResult(False, "Tidak ada Bahan Kajian untuk dievaluasi.")
    used = {(m.bahan_kajian_topik or "").strip() for m in _non_exam_meetings(meetings)}
    unused = [b for b in bk if b not in used]
    if not unused:
        return CriterionResult(True, "Setiap Bahan Kajian dipakai minimal sekali.")
    return CriterionResult(
        False,
        f"Bahan Kajian yang tidak terpakai: {', '.join(unused[:3])}"
        + (f" (+{len(unused) - 3} lainnya)" if len(unused) > 3 else "") + ".",
    )


# --- Pertemuan (rps_level shape) -----------------------------------------


def _v_meeting_count(_rps, meetings):
    n = len(list(meetings))
    if n == 16:
        return CriterionResult(True, "16 pertemuan terdefinisi.")
    return CriterionResult(False, f"Hanya {n} pertemuan — wajib 16.")


# --- Variasi metode & evaluasi -------------------------------------------


def _v_method_variety(_rps, meetings):
    methods = {
        (m.learning_method or "").strip()
        for m in _non_exam_meetings(meetings)
        if (m.learning_method or "").strip()
    }
    # learning_method can be comma-separated; split before counting unique values.
    flat: set[str] = set()
    for raw in methods:
        for token in raw.split(","):
            t = token.strip()
            if t:
                flat.add(t)
    if len(flat) >= 3:
        return CriterionResult(True, f"{len(flat)} metode unik dipakai: {', '.join(sorted(flat))}.")
    return CriterionResult(False, f"Hanya {len(flat)} metode unik — minimal 3.")


def _v_evaluation_variety(_rps, meetings):
    flat: set[str] = set()
    for m in _non_exam_meetings(meetings):
        for token in (m.evaluation_method or "").split(","):
            t = token.strip()
            if t:
                flat.add(t)
    if len(flat) >= 2:
        return CriterionResult(True, f"{len(flat)} bentuk evaluasi: {', '.join(sorted(flat))}.")
    return CriterionResult(False, f"Hanya {len(flat)} bentuk evaluasi — minimal 2.")


# --- Referensi & Modalitas ------------------------------------------------


def _v_references_minimum(rps, _meetings):
    refs = [r for r in (rps.references_list or []) if _non_empty_str(r)]
    if len(refs) >= 5:
        return CriterionResult(True, f"{len(refs)} referensi terdaftar.")
    return CriterionResult(False, f"Hanya {len(refs)} referensi — minimal 5.")


def _v_modality_set(rps, _meetings):
    mod = (rps.learning_modality or "").strip()
    if mod:
        return CriterionResult(True, f"Modalitas: {mod}.")
    return CriterionResult(False, "Modalitas pembelajaran belum dipilih.")


# ---------------------------------------------------------------------------
# per_week validators (operate on a single meeting)
# ---------------------------------------------------------------------------


def _v_uts_at_8(_rps, meeting):
    if meeting.week_number != UTS_MODULE:
        # Only the meeting at week 8 is eligible.
        return CriterionResult(True, "", applicable=False)
    title = (meeting.sub_topic_title or meeting.topic or "").upper()
    if "UTS" in title or "TENGAH SEMESTER" in title:
        return CriterionResult(True, "Modul 8 berlabel UTS.", target_week=UTS_MODULE)
    from app.core.rps_constants import UTS_TITLE
    return CriterionResult(
        False,
        "Modul 8 belum berlabel Ujian Tengah Semester.",
        target_week=UTS_MODULE,
        suggested_value=UTS_TITLE,
    )


def _v_uas_at_16(_rps, meeting):
    if meeting.week_number != UAS_MODULE:
        return CriterionResult(True, "", applicable=False)
    title = (meeting.sub_topic_title or meeting.topic or "").upper()
    if "UAS" in title or "AKHIR SEMESTER" in title:
        return CriterionResult(True, "Modul 16 berlabel UAS.", target_week=UAS_MODULE)
    from app.core.rps_constants import UAS_TITLE
    return CriterionResult(
        False,
        "Modul 16 belum berlabel Ujian Akhir Semester.",
        target_week=UAS_MODULE,
        suggested_value=UAS_TITLE,
    )


def _v_per_week_field(field_name: str, label: str, allow_list: bool = False):
    def validator(rps, meeting):
        if is_exam_week(meeting.week_number):
            return CriterionResult(True, "", applicable=False)
        value = getattr(meeting, field_name, None)
        if allow_list:
            ok = bool(value)
        else:
            ok = _non_empty_str(value)
        if ok:
            return CriterionResult(
                True,
                f"{label} terisi.",
                target_week=meeting.week_number,
            )
        return CriterionResult(
            False,
            f"{label} kosong di Modul {meeting.week_number}.",
            target_week=meeting.week_number,
        )

    return validator


# Specialized: cpmk_number must be a valid index
def _v_cpmk_number_valid(rps, meeting):
    if is_exam_week(meeting.week_number):
        return CriterionResult(True, "", applicable=False)
    cpmk_count = len(rps.cpmk_list or [])
    n = meeting.cpmk_number
    if cpmk_count == 0:
        return CriterionResult(
            False,
            f"Modul {meeting.week_number}: belum ada CPMK terdaftar di tingkat RPS.",
            target_week=meeting.week_number,
        )
    if n is None:
        return CriterionResult(
            False,
            f"Modul {meeting.week_number}: nomor CPMK belum dipilih.",
            target_week=meeting.week_number,
        )
    if not (1 <= int(n) <= cpmk_count):
        return CriterionResult(
            False,
            f"Modul {meeting.week_number}: CPMK-{n} di luar rentang 1..{cpmk_count}.",
            target_week=meeting.week_number,
        )
    return CriterionResult(
        True,
        f"Modul {meeting.week_number}: CPMK-{n} valid.",
        target_week=meeting.week_number,
    )


# Specialized: bahan_kajian_topik must match the parent list
def _v_bahan_kajian_topik(rps, meeting):
    if is_exam_week(meeting.week_number):
        return CriterionResult(True, "", applicable=False)
    val = (meeting.bahan_kajian_topik or "").strip()
    if not val:
        return CriterionResult(
            False,
            f"Modul {meeting.week_number}: Bahan Kajian belum dipilih.",
            target_week=meeting.week_number,
        )
    allowed = {b.strip() for b in (rps.bahan_kajian or []) if b}
    if val not in allowed:
        return CriterionResult(
            False,
            f"Modul {meeting.week_number}: '{val[:50]}…' tidak ada di daftar Bahan Kajian RPS.",
            target_week=meeting.week_number,
            suggested_value="",
        )
    return CriterionResult(
        True,
        f"Modul {meeting.week_number}: Bahan Kajian '{val[:40]}…' valid.",
        target_week=meeting.week_number,
    )


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

REGULATION_SUMMARY = "Permendikbudristek 53/2023 Pasal 12 ayat (1) (Komponen RPS); SN-Dikti 2023."


SNDIKTI_CATALOG: list[SNDIKTI_Criterion] = [
    # --- Identitas mata kuliah --------------------------------------------
    SNDIKTI_Criterion(
        id="SND-001",
        title="Nama mata kuliah terisi",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf a",
        severity="critical",
        weight=4,
        scope="rps_level",
        field="course.name",
        group="Identitas",
        validator=_v_course_name,
    ),
    SNDIKTI_Criterion(
        id="SND-002",
        title="Kode mata kuliah terisi",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf a",
        severity="critical",
        weight=4,
        scope="rps_level",
        field="course.code",
        group="Identitas",
        validator=_v_course_code,
    ),
    SNDIKTI_Criterion(
        id="SND-003",
        title="SKS terisi (1–6)",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf a",
        severity="critical",
        weight=4,
        scope="rps_level",
        field="course.sks",
        group="Identitas",
        validator=_v_sks,
    ),
    SNDIKTI_Criterion(
        id="SND-004",
        title="Semester terisi (1–14)",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf a",
        severity="critical",
        weight=4,
        scope="rps_level",
        field="course.semester",
        group="Identitas",
        validator=_v_semester,
    ),
    SNDIKTI_Criterion(
        id="SND-005",
        title="Program studi terisi",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf a",
        severity="critical",
        weight=4,
        scope="rps_level",
        field="course.program_study",
        group="Identitas",
        validator=_v_program_study,
    ),
    # --- Capaian Pembelajaran ---------------------------------------------
    SNDIKTI_Criterion(
        id="SND-010",
        title="Minimal satu CPL terdaftar",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf b",
        severity="critical",
        weight=6,
        scope="rps_level",
        field="cpl_list",
        group="Capaian Pembelajaran",
        validator=_v_cpl_present,
    ),
    SNDIKTI_Criterion(
        id="SND-011",
        title="Minimal tiga CPMK terdaftar",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf b",
        severity="critical",
        weight=6,
        scope="rps_level",
        field="cpmk_list",
        group="Capaian Pembelajaran",
        validator=_v_cpmk_minimum,
    ),
    SNDIKTI_Criterion(
        id="SND-012",
        title="Setiap CPMK terhubung ke pertemuan",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf b",
        severity="critical",
        weight=6,
        scope="rps_level",
        field="cpmk_list",
        group="Capaian Pembelajaran",
        validator=_v_cpmk_used,
    ),
    SNDIKTI_Criterion(
        id="SND-013",
        title="Setiap CPL ditutupi minimal satu CPMK",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf b",
        severity="critical",
        weight=6,
        scope="rps_level",
        field="cpl_list",
        group="Capaian Pembelajaran",
        validator=_v_cpl_covered,
    ),
    # --- Bahan Kajian ------------------------------------------------------
    SNDIKTI_Criterion(
        id="SND-020",
        title="Minimal tiga Bahan Kajian terdaftar",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf c",
        severity="warning",
        weight=3,
        scope="rps_level",
        field="bahan_kajian",
        group="Bahan Kajian",
        validator=_v_bahan_kajian_count,
    ),
    SNDIKTI_Criterion(
        id="SND-021",
        title="Setiap Bahan Kajian dipakai minimal sekali",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf c",
        severity="warning",
        weight=3,
        scope="rps_level",
        field="bahan_kajian",
        group="Bahan Kajian",
        validator=_v_bahan_kajian_used,
    ),
    # --- Pertemuan (rps_level) --------------------------------------------
    SNDIKTI_Criterion(
        id="SND-030",
        title="16 pertemuan terdefinisi",
        regulation_ref="SN-Dikti — durasi semester 16 minggu (termasuk UTS+UAS)",
        severity="critical",
        weight=10,
        scope="rps_level",
        field="meetings",
        group="Pertemuan",
        validator=_v_meeting_count,
    ),
    # --- Pertemuan (per_week) ---------------------------------------------
    SNDIKTI_Criterion(
        id="SND-031",
        title="Modul 8 berlabel UTS",
        regulation_ref="Pedoman Akademik Institusi — UTS pada Minggu ke-8",
        severity="critical",
        weight=4,
        scope="per_week",
        field="meetings.sub_topic_title",
        group="Pertemuan",
        validator=_v_uts_at_8,
    ),
    SNDIKTI_Criterion(
        id="SND-032",
        title="Modul 16 berlabel UAS",
        regulation_ref="Pedoman Akademik Institusi — UAS pada Minggu ke-16",
        severity="critical",
        weight=4,
        scope="per_week",
        field="meetings.sub_topic_title",
        group="Pertemuan",
        validator=_v_uas_at_16,
    ),
    SNDIKTI_Criterion(
        id="SND-033",
        title="Bahan Kajian/Topik terisi tiap pertemuan",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf c",
        severity="warning",
        weight=2,
        scope="per_week",
        field="meetings.bahan_kajian_topik",
        group="Pertemuan",
        validator=_v_bahan_kajian_topik,
    ),
    SNDIKTI_Criterion(
        id="SND-034",
        title="Sub-Topik terisi tiap pertemuan",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf d",
        severity="warning",
        weight=2,
        scope="per_week",
        field="meetings.sub_topic_title",
        group="Pertemuan",
        validator=_v_per_week_field("sub_topic_title", "Sub-Topik (judul)"),
    ),
    SNDIKTI_Criterion(
        id="SND-035",
        title="Nomor CPMK valid tiap pertemuan",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf b & d",
        severity="warning",
        weight=2,
        scope="per_week",
        field="meetings.cpmk_number",
        group="Pertemuan",
        validator=_v_cpmk_number_valid,
    ),
    SNDIKTI_Criterion(
        id="SND-036",
        title="Referensi dikutip tiap pertemuan",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf g",
        severity="warning",
        weight=2,
        scope="per_week",
        field="meetings.reference_indices",
        group="Pertemuan",
        validator=_v_per_week_field(
            "reference_indices", "Referensi", allow_list=True
        ),
    ),
    SNDIKTI_Criterion(
        id="SND-037",
        title="Metode pembelajaran terisi tiap pertemuan",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf e",
        severity="warning",
        weight=2,
        scope="per_week",
        field="meetings.learning_method",
        group="Pertemuan",
        validator=_v_per_week_field("learning_method", "Metode pembelajaran"),
    ),
    SNDIKTI_Criterion(
        id="SND-038",
        title="Bentuk evaluasi terisi tiap pertemuan",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf f",
        severity="warning",
        weight=2,
        scope="per_week",
        field="meetings.evaluation_method",
        group="Pertemuan",
        validator=_v_per_week_field("evaluation_method", "Bentuk evaluasi"),
    ),
    # --- Variasi metode & evaluasi ----------------------------------------
    SNDIKTI_Criterion(
        id="SND-040",
        title="Minimal tiga metode pembelajaran unik",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf e",
        severity="warning",
        weight=4,
        scope="rps_level",
        field="meetings.learning_method",
        group="Metode & Evaluasi",
        validator=_v_method_variety,
    ),
    SNDIKTI_Criterion(
        id="SND-041",
        title="Minimal dua bentuk evaluasi unik",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf f",
        severity="warning",
        weight=4,
        scope="rps_level",
        field="meetings.evaluation_method",
        group="Metode & Evaluasi",
        validator=_v_evaluation_variety,
    ),
    # --- Referensi & Modalitas --------------------------------------------
    SNDIKTI_Criterion(
        id="SND-050",
        title="Minimal lima referensi terdaftar",
        regulation_ref="Permendikbudristek 53/2023 Pasal 12 ayat (1) huruf g",
        severity="warning",
        weight=3,
        scope="rps_level",
        field="references_list",
        group="Referensi",
        validator=_v_references_minimum,
    ),
    SNDIKTI_Criterion(
        id="SND-051",
        title="Modalitas pembelajaran terpilih",
        regulation_ref="SN-Dikti — Bentuk pembelajaran tatap muka / daring / hybrid",
        severity="warning",
        weight=3,
        scope="rps_level",
        field="learning_modality",
        group="Referensi",
        validator=_v_modality_set,
    ),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_catalog(rps, meetings, *, course=None) -> ComplianceReport:
    """Run every catalog validator against an RPS and return a report.

    `course` is optional; when provided, identitas validators read from it.
    For convenience, we attach the course onto the rps object as `_course`
    so the validators can stay call-site agnostic.
    """
    if course is not None:
        # Stash the course on the RPS for the duration of the run. Mutating a
        # transient attribute is safe — we don't commit it.
        try:
            rps._course = course  # type: ignore[attr-defined]
        except Exception:
            pass

    rows: list[CriterionRow] = []
    earned_weight = 0
    total_weight = 0

    meetings_list = list(meetings)

    for crit in SNDIKTI_CATALOG:
        if crit.scope == "rps_level":
            res = crit.validator(rps, meetings_list)
            if not res.applicable:
                continue
            total_weight += crit.weight
            contributed = crit.weight if res.passed else 0
            earned_weight += contributed
            rows.append(
                CriterionRow(
                    id=crit.id,
                    title=crit.title,
                    regulation_ref=crit.regulation_ref,
                    severity=crit.severity,
                    scope=crit.scope,
                    weight=crit.weight,
                    contributed_weight=contributed,
                    passed=res.passed,
                    detail=res.detail,
                    field=crit.field,
                    group=crit.group,
                    target_week=res.target_week,
                    suggested_value=res.suggested_value,
                )
            )
        else:
            # per_week: fan out across every meeting; the validator decides
            # which ones are applicable via the `applicable` flag.
            for m in meetings_list:
                res = crit.validator(rps, m)
                if not res.applicable:
                    continue
                total_weight += crit.weight
                contributed = crit.weight if res.passed else 0
                earned_weight += contributed
                rows.append(
                    CriterionRow(
                        id=crit.id,
                        title=crit.title,
                        regulation_ref=crit.regulation_ref,
                        severity=crit.severity,
                        scope=crit.scope,
                        weight=crit.weight,
                        contributed_weight=contributed,
                        passed=res.passed,
                        detail=res.detail,
                        field=crit.field,
                        group=crit.group,
                        target_week=res.target_week,
                        suggested_value=res.suggested_value,
                    )
                )

    # Aggregate by group for the segmented progress bar
    groups_acc: dict[str, ComplianceGroup] = {}
    for row in rows:
        g = groups_acc.setdefault(
            row.group,
            ComplianceGroup(group=row.group, passed=0, total=0, earned_weight=0, total_weight=0),
        )
        g.total += 1
        g.total_weight += row.weight
        if row.passed:
            g.passed += 1
            g.earned_weight += row.contributed_weight

    score = round((earned_weight / total_weight) * 100) if total_weight else 0
    return ComplianceReport(
        score=score,
        total_weight=total_weight,
        earned_weight=earned_weight,
        regulation_summary=REGULATION_SUMMARY,
        criteria=rows,
        groups=list(groups_acc.values()),
    )
