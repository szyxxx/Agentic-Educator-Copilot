import time
import secrets
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.database import get_session
from app.core.access import current_user
from app.core.auth import (
    COOKIE,
    PASSWORDS,
    DUMMY_HASH,
    hash_token,
    secure_cookie,
    check_password,
    create_user,
)
from app.models.security import User, AuthSession, CourseAccess, LoginAttempt
from app.models.course import Course

router = APIRouter()


class Login(BaseModel):
    username: str = Field(max_length=80)
    password: str = Field(max_length=1024)


@router.post("/login")
def login(
    payload: Login,
    request: Request,
    response: Response,
    db: Session = Depends(get_session),
):
    name = payload.username.strip().lower()
    # Persisted rate limit per source + account, survives application restarts.
    key = hash_token(f"{request.client.host if request.client else 'unknown'}:{name}")
    now = time.time()
    attempt = db.get(LoginAttempt, key)
    if attempt and attempt.reset_at > now and attempt.count >= 10:
        from app.core.audit import record
        from types import SimpleNamespace

        record(
            db,
            "login_failed",
            "account",
            name or "(empty)",
            actor=SimpleNamespace(
                id=None, username=name or "(empty)", role="anonymous"
            ),
            details={"reason": "rate_limited"},
        )
        db.commit()
        raise HTTPException(429, "Terlalu banyak percobaan. Coba lagi dalam 15 menit.")
    user = db.query(User).filter(User.username == name).first()
    valid = check_password(user.password_hash if user else DUMMY_HASH, payload.password)
    if not valid or not user or not user.active:
        if not attempt:
            attempt = LoginAttempt(key=key, count=0, reset_at=now + 900)
            db.add(attempt)
        if attempt.reset_at <= now:
            attempt.count = 0
            attempt.reset_at = now + 900
        attempt.count += 1
        from app.core.audit import record
        from types import SimpleNamespace

        record(
            db,
            "login_failed",
            "account",
            name or "(empty)",
            actor=SimpleNamespace(
                id=None, username=name or "(empty)", role="anonymous"
            ),
            details={"reason": "invalid_credentials"},
        )
        db.commit()
        raise HTTPException(401, "Nama akun atau password salah.")
    if attempt:
        db.delete(attempt)
    old = request.cookies.get(COOKIE)
    if old:
        previous = db.get(AuthSession, hash_token(old))
        if previous:
            db.delete(previous)
    token = secrets.token_urlsafe(48)
    ttl = 8 * 3600
    db.add(
        AuthSession(
            token_hash=hash_token(token),
            user_id=user.id,
            created_at=now,
            expires_at=now + ttl,
        )
    )
    db.query(AuthSession).filter(AuthSession.expires_at <= now).delete(
        synchronize_session=False
    )
    from app.core.audit import record

    record(db, "login", "account", user.id, actor=user)
    db.commit()
    response.set_cookie(
        COOKIE,
        token,
        max_age=ttl,
        httponly=True,
        secure=secure_cookie(),
        samesite="strict",
        path="/",
    )
    return {"id": user.id, "username": user.username, "role": user.role}


@router.get("/me")
def me(user=Depends(current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "course_ids": user.course_ids,
    }


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_session)):
    token = request.cookies.get(COOKIE, "")
    row = db.get(AuthSession, hash_token(token))
    if row:
        db.delete(row)
    from app.core.audit import record

    record(db, "logout", "account", getattr(request.state.user, "id", "unknown"))
    db.commit()
    response.delete_cookie(
        COOKIE, path="/", secure=secure_cookie(), httponly=True, samesite="strict"
    )
    return {"status": "success"}


class Account(BaseModel):
    username: str
    password: str
    role: Literal["admin", "dosen", "penjamin_mutu"]
    course_ids: list[str] = Field(default_factory=list)


@router.get("/users")
def users(db: Session = Depends(get_session)):
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "active": u.active,
            "course_ids": [
                a.course_id
                for a in db.query(CourseAccess).filter(CourseAccess.user_id == u.id)
            ],
        }
        for u in db.query(User).order_by(User.username)
    ]


@router.post("/users", status_code=201)
def add_user(payload: Account, db: Session = Depends(get_session)):
    if payload.course_ids and payload.role != "dosen":
        raise HTTPException(400, "Penugasan hanya untuk dosen.")
    for cid in payload.course_ids:
        if not db.get(Course, cid):
            raise HTTPException(404, "Mata kuliah tidak ditemukan.")
    try:
        user = create_user(db, payload.username, payload.password, payload.role)
    except ValueError as e:
        raise HTTPException(400, str(e))
    for cid in set(payload.course_ids):
        db.add(CourseAccess(user_id=user.id, course_id=cid))
    db.commit()
    return {"id": user.id, "username": user.username, "role": user.role}


class AccountUpdate(BaseModel):
    active: bool | None = None
    password: str | None = None
    course_ids: list[str] | None = None


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    payload: AccountUpdate,
    db: Session = Depends(get_session),
    actor=Depends(current_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Akun tidak ditemukan.")
    if user.id == actor.id and payload.active is False:
        raise HTTPException(400, "Admin tidak boleh menonaktifkan akunnya sendiri.")
    if payload.password is not None:
        if not 12 <= len(payload.password) <= 1024:
            raise HTTPException(400, "Password harus 12–1024 karakter.")
        user.password_hash = PASSWORDS.hash(payload.password)
    if payload.course_ids is not None:
        if user.role != "dosen":
            raise HTTPException(400, "Penugasan hanya untuk dosen.")
        for cid in payload.course_ids:
            if not db.get(Course, cid):
                raise HTTPException(404, "Mata kuliah tidak ditemukan.")
        db.query(CourseAccess).filter(CourseAccess.user_id == user.id).delete(
            synchronize_session=False
        )
        for cid in set(payload.course_ids):
            db.add(CourseAccess(user_id=user.id, course_id=cid))
    if payload.active is not None:
        user.active = payload.active
    db.query(AuthSession).filter(AuthSession.user_id == user.id).delete(
        synchronize_session=False
    )
    db.commit()
    return {"status": "success"}
