"""Aggregations used by the dashboard endpoints.

Everything in here is computed on demand from concrete tables (Quiz,
Submission, Student, Material). No mock numbers, no defaults baked in.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.material import Material
from app.models.quiz import Quiz
from app.models.rps import RPS
from app.models.rps_meeting import RPSMeeting
from app.models.student import Student
from app.models.submission import Submission


# ---------------------------------------------------------------------------
# Per-course analytics
# ---------------------------------------------------------------------------


def submission_scores(db: Session, course_id: str) -> list[float]:
    """All graded submission scores for a course's quizzes."""
    quiz_ids = [
        q.id for q in db.query(Quiz.id).filter(Quiz.course_id == course_id).all()
    ]
    if not quiz_ids:
        return []
    rows = (
        db.query(Submission.score)
        .filter(Submission.quiz_id.in_(quiz_ids), Submission.score.isnot(None))
        .all()
    )
    return [float(r[0]) for r in rows]


def unique_submitters(db: Session, course_id: str) -> int:
    """Count distinct NIMs that have at least one submission for this course's quizzes."""
    quiz_ids = [
        q.id for q in db.query(Quiz.id).filter(Quiz.course_id == course_id).all()
    ]
    if not quiz_ids:
        return 0
    from sqlalchemy import distinct
    return (
        db.query(distinct(Submission.nim))
        .filter(Submission.quiz_id.in_(quiz_ids))
        .count()
    )


def avg_score(db: Session, course_id: str) -> float:
    scores = submission_scores(db, course_id)
    return round(sum(scores) / len(scores), 1) if scores else 0.0


def pass_rate(db: Session, course_id: str, passing: float = 60.0) -> float:
    scores = submission_scores(db, course_id)
    if not scores:
        return 0.0
    passed = sum(1 for s in scores if s >= passing)
    return round(passed / len(scores) * 100, 1)


def distribution(db: Session, course_id: str) -> list[dict]:
    """Bucket students by their average score across all course quizzes."""
    student_avg = _student_average_scores(db, course_id)
    buckets = [
        {"label": "A (90-100)", "lo": 90, "hi": 101, "color": "bg-emerald-500"},
        {"label": "B (75-89)", "lo": 75, "hi": 90, "color": "bg-teal-500"},
        {"label": "C (60-74)", "lo": 60, "hi": 75, "color": "bg-amber-500"},
        {"label": "D (<60)", "lo": 0, "hi": 60, "color": "bg-rose-500"},
    ]
    out = []
    total = len(student_avg)
    for b in buckets:
        count = sum(1 for v in student_avg.values() if b["lo"] <= v < b["hi"])
        percent = round(count / total * 100) if total else 0
        out.append(
            {
                "label": b["label"],
                "value": f"{count} mhs",
                "percent": percent,
                "color": b["color"],
            }
        )
    return out


def _student_average_scores(db: Session, course_id: str) -> dict[str, float]:
    """Map nim → average score across the course's submitted quizzes."""
    quiz_ids = [
        q.id for q in db.query(Quiz.id).filter(Quiz.course_id == course_id).all()
    ]
    if not quiz_ids:
        return {}
    rows = (
        db.query(Submission.nim, Submission.score)
        .filter(Submission.quiz_id.in_(quiz_ids), Submission.score.isnot(None))
        .all()
    )
    grouped: dict[str, list[float]] = defaultdict(list)
    for nim, score in rows:
        grouped[nim].append(float(score))
    return {k: sum(v) / len(v) for k, v in grouped.items() if v}


def trend_per_quiz(db: Session, course_id: str) -> list[dict]:
    """Average score of each quiz in chronological order — used as the trend chart."""
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.course_id == course_id)
        .order_by(Quiz.created_at.asc())
        .all()
    )
    out = []
    for idx, quiz in enumerate(quizzes, start=1):
        scores = (
            db.query(Submission.score)
            .filter(Submission.quiz_id == quiz.id, Submission.score.isnot(None))
            .all()
        )
        if not scores:
            continue
        avg = round(sum(s[0] for s in scores) / len(scores), 1)
        out.append({"label": f"Q{idx}", "value": avg})
    return out


def cpmk_progress(db: Session, course_id: str) -> list[dict]:
    """Show CPMKs from the course's RPS, with a placeholder progress band.

    We don't have an explicit per-question→CPMK mapping yet, so progress is
    derived from the course-wide quiz average. This is intentionally simple
    — once questions carry CPMK tags, this can become per-CPMK accurate.
    """
    rps = db.query(RPS).filter(RPS.course_id == course_id).first()
    if not rps or not rps.cpmk_list:
        return []
    course_avg = avg_score(db, course_id)
    items = []
    for idx, cpmk in enumerate(rps.cpmk_list, start=1):
        progress = int(course_avg)
        if progress >= 75:
            status = "good"
        elif progress >= 60:
            status = "warning"
        else:
            status = "danger"
        items.append(
            {
                "id": f"CPMK-{idx}",
                "title": cpmk[:120],
                "progress": progress,
                "status": status,
            }
        )
    return items


