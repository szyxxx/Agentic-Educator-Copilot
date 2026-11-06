"""Cookie sessions, explicit accounts and centralized authorization."""

import hashlib
import os
import re
import secrets
import time
from datetime import datetime, timezone
from types import SimpleNamespace

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import event, select
from sqlalchemy.orm import Session, with_loader_criteria

from app.core.database import SessionLocal, require_database_present
from app.models.security import User, AuthSession, CourseAccess

PASSWORDS = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
COOKIE = "educopilot_session"
ROLES = ("admin", "dosen", "penjamin_mutu")
DUMMY_HASH = PASSWORDS.hash(secrets.token_urlsafe(32))


def allowed_origins():
    return [
        s.strip().rstrip("/")
        for s in os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if s.strip() and s.strip() != "*"
    ]


def secure_cookie():
    return os.getenv("AUTH_COOKIE_SECURE", "true").lower() not in ("false", "0")


def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_user(db, username, password, role="admin"):
    username = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.@-]{2,79}", username):
        raise ValueError(
            "Nama akun harus 3–80 karakter huruf kecil, angka, titik, @, _ atau -."
        )
    if role not in ROLES:
        raise ValueError("Peran tidak dikenal.")
    if not isinstance(password, str) or len(password) < 12 or len(password) > 1024:
        raise ValueError("Password harus 12–1024 karakter.")
    if db.query(User).filter(User.username == username).first():
        raise ValueError("Nama akun sudah digunakan.")
    user = User(
        id="u-" + secrets.token_hex(16),
        username=username,
        role=role,
        password_hash=PASSWORDS.hash(password),
        active=True,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(user)
    db.flush()
    return user


def bootstrap_from_env():
    username = os.getenv("EDUCOPILOT_ADMIN_USERNAME", "").strip()
    password = os.getenv("EDUCOPILOT_ADMIN_PASSWORD", "")
    if not username and not password:
        return
    if not username or not password:
        raise RuntimeError(
            "Bootstrap memerlukan EDUCOPILOT_ADMIN_USERNAME dan EDUCOPILOT_ADMIN_PASSWORD sekaligus."
        )
    with SessionLocal() as db:
        if db.query(User).count() == 0:
            create_user(db, username, password, "admin")
            from app.core.audit import record

            record(
                db,
                "account_create",
                "users",
                db.query(User).first().id,
                actor=SimpleNamespace(
                    id=None, username="operator-env", role="operator"
                ),
            )
            db.commit()


def check_password(stored, supplied):
    try:
        return PASSWORDS.verify(stored, supplied)
    except (VerificationError, InvalidHashError):
        return False


def _qm_allowed(method, path):
    if method in ("GET", "HEAD"):
        return True
    return bool(
        re.fullmatch(r"/api/rps/[^/]+/(approve|review)", path)
        or re.fullmatch(r"/api/materials/[^/]+/approve", path)
        or path == "/api/knowledge/query"
    )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    @staticmethod
    def denied(request, detail, status=403, actor=None):
        from app.core.audit import record

        try:
            require_database_present()
            with SessionLocal() as db:
                record(
                    db,
                    "access_denied",
                    "request",
                    request.url.path[:255],
                    actor=actor,
                    details={"status": status, "method": request.method},
                )
                db.commit()
        except RuntimeError:
            pass  # The unavailable database cannot receive an audit event.
        return JSONResponse({"detail": detail}, status_code=status)

    async def dispatch(self, request, call_next):
        path = request.url.path.rstrip("/") or "/"
        origin = request.headers.get("origin")
        unsafe = request.method not in ("GET", "HEAD", "OPTIONS")
        if unsafe and origin and origin.rstrip("/") not in allowed_origins():
            return self.denied(request, "Origin tidak diizinkan.")
        if path in ("/health", "/api/auth/login"):
            return await call_next(request)
        try:
            require_database_present()
        except RuntimeError:
            return JSONResponse(
                {
                    "detail": "Database tidak tersedia. Hentikan backend lalu restore backup."
                },
                status_code=503,
            )
        token = request.cookies.get(COOKIE, "")
        with SessionLocal() as db:
            session = db.get(AuthSession, hash_token(token)) if token else None
            user = (
                db.get(User, session.user_id)
                if session and session.expires_at > time.time()
                else None
            )
            if not user or not user.active:
                return JSONResponse(
                    {"detail": "Login diperlukan atau sesi telah berakhir."},
                    status_code=401,
                )
            ids = tuple(
                db.scalars(
                    select(CourseAccess.course_id).where(
                        CourseAccess.user_id == user.id
                    )
                )
            )
            actor = SimpleNamespace(
                id=user.id, username=user.username, role=user.role, course_ids=ids
            )
        if unsafe and not origin:
            return self.denied(
                request, "Origin diperlukan untuk permintaan dengan sesi.", actor=actor
            )
        if path.startswith("/api/auth/users") and actor.role != "admin":
            return self.denied(
                request, "Hanya admin dapat mengelola akun dan penugasan.", actor=actor
            )
        if path.startswith("/api/audit") and actor.role not in (
            "admin",
            "penjamin_mutu",
        ):
            return self.denied(request, "Peran tidak boleh membaca audit.", actor=actor)
        if (
            path.startswith("/api/settings") or path == "/api/dashboard/settings"
        ) and actor.role != "admin":
            return self.denied(
                request, "Pengaturan layanan hanya untuk admin.", actor=actor
            )
        if (
            actor.role == "penjamin_mutu"
            and unsafe
            and not path.startswith("/api/auth/")
            and not _qm_allowed(request.method, path)
        ):
            return self.denied(
                request,
                "Peran penjamin mutu tidak boleh mengubah data pengajaran atau nilai.",
                actor=actor,
            )
        request.state.user = actor
        if unsafe and path.startswith("/api/"):
            # Validate references before writes, including existing course codes hidden by scope.
            try:
                content_type = (
                    request.headers.get("content-type", "")
                    .split(";", 1)[0]
                    .strip()
                    .lower()
                )
                if content_type == "application/json" or content_type.endswith("+json"):
                    data = await request.json()
                elif "form" in content_type:
                    # Read from a separate Request: downstream still receives the cached raw body.
                    from starlette.requests import Request

                    raw = await request.body()

                    async def receive():
                        return {"type": "http.request", "body": raw, "more_body": False}

                    form_request = Request(request.scope, receive=receive)
                    data = dict(await form_request.form())
                else:
                    data = {}
                self.validate_references(actor, data)
            except HTTPException as exc:
                return self.denied(request, exc.detail, exc.status_code, actor)
            except (ValueError, TypeError):
                pass  # Endpoint validation emits the precise 422 response.
        from app.core.audit import request_context, record
        from uuid import uuid4

        ctx = {
            "actor": actor,
            "request_id": uuid4().hex,
            "models": [],
            "path": path,
            "method": request.method,
        }
        handle = request_context.set(ctx)
        try:
            response = await call_next(request)
            if unsafe and response.status_code >= 400:
                with SessionLocal() as audit_db:
                    record(
                        audit_db,
                        "operation_failed",
                        "request",
                        path,
                        details={"status": response.status_code},
                    )
                    audit_db.commit()
            return response
        except Exception:
            with SessionLocal() as audit_db:
                record(
                    audit_db,
                    "operation_failed",
                    "request",
                    path[:255],
                    details={"status": 500},
                )
                audit_db.commit()
            raise
        finally:
            request_context.reset(handle)

    @staticmethod
    def validate_references(actor, data):
        if not isinstance(data, dict):
            return
        refs = dict(data)
        from app.models import Course, RPS

        with SessionLocal() as db:
            courses = []
            if refs.get("course_id"):
                course = db.get(Course, refs["course_id"])
                if not course:
                    raise HTTPException(404, "Mata kuliah tidak ditemukan.")
                courses.append(course)
            if refs.get("course_code"):
                course = (
                    db.query(Course).filter(Course.code == refs["course_code"]).first()
                )
                if course:
                    courses.append(course)
            if refs.get("rps_id"):
                rps = db.get(RPS, refs["rps_id"])
                if not rps:
                    raise HTTPException(404, "RPS tidak ditemukan.")
                course = db.get(Course, rps.course_id)
                if course:
                    courses.append(course)
            if actor.role == "dosen" and any(
                c.id not in actor.course_ids for c in courses
            ):
                raise HTTPException(403, "Mata kuliah bukan penugasan Anda.")
            if len({c.id for c in courses}) > 1:
                raise HTTPException(400, "Rujukan mata kuliah dan RPS tidak konsisten.")


@event.listens_for(Session, "do_orm_execute")
def scope_queries(state):
    actor = state.session.info.get("actor")
    if (
        not actor
        or actor.role != "dosen"
        or state.execution_options.get("unscoped_internal")
    ):
        return
    from app.models import (
        Course,
        RPS,
        RPSMeeting,
        RPSFinding,
        Quiz,
        Material,
        Submission,
        Student,
    )

    ids = tuple(state.session.info.get("course_ids", actor.course_ids))
    rps_ids = select(RPS.id).where(RPS.course_id.in_(ids))
    quiz_ids = select(Quiz.id).where(Quiz.course_id.in_(ids))
    for model, condition in (
        (Course, Course.id.in_(ids)),
        (RPS, RPS.course_id.in_(ids)),
        (Quiz, Quiz.course_id.in_(ids)),
        (Material, Material.course_id.in_(ids)),
        (Student, Student.course_id.in_(ids)),
        (Submission, Submission.quiz_id.in_(quiz_ids)),
        (RPSMeeting, RPSMeeting.rps_id.in_(rps_ids)),
        (RPSFinding, RPSFinding.rps_id.in_(rps_ids)),
    ):
        state.statement = state.statement.options(
            with_loader_criteria(model, condition, include_aliases=True)
        )


@event.listens_for(Session, "before_flush")
def grant_new_courses(db, *_):
    actor = db.info.get("actor")
    if not actor or actor.role != "dosen":
        return
    from app.models import Course

    ids = set(db.info.get("course_ids", actor.course_ids))
    for obj in list(db.new):
        if isinstance(obj, Course):
            ids.add(obj.id)
            db.add(CourseAccess(user_id=actor.id, course_id=obj.id))
    db.info["course_ids"] = tuple(ids)


@event.listens_for(Session, "before_flush")
def enforce_write_scope(db, *_):
    """Validate persisted ORM values too; unrecognized JSON keys cannot bypass access."""
    actor = db.info.get("actor")
    if not actor or actor.role != "dosen":
        return
    from app.models import (
        Course,
        RPS,
        RPSMeeting,
        RPSFinding,
        Quiz,
        Material,
        Submission,
        Student,
    )

    ids = set(db.info.get("course_ids", actor.course_ids))
    pending = {(type(obj), obj.id): obj for obj in db.new if hasattr(obj, "id")}

    def parent_course(model, object_id):
        obj = pending.get((model, object_id))
        if obj is not None:
            return obj.course_id
        return (
            db.connection()
            .execute(select(model.course_id).where(model.id == object_id))
            .scalar_one_or_none()
        )

    for obj in list(db.new) + list(db.dirty) + list(db.deleted):
        cid = None
        if isinstance(obj, Course):
            cid = obj.id
            if obj in db.new:
                existing = (
                    db.connection()
                    .execute(select(Course.id).where(Course.code == obj.code))
                    .scalar_one_or_none()
                )
                if existing is not None and existing not in actor.course_ids:
                    raise HTTPException(403, "Kode mata kuliah bukan penugasan Anda.")
        elif isinstance(obj, (RPS, Quiz, Material, Student)):
            cid = obj.course_id
        elif isinstance(obj, Submission):
            cid = parent_course(Quiz, obj.quiz_id)
        elif isinstance(obj, (RPSMeeting, RPSFinding)):
            cid = parent_course(RPS, obj.rps_id)
        else:
            continue
        if cid not in ids:
            raise HTTPException(
                403, "Objek bukan bagian dari mata kuliah yang ditugaskan."
            )
        if (
            isinstance(obj, Material)
            and obj.rps_id
            and parent_course(RPS, obj.rps_id) != obj.course_id
        ):
            raise HTTPException(400, "Mata kuliah materi dan RPS tidak konsisten.")
