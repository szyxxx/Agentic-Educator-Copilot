"""Initial seed data.

Only seeds courses + a few default settings so the UI has something to
render on first run. Everything statistical (pulse trend, grade
distribution, etc.) is computed at request time from actual student /
quiz / submission rows.
"""

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.setting import Setting
from app.models.student import Student

DEFAULT_SETTINGS: dict[str, dict] = {
    "profile.name": {"str_value": "Dosen"},
    "profile.email": {"str_value": ""},
    "profile.institution": {"str_value": ""},
    "profile.semester": {"str_value": "Semester Genap 2025/2026"},
    "notif.quiz_graded": {"bool_value": True},
    "notif.remedial_active": {"bool_value": True},
    "notif.rps_review": {"bool_value": False},
    "system.language": {"str_value": "Bahasa Indonesia"},
    "system.timezone": {"str_value": "WIB (GMT+7)"},
    "system.ai_mode": {"str_value": "Hybrid (Cloud + Local)"},
}


def seed_data(session_factory):
    db: Session = session_factory()
    try:
        _seed_settings(db)
        _seed_sample_courses(db)
        _seed_sample_students(db)
    finally:
        db.close()


def _seed_settings(db: Session):
    existing = {s.key for s in db.query(Setting).all()}
    for key, payload in DEFAULT_SETTINGS.items():
        if key in existing:
            continue
        db.add(
            Setting(
                key=key,
                str_value=payload.get("str_value"),
                bool_value=payload.get("bool_value"),
            )
        )
    db.commit()


def _seed_sample_courses(db: Session):
    # If the user already has any courses, leave them alone
    if db.query(Course).count() > 0:
        return

    samples = [
        {
            "id": "c1",
            "code": "II5003",
            "name": "Applied Artificial Inteligence",
            "sks": 3,
            "semester": 1,
            "program_study": "S2 Sistem dan Teknologi Informasi",
            "academic_year": "2025/2026",
        },
    ]
    for s in samples:
        db.add(
            Course(
                **s,
                students_count=3,
                avg_score=0.0,
                active_quizzes=0,
                pending_grades=0,
                status="ok",
                status_text="On Track",
                pulse_trend=[],
                distribution=[],
                cpmk_progress=[],
                heatmap={},
                insight="",
                updated_at="",
            )
        )
    db.commit()


def _seed_sample_students(db: Session):
    if db.query(Student).count() > 0:
        return

    students = [
        {"id": "s1", "course_id": "c1", "nim": "28225304", "name": "Muhammad Tegar Anghofal"},
        {"id": "s2", "course_id": "c1", "nim": "28225305", "name": "Axel David"},
        {"id": "s3", "course_id": "c1", "nim": "28225308", "name": "Warham Aliansa"},
    ]
    for s in students:
        db.add(Student(**s))
    db.commit()
