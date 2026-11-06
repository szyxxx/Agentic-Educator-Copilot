from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.models.audit import AuditEvent

router = APIRouter()


@router.get("/")
def list_audit(
    action: str | None = None,
    object_id: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_session),
):
    q = db.query(AuditEvent)
    if action:
        q = q.filter(AuditEvent.action == action)
    if object_id:
        q = q.filter(AuditEvent.object_id == object_id)
    total = q.count()
    events = (
        q.order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "events": [
            {c.name: getattr(row, c.name) for c in AuditEvent.__table__.columns}
            for row in events
        ],
    }
