from sqlalchemy import Column, String
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True)
    course_id = Column(String, nullable=False, index=True)
    nim = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
