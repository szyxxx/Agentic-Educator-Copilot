from pathlib import Path
from fastapi import Request

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL


def make_engine(url):
    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    target = create_engine(url, connect_args=args, future=True)
    if url.startswith("sqlite") and target.url.database not in (None, "", ":memory:"):
        path = Path(target.url.database).resolve()

        @event.listens_for(target, "do_connect")
        def connect_existing(dialect, conn_rec, cargs, cparams):
            cargs[0] = path.as_uri() + "?mode=rw"
            cparams["uri"] = True

        @event.listens_for(target, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

    return target


engine = make_engine(DATABASE_URL)
_database_identity = None
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_session(request: Request):
    require_database_present()
    db = SessionLocal()
    actor = getattr(request.state, "user", None)
    if actor:
        db.info["actor"] = actor
    try:
        yield db
    finally:
        db.close()


def init_db(*, target_engine=None, allow_create=False, seed_demo=False):
    """Open an existing database, or provision one only by explicit instruction."""
    import os
    from app import models  # noqa: F401

    target = target_engine or engine
    seed_demo = seed_demo or os.getenv("EDUCOPILOT_SEED_DEMO", "").lower() in (
        "1",
        "true",
    )
    allow_create = (
        allow_create
        or seed_demo
        or os.getenv("EDUCOPILOT_INIT_DB", "").lower() in ("1", "true")
    )
    if target.url.drivername.startswith("sqlite") and target.url.database not in (
        None,
        "",
        ":memory:",
    ):
        path = Path(target.url.database).resolve()
        protected = Path(__file__).resolve().parents[2] / "educopilot.db"
        if path == protected:
            raise RuntimeError(
                "DB contoh repo dilindungi. Pakai salinan melalui DATABASE_URL."
            )
        if not path.exists():
            if not allow_create:
                raise RuntimeError(
                    f"Database tidak ditemukan: {path}. Restore backup atau jalankan init-db secara eksplisit; seed tidak dibuat."
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(mode=0o600, exist_ok=False)
        if not allow_create:
            from sqlalchemy import inspect

            if not inspect(target).has_table("courses"):
                raise RuntimeError(
                    "Database belum diinisialisasi. Jalankan init-db secara eksplisit."
                )
    Base.metadata.create_all(bind=target)
    _ensure_columns(target)
    from app.core.governance_migration import migrate_governance

    migrate_governance(target)
    factory = sessionmaker(bind=target, autocommit=False, autoflush=False)
    from app.core.rps_migration import migrate_legacy_meetings

    migrate_legacy_meetings(factory)
    if seed_demo:
        from app.seed import seed_data

        seed_data(factory)
    if target is engine and target.url.database not in (None, "", ":memory:"):
        global _database_identity
        stat = Path(target.url.database).resolve().stat()
        _database_identity = (stat.st_dev, stat.st_ino)


def require_database_present():
    if engine.url.drivername.startswith("sqlite") and engine.url.database not in (
        None,
        "",
        ":memory:",
    ):
        path = Path(engine.url.database).resolve()
        if not path.is_file():
            raise RuntimeError(
                "Database tidak ditemukan. Backend perlu dihentikan dan backup dipulihkan."
            )
        stat = path.stat()
        if _database_identity and _database_identity != (stat.st_dev, stat.st_ino):
            raise RuntimeError(
                "Database diganti saat backend aktif. Hentikan dan mulai ulang setelah restore."
            )


def _ensure_columns(target=None):
    target = target or engine
    from sqlalchemy import inspect, text

    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(target)
    needed = {
        "materials": [
            ("rps_id", "VARCHAR"),
            ("url", "VARCHAR(1024)"),
            ("content_text", "TEXT"),
        ],
        "rps": [
            ("feedback", "TEXT"),
            ("bahan_kajian", "JSON"),
            ("learning_methods", "JSON"),
            ("learning_modality", "VARCHAR(50)"),
        ],
        "rps_meetings": [
            ("feedback", "TEXT"),
            ("bahan_kajian_topik", "VARCHAR(255)"),
            ("sub_topic_title", "VARCHAR(500)"),
            ("sub_topic_description", "TEXT"),
            ("cpmk_number", "INTEGER"),
            ("reference_indices", "JSON"),
        ],
        "submissions": [
            ("answers", "JSON"),
            ("answered_count", "INTEGER DEFAULT 0"),
        ],
        "quizzes": [
            ("week_number", "INTEGER DEFAULT 0"),
        ],
    }
    with target.begin() as conn:
        for table, cols in needed.items():
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, sqltype in cols:
                if name not in existing:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {sqltype}")
                    )
