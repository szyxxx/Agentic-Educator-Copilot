from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core import stats
from app.core.stats import unique_submitters
from app.core.sndikti_catalog import run_catalog
from app.models.course import Course
from app.models.material import Material
from app.models.quiz import Quiz
from app.models.rps import RPS
from app.models.rps_meeting import RPSMeeting
from app.models.setting import Setting
from app.models.student import Student
from app.models.submission import Submission

router = APIRouter()


def _setting(db: Session, key: str, default: str | bool = "") -> str | bool:
    row = db.query(Setting).filter(Setting.key == key).first()
    if not row:
        return default
    if isinstance(default, bool):
        return row.bool_value if row.bool_value is not None else default
    return row.str_value or default


@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_session)):
    courses = db.query(Course).all()

    # Refresh cached course metrics so the dashboard never shows stale numbers
    for course in courses:
        stats.refresh_course_metrics(db, course)
    db.commit()

    total_courses = len(courses)
    active_quizzes = db.query(Quiz).filter(Quiz.status == "active").count()
    needs_grading = (
        db.query(Submission)
        .filter(Submission.score.is_(None))
        .count()
    )

    avg_scores_list = [c.avg_score for c in courses if c.avg_score]
    avg_score = (
        round(sum(avg_scores_list) / len(avg_scores_list), 1)
        if avg_scores_list
        else 0
    )

    stats_blocks = [
        {
            "label": "Mata Kuliah Aktif",
            "value": str(total_courses),
            "note": "Mata kuliah terdaftar",
        },
        {
            "label": "Kuis Aktif",
            "value": str(active_quizzes),
            "note": "Sedang berjalan",
        },
        {
            "label": "Perlu Dinilai",
            "value": str(needs_grading),
            "note": "Submission menunggu nilai",
        },
        {
            "label": "Rata-rata Nilai",
            "value": f"{avg_score}",
            "note": "Rata-rata seluruh kelas",
        },
    ]

    course_pulse = []
    for course in courses:
        trend = stats.trend_per_quiz(db, course.id)
        course_pulse.append(
            {
                "course": course.name,
                "avg": f"{course.avg_score:.1f}",
                "trend": [t["value"] for t in trend],
            }
        )

    alerts = []
    for course in courses:
        if course.avg_score and course.avg_score < 60:
            alerts.append(
                {
                    "id": course.id,
                    "title": f"{course.name} di bawah batas lulus",
                    "note": f"Rata-rata {course.avg_score:.1f}. Pertimbangkan remedial.",
                }
            )
        rps = db.query(RPS).filter(RPS.course_id == course.id).first()
        if rps and rps.status != "validated":
            alerts.append(
                {
                    "id": f"rps-{course.id}",
                    "title": f"RPS {course.name} belum disetujui",
                    "note": f"Status: {rps.status}.",
                }
            )
    if not alerts:
        alerts.append(
            {
                "id": "ok",
                "title": "Semua kelas stabil",
                "note": "Tidak ada isu utama saat ini.",
            }
        )

    recent_activities = []
    for q in db.query(Quiz).order_by(Quiz.created_at.desc()).limit(3).all():
        recent_activities.append(
            {
                "id": f"q_{q.id}",
                "type": "info",
                "message": f"Kuis '{q.title}' diperbarui",
            }
        )
    for r in db.query(RPS).order_by(RPS.created_at.desc()).limit(3).all():
        c = db.query(Course).filter(Course.id == r.course_id).first()
        c_name = c.name if c else ""
        recent_activities.append(
            {
                "id": f"r_{r.id}",
                "type": "success",
                "message": f"RPS {c_name} diperbarui",
            }
        )

    calendar = []
    for q in db.query(Quiz).filter(Quiz.status == "active").all():
        c = db.query(Course).filter(Course.id == q.course_id).first()
        calendar.append(
            {
                "id": q.id,
                "title": q.title,
                "course": c.name if c else "",
                "date": "Tenggat: " + (q.time_left or "N/A"),
                "time": "23:59",
            }
        )

    # Focus actions — derive percentages from concrete state
    total_quizzes = db.query(Quiz).count() or 1
    total_subs = db.query(Submission).count()
    review_pct = (
        int(round(needs_grading / total_subs * 100)) if total_subs else 0
    )
    monitor_pct = int(round(active_quizzes / total_quizzes * 100))
    rps_total = db.query(RPS).count() or 1
    rps_validated = db.query(RPS).filter(RPS.status == "validated").count()
    rps_pct = int(round(rps_validated / rps_total * 100))

    educator_name = _setting(db, "profile.name", "Dosen") or "Dosen"
    semester = _setting(db, "profile.semester", "") or ""

    return {
        "educator": {"name": educator_name, "semester": semester},
        "stats_blocks": stats_blocks,
        "course_pulse": course_pulse,
        "recent_activities": recent_activities,
        "alerts": alerts,
        "calendar": calendar,
        "focus_actions": [
            {"label": "Submission menunggu nilai", "value": review_pct, "color": "bg-rose-500"},
            {"label": "Monitoring kuis aktif", "value": monitor_pct, "color": "bg-teal-500"},
            {"label": "RPS sudah disetujui", "value": rps_pct, "color": "bg-amber-500"},
        ],
    }


