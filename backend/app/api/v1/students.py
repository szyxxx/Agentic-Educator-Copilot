import csv
import io
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.models.course import Course
from app.models.student import Student

router = APIRouter()


class StudentPayload(BaseModel):
    course_id: str
    nim: str
    name: str
    email: Optional[str] = None


class BulkPayload(BaseModel):
    course_id: str
    students: List[StudentPayload]


def _refresh_count(db: Session, course_id: str):
    """Keep the cached `students_count` on the course in sync."""
    count = db.query(Student).filter(Student.course_id == course_id).count()
    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        course.students_count = count
        course.updated_at = datetime.now().strftime("%d %b %Y")
        db.commit()


@router.get("/")
def list_students(course_id: str, db: Session = Depends(get_session)):
    rows = (
        db.query(Student)
        .filter(Student.course_id == course_id)
        .order_by(Student.nim.asc())
        .all()
    )
    return [
        {
            "id": s.id,
            "course_id": s.course_id,
            "nim": s.nim,
            "name": s.name,
            "email": s.email,
        }
        for s in rows
    ]


@router.post("/")
def add_student(payload: StudentPayload, db: Session = Depends(get_session)):
    if not db.query(Course).filter(Course.id == payload.course_id).first():
        raise HTTPException(status_code=404, detail="Course not found")

    nim = payload.nim.strip()
    if not nim:
        raise HTTPException(status_code=400, detail="NIM tidak boleh kosong.")
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Nama tidak boleh kosong.")

    existing = (
        db.query(Student)
        .filter(Student.course_id == payload.course_id, Student.nim == nim)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail=f"NIM {nim} sudah terdaftar.")

    student = Student(
        id=f"s-{uuid4().hex[:10]}",
        course_id=payload.course_id,
        nim=nim,
        name=payload.name.strip(),
        email=(payload.email or "").strip() or None,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    _refresh_count(db, payload.course_id)
    return {"id": student.id, "nim": student.nim, "name": student.name}


@router.post("/import")
async def import_students_csv(
    course_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    """Import a CSV with at least `nim` and `name` columns. `email` optional.

    Header detection is forgiving: column order doesn't matter, and the keys
    are matched case-insensitively (so `NIM`, `Nama`, `Nama Mahasiswa`, etc. work).
    """
    if not db.query(Course).filter(Course.id == course_id).first():
        raise HTTPException(status_code=404, detail="Course not found")

    raw = await file.read()
    text = raw.decode("utf-8-sig", errors="ignore")

    # Sniff delimiter (comma vs semicolon — common in Indonesian Excel exports)
    sample = text.splitlines()[:5]
    sample_text = "\n".join(sample)
    try:
        dialect = csv.Sniffer().sniff(sample_text, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV kosong atau tanpa header.")

    # Build a normalized header → original-key lookup
    def norm(s: str) -> str:
        return (s or "").strip().lower()

    header_map = {norm(h): h for h in reader.fieldnames}

    def pick(row: dict, *aliases: str) -> str:
        for a in aliases:
            key = header_map.get(norm(a))
            if key and row.get(key) is not None:
                value = str(row.get(key) or "").strip()
                if value:
                    return value
        return ""

    existing_nims = {
        s.nim
        for s in db.query(Student.nim).filter(Student.course_id == course_id).all()
    }

    added = 0
    skipped: List[dict] = []
    seen_nims: set[str] = set()

    for idx, row in enumerate(reader, start=2):  # start=2 to account for header
        nim = pick(row, "nim", "no_induk", "no induk")
        name = pick(row, "name", "nama", "nama mahasiswa")
        email = pick(row, "email", "e-mail")

        if not nim or not name:
            skipped.append({"row": idx, "reason": "Kolom nim/nama kosong"})
            continue
        if nim in existing_nims or nim in seen_nims:
            skipped.append({"row": idx, "reason": f"NIM {nim} duplikat"})
            continue

        db.add(
            Student(
                id=f"s-{uuid4().hex[:10]}",
                course_id=course_id,
                nim=nim,
                name=name,
                email=email or None,
            )
        )
        seen_nims.add(nim)
        added += 1

    db.commit()
    _refresh_count(db, course_id)
    return {"added": added, "skipped": skipped}


@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_session)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    course_id = student.course_id
    db.delete(student)
    db.commit()
    _refresh_count(db, course_id)
    return {"status": "success"}


@router.delete("/")
def clear_students(course_id: str, db: Session = Depends(get_session)):
    """Remove every student enrolled in the given course."""
    db.query(Student).filter(Student.course_id == course_id).delete()
    db.commit()
    _refresh_count(db, course_id)
    return {"status": "success"}
