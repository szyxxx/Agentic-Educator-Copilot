"""Per-question proposals, finalization and quiz-level final-only outcomes."""

from datetime import datetime
from app.agents.grading_agent import grade_mcq_node
from app.models.submission import Submission


def snapshot_scores(quiz, sub, result=None):
    questions = (sub.grading_snapshot or {}).get("questions") or quiz.questions or []
    if result is None and sub.question_scores:
        return [dict(s) for s in sub.question_scores]
    mcq = (result or {}).get("mcq_scores") or grade_mcq_node(
        {"questions": questions, "student_answers": sub.answers}
    )["mcq_scores"]
    essays = (result or {}).get("essay_scores") or []
    values = {s["id"]: s for s in mcq + essays}
    out = []
    for q in questions:
        kind = q.get("type")
        item = values.get(q["id"], {})
        out.append(
            {
                "id": q["id"],
                "type": kind,
                "score": item.get("score"),
                "max_score": float(q.get("weight") or 10)
                if kind == "multiple_choice"
                else float(q.get("max_score") or 30),
                "feedback": item.get("feedback")
                or ("Benar" if item.get("correct") else "Salah")
                if kind == "multiple_choice"
                else item.get("feedback", ""),
                "source": "deterministic" if kind == "multiple_choice" else "llm",
            }
        )
    return out


def total_score(items):
    if not items or any(s.get("score") is None for s in items):
        return None
    maximum = sum(s["max_score"] for s in items)
    return round(sum(s["score"] for s in items) / maximum * 100, 1) if maximum else 0.0


def refresh_quiz(db, quiz):
    db.flush()
    rows = db.query(Submission).filter(Submission.quiz_id == quiz.id).all()
    pending = [s for s in rows if s.score is None]
    finals = [s.score for s in rows if s.score is not None]
    average = round(sum(finals) / len(finals), 1) if finals else None
    quiz.status = (
        "review"
        if any(s.status in ("needs_review", "manual_review") for s in pending)
        else (
            "active"
            if pending
            else ("attention" if average is not None and average < 60 else "completed")
        )
    )
    quiz.updated_at = datetime.now().strftime("%d %b %Y")
    return average, len(pending)


def create_auto_material(db, quiz, average, pending):
    if pending or average is None:
        return None
    from app.agents.auto_material_agent import generate_post_quiz_material

    weak = []
    for sub in db.query(Submission).filter(Submission.quiz_id == quiz.id).all():
        for item in sub.question_scores or []:
            if (
                item.get("score") is not None
                and item["score"] < item["max_score"] * 0.6
            ):
                q = next((q for q in quiz.questions or [] if q["id"] == item["id"]), {})
                topic = q.get("question", item["id"])[:200]
                if topic not in weak:
                    weak.append(topic)
    try:
        return generate_post_quiz_material(
            db, quiz=quiz, average_score=average, weak_topics=weak[:5]
        )
    except Exception:
        db.rollback()
        return None
