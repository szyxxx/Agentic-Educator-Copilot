from sqlalchemy import Column, Integer, JSON, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class RPSMeeting(Base):
    __tablename__ = "rps_meetings"

    id = Column(String, primary_key=True)
    rps_id = Column(String, nullable=False)
    week_number = Column(Integer, nullable=False)

    # Institutional schema (Bahan Kajian/Topik, Sub-Topik, CPMK number, ref indices)
    bahan_kajian_topik = Column(String(255), nullable=True)
    sub_topic_title = Column(String(500), nullable=True)
    sub_topic_description = Column(Text, nullable=True)
    cpmk_number = Column(Integer, nullable=True)
    reference_indices = Column(JSON, nullable=True)

    # Legacy / fallback string fields (kept so old data still renders during the
    # transition; the institutional layout reads from the new columns above).
    topic = Column(String(500))
    cpmk = Column(String(50))
    references = Column(String(255))

    # Internal pedagogy fields — hidden from the institutional view but used
    # by compliance scoring, the knowledge graph indexer, and the per-week
    # regenerate agent.
    learning_method = Column(String(255))
    evaluation_method = Column(String(255))

    feedback = Column(Text, nullable=True)
    status = Column(String(50), default="ok")
    status_text = Column(String(50), default="OK")
    created_at = Column(DateTime, server_default=func.now())
