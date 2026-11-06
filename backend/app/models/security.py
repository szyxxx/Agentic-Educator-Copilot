"""Authentication state; raw session tokens and passwords are never persisted."""

from sqlalchemy import Boolean, Column, Float, ForeignKey, String
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(String(64), primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(String(40), nullable=False)


class CourseAccess(Base):
    __tablename__ = "course_access"
    user_id = Column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    course_id = Column(
        String, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    token_hash = Column(String(64), primary_key=True)
    user_id = Column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expires_at = Column(Float, nullable=False, index=True)
    created_at = Column(Float, nullable=False)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    key = Column(String(64), primary_key=True)
    count = Column(Float, nullable=False, default=0)
    reset_at = Column(Float, nullable=False)
