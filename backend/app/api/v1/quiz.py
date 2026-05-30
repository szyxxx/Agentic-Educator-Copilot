from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from typing import List, Dict, Any, Optional
import csv
import io
import re

from app.agents.quiz_agent import build_quiz_graph
from app.core.database import get_session
from app.models.quiz import Quiz
from app.models.student import Student
from app.models.submission import Submission

router = APIRouter()


class QuizConfig(BaseModel):
    """Shared configuration for both manual and AI quiz creation."""

    course_id: str
    week_number: int = 1
    quiz_type: str = "mixed"  # multiple_choice | essay | mixed
    difficulty_level: str = "medium"
    num_questions: int = 5
    title: Optional[str] = None


class QuizGenerationRequest(QuizConfig):
    material_content: str = ""


class QuizManualRequest(QuizConfig):
    questions: List[Dict[str, Any]] = []


def _build_title(cfg: QuizConfig, default_prefix: str) -> str:
    if cfg.title:
        return cfg.title
    return f"{default_prefix} Minggu {cfg.week_number}"


def _build_details(cfg: QuizConfig, num: int) -> str:
    label_map = {
        "multiple_choice": "MCQ",
        "essay": "Esai",
        "mixed": "MCQ + Esai",
    }
    return f"{num} soal | {label_map.get(cfg.quiz_type, cfg.quiz_type)}"


