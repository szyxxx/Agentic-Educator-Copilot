from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_session
from app.models.setting import Setting

router = APIRouter()


class ProfilePayload(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    institution: Optional[str] = None
    semester: Optional[str] = None


class NotificationToggle(BaseModel):
    id: str
    enabled: bool


def _set(db: Session, key: str, *, str_value: str | None = None, bool_value: bool | None = None):
    row = db.query(Setting).filter(Setting.key == key).first()
    if row is None:
        row = Setting(key=key)
        db.add(row)
    if str_value is not None:
        row.str_value = str_value
    if bool_value is not None:
        row.bool_value = bool_value


@router.put("/profile")
def update_profile(payload: ProfilePayload, db: Session = Depends(get_session)):
    if payload.name is not None:
        _set(db, "profile.name", str_value=payload.name.strip())
    if payload.email is not None:
        _set(db, "profile.email", str_value=payload.email.strip())
    if payload.institution is not None:
        _set(db, "profile.institution", str_value=payload.institution.strip())
    if payload.semester is not None:
        _set(db, "profile.semester", str_value=payload.semester.strip())
    db.commit()
    return {"status": "success"}


@router.put("/notifications")
def update_notification(
    payload: NotificationToggle, db: Session = Depends(get_session)
):
    if not payload.id.startswith("notif."):
        raise HTTPException(status_code=400, detail="Invalid notification key.")
    _set(db, payload.id, bool_value=payload.enabled)
    db.commit()
    return {"status": "success"}
