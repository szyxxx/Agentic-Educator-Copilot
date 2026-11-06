from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.grading_agent import build_grading_graph
from app.core.database import get_session
from app.core.access import current_user
from app.core.grade_review import (
    snapshot_scores,
    total_score,
    refresh_quiz,
    create_auto_material,
)
from app.models.quiz import Quiz
from app.models.submission import Submission

router = APIRouter()


@router.post("/run/{quiz_id}")
def run_auto_grading(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    submissions = (
        db.query(Submission)
        .filter(
            Submission.quiz_id == quiz_id,
            Submission.score.is_(None),
            Submission.status.in_(["submitted", "unmatched", "manual_review"]),
        )
        .all()
    )
    submissions = [
        s
        for s in submissions
        if s.answers
        and not any(q.get("source") == "human" for q in (s.question_scores or []))
    ]
    if not submissions:
        return {
            "status": "success",
            "message": "Tidak ada submission yang perlu dinilai otomatis. Usulan yang tersedia perlu tinjauan dosen.",
            "data": {
                "graded_count": 0,
                "proposed_count": 0,
                "failed_count": 0,
                "average_score": None,
                "weak_topics": [],
                "overall_feedback": "Tidak ada submission untuk penilaian otomatis.",
            },
        }
    graph = build_grading_graph()
    graded = proposed = failed = conflicts = 0
    proposals = []
    weak = []
    for sub in submissions:
        expected_version = sub.version
        snapshot = {
            "questions": quiz.questions or [],
            "answer_key": quiz.answer_key or [],
        }
        state = {
            "quiz_id": quiz_id,
            "student_id": sub.student_id or "",
            "nim": sub.nim,
            "questions": quiz.questions or [],
            "answer_key": quiz.answer_key or [],
            "student_answers": sub.answers or {},
            "mcq_scores": [],
            "essay_scores": [],
            "total_score": None,
            "feedback_per_question": [],
            "overall_feedback": "",
            "weak_topics": [],
            "messages": [],
        }
        try:
            result = graph.invoke(state)
        except Exception:
            result = {
                "total_score": None,
                "overall_feedback": "Gagal menilai otomatis. Mohon dinilai manual.",
            }
        items = snapshot_scores(quiz, sub, result)
        value = total_score(items) if result.get("total_score") is not None else None
        has_essay = any(q.get("type") == "essay" for q in (quiz.questions or []))
        status = (
            "manual_review"
            if value is None
            else ("needs_review" if has_essay else "graded")
        )
        feedback = result.get("overall_feedback") or ""
        if has_essay and value is not None:
            feedback = "Menunggu tinjauan dosen. " + feedback.replace(
                "Skor total", "Usulan skor", 1
            )
        values = {
            "grading_snapshot": snapshot,
            "question_scores": items,
            "grading_model": result.get("grading_model"),
            "grading_version": "rubric-json-v1",
            "version": expected_version + 1,
            "reviewed_by": None,
            "reviewed_at": None,
            "feedback": feedback,
            "score": value if not has_essay else None,
            "proposed_score": value,
            "status": status,
        }
        changed = (
            db.query(Submission)
            .filter(
                Submission.id == sub.id,
                Submission.version == expected_version,
                Submission.score.is_(None),
                Submission.status.in_(["submitted", "unmatched", "manual_review"]),
            )
            .update(values, synchronize_session=False)
        )
        if changed != 1:
            conflicts += 1
            db.expire(sub)
            continue
        db.refresh(sub)
        if value is None:
            failed += 1
        elif has_essay:
            proposed += 1
            proposals.append(value)
        else:
            graded += 1
        weak.extend(result.get("weak_topics") or [])
    average, pending = refresh_quiz(db, quiz)
    db.commit()
    if conflicts and not (graded or proposed or failed):
        raise HTTPException(
            status_code=409,
            detail="Submission berubah saat inferensi. Hasil otomatis dibuang; tinjauan manusia dipertahankan.",
        )
    if failed and not (graded or proposed):
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "detail": "Penilaian otomatis gagal. Esai perlu penilaian manual atau dinilai ulang; nilai akhir belum ditetapkan.",
                "data": {
                    "graded_count": 0,
                    "proposed_count": 0,
                    "failed_count": failed,
                    "average_score": average,
                    "weak_topics": [],
                },
            },
        )
    material = create_auto_material(db, quiz, average, pending)
    return {
        "status": "partial" if failed else ("needs_review" if proposed else "success"),
        "message": "Usulan nilai esai menunggu tinjauan dosen."
        if proposed
        else "Penilaian selesai.",
        "data": {
            "graded_count": graded,
            "proposed_count": proposed,
            "failed_count": failed,
            "average_score": average,
            "proposed_average": round(sum(proposals) / len(proposals), 1)
            if proposals
            else None,
            "total_score": average,
            "weak_topics": list(dict.fromkeys(weak))[:5],
            "overall_feedback": f"{graded} nilai final, {proposed} usulan perlu ditinjau, {failed} gagal otomatis.",
            "auto_material_id": material.id if material else None,
            "auto_material_week": material.week if material else None,
        },
    }


