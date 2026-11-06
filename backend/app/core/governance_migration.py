"""Idempotent additive migration and one-time human-review gates for legacy data."""

from datetime import datetime, timezone
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker

COLUMNS = {
    "submissions": [
        ("proposed_score", "FLOAT"),
        ("question_scores", "JSON"),
        ("grading_snapshot", "JSON"),
        ("grading_model", "VARCHAR(255)"),
        ("grading_version", "VARCHAR(100)"),
        ("version", "INTEGER NOT NULL DEFAULT 1"),
        ("reviewed_by", "VARCHAR(64)"),
        ("reviewed_at", "VARCHAR(40)"),
        ("review_note", "TEXT"),
    ],
    "materials": [
        ("index_status", "VARCHAR(50) NOT NULL DEFAULT 'not_indexed'"),
        ("generation_model", "VARCHAR(255)"),
        ("source_quiz_id", "VARCHAR(64)"),
        ("version", "INTEGER NOT NULL DEFAULT 1"),
        ("approved_by", "VARCHAR(64)"),
        ("approved_at", "VARCHAR(40)"),
    ],
}


def migrate_governance(engine):
    if engine.dialect.name != "sqlite":
        raise RuntimeError("Migrasi tata kelola ini membutuhkan SQLite.")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS governance_migrations (version VARCHAR PRIMARY KEY, applied_at VARCHAR NOT NULL)"
            )
        )
        inspector = inspect(conn)
        for table, columns in COLUMNS.items():
            present = {c["name"] for c in inspector.get_columns(table)}
            for name, definition in columns:
                if name not in present:
                    conn.execute(
                        text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
                    )
        done = conn.execute(
            text("SELECT 1 FROM governance_migrations WHERE version='human-review-v1'")
        ).first()
    if done:
        return
    from app.models.material import Material
    from app.models.submission import Submission
    from app.models.quiz import Quiz

    with sessionmaker(bind=engine)() as db:
        for material in db.query(Material).all():
            if (material.material_type or "").upper() == "AUTO":
                material.status = "pending_review"
                material.status_text = "Menunggu persetujuan"
                material.index_status = "not_indexed"
                material.approved_by = None
                material.approved_at = None
            else:
                material.index_status = (
                    "indexed"
                    if material.status == "indexed"
                    else (
                        "index_failed"
                        if material.status == "index_failed"
                        else "unverified"
                    )
                )
                material.status = "ready"
                if (
                    material.status_text == "Terindeks"
                    and material.index_status != "indexed"
                ):
                    material.status_text = "Belum diverifikasi"
        quizzes = {q.id: q for q in db.query(Quiz).all()}
        for sub in db.query(Submission).filter(Submission.score.isnot(None)).all():
            quiz = quizzes.get(sub.quiz_id)
            if (
                quiz
                and any(q.get("type") == "essay" for q in (quiz.questions or []))
                and not sub.reviewed_by
            ):
                sub.proposed_score = sub.score
                sub.score = None
                sub.status = "needs_review"
                sub.grading_model = "legacy:unknown"
                sub.grading_version = "legacy-without-question-scores"
                quiz.status = "review"
        db.execute(
            text("INSERT INTO governance_migrations VALUES ('human-review-v1', :now)"),
            {"now": datetime.now(timezone.utc).isoformat()},
        )
        db.commit()
