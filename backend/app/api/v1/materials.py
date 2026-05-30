from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from uuid import uuid4
from datetime import datetime

from app.core.database import get_session
from app.models.material import Material
from app.models.rps import RPS

router = APIRouter()


class MaterialPayload(BaseModel):
    course_id: str
    title: str
    topic: str = ""
    material_type: str = "URL"  # PDF | DOCX | URL | PPT | TEXT
    url: Optional[str] = None
    content_text: Optional[str] = None
    week: int = 1
    cpmk: str = ""
    rps_id: Optional[str] = None
    size: str = "-"


def _index_in_rag(material: Material) -> int:
    """Best-effort index into Chroma. Errors are swallowed so DB save still succeeds."""
    if not material.content_text:
        return 0
    try:
        from app.core.rag import index_material

        return index_material(
            material.content_text,
            metadata={
                "material_id": material.id,
                "course_id": material.course_id or "",
                "rps_id": material.rps_id or "",
                "week": material.week or 0,
                "title": material.title,
                "type": material.material_type,
            },
        )
    except Exception as e:  # pragma: no cover
        print(f"[materials] RAG indexing skipped: {e}")
        return 0


def _save(db: Session, m: Material):
    db.add(m)
    db.commit()
    db.refresh(m)


@router.get("/")
def list_materials(
    rps_id: Optional[str] = None,
    course_id: Optional[str] = None,
    week: Optional[int] = None,
    db: Session = Depends(get_session),
):
    q = db.query(Material)
    if rps_id:
        q = q.filter(Material.rps_id == rps_id)
    if course_id:
        q = q.filter(Material.course_id == course_id)
    if week is not None:
        q = q.filter(Material.week == week)
    return [
        {
            "id": m.id,
            "title": m.title,
            "topic": m.topic,
            "type": m.material_type,
            "url": m.url,
            "week": m.week,
            "cpmk": m.cpmk,
            "course_id": m.course_id,
            "rps_id": m.rps_id,
            "status": m.status,
            "status_text": m.status_text,
            "size": m.size,
            "updated_at": m.updated_at,
            "has_content": bool(m.content_text),
        }
        for m in q.order_by(Material.week.asc(), Material.created_at.desc()).all()
    ]


@router.post("/")
def create_material(data: MaterialPayload, db: Session = Depends(get_session)):
    material = Material(
        id=f"m-{uuid4().hex[:8]}",
        course_id=data.course_id,
        rps_id=data.rps_id,
        title=data.title,
        topic=data.topic,
        material_type=data.material_type,
        url=data.url,
        content_text=data.content_text,
        week=data.week,
        cpmk=data.cpmk,
        status="ready",
        status_text="Terindeks" if data.content_text else "Ready",
        updated_at=datetime.now().strftime("%d %b %Y"),
        size=data.size,
    )
    _save(db, material)
    chunks = _index_in_rag(material)
    return {
        "id": material.id,
        "title": material.title,
        "course_id": material.course_id,
        "rps_id": material.rps_id,
        "indexed_chunks": chunks,
    }


@router.post("/upload")
async def upload_material(
    course_id: str = Form(...),
    title: str = Form(...),
    topic: str = Form(""),
    week: int = Form(1),
    cpmk: str = Form(""),
    rps_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    """Upload a PDF / DOCX / TXT, extract text, store and index it."""
    raw = await file.read()
    filename = file.filename or "upload"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "bin"

    text_content = ""
    if ext == "pdf":
        try:
            import io
            import PyPDF2

            reader = PyPDF2.PdfReader(io.BytesIO(raw))
            text_content = "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:
            print(f"[materials] PDF extraction failed: {e}")
    elif ext in ("txt", "md"):
        try:
            text_content = raw.decode("utf-8", errors="ignore")
        except Exception:
            text_content = ""

    size_kb = len(raw) // 1024
    size_label = f"{size_kb} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"

    # If rps_id is supplied, derive course from it so the upload is consistent
    if rps_id and not course_id:
        rps = db.query(RPS).filter(RPS.id == rps_id).first()
        if rps:
            course_id = rps.course_id

    material = Material(
        id=f"m-{uuid4().hex[:8]}",
        course_id=course_id,
        rps_id=rps_id,
        title=title or filename,
        topic=topic,
        material_type=ext.upper() if ext in ("pdf", "docx", "txt", "md") else "FILE",
        url=None,
        content_text=text_content or None,
        week=week,
        cpmk=cpmk,
        status="ready",
        status_text="Terindeks" if text_content else "Ready",
        updated_at=datetime.now().strftime("%d %b %Y"),
        size=size_label,
    )
    _save(db, material)
    chunks = _index_in_rag(material)
    return {
        "id": material.id,
        "title": material.title,
        "indexed_chunks": chunks,
        "extracted_chars": len(text_content or ""),
    }


@router.get("/{material_id}/content")
def get_material_content(material_id: str, db: Session = Depends(get_session)):
    """Return the extracted text content of a material (used by quiz picker)."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return {
        "id": material.id,
        "title": material.title,
        "type": material.material_type,
        "content_text": material.content_text or "",
        "url": material.url,
        "course_id": material.course_id,
        "rps_id": material.rps_id,
    }


class MaterialAttachment(BaseModel):
    rps_id: Optional[str] = None
    week: Optional[int] = None
    cpmk: Optional[str] = None


@router.patch("/{material_id}")
def update_material(
    material_id: str,
    payload: MaterialAttachment,
    db: Session = Depends(get_session),
):
    """Attach (or detach with `rps_id=null`) an existing material to a week."""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    if payload.rps_id is not None:
        material.rps_id = payload.rps_id or None
    if payload.week is not None:
        material.week = payload.week
    if payload.cpmk is not None:
        material.cpmk = payload.cpmk
    material.updated_at = datetime.now().strftime("%d %b %Y")
    db.commit()
    db.refresh(material)
    return {
        "id": material.id,
        "rps_id": material.rps_id,
        "week": material.week,
        "cpmk": material.cpmk,
    }


@router.delete("/{material_id}")
def delete_material(material_id: str, db: Session = Depends(get_session)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    db.delete(material)
    db.commit()
    return {"status": "success"}
