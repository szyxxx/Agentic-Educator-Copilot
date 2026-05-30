"""Auto-generate remediation/preparatory study material after a quiz is graded.

The grading endpoint calls `generate_post_quiz_material` once it finishes.
The agent looks at the just-graded quiz (its weak topics, average score, and
the questions that tripped the class up), then asks the LLM to write a
short Markdown digest aimed at the **next** RPS week. The digest is stored
as a `Material` row attached to that week and indexed into the RAG store
so future quizzes / RPS regenerations can use it as additional context.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.llm import get_llm
from app.models.course import Course
from app.models.material import Material
from app.models.quiz import Quiz
from app.models.rps import RPS
from app.models.rps_meeting import RPSMeeting

log = logging.getLogger(__name__)


def _format_questions(questions: list[dict] | None, limit: int = 6) -> str:
    if not questions:
        return "(tidak ada data soal)"
    lines: list[str] = []
    for q in questions[:limit]:
        qid = q.get("id") or "?"
        text = (q.get("question") or "").strip()
        qtype = "MCQ" if q.get("type") == "multiple_choice" else "Esai"
        lines.append(f"- [{qid} · {qtype}] {text[:160]}")
    if len(questions) > limit:
        lines.append(f"- ... (+{len(questions) - limit} soal lain)")
    return "\n".join(lines)


def _format_topics(topics: Iterable[str]) -> str:
    cleaned = [t.strip() for t in topics if t and t.strip()]
    if not cleaned:
        return "(tidak ada topik lemah teridentifikasi)"
    return "\n".join(f"- {t[:160]}" for t in cleaned[:8])


def _meeting_label(meeting: RPSMeeting | None, week: int) -> str:
    if meeting:
        title = (meeting.sub_topic_title or meeting.topic or "").strip()
        if title:
            return f"Minggu {week}: {title}"
    return f"Minggu {week}"


def _meeting_topic_blurb(meeting: RPSMeeting | None) -> str:
    """Return the most descriptive label we have for a meeting."""
    if not meeting:
        return "tidak diketahui"
    title = (meeting.sub_topic_title or "").strip()
    desc = (meeting.sub_topic_description or "").strip()
    bahan = (meeting.bahan_kajian_topik or "").strip()
    if title and desc:
        out = f"{title}: {desc}"
    elif title:
        out = title
    else:
        out = (meeting.topic or "tidak diketahui").strip() or "tidak diketahui"
    if bahan:
        out = f"[{bahan}] {out}"
    return out


def generate_post_quiz_material(
    db: Session,
    *,
    quiz: Quiz,
    average_score: float,
    weak_topics: list[str],
) -> Material | None:
    """Generate one auto-material for the week *after* the graded quiz.

    Returns the persisted Material on success, or None if it was skipped
    (no RPS for the course, no next week, or the LLM call failed).
    """
    quiz_week = int(quiz.week_number or 0)
    if quiz_week <= 0:
        log.info("[auto-material] quiz %s has no week_number, skipping", quiz.id)
        return None

    rps = db.query(RPS).filter(RPS.course_id == quiz.course_id).first()
    if not rps:
        log.info("[auto-material] course %s has no RPS yet, skipping", quiz.course_id)
        return None

    next_week = quiz_week + 1
    next_meeting = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps.id, RPSMeeting.week_number == next_week)
        .first()
    )
    if next_week > 16:
        log.info("[auto-material] quiz on last week, no next week to enrich")
        return None

    course = db.query(Course).filter(Course.id == quiz.course_id).first()
    course_name = course.name if course else "Mata Kuliah"

    current_meeting = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps.id, RPSMeeting.week_number == quiz_week)
        .first()
    )

    prompt = f"""
    Anda adalah asisten dosen untuk mata kuliah {course_name}.
    Setelah kuis Minggu {quiz_week} selesai dinilai, susun materi tambahan
    singkat untuk Minggu {next_week} agar mahasiswa siap melanjutkan ke topik
    berikut. Materi akan disimpan sebagai bahan ajar resmi untuk pertemuan
    tersebut, jadi tulis dalam bahasa Indonesia formal dan ringkas.

    Konteks:
    - Topik Minggu {quiz_week} (sumber kuis): {_meeting_topic_blurb(current_meeting)}
    - Topik Minggu {next_week} (target): {_meeting_topic_blurb(next_meeting)}
    - Rata-rata kelas pada kuis: {round(average_score, 1)}/100
    - CPMK yang relevan minggu depan: {(f"CPMK-{next_meeting.cpmk_number}" if next_meeting and next_meeting.cpmk_number else (next_meeting.cpmk if next_meeting else "")) or "-"}

    Topik-topik yang masih lemah pada kuis kemarin (prioritas remediasi):
    {_format_topics(weak_topics)}

    Soal-soal kuis yang dipakai sebagai patokan:
    {_format_questions(quiz.questions or [])}

    Format output (Markdown, total ±400 kata, langsung tanpa preamble):

    # Penguatan Minggu {next_week}: <judul ringkas>

    ## Ringkasan dari Minggu {quiz_week}
    Tiga sampai lima poin singkat tentang miskonsepsi/kelemahan yang muncul.

    ## Persiapan Minggu {next_week}
    Penjelasan konseptual dasar yang harus mahasiswa pegang sebelum sesi.
    Sertakan tautan logis dari topik minggu lalu ke topik minggu depan.

    ## Latihan Mandiri
    Tiga aktivitas mandiri (bisa berupa pertanyaan reflektif atau studi kasus singkat).

    ## Bahan Bacaan Pendukung
    Maksimal tiga referensi akademik kredibel (buku/jurnal/konferensi) — JANGAN gunakan placeholder
    seperti "Materi Minggu X" atau "Buku Panduan".
    """

    try:
        llm = get_llm("complex")
        response = llm.invoke(prompt)
        content = (response.content or "").strip()
        if not content:
            log.warning("[auto-material] LLM returned empty content for quiz %s", quiz.id)
            return None
    except Exception as e:  # pragma: no cover
        log.exception("[auto-material] LLM call failed: %s", e)
        return None

    title = f"Penguatan Minggu {next_week} — {course_name}"
    topic_label = _meeting_label(next_meeting, next_week)
    cpmk_label = (next_meeting.cpmk if next_meeting else "") or ""

    material = Material(
        id=f"m-{uuid4().hex[:8]}",
        course_id=quiz.course_id,
        rps_id=rps.id,
        title=title,
        topic=topic_label[:255],
        material_type="AUTO",
        url=None,
        content_text=content,
        week=next_week,
        cpmk=cpmk_label[:50],
        status="ready",
        status_text="Auto-Generated",
        updated_at=datetime.now().strftime("%d %b %Y"),
        size=f"{max(1, len(content) // 1024)} KB",
    )
    db.add(material)
    db.commit()
    db.refresh(material)

    # RAG indexing is best-effort — never block the grading pipeline on it.
    try:
        from app.core.rag import index_material

        index_material(
            content,
            metadata={
                "material_id": material.id,
                "course_id": material.course_id or "",
                "rps_id": material.rps_id or "",
                "week": material.week or 0,
                "title": material.title,
                "type": material.material_type,
                "auto": True,
                "source_quiz_id": quiz.id,
            },
        )
    except Exception as e:  # pragma: no cover
        log.info("[auto-material] RAG indexing skipped: %s", e)

    log.info(
        "[auto-material] generated material %s for course=%s week=%s (avg=%.1f)",
        material.id,
        quiz.course_id,
        next_week,
        average_score,
    )
    return material
