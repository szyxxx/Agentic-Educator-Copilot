"""Append-only application audit in the same SQL transaction as domain mutations."""

from contextvars import ContextVar
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
from uuid import uuid4
from sqlalchemy import event, inspect, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent, ObjectRevision

request_context = ContextVar("audit_context", default=None)
TRACKED = {
    "courses",
    "rps",
    "rps_meetings",
    "rps_findings",
    "quizzes",
    "submissions",
    "materials",
    "students",
    "settings",
    "users",
    "course_access",
}
# A content fingerprint identifies an uncommitted deployment as well as committed versions.
_root = Path(__file__).resolve().parents[1]
APPLICATION_VERSION = (
    os.getenv("APPLICATION_VERSION")
    or "code-"
    + hashlib.sha256(
        b"".join(p.read_bytes() for p in sorted(_root.rglob("*.py")))
    ).hexdigest()[:20]
)


def model_used(model):
    ctx = request_context.get()
    if ctx is not None and model not in ctx["models"]:
        ctx["models"].append(model)


def action_for(path, method, kind):
    if method == "DELETE":
        return "delete"
    if "/approve" in path:
        return "approve"
    if "/publish/" in path:
        return "publish"
    if "/grading/" in path and "/review" in path:
        return "grade_edit"
    if "/grading/run/" in path:
        return "grade_propose" if kind == "submissions" else "generate"
    if any(x in path for x in ("generate", "fill-missing")):
        return "generate"
    if path.endswith("/review"):
        return "review"
    if "/auth/" in path:
        return "account_change"
    return "create" if method == "POST" else "update"


def record(
    db, action, kind, object_id, *, actor=None, model=None, details=None, context=None
):
    ctx = context or request_context.get() or {}
    actor = actor or ctx.get("actor") or db.info.get("actor")
    key = {"object_type": kind, "object_id": str(object_id)}
    stmt = insert(ObjectRevision).values(**key, version=1)
    stmt = stmt.on_conflict_do_update(
        index_elements=["object_type", "object_id"],
        set_={"version": ObjectRevision.version + 1},
    ).returning(ObjectRevision.version)
    revision = db.connection().execute(stmt).scalar_one()
    models = list(ctx.get("models", []))
    if not model and not models:
        previous = (
            db.query(AuditEvent)
            .filter(
                AuditEvent.object_type == kind,
                AuditEvent.object_id == str(object_id),
                AuditEvent.llm_model.isnot(None),
            )
            .order_by(AuditEvent.occurred_at.desc())
            .first()
        )
        model = previous.llm_model if previous else None
    if model and model not in models:
        models.append(model)
    details = dict(details or {})
    details["llm_called"] = bool(ctx.get("models"))
    db.add(
        AuditEvent(
            id="audit-" + uuid4().hex,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            actor_id=getattr(actor, "id", None),
            actor_name=getattr(actor, "username", "anonymous"),
            actor_role=getattr(actor, "role", "anonymous"),
            action=action,
            object_type=kind,
            object_id=str(object_id),
            version=revision,
            application_version=APPLICATION_VERSION,
            llm_model=",".join(models) or None,
            request_id=ctx.get("request_id") or uuid4().hex,
            details=details or {},
        )
    )


@event.listens_for(Session, "before_flush")
def audit_instances(db, *_):
    ctx = request_context.get()
    if not ctx or not ctx.get("actor"):
        return
    for obj in list(db.new) + list(db.dirty) + list(db.deleted):
        table = getattr(obj, "__tablename__", None)
        if table not in TRACKED:
            continue
        state = inspect(obj)
        changed = [
            a.key
            for a in state.mapper.column_attrs
            if state.attrs[a.key].history.has_changes()
        ]
        if obj in db.dirty and not changed:
            continue
        primary = [getattr(obj, c.key) for c in state.mapper.primary_key]
        object_id = ":".join(str(v) for v in primary)
        action = action_for(ctx.get("path", ""), ctx.get("method", ""), table)
        if table == "materials":
            if (
                obj in db.new
                and (getattr(obj, "material_type", "") or "").upper() == "AUTO"
            ):
                action = "generate"
            elif obj in db.dirty and set(changed) <= {"index_status", "status_text"}:
                action = "index"
        if obj in db.deleted:
            action = "delete"
        details = {
            "fields": [c for c in changed if c not in ("password_hash",)],
            "object_version": getattr(obj, "version", None),
        }
        record(
            db,
            action,
            table,
            object_id,
            model=getattr(obj, "grading_model", None)
            or getattr(obj, "generation_model", None),
            details=details,
        )


@event.listens_for(Session, "do_orm_execute", retval=True)
def audit_bulk(state):
    ctx = request_context.get()
    mapper = state.bind_mapper
    if (
        not ctx
        or not ctx.get("actor")
        or not (state.is_update or state.is_delete)
        or not mapper
        or mapper.local_table.name not in TRACKED
    ):
        return state.invoke_statement()
    table = mapper.local_table
    stmt = select(*[getattr(mapper.class_, c.key) for c in table.primary_key.columns])
    if state.statement.whereclause is not None:
        stmt = stmt.where(state.statement.whereclause)
    ids = state.session.execute(stmt).all()
    result = state.invoke_statement()
    if result.rowcount:
        for row in ids:
            record(
                state.session,
                action_for(ctx["path"], ctx["method"], table.name),
                table.name,
                ":".join(str(v) for v in row),
                details={"bulk": True},
            )
    return result
