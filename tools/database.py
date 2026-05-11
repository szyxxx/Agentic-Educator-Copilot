"""
Educator Copilot — Database Tool
==================================
SQLite database setup and LangGraph tool for persistent storage.
Handles all CRUD operations and schema initialization.
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime

from langchain_core.tools import tool

DB_PATH = os.getenv("DB_PATH", "educator_copilot.db")


# ── Schema Definition ───────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    preset TEXT DEFAULT 'standard',
    name TEXT NOT NULL,
    name_en TEXT,
    code TEXT NOT NULL,
    credits INTEGER NOT NULL,
    semester INTEGER,
    course_type TEXT,
    description TEXT,
    form_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cpl_cpmk (
    id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    type TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    bloom_level TEXT,
    cpl_refs TEXT,
    aspect TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS rps_weeks (
    week_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    week_number INTEGER NOT NULL,
    type TEXT DEFAULT 'materi',
    title TEXT,
    description TEXT,
    sub_cpmk TEXT,
    learning_indicators TEXT,
    teaching_method TEXT,
    teaching_form TEXT,
    topics TEXT,
    time_tm INTEGER,
    time_pt INTEGER,
    time_bm INTEGER,
    student_activity TEXT,
    assessment_indicators TEXT,
    assessment_weight REAL,
    references_json TEXT,
    status TEXT DEFAULT 'draft',
    dosen_note TEXT,
    approved_at TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS materials (
    material_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    week_number INTEGER,
    filename TEXT,
    file_path TEXT,
    extracted_text TEXT,
    ai_review TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS quiz_sessions (
    quiz_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL,
    week_number INTEGER,
    quiz_type TEXT,
    answer_key TEXT,
    question_mapping TEXT,
    rubric TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE IF NOT EXISTS quiz_results (
    result_id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL,
    student_id TEXT,
    answers TEXT,
    score REAL,
    wrong_questions TEXT,
    ai_feedback TEXT,
    FOREIGN KEY (quiz_id) REFERENCES quiz_sessions(quiz_id)
);

CREATE TABLE IF NOT EXISTS quiz_analysis (
    analysis_id TEXT PRIMARY KEY,
    quiz_id TEXT NOT NULL,
    class_stats TEXT,
    topic_performance TEXT,
    misconceptions TEXT,
    summary_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quiz_sessions(quiz_id)
);

CREATE TABLE IF NOT EXISTS remedial_slides (
    slide_id TEXT PRIMARY KEY,
    quiz_id TEXT,
    course_id TEXT,
    for_week_number INTEGER,
    slide_data TEXT,
    is_approved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_decision_log (
    log_id TEXT PRIMARY KEY,
    session_id TEXT,
    agent_name TEXT,
    step_name TEXT,
    input_summary TEXT,
    output_summary TEXT,
    tool_used TEXT,
    model_used TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode for better concurrency."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_database(db_path: str = None):
    """Initialize the database with all required tables."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def generate_id() -> str:
    """Generate a short unique ID."""
    return str(uuid.uuid4())[:8]


# ── LangGraph Tool ──────────────────────────────────────────────