@router.get("/rps")
def get_rps_list(db: Session = Depends(get_session)):
    rps_items = db.query(RPS).all()
    courses = {course.id: course for course in db.query(Course).all()}

    items = []
    for rps in rps_items:
        course = courses.get(rps.course_id)
        if not course:
            continue
        items.append(
            {
                "id": rps.id,
                "course": course.name,
                "details": f"{course.program_study} | {course.sks} SKS | Smt {course.semester}",
                "status": "compliant" if rps.status == "validated" else "warning",
                "status_text": "Compliant SN-Dikti" if rps.status == "validated" else "Perlu Review CPL",
                "compliance_score": int(rps.compliance_score),
                "issues_count": rps.issues_count,
                "updated_at": rps.updated_at,
            }
        )

    compliant_count = len([i for i in items if i["status"] == "compliant"])

    return {
        "summary": [
            {"label": "Total RPS", "value": str(len(items)), "note": "Semester aktif"},
            {"label": "Compliant", "value": str(compliant_count), "note": "Sudah disetujui"},
            {
                "label": "Perlu Review",
                "value": str(len(items) - compliant_count),
                "note": "Belum disetujui",
            },
        ],
        "items": items,
    }


@router.get("/rps/{rps_id}")
def get_rps_detail(rps_id: str, db: Session = Depends(get_session)):
    rps = db.query(RPS).filter(RPS.id == rps_id).first()
    if not rps:
        raise HTTPException(status_code=404, detail="RPS not found")

    course = db.query(Course).filter(Course.id == rps.course_id).first()
    meetings = (
        db.query(RPSMeeting)
        .filter(RPSMeeting.rps_id == rps.id)
        .order_by(RPSMeeting.week_number)
        .all()
    )

    compliance_report = run_catalog(rps, meetings, course=course)
    failed = sum(1 for r in compliance_report.criteria if not r.passed)
    rps.issues_count = failed
    rps.compliance_score = float(compliance_report.score)
    db.commit()

    return {
        "id": rps.id,
        "status": rps.status,
        "course": course.name if course else "",
        "course_id": course.id if course else "",
        "feedback": rps.feedback or "",
        "details": f"{course.program_study} | {course.sks} SKS | Smt {course.semester}"
        if course
        else "",
        "cpl_list": rps.cpl_list or [],
        "cpmk_list": rps.cpmk_list or [],
        "references_list": rps.references_list or [],
        "bahan_kajian": rps.bahan_kajian or [],
        "learning_methods": rps.learning_methods or [],
        "learning_modality": rps.learning_modality or "",
        "summary": [
            {
                "label": "Compliance",
                "value": f"{int(rps.compliance_score)}%",
                "note": "Target tercapai" if rps.compliance_score >= 85 else "Butuh review",
            },
            {
                "label": "CPMK Aktif",
                "value": str(len(rps.cpmk_list or [])),
                "note": "Selaras CPL",
            },
            {
                "label": "Referensi",
                "value": str(len(rps.references_list or [])),
                "note": "Termasuk yang diunggah",
            },
        ],
        "compliance": [
            {
                "label": r.title,
                "status": "ok" if r.passed else (
                    "danger" if r.severity == "critical" else "warning"
                ),
                "status_text": "OK" if r.passed else r.severity.capitalize(),
                "note": r.detail or "",
            }
            for r in compliance_report.criteria
        ],
        "compliance_summary": {
            "score": compliance_report.score,
            "earned_weight": compliance_report.earned_weight,
            "total_weight": compliance_report.total_weight,
            "regulation_summary": compliance_report.regulation_summary,
        },
        "meetings": [
            {
                "week": f"W{meeting.week_number}",
                "week_number": meeting.week_number,
                "is_exam_week": meeting.week_number in (8, 16),

                # Institutional schema
                "bahan_kajian_topik": meeting.bahan_kajian_topik or "",
                "sub_topic_title": meeting.sub_topic_title or "",
                "sub_topic_description": meeting.sub_topic_description or "",
                "cpmk_number": meeting.cpmk_number,
                "reference_indices": meeting.reference_indices or [],

                # Legacy fields kept for one transition release
                "topic": meeting.topic,
                "cpmk": meeting.cpmk,
                "references": meeting.references,

                # Internal pedagogy fields (compliance + per-week regenerate)
                "method": meeting.learning_method,
                "evaluation": meeting.evaluation_method,

                "feedback": meeting.feedback or "",
                "status": meeting.status,
                "status_text": meeting.status_text,
            }
            for meeting in meetings
        ],
    }


