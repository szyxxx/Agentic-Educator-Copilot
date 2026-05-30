from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from app.core.database import get_session
from app.models.course import Course
from app.models.rps import RPS
from app.models.rps_meeting import RPSMeeting
from app.models.quiz import Quiz
from app.models.material import Material
from app.models.student import Student

router = APIRouter()


class CoursePayload(BaseModel):
    name: str
    code: str
    sks: int = 3
    semester: int = 1
    program_study: str = ""


@router.get("/")
def list_courses(db: Session = Depends(get_session)):
    """Light list used by dropdowns on quiz/RPS forms."""
    return [
        {
            "id": c.id,
            "name": c.name,
            "code": c.code,
            "sks": c.sks,
            "semester": c.semester,
            "program_study": c.program_study,
        }
        for c in db.query(Course).all()
    ]


@router.post("/")
def create_course(data: CoursePayload, db: Session = Depends(get_session)):
    if db.query(Course).filter(Course.code == data.code).first():
        raise HTTPException(status_code=400, detail="Kode mata kuliah sudah dipakai.")
    course = Course(
        id=f"c-{uuid4().hex[:8]}",
        name=data.name,
        code=data.code,
        sks=data.sks,
        semester=data.semester,
        program_study=data.program_study,
        status="ok",
        status_text="On Track",
        updated_at=datetime.now().strftime("%d %b %Y"),
        pulse_trend=[],
        distribution=[],
        cpmk_progress=[],
        heatmap={},
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return {
        "id": course.id,
        "name": course.name,
        "code": course.code,
        "sks": course.sks,
        "semester": course.semester,
        "program_study": course.program_study,
    }


@router.delete("/{course_id}")
def delete_course(course_id: str, db: Session = Depends(get_session)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Cascade-delete dependents to keep the DB consistent
    rps_ids = [r.id for r in db.query(RPS).filter(RPS.course_id == course_id).all()]
    if rps_ids:
        db.query(RPSMeeting).filter(RPSMeeting.rps_id.in_(rps_ids)).delete(synchronize_session=False)
        db.query(RPS).filter(RPS.id.in_(rps_ids)).delete(synchronize_session=False)
    db.query(Quiz).filter(Quiz.course_id == course_id).delete()
    db.query(Material).filter(Material.course_id == course_id).delete()
    db.query(Student).filter(Student.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    return {"status": "success"}
