from sqlalchemy import JSON, Column, Float, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True)
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    sks = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    program_study = Column(String(255))
    academic_year = Column(String(20))
    students_count = Column(Integer, default=0)
    avg_score = Column(Float, default=0)
    active_quizzes = Column(Integer, default=0)
    pending_grades = Column(Integer, default=0)
    status = Column(String(50), default="ok")
    status_text = Column(String(50), default="On Track")
    pulse_trend = Column(JSON, default=list)
    distribution = Column(JSON, default=list)
    cpmk_progress = Column(JSON, default=list)
    heatmap = Column(JSON, default=dict)
    insight = Column(String(255))
    updated_at = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
