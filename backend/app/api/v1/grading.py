from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.agents.grading_agent import build_grading_graph
from app.agents.auto_material_agent import generate_post_quiz_material
from app.core.database import get_session
from app.models.quiz import Quiz
from app.models.submission import Submission

router = APIRouter()


@router.post("/run/{quiz_id}")
def run_auto_grading(quiz_id: str, db: Session = Depends(get_session)):
    """Grade every submission attached to a quiz that hasn't been graded yet."""
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz.questions or []
    answer_key = quiz.answer_key or []

    # Only grade submissions that have at least one answer
    submissions = (
        db.query(Submission)
        .filter(Submission.quiz_id == quiz_id, Submission.score.is_(None))
        .all()
    )
    submissions = [s for s in submissions if s.answers]

    if not submissions:
        return {
            "status": "success",
            "message": "Tidak ada submission yang bisa dinilai.",
            "data": {
                "graded_count": 0,
                "average_score": 0.0,
                "weak_topics": [],
                "overall_feedback": (
                    "Tidak ada submission. Upload CSV jawaban mahasiswa terlebih dahulu."
                ),
            },
        }

    graph = build_grading_graph()
    scores: list[float] = []
    weak_topics_pool: list[str] = []
    overall_feedback_pool: list[str] = []

    for sub in submissions:
        state = {
            "quiz_id": quiz_id,
            "student_id": sub.student_id or "",
            "nim": sub.nim,
            "questions": questions,
            "answer_key": answer_key,
            "student_answers": sub.answers or {},
            "mcq_scores": [],
            "essay_scores": [],
            "total_score": 0.0,
            "feedback_per_question": [],
            "overall_feedback": "",
            "weak_topics": [],
            "messages": [],
        }
        try:
            result = graph.invoke(state)
        except Exception as e:
            print(f"[grading] {sub.id} failed: {e}")
            continue

        sub.score = float(result.get("total_score") or 0.0)
        sub.feedback = result.get("overall_feedback") or ""
        sub.status = "graded"
        scores.append(sub.score)
        weak_topics_pool.extend(result.get("weak_topics") or [])
        if sub.feedback:
            overall_feedback_pool.append(sub.feedback)

    if not scores:
        db.commit()
        return {
            "status": "error",
            "message": "Penilaian gagal untuk semua submission.",
            "data": {
                "graded_count": 0,
                "average_score": 0.0,
                "weak_topics": [],
                "overall_feedback": "Cek log server.",
            },
        }

    average = round(sum(scores) / len(scores), 1)
    quiz.progress_percent = 100
    quiz.status = "attention" if average < 60 else "completed"
    quiz.updated_at = datetime.now().strftime("%d %b %Y")
    db.commit()

    # De-dup weak topics, keep most-mentioned first
    from collections import Counter

    most_common = [t for t, _ in Counter(weak_topics_pool).most_common(5)]

    # Auto-generate next-week study material from this quiz's outcome.
    # Best-effort: any failure here must not break the grading response.
    auto_material_id: str | None = None
    auto_material_week: int | None = None
    try:
        material = generate_post_quiz_material(
            db,
            quiz=quiz,
            average_score=average,
            weak_topics=most_common,
        )
        if material is not None:
            auto_material_id = material.id
            auto_material_week = material.week
    except Exception as e:
        print(f"[grading] auto-material generation failed: {e}")

    summary_feedback = (
        f"{len(scores)} submission dinilai. Rata-rata {average}."
        + (f" Topik terlemah: {', '.join(most_common)}." if most_common else "")
    )

    return {
        "status": "success",
        "message": "Auto-grading selesai.",
        "data": {
            "graded_count": len(scores),
            "average_score": average,
            "total_score": average,  # backward compat with current frontend
            "weak_topics": most_common,
            "overall_feedback": summary_feedback,
            "auto_material_id": auto_material_id,
            "auto_material_week": auto_material_week,
        },
    }