def at_risk_heatmap(db: Session, course_id: str) -> dict:
    """Per-student row of quiz statuses (good / mid / low / none).

    Falls back to graded submitters when the roster (Student table) is empty,
    so the heatmap shows real data even before students are formally enrolled.
    """
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.course_id == course_id)
        .order_by(Quiz.created_at.asc())
        .all()
    )
    if not quizzes:
        return {"weeks": [], "students": []}

    quiz_ids = [q.id for q in quizzes]

    by_quiz_nim: dict[int, dict[str, Any]] = defaultdict(dict)
    for q_idx, quiz in enumerate(quizzes):
        rows = (
            db.query(Submission.nim, Submission.score)
            .filter(Submission.quiz_id == quiz.id)
            .all()
        )
        for nim, score in rows:
            by_quiz_nim[q_idx][nim] = score

    # Prefer roster students; fall back to all unique submitting NIMs
    students = (
        db.query(Student)
        .filter(Student.course_id == course_id)
        .order_by(Student.nim.asc())
        .all()
    )

    if students:
        student_list = [(s.nim, s.name) for s in students[:12]]
    else:
        # Collect unique NIMs from submissions, sorted
        seen: dict[str, str] = {}
        for q_idx in range(len(quizzes)):
            subs = (
                db.query(Submission.nim, Submission.name)
                .filter(Submission.quiz_id == quiz_ids[q_idx])
                .all()
            )
            for nim, name in subs:
                if nim not in seen:
                    seen[nim] = name or nim
        student_list = sorted(seen.items())[:12]

    if not student_list:
        return {"weeks": [f"Q{i + 1}" for i in range(len(quizzes))], "students": []}

    def bucket(score) -> str:
        if score is None:
            return "none"
        if score >= 75:
            return "good"
        if score >= 60:
            return "mid"
        return "low"

    rows_out = []
    for nim, name in student_list:
        statuses = [
            bucket(by_quiz_nim[q_idx].get(nim))
            for q_idx in range(len(quizzes))
        ]
        rows_out.append({"name": name, "nim": nim, "status": statuses})

    return {
        "weeks": [f"Q{i + 1}" for i in range(len(quizzes))],
        "students": rows_out,
    }


def insight_for(db: Session, course_id: str) -> str:
    """Auto-generated one-liner about the course's recent performance."""
    scores = submission_scores(db, course_id)
    if not scores:
        return "Belum ada nilai submission. Jalankan auto-grading untuk melihat insight."
    avg = sum(scores) / len(scores)
    pr = pass_rate(db, course_id)
    risk = sum(1 for s in scores if s < 60)
    if avg >= 80:
        verdict = "Performa kelas baik."
    elif avg >= 60:
        verdict = "Performa kelas cukup, perlu perhatian pada CPMK lemah."
    else:
        verdict = "Performa kelas rendah, butuh remedial menyeluruh."
    return (
        f"{verdict} Rata-rata {round(avg, 1)} dari {len(scores)} submission, "
        f"pass rate {pr}% — {risk} mahasiswa di bawah batas lulus."
    )


# ---------------------------------------------------------------------------
# Per-course course-level numbers used in lists
# ---------------------------------------------------------------------------


def refresh_course_metrics(db: Session, course: Course) -> None:
    """Update cached metrics on the Course row from live data."""
    course.students_count = (
        db.query(Student).filter(Student.course_id == course.id).count()
    )
    course.active_quizzes = (
        db.query(Quiz)
        .filter(Quiz.course_id == course.id, Quiz.status == "active")
        .count()
    )
    course.pending_grades = (
        db.query(Submission)
        .join(Quiz, Submission.quiz_id == Quiz.id)
        .filter(Quiz.course_id == course.id, Submission.score.is_(None))
        .count()
    )
    course.avg_score = avg_score(db, course.id)


# ---------------------------------------------------------------------------
# Knowledge-base storage
# ---------------------------------------------------------------------------


def storage_human_size(db: Session) -> str:
    """Best-effort estimate of storage used by uploaded materials."""
    total_bytes = 0
    for m in db.query(Material).all():
        total_bytes += _parse_size(m.size)
    if total_bytes <= 0:
        return "0 KB"
    if total_bytes < 1024 * 1024:
        return f"{total_bytes // 1024} KB"
    if total_bytes < 1024 * 1024 * 1024:
        return f"{total_bytes / (1024 * 1024):.1f} MB"
    return f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"


def _parse_size(label: str | None) -> int:
    if not label:
        return 0
    s = label.strip().upper().replace(" ", "")
    try:
        if s.endswith("KB"):
            return int(float(s[:-2]) * 1024)
        if s.endswith("MB"):
            return int(float(s[:-2]) * 1024 * 1024)
        if s.endswith("GB"):
            return int(float(s[:-2]) * 1024 * 1024 * 1024)
        if s.endswith("B"):
            return int(float(s[:-1]))
    except ValueError:
        return 0
    return 0


# ---------------------------------------------------------------------------
# RPS overview
# ---------------------------------------------------------------------------
#
# SN-DIKTI compliance scoring lives in `app.core.sndikti_catalog.run_catalog`.
# This module used to host a hand-rolled `compliance_checks` function — that
# heuristic is replaced by the deterministic, regulation-cited catalog so the
# score is auditable. Look in `sndikti_catalog.py` for the validators.
