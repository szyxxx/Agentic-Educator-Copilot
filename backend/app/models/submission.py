from sqlalchemy import Column, Float, Integer, JSON, String, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Submission(Base):
    """A single student's quiz answers, ingested from a CSV row.

    `answers` is a flat mapping of `{question_id: answer_value}` where the
    value is an MCQ letter (`A`/`B`/`C`/`D`) for multiple-choice questions
    or a free-text response for essays.
    """

    __tablename__ = "submissions"

    id = Column(String, primary_key=True)
    quiz_id = Column(String, nullable=False, index=True)
    student_id = Column(String, nullable=True, index=True)
    nim = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    answers = Column(JSON, nullable=True)
    answered_count = Column(Integer, default=0)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(
        String(50), default="submitted"
    )  # submitted | graded | unmatched
    created_at = Column(DateTime, server_default=func.now())
