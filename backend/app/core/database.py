from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Lightweight ad-hoc migrations for SQLite (Base.metadata.create_all
    # does not add new columns to existing tables).
    _ensure_columns()

    # One-shot data migration: lift legacy meeting rows into the institutional
    # schema (`bahan_kajian_topik`, `sub_topic_title`, ...). Idempotent.
    from app.core.rps_migration import migrate_legacy_meetings

    migrate_legacy_meetings(SessionLocal)

    from app.seed import seed_data

    seed_data(SessionLocal)


def _ensure_columns():
    from sqlalchemy import inspect, text

    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
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
    with engine.begin() as conn:
        for table, cols in needed.items():
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, sqltype in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sqltype}"))