@router.get("/quizzes")
def get_quizzes(db: Session = Depends(get_session)):
    quizzes = db.query(Quiz).all()
    active = [quiz for quiz in quizzes if quiz.status == "active"]
    attention = [quiz for quiz in quizzes if quiz.status == "attention"]
    draft = [quiz for quiz in quizzes if quiz.status == "draft"]

    return {
        "summary": [
            {"label": "Kuis Aktif", "value": str(len(active)), "note": "Sedang berjalan"},
            {"label": "Butuh Review", "value": str(len(attention)), "note": "Nilai rendah"},
            {"label": "Draft", "value": str(len(draft)), "note": "Siap dipublikasikan"},
        ],
        "active": [
            {
                "id": quiz.id,
                "title": quiz.title,
                "course": _course_name(db, quiz.course_id),
                "details": quiz.details,
                "time_left": quiz.time_left,
                "submissions": quiz.submissions,
                "total_students": quiz.total_students,
                "progress_percent": quiz.progress_percent,
            }
            for quiz in active
        ],
        "needs_attention": [
            {
                "id": quiz.id,
                "title": quiz.title,
                "issue": "Mahasiswa nilai < 60 membutuhkan remedial",
            }
            for quiz in attention
        ],
        "draft": [
            {
                "id": quiz.id,
                "title": quiz.title,
                "course": _course_name(db, quiz.course_id),
                "questions": len(quiz.questions or []),
            }
            for quiz in draft
        ],
    }


@router.get("/analytics")
def get_analytics(course_id: str | None = None, db: Session = Depends(get_session)):
    course = None
    if course_id:
        course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        course = db.query(Course).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Refresh cached numbers
    stats.refresh_course_metrics(db, course)
    db.commit()

    avg = stats.avg_score(db, course.id)
    pr = stats.pass_rate(db, course.id)
    risk = sum(1 for s in stats.submission_scores(db, course.id) if s < 60)
    quizzes_total = db.query(Quiz).filter(Quiz.course_id == course.id).count()
    total_submitters = unique_submitters(db, course.id)
    roster_count = course.students_count  # enrolled in roster

    semester = (
        _setting(db, "profile.semester", "")
        or f"Semester {course.semester} {course.academic_year or ''}"
    )

    # Per-student scores for the analytics detail table
    quiz_ids = [q.id for q in db.query(Quiz.id).filter(Quiz.course_id == course.id).all()]
    from collections import defaultdict
    _nim_scores: dict = defaultdict(list)
    _nim_names: dict = {}
    for sub in (
        db.query(Submission)
        .filter(Submission.quiz_id.in_(quiz_ids), Submission.score.isnot(None))
        .all()
    ):
        _nim_scores[sub.nim].append(sub.score)
        _nim_names[sub.nim] = sub.name
    per_student = [
        {
            "nim": nim,
            "name": _nim_names.get(nim, nim),
            "avg_score": round(sum(scores) / len(scores), 1),
            "status": "pass" if sum(scores) / len(scores) >= 60 else "fail",
        }
        for nim, scores in sorted(_nim_scores.items())
    ]

    return {
        "course_overview": {
            "course": course.name,
            "semester": semester,
            "total_students": total_submitters,
            "avg_score": course.avg_score,
            "pass_rate": pr,
            "remedial_students": risk,
        },
        "kpis": [
            {
                "label": "Total Peserta",
                "value": str(total_submitters),
                "note": f"{roster_count} terdaftar di roster",
            },
            {
                "label": "Avg Score",
                "value": f"{course.avg_score}",
                "note": f"Dari {len(stats.submission_scores(db, course.id))} submission",
            },
            {
                "label": "Pass Rate",
                "value": f"{pr}%",
                "note": "≥ 60",
            },
            {
                "label": "Remedial",
                "value": str(risk),
                "note": "Nilai < 60",
            },
        ],
        "trend": stats.trend_per_quiz(db, course.id),
        "distribution": stats.distribution(db, course.id),
        "cpmk_progress": stats.cpmk_progress(db, course.id),
        "insight": stats.insight_for(db, course.id),
        "heatmap": stats.at_risk_heatmap(db, course.id),
        "quizzes_total": quizzes_total,
        "per_student": per_student,
    }


