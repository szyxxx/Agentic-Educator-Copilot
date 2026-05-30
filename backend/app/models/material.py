from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(String, primary_key=True)
    course_id = Column(String, nullable=False)
    rps_id = Column(String, nullable=True)
    title = Column(String(255), nullable=False)
    topic = Column(String(255))
    material_type = Column(String(50))  # PDF | DOCX | URL | PPT
    url = Column(String(1024), nullable=True)
    content_text = Column(Text, nullable=True)  # Extracted text used for RAG indexing
    week = Column(Integer, default=1)
    cpmk = Column(String(50))
    status = Column(String(50), default="ready")
    status_text = Column(String(50), default="Ready")
    updated_at = Column(String(50))
    size = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