class EssayEdit(BaseModel):
    id: str
    score: Annotated[float, Field(ge=0, allow_inf_nan=False, strict=True)]
    feedback: str | None = Field(default=None, max_length=4000)


class ReviewEdit(BaseModel):
    version: int = Field(ge=1)
    essay_scores: list[EssayEdit] = Field(min_length=1)
    note: str = Field(default="", max_length=4000)


class Approval(BaseModel):
    version: int = Field(ge=1)
    note: str = Field(default="", max_length=4000)


def _submission(db, id):
    sub = db.query(Submission).filter(Submission.id == id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission tidak ditemukan.")
    quiz = db.query(Quiz).filter(Quiz.id == sub.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Kuis tidak ditemukan.")
    return sub, quiz


@router.patch("/submissions/{submission_id}/review")
def edit_review(
    submission_id: str,
    payload: ReviewEdit,
    db: Session = Depends(get_session),
    user=Depends(current_user),
):
    if user.role not in ("admin", "dosen"):
        raise HTTPException(status_code=403, detail="Peran tidak boleh mengubah nilai.")
    sub, quiz = _submission(db, submission_id)
    items = snapshot_scores(quiz, sub)
    edits = {item.id: item for item in payload.essay_scores}
    if len(edits) != len(payload.essay_scores):
        raise HTTPException(status_code=400, detail="ID esai ganda.")
    by_id = {item["id"]: item for item in items}
    for qid, edit in edits.items():
        item = by_id.get(qid)
        if not item or item["type"] != "essay" or edit.score > item["max_score"]:
            raise HTTPException(
                status_code=400,
                detail="Hanya esai yang dapat diubah, dalam rentang skor soal.",
            )
        if item.get("source") == "llm":
            item.setdefault("llm_score", item.get("score"))
            item.setdefault("llm_feedback", item.get("feedback"))
        item["score"] = edit.score
        item["source"] = "human"
        if edit.feedback is not None:
            item["feedback"] = edit.feedback
    proposal = total_score(items)
    values = {
        "question_scores": items,
        "proposed_score": proposal,
        "score": None,
        "status": "needs_review" if proposal is not None else "manual_review",
        "review_note": payload.note,
        "feedback": f"Usulan nilai diperbarui dosen: {proposal if proposal is not None else 'belum lengkap'}. "
        + " ".join(f"{q['id']}: {q.get('feedback', '')}" for q in items),
        "reviewed_by": None,
        "reviewed_at": None,
        "version": payload.version + 1,
    }
    changed = (
        db.query(Submission)
        .filter(Submission.id == sub.id, Submission.version == payload.version)
        .update(values, synchronize_session=False)
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Versi berubah. Muat ulang sebelum menyimpan."
        )
    db.refresh(sub)
    refresh_quiz(db, quiz)
    db.commit()
    return {
        "status": "needs_review",
        "version": sub.version,
        "proposed_score": sub.proposed_score,
    }


@router.post("/submissions/{submission_id}/approve")
def approve_review(
    submission_id: str,
    payload: Approval,
    db: Session = Depends(get_session),
    user=Depends(current_user),
):
    if user.role not in ("admin", "dosen"):
        raise HTTPException(
            status_code=403, detail="Peran tidak boleh menyetujui nilai."
        )
    sub, quiz = _submission(db, submission_id)
    if sub.version != payload.version or sub.status == "graded":
        raise HTTPException(
            status_code=409, detail="Versi berubah atau nilai telah disetujui."
        )
    if not sub.question_scores or total_score(sub.question_scores) is None:
        raise HTTPException(
            status_code=400,
            detail="Seluruh nilai per soal harus lengkap sebelum persetujuan.",
        )
    final = total_score(sub.question_scores)
    values = {
        "score": final,
        "proposed_score": final,
        "status": "graded",
        "reviewed_by": user.id,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "feedback": f"Nilai final {final} dari 100. Disetujui dosen. "
        + " ".join(f"{q['id']}: {q.get('feedback', '')}" for q in sub.question_scores),
        "review_note": payload.note or sub.review_note,
        "version": payload.version + 1,
    }
    changed = (
        db.query(Submission)
        .filter(Submission.id == sub.id, Submission.version == payload.version)
        .update(values, synchronize_session=False)
    )
    if changed != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Versi berubah. Muat ulang.")
    db.refresh(sub)
    average, pending = refresh_quiz(db, quiz)
    db.commit()
    material = create_auto_material(db, quiz, average, pending)
    return {
        "status": "success",
        "score": sub.score,
        "version": sub.version,
        "auto_material_id": material.id if material else None,
    }
