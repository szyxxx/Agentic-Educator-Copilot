from sqlalchemy import Column, Float, Integer, String, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class RPS(Base):
    __tablename__ = "rps"

    id = Column(String, primary_key=True)
    course_id = Column(String, nullable=False)
    status = Column(String(50), default="draft")
    draft_content = Column(String, nullable=True)
    cpl_list = Column(JSON, nullable=True)
    cpmk_list = Column(JSON, nullable=True)
    references_list = Column(JSON, nullable=True)
    bahan_kajian = Column(JSON, nullable=True)
    learning_methods = Column(JSON, nullable=True)
    learning_modality = Column(String(50), nullable=True)
    compliance_score = Column(Float, default=0)
    issues_count = Column(Integer, default=0)
    cpmk_count = Column(Integer, default=0)
    references_count = Column(Integer, default=0)
    feedback = Column(Text, nullable=True)
    updated_at = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
