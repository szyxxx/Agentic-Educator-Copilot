from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True)
    course_id = Column(String, nullable=False)
    title = Column(String(255), nullable=False)
    details = Column(String(255))
    status = Column(String(50), default="draft")
    questions = Column(JSON, nullable=True)
    answer_key = Column(JSON, nullable=True)
    week_number = Column(Integer, default=0)
    time_left = Column(String(50))
    submissions = Column(Integer, default=0)
    total_students = Column(Integer, default=0)
    progress_percent = Column(Integer, default=0)
    updated_at = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