@router.get("/courses")
def get_courses(db: Session = Depends(get_session)):
    courses = db.query(Course).all()

    # Refresh metrics from concrete tables before returning
    for course in courses:
        stats.refresh_course_metrics(db, course)
    db.commit()

    total_students = sum(course.students_count for course in courses)
    avg_scores = [c.avg_score for c in courses if c.avg_score]
    avg = round(sum(avg_scores) / len(avg_scores), 1) if avg_scores else 0

    return {
        "summary": [
            {"label": "Kelas Aktif", "value": str(len(courses)), "note": "Mata kuliah aktif"},
            {"label": "Total Mahasiswa", "value": str(total_students), "note": "Semua kelas"},
            {"label": "Avg Score", "value": f"{avg}", "note": "Rata-rata terkini"},
        ],
        "items": [
            {
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "sks": course.sks,
                "semester": course.semester,
                "program_study": course.program_study,
                "students": course.students_count,
                "avg_score": course.avg_score,
                "active_quizzes": course.active_quizzes,
                "status": course.status,
                "status_text": course.status_text,
                "updated_at": course.updated_at,
            }
            for course in courses
        ],
    }


@router.get("/knowledge-base")
def get_knowledge_base(db: Session = Depends(get_session)):
    materials = db.query(Material).all()
    indexed_count = sum(1 for m in materials if m.content_text)

    return {
        "summary": [
            {"label": "Total Materi", "value": str(len(materials)), "note": "Materi terdaftar"},
            {
                "label": "Terindeks",
                "value": str(indexed_count),
                "note": "Terindeks ke RAG",
            },
            {
                "label": "Storage",
                "value": stats.storage_human_size(db),
                "note": "Estimasi dari ukuran file",
            },
        ],
        "materials": [
            {
                "id": material.id,
                "title": material.title,
                "topic": material.topic,
                "type": material.material_type,
                "url": material.url,
                "week": material.week,
                "cpmk": material.cpmk,
                "course_id": material.course_id,
                "rps_id": material.rps_id,
                "status": material.status,
                "status_text": material.status_text,
                "updated_at": material.updated_at,
                "size": material.size,
            }
            for material in materials
        ],
    }


@router.get("/settings")
def get_settings(db: Session = Depends(get_session)):
    return {
        "profile": {
            "name": _setting(db, "profile.name", "") or "",
            "email": _setting(db, "profile.email", "") or "",
            "institution": _setting(db, "profile.institution", "") or "",
            "semester": _setting(db, "profile.semester", "") or "",
        },
        "notifications": [
            {
                "id": "notif.quiz_graded",
                "label": "Kuis selesai dinilai",
                "enabled": bool(_setting(db, "notif.quiz_graded", True)),
            },
            {
                "id": "notif.remedial_active",
                "label": "Remedial aktif",
                "enabled": bool(_setting(db, "notif.remedial_active", True)),
            },
            {
                "id": "notif.rps_review",
                "label": "RPS perlu review",
                "enabled": bool(_setting(db, "notif.rps_review", False)),
            },
        ],
        "system": [
            {
                "label": "Bahasa",
                "value": _setting(db, "system.language", "Bahasa Indonesia"),
            },
            {
                "label": "Zona Waktu",
                "value": _setting(db, "system.timezone", "WIB (GMT+7)"),
            },
            {
                "label": "Mode AI",
                "value": _setting(db, "system.ai_mode", "Hybrid (Cloud + Local)"),
            },
        ],
    }


def _course_name(db: Session, course_id: str) -> str:
    course = db.query(Course).filter(Course.id == course_id).first()
    return course.name if course else ""
