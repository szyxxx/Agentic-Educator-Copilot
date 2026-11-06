from sqlalchemy import Column, Integer, JSON, String
from app.core.database import Base


class ObjectRevision(Base):
    __tablename__ = "object_revisions"
    object_type = Column(String(80), primary_key=True)
    object_id = Column(String(255), primary_key=True)
    version = Column(Integer, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String(64), primary_key=True)
    occurred_at = Column(String(40), nullable=False, index=True)
    actor_id = Column(String(64), nullable=True, index=True)
    actor_name = Column(String(80), nullable=False)
    actor_role = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False, index=True)
    object_type = Column(String(80), nullable=False)
    object_id = Column(String(255), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    application_version = Column(String(100), nullable=False)
    llm_model = Column(String(1000), nullable=True)
    request_id = Column(String(64), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
