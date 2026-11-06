from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.rps import router as rps_router
from app.api.v1.quiz import router as quiz_router
from app.api.v1.grading import router as grading_router
from app.core.database import init_db

app = FastAPI(title="EduCopilot API")

from app.core import audit  # Registers transactional audit hooks.
from app.core.auth import AuthenticationMiddleware, allowed_origins

app.add_middleware(AuthenticationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.auth import router as auth_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
from app.api.v1.audit import router as audit_router

app.include_router(audit_router, prefix="/api/audit", tags=["audit"])

app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(rps_router, prefix="/api/rps", tags=["rps"])
app.include_router(quiz_router, prefix="/api/quiz", tags=["quiz"])
app.include_router(grading_router, prefix="/api/grading", tags=["grading"])

from app.api.v1.courses import router as courses_router
from app.api.v1.materials import router as materials_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.students import router as students_router
from app.api.v1.settings import router as settings_router

app.include_router(courses_router, prefix="/api/courses", tags=["courses"])
app.include_router(materials_router, prefix="/api/materials", tags=["materials"])
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(students_router, prefix="/api/students", tags=["students"])
app.include_router(settings_router, prefix="/api/settings", tags=["settings"])


@app.on_event("startup")
def on_startup():
    from pathlib import Path
    from app.core.database import engine
    from app.core.recovery import DatabaseLease

    lease = None
    if engine.url.database not in (None, "", ":memory:"):
        # Lock the path before any migration writes. Missing parent is a clear startup error.
        parent = Path(engine.url.database).resolve().parent
        if not parent.exists():
            import os

            if os.getenv("EDUCOPILOT_INIT_DB", "").lower() in (
                "1",
                "true",
            ) or os.getenv("EDUCOPILOT_SEED_DEMO", "").lower() in ("1", "true"):
                parent.mkdir(parents=True, exist_ok=True)
            else:
                raise RuntimeError(
                    "Database tidak ditemukan. Restore backup atau init-db secara eksplisit."
                )
        lease = DatabaseLease(engine.url.database)
    try:
        init_db()
        from app.core.auth import bootstrap_from_env

        bootstrap_from_env()
        app.state.database_lease = lease
    except Exception:
        if lease:
            lease.close()
        raise


@app.on_event("shutdown")
def on_shutdown():
    lease = getattr(app.state, "database_lease", None)
    if lease:
        lease.close()
        app.state.database_lease = None


@app.get("/health")
def health():
    from app.core.database import require_database_present
    from fastapi.responses import JSONResponse

    try:
        require_database_present()
    except RuntimeError:
        return JSONResponse(status_code=503, content={"status": "database_unavailable"})
    return {"status": "ok"}