@router.post("/generate")
def generate_quiz(request: QuizGenerationRequest, db: Session = Depends(get_session)):
    graph = build_quiz_graph()
    initial_state = {
        "material_content": request.material_content,
        "course_id": request.course_id,
        "week_number": request.week_number,
        "quiz_type": request.quiz_type,
        "difficulty_level": request.difficulty_level,
        "num_questions": request.num_questions,
        "generated_questions": [],
        "answer_key": [],
        "validated": False,
        "messages": [],
    }
    try:
        result = graph.invoke(initial_state)
        questions = result.get("generated_questions", [])
        answer_key = result.get("answer_key", [])

        new_quiz = Quiz(
            id=f"q-{uuid4().hex[:8]}",
            course_id=request.course_id,
            title=_build_title(request, "AI Draft Kuis"),
            details=_build_details(request, len(questions)),
            status="draft",
            questions=questions,
            answer_key=answer_key,
            week_number=request.week_number or 0,
            time_left="Draft",
            updated_at=datetime.now().strftime("%d %b %Y"),
        )
        db.add(new_quiz)
        db.commit()
        db.refresh(new_quiz)

        return {
            "status": "success",
            "message": "Quiz generation completed successfully and saved to DB.",
            "data": {
                "quiz_id": new_quiz.id,
                "questions": questions,
                "answer_key": answer_key,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
def create_manual_quiz(request: QuizManualRequest, db: Session = Depends(get_session)):
    questions = request.questions or []
    # Build a simple answer key from the question payload
    answer_key = []
    for q in questions:
        if q.get("type") == "essay":
            answer_key.append({"id": q.get("id"), "answer": q.get("rubric")})
        else:
            answer_key.append({"id": q.get("id"), "answer": q.get("correct_answer")})

    quiz = Quiz(
        id=f"q-{uuid4().hex[:8]}",
        course_id=request.course_id,
        title=_build_title(request, "Kuis"),
        details=_build_details(request, len(questions)),
        status="draft",
        questions=questions,
        answer_key=answer_key,
        week_number=request.week_number or 0,
        time_left="Draft",
        updated_at=datetime.now().strftime("%d %b %Y"),
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return {"status": "success", "data": {"quiz_id": quiz.id}}


@router.post("/publish/{quiz_id}")
def publish_quiz(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    quiz.status = "active"
    quiz.time_left = "2 hari"
    students_count = db.query(Student).filter(Student.course_id == quiz.course_id).count()
    quiz.total_students = students_count or 0
    db.commit()
    return {"status": "success", "message": "Quiz published"}


@router.post("/close/{quiz_id}")
def close_quiz(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    quiz.status = "completed"
    quiz.time_left = "Selesai"
    quiz.progress_percent = 100
    db.commit()
    return {"status": "success"}


@router.delete("/{quiz_id}")
def delete_quiz(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    db.query(Submission).filter(Submission.quiz_id == quiz_id).delete()
    db.delete(quiz)
    db.commit()
    return {"status": "success"}


@router.put("/{quiz_id}")
def update_quiz(quiz_id: str, request: QuizManualRequest, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    if quiz.status != "draft":
        raise HTTPException(status_code=400, detail="Hanya kuis draft yang dapat diedit")

    questions = request.questions or []
    answer_key = []
    for q in questions:
        if q.get("type") == "essay":
            answer_key.append({"id": q.get("id"), "answer": q.get("rubric")})
        else:
            answer_key.append({"id": q.get("id"), "answer": q.get("correct_answer")})

    quiz.course_id = request.course_id
    quiz.title = _build_title(request, "Kuis")
    quiz.details = _build_details(request, len(questions))
    quiz.questions = questions
    quiz.answer_key = answer_key
    quiz.week_number = request.week_number or 0
    quiz.updated_at = datetime.now().strftime("%d %b %Y")
    
    db.commit()
    return {"status": "success"}


@router.get("/{quiz_id}")
def get_quiz(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    students_count = db.query(Student).filter(Student.course_id == quiz.course_id).count()
    if quiz.total_students != students_count:
        quiz.total_students = students_count
        if quiz.total_students and quiz.total_students > 0:
            quiz.progress_percent = min(100, int(round((quiz.submissions or 0) / quiz.total_students * 100)))
        db.commit()

    return {
        "id": quiz.id,
        "course_id": quiz.course_id,
        "title": quiz.title,
        "details": quiz.details,
        "status": quiz.status,
        "questions": quiz.questions or [],
        "answer_key": quiz.answer_key or [],
        "week_number": quiz.week_number or 0,
        "time_left": quiz.time_left,
        "submissions": quiz.submissions,
        "total_students": quiz.total_students,
        "progress_percent": quiz.progress_percent,
        "updated_at": quiz.updated_at,
    }


@router.get("/{quiz_id}/template.csv")
def download_template(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
        
    questions = quiz.questions or []
    
    headers = ["NIM Mahasiswa", "Nama Mahasiswa"]
    mcq_count = 1
    essay_count = 1
    
    for q in questions:
        if q.get("type") == "essay":
            headers.append(f"ESSAY-{essay_count}")
            essay_count += 1
        else:
            headers.append(f"PG-{mcq_count}")
            mcq_count += 1
            
    students = db.query(Student).filter(Student.course_id == quiz.course_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    
    for s in students:
        row = [s.nim, s.name] + ([""] * len(questions))
        writer.writerow(row)
        
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=template_{quiz_id}.csv"}
    )



# ---------------------------------------------------------------------------
# Student submissions (CSV upload — one row per student)
# ---------------------------------------------------------------------------


# Column header patterns. Examples:
#   "PG-1", "PG 1", "MCQ-1", "Pilihan Ganda 1"
#   "ESSAY-1", "Esai 1", "ES-1"
MCQ_HEADER_RE = re.compile(r"^(?:pg|mcq|pilihan(?:\s*ganda)?)\s*[-_ ]?\s*(\d+)$", re.I)
ESSAY_HEADER_RE = re.compile(r"^(?:essay|esai|es)\s*[-_ ]?\s*(\d+)$", re.I)
NIM_HEADER_RE = re.compile(r"^(?:nim|no(?:\s*induk)?)\b", re.I)
NAME_HEADER_RE = re.compile(r"^(?:nama(?:\s*mahasiswa)?|name)\b", re.I)


def _normalize_header(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _read_csv_rows(raw: bytes) -> tuple[list[str], list[list[str]]]:
    """Decode a CSV blob and return (header, rows).

    Handles two-row headers (where the first row is just a banner like
    "Jawaban Mahasiswa" spanning answer columns) by picking the first row
    that actually contains a NIM column as the real header.
    """
    text = raw.decode("utf-8-sig", errors="ignore")
    sample = "\n".join(text.splitlines()[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.reader(io.StringIO(text), dialect=dialect)
    all_rows = [row for row in reader if any((cell or "").strip() for cell in row)]
    if not all_rows:
        raise HTTPException(status_code=400, detail="CSV kosong.")

    header_idx = 0
    for i, row in enumerate(all_rows[:3]):
        if any(NIM_HEADER_RE.match(_normalize_header(c)) for c in row):
            header_idx = i
            break

    header = [_normalize_header(c) for c in all_rows[header_idx]]
    rows = all_rows[header_idx + 1 :]
    return header, rows


def _build_column_map(
    header: list[str], questions: list[dict]
) -> tuple[Optional[int], Optional[int], dict[str, int], list[str]]:
    """Match CSV columns to quiz question ids.

    Returns:
        nim_col, name_col, mapping {question_id: column_index}, missing_qids
    """
    mcqs = [q for q in questions if q.get("type") == "multiple_choice"]
    essays = [q for q in questions if q.get("type") == "essay"]

    nim_col = name_col = None
    mcq_cols: dict[int, int] = {}    # 1-based PG number → column index
    essay_cols: dict[int, int] = {}  # 1-based ESSAY number → column index

    for idx, raw in enumerate(header):
        col = _normalize_header(raw)
        if not col:
            continue
        if nim_col is None and NIM_HEADER_RE.match(col):
            nim_col = idx
            continue
        if name_col is None and NAME_HEADER_RE.match(col):
            name_col = idx
            continue
        m = MCQ_HEADER_RE.match(col)
        if m:
            mcq_cols[int(m.group(1))] = idx
            continue
        m = ESSAY_HEADER_RE.match(col)
        if m:
            essay_cols[int(m.group(1))] = idx

    mapping: dict[str, int] = {}
    missing: list[str] = []
    for i, q in enumerate(mcqs, start=1):
        if i in mcq_cols:
            mapping[q["id"]] = mcq_cols[i]
        else:
            missing.append(q["id"])
    for i, q in enumerate(essays, start=1):
        if i in essay_cols:
            mapping[q["id"]] = essay_cols[i]
        else:
            missing.append(q["id"])

    return nim_col, name_col, mapping, missing


def _clean_mcq_answer(value: str) -> Optional[str]:
    """Coerce loose MCQ answers into a single uppercase letter A-D."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"[A-Da-d]", text)
    return match.group(0).upper() if match else None


@router.get("/{quiz_id}/submissions")
def list_submissions(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    rows = (
        db.query(Submission)
        .filter(Submission.quiz_id == quiz_id)
        .order_by(Submission.nim.asc())
        .all()
    )
    return [
        {
            "id": s.id,
            "nim": s.nim,
            "name": s.name,
            "answered_count": s.answered_count or 0,
            "answers": s.answers or {},
            "status": s.status,
            "score": s.score,
            "feedback": s.feedback,
        }
        for s in rows
    ]


@router.post("/{quiz_id}/submissions/upload-csv")
async def upload_submissions_csv(
    quiz_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    """Ingest a CSV where each row is one student's answers.

    Expected layout (header row):

        NIM Mahasiswa, PG-1, PG-2, ..., ESSAY-1, ESSAY-2, ...

    A `Nama Mahasiswa` column is optional — when missing we look the name up
    from the course's roster using the NIM, falling back to "(tanpa nama)".
    Banner rows like "Jawaban Mahasiswa" above the real header are skipped
    automatically.
    """

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz.questions or []
    if not questions:
        raise HTTPException(
            status_code=400,
            detail="Kuis ini belum punya soal — tidak bisa mengimpor jawaban.",
        )

    raw = await file.read()
    header, rows = _read_csv_rows(raw)
    nim_col, name_col, mapping, missing = _build_column_map(header, questions)

    if nim_col is None:
        raise HTTPException(
            status_code=400,
            detail="Kolom NIM tidak ditemukan di header CSV.",
        )
    if not mapping:
        raise HTTPException(
            status_code=400,
            detail="Tidak ada kolom jawaban (PG-x / ESSAY-x) yang dikenali.",
        )

    enrolled = (
        db.query(Student).filter(Student.course_id == quiz.course_id).all()
    )
    enrolled_by_nim = {s.nim: s for s in enrolled}

    existing_nims = {
        s.nim
        for s in db.query(Submission.nim)
        .filter(Submission.quiz_id == quiz_id)
        .all()
    }

    added = 0
    matched = 0
    unmatched: list[dict] = []
    skipped: list[dict] = []

    for line_no, row in enumerate(rows, start=2):
        nim = (row[nim_col].strip() if nim_col < len(row) else "")
        if not nim:
            skipped.append({"row": line_no, "reason": "NIM kosong"})
            continue
        if nim in existing_nims:
            skipped.append({"row": line_no, "reason": f"NIM {nim} sudah punya submission"})
            continue

        # Build the answers dict from the column mapping
        answers: dict[str, Any] = {}
        for q in questions:
            col_idx = mapping.get(q["id"])
            if col_idx is None or col_idx >= len(row):
                continue
            cell = row[col_idx]
            if q.get("type") == "multiple_choice":
                cleaned = _clean_mcq_answer(cell)
                if cleaned:
                    answers[q["id"]] = cleaned
            else:
                text = (cell or "").strip()
                if text:
                    answers[q["id"]] = text

        student = enrolled_by_nim.get(nim)
        if student:
            display_name = student.name
            student_id = student.id
            status = "submitted"
            matched += 1
        else:
            csv_name = (row[name_col].strip() if name_col is not None and name_col < len(row) else "")
            display_name = csv_name or "(tanpa nama)"
            student_id = None
            status = "unmatched"
            unmatched.append({"row": line_no, "nim": nim})

        db.add(
            Submission(
                id=f"sub-{uuid4().hex[:10]}",
                quiz_id=quiz_id,
                student_id=student_id,
                nim=nim,
                name=display_name,
                answers=answers,
                answered_count=len(answers),
                status=status,
            )
        )
        existing_nims.add(nim)
        added += 1

    total_subs = (
        db.query(Submission).filter(Submission.quiz_id == quiz_id).count()
    )
    quiz.submissions = total_subs
    if quiz.total_students and quiz.total_students > 0:
        quiz.progress_percent = min(
            100, int(round(total_subs / quiz.total_students * 100))
        )
    quiz.updated_at = datetime.now().strftime("%d %b %Y")
    db.commit()

    return {
        "added": added,
        "matched": matched,
        "unmatched": unmatched,
        "skipped": skipped,
        "missing_questions": missing,
        "total_submissions": total_subs,
    }


@router.delete("/{quiz_id}/submissions")
def clear_submissions(quiz_id: str, db: Session = Depends(get_session)):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    db.query(Submission).filter(Submission.quiz_id == quiz_id).delete()
    quiz.submissions = 0
    quiz.progress_percent = 0
    db.commit()
    return {"status": "success"}


@router.delete("/{quiz_id}/submissions/{submission_id}")
def delete_submission(
    quiz_id: str, submission_id: str, db: Session = Depends(get_session)
):
    sub = (
        db.query(Submission)
        .filter(Submission.id == submission_id, Submission.quiz_id == quiz_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    db.delete(sub)
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz:
        quiz.submissions = max(0, (quiz.submissions or 0) - 1)
        if quiz.total_students:
            quiz.progress_percent = min(
                100, int(round(quiz.submissions / quiz.total_students * 100))
            )
    db.commit()
    return {"status": "success"}
