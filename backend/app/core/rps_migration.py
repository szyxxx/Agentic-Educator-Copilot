"""One-shot data migration to lift legacy RPSMeeting rows into the
institutional schema.

Idempotent: if the new columns are already populated for a row we leave it
alone. If a row has none of the new fields filled, we derive them from
legacy `topic`, `cpmk`, and `references` strings.

Called from `init_db()` after `_ensure_columns()` so the schema is always
ready before we write to the new columns.
"""

from __future__ import annotations

import re
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.rps_constants import (
    UAS_MODULE,
    UAS_TITLE,
    UTS_MODULE,
    UTS_TITLE,
    is_exam_week,
)
from app.models.rps import RPS
from app.models.rps_meeting import RPSMeeting


def migrate_legacy_meetings(session_factory) -> dict:
    """Walk every meeting once and fill the institutional columns when blank.

    Returns a small report dict so the caller can log what happened. Safe to
    invoke on every startup.
    """
    db: Session = session_factory()
    try:
        report = {
            "scanned": 0,
            "migrated": 0,
            "exam_locked": 0,
            "skipped_already_filled": 0,
        }

        rps_cache: dict[str, RPS] = {}
        for meeting in db.query(RPSMeeting).all():
            report["scanned"] += 1

            if _already_migrated(meeting):
                report["skipped_already_filled"] += 1
                continue

            week = int(meeting.week_number or 0)

            if week == UTS_MODULE:
                meeting.sub_topic_title = UTS_TITLE
                meeting.sub_topic_description = ""
                meeting.bahan_kajian_topik = ""
                meeting.cpmk_number = None
                meeting.reference_indices = []
                report["exam_locked"] += 1
                continue
            if week == UAS_MODULE:
                meeting.sub_topic_title = UAS_TITLE
                meeting.sub_topic_description = ""
                meeting.bahan_kajian_topik = ""
                meeting.cpmk_number = None
                meeting.reference_indices = []
                report["exam_locked"] += 1
                continue

            # Resolve parent RPS once per id (rare DB query saver)
            parent: RPS | None = rps_cache.get(meeting.rps_id)
            if parent is None and meeting.rps_id:
                parent = db.query(RPS).filter(RPS.id == meeting.rps_id).first()
                if parent:
                    rps_cache[meeting.rps_id] = parent

            title, description = _split_legacy_topic(meeting.topic or "")
            meeting.sub_topic_title = title
            meeting.sub_topic_description = description
            meeting.bahan_kajian_topik = ""  # Dosen will fill on next edit

            cpmk_list_len = len((parent.cpmk_list if parent else []) or [])
            meeting.cpmk_number = _legacy_cpmk_to_number(meeting.cpmk, cpmk_list_len)

            references_list = (parent.references_list if parent else []) or []
            meeting.reference_indices = _match_legacy_refs(
                meeting.references or "", references_list
            )

            report["migrated"] += 1

        if report["migrated"] or report["exam_locked"]:
            db.commit()
        return report
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _already_migrated(meeting: RPSMeeting) -> bool:
    """A row is considered migrated if any institutional field is filled."""
    if (meeting.sub_topic_title or "").strip():
        return True
    if (meeting.sub_topic_description or "").strip():
        return True
    if (meeting.bahan_kajian_topik or "").strip():
        return True
    if meeting.cpmk_number is not None:
        return True
    if meeting.reference_indices:
        return True
    return False


_TOPIC_SPLIT_RE = re.compile(r"^(?P<title>[^:]+):\s*(?P<desc>.+)$", re.S)


def _split_legacy_topic(topic: str) -> tuple[str, str]:
    """Split `'Title: rest'` → (title, rest); else (topic, '')."""
    text = (topic or "").strip()
    if not text:
        return "", ""
    m = _TOPIC_SPLIT_RE.match(text)
    if not m:
        return text, ""
    return m.group("title").strip(), m.group("desc").strip()


def _legacy_cpmk_to_number(value: str | None, list_len: int) -> int | None:
    """Pull the first integer out of a legacy CPMK string, clamp to [1, len]."""
    if list_len <= 0:
        return None
    text = (value or "").strip()
    if not text:
        return None
    m = re.search(r"\d+", text)
    if not m:
        return None
    n = int(m.group(0))
    return n if 1 <= n <= list_len else None


def _match_legacy_refs(legacy: str, references_list: Iterable[str]) -> list[int]:
    """Match a legacy free-text references string against the numbered list.

    Strategy: case-insensitive substring containment in either direction.
    Returns 1-based indices in ascending order, deduplicated.
    """
    text = (legacy or "").strip().lower()
    if not text:
        return []
    indices: list[int] = []
    for idx, entry in enumerate(references_list, start=1):
        norm = (entry or "").strip().lower()
        if not norm:
            continue
        if norm in text or text in norm:
            indices.append(idx)
    return sorted(set(indices))