@tool
def database_tool(action: str, table: str, data: dict = None, query: str = None) -> str:
    """
    Baca atau tulis data ke SQLite database.
    action: 'read' | 'write' | 'update'
    Digunakan untuk menyimpan RPS, quiz results, agent state, dan histori keputusan.
    """
    conn = get_connection()
    try:
        if action == "read" and query:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return json.dumps(result, default=str)

        elif action == "write" and data:
            if "id" not in data and f"{table[:-1]}_id" not in data:
                # Auto-generate ID
                id_field = f"{table[:-1]}_id" if table.endswith("s") else "id"
                if id_field not in data:
                    data[id_field] = generate_id()

            cols = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            conn.execute(
                f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
            conn.commit()
            return json.dumps({"status": "OK", "id": list(data.values())[0]})

        elif action == "update" and data and query:
            set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
            conn.execute(f"UPDATE {table} SET {set_clause} WHERE {query}", list(data.values()))
            conn.commit()
            return json.dumps({"status": "OK"})

        else:
            return json.dumps({"error": f"Invalid action '{action}' or missing parameters"})

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ── Convenience Functions (for Streamlit pages) ─────────────────

def save_course(course_data: dict) -> str:
    """Save course data and return course_id."""
    conn = get_connection()
    course_id = course_data.get("course_id", generate_id())
    conn.execute(
        """INSERT OR REPLACE INTO courses
           (course_id, preset, name, name_en, code, credits, semester,
            course_type, description, form_data, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            course_id,
            course_data.get("preset", "standard"),
            course_data["name"],
            course_data.get("name_en"),
            course_data["code"],
            course_data["credits"],
            course_data.get("semester"),
            course_data.get("course_type"),
            course_data.get("description"),
            json.dumps(course_data),
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return course_id


def save_rps_week(course_id: str, week_data: dict):
    """Save a single RPS week."""
    conn = get_connection()
    week_id = week_data.get("week_id", f"{course_id}_w{week_data['week']}")
    conn.execute(
        """INSERT OR REPLACE INTO rps_weeks
           (week_id, course_id, week_number, type, title, description,
            sub_cpmk, learning_indicators, teaching_method, teaching_form,
            topics, time_tm, time_pt, time_bm, student_activity,
            assessment_indicators, assessment_weight, references_json, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            week_id, course_id, week_data.get("week"),
            week_data.get("type", "materi"),
            week_data.get("title"), week_data.get("description"),
            json.dumps(week_data.get("sub_cpmk", "")),
            json.dumps(week_data.get("learning_indicators", [])),
            week_data.get("teaching_method"),
            week_data.get("teaching_form"),
            json.dumps(week_data.get("topics_covered", [])),
            week_data.get("time_tm"),
            week_data.get("time_pt"),
            week_data.get("time_bm"),
            week_data.get("student_activity"),
            json.dumps(week_data.get("assessment_indicators", "")),
            week_data.get("assessment_weight"),
            json.dumps(week_data.get("references", [])),
            week_data.get("status", "draft"),
        ),
    )
    conn.commit()
    conn.close()


def load_rps_weeks(course_id: str) -> list[dict]:
    """Load all RPS weeks for a course."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM rps_weeks WHERE course_id = ? ORDER BY week_number",
        (course_id,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Parse JSON fields
    for row in rows:
        for json_field in ["sub_cpmk", "learning_indicators", "topics", "assessment_indicators", "references_json"]:
            if row.get(json_field):
                try:
                    row[json_field] = json.loads(row[json_field])
                except (json.JSONDecodeError, TypeError):
                    pass
    return rows


def load_courses() -> list[dict]:
    """Load all courses."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM courses ORDER BY updated_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def update_week_status(week_id: str, status: str, note: str = None):
    """Update a week's approval status."""
    conn = get_connection()
    if status == "disetujui":
        conn.execute(
            "UPDATE rps_weeks SET status = ?, approved_at = ?, dosen_note = ? WHERE week_id = ?",
            (status, datetime.now().isoformat(), note, week_id),
        )
    else:
        conn.execute(
            "UPDATE rps_weeks SET status = ?, dosen_note = ? WHERE week_id = ?",
            (status, note, week_id),
        )
    conn.commit()
    conn.close()


def log_agent_decision(session_id: str, agent_name: str, step_name: str,
                       input_summary: str, output_summary: str,
                       tool_used: str = None, model_used: str = None,
                       tokens_used: int = None):
    """Log an agent decision for auditability."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO agent_decision_log
           (log_id, session_id, agent_name, step_name, input_summary,
            output_summary, tool_used, model_used, tokens_used)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (generate_id(), session_id, agent_name, step_name,
         input_summary, output_summary, tool_used, model_used, tokens_used),
    )
    conn.commit()
    conn.close()


# Auto-initialize on import
init_database()
