"""Shared constants for the institutional RPS template.

The template fixes two modules to exam slots:

- Modul 8 → Ujian Tengah Semester (UTS)
- Modul 16 → Ujian Akhir Semester (UAS)

These weeks are NOT user-configurable. The API, the AI agent, and the
migration all consult these constants so the same rules apply everywhere.
"""

from __future__ import annotations

UTS_MODULE: int = 8
UAS_MODULE: int = 16

UTS_TITLE: str = "Ujian Tengah Semester (UTS)"
UAS_TITLE: str = "Ujian Akhir Semester (UAS)"


def is_exam_week(week_number: int | None) -> bool:
    """Return True when the week is the UTS or UAS module."""
    if week_number is None:
        return False
    return int(week_number) in (UTS_MODULE, UAS_MODULE)


def exam_title_for(week_number: int | None) -> str:
    """Return the canonical exam title for week 8 / week 16, or '' otherwise."""
    if week_number == UTS_MODULE:
        return UTS_TITLE
    if week_number == UAS_MODULE:
        return UAS_TITLE
    return ""
