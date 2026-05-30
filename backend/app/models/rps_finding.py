from sqlalchemy import Boolean, Column, Integer, JSON, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class RPSFinding(Base):
    """One actionable issue raised by the Review_Agent against an RPS draft.

    The Review_Agent is read-only — Findings are how it surfaces what needs
    attention without overwriting the dosen's work. Findings persist across
    re-runs so dismissals stick: when a re-run re-emits the same
    `(scope, target_week, field, category, normalized_issue)` tuple, the
    existing row's `last_seen_at` is bumped instead of a fresh row being
    inserted.
    """

    __tablename__ = "rps_findings"

    id = Column(String, primary_key=True)
    rps_id = Column(String, nullable=False, index=True)

    severity = Column(String(16), nullable=False)        # info | warning | critical
    scope = Column(String(16), nullable=False)           # per_week | cross_cutting
    target_week = Column(Integer, nullable=True)
    category = Column(String(32), nullable=False)        # cpl_alignment | cpmk_alignment | sndikti_compliance | content_quality | continuity
    field = Column(String(64), nullable=True)            # column or list name being flagged

    issue = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    suggested_value = Column(JSON, nullable=True)

    issue_hash = Column(String(64), nullable=False, index=True)
    regulation_ref = Column(String(255), nullable=True)
    criterion_id = Column(String(32), nullable=True)     # e.g. "SND-013" when the finding came from the catalog

    dismissed = Column(Boolean, default=False, nullable=False)
    applied = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    last_seen_at = Column(DateTime, server_default=func.now())
