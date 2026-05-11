"""
Educator Copilot — Learning Cycle Agent (LangGraph Subgraph)
==============================================================
Analyzes quiz results, detects misconceptions, generates remedial slides.

Chain: load_context → score_responses → aggregate_stats → detect_misconceptions
       → prioritize_gaps → generate_summary → generate_remedial → save_state
"""

import json
import uuid
from datetime import datetime

from langgraph.graph import StateGraph, END

from agents.state import EducatorCopilotState
from lib.llm_router import call_llm_with_fallback, get_model_name
from tools.calculator import quiz_calculator_tool, calculate_error_rates, get_problematic_questions
from tools.database import log_agent_decision, get_connection, generate_id


def node_load_context(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    quiz = state.get("quiz_results", {})
    steps.append({"step": "load_context",
                  "result": f"Loaded quiz for week {state.get('current_week', '?')}. "
                            f"{len(quiz.get('student_responses', []))} students.",
                  "timestamp": datetime.now().isoformat()})
    return {"reasoning_steps": steps}


def node_score_responses(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    quiz = state.get("quiz_results", {})
    answer_key = quiz.get("answer_key", {})
    responses = quiz.get("student_responses", [])

    scored = []
    all_scores = []
    for student in responses:
        sid = student.get("student_id", "unknown")
        answers = student.get("answers", {})
        correct = sum(1 for q, a in answers.items() if answer_key.get(q) == a)
        total = len(answer_key) if answer_key else 1
        score = round(correct / total * 100, 1)
        all_scores.append(score)
        wrong = [q for q, a in answers.items() if answer_key.get(q) != a]
        scored.append({"student_id": sid, "score": score, "correct": correct,
                       "total": total, "wrong_questions": wrong})

    stats = quiz_calculator_tool.invoke(all_scores) if all_scores else {}

    steps.append({"step": "score_responses",
                  "result": f"{len(scored)} students scored. Mean: {stats.get('mean', 0)}, "
                            f"Below KKM: {stats.get('pct_below_kkm', 0)}%",
                  "timestamp": datetime.now().isoformat()})
    return {"scored_students": scored, "class_stats": stats, "reasoning_steps": steps}


def node_aggregate_stats(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    scored = state.get("scored_students", [])
    quiz = state.get("quiz_results", {})
    answer_key = quiz.get("answer_key", {})
    q_mapping = quiz.get("question_mapping", {})

    error_rates = calculate_error_rates(scored, answer_key, q_mapping)
    problematic = get_problematic_questions(error_rates)

    steps.append({"step": "aggregate_stats",
                  "result": f"{len(problematic)} questions with >40% error rate.",
                  "timestamp": datetime.now().isoformat()})
    return {"error_rates": error_rates, "reasoning_steps": steps}


def node_detect_misconceptions(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    error_rates = state.get("error_rates", {})
    problematic = get_problematic_questions(error_rates)

    if not problematic:
        steps.append({"step": "detect_misconceptions",
                      "result": "No significant misconceptions detected.",
                      "timestamp": datetime.now().isoformat()})
        return {"detected_gaps": [], "reasoning_steps": steps}

    prompt = f"""Analisis pola kesalahan mahasiswa pada kuis berikut.
Soal dengan error rate tinggi: {json.dumps(problematic, indent=2)}
Konteks materi: {state.get('week_material_summary', 'N/A')}

Identifikasi 2-4 miskonsepsi. Output JSON array (tanpa fence):
[{{"misconception":"...","affected_topics":["..."],"likely_cause":"...","severity":"high|medium"}}]"""

    response = call_llm_with_fallback("pg_misconception", prompt)
    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        misconceptions = json.loads(cleaned.strip())
    except (json.JSONDecodeError, IndexError):
        misconceptions = [{"misconception": "Analisis gagal di-parse",
                           "affected_topics": list(set(v["topic"] for v in problematic.values())),
                           "likely_cause": "Perlu review manual", "severity": "medium"}]

    steps.append({"step": "detect_misconceptions",
                  "result": f"{len(misconceptions)} misconceptions identified.",
                  "timestamp": datetime.now().isoformat()})
    return {"detected_gaps": misconceptions, "reasoning_steps": steps}


def node_prioritize_gaps(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    gaps = state.get("detected_gaps", [])
    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    gaps.sort(key=lambda g: severity_order.get(g.get("severity", "medium"), 1))

    steps.append({"step": "prioritize_gaps",
                  "result": f"Gaps prioritized. Top: {gaps[0]['misconception'] if gaps else 'none'}",
                  "timestamp": datetime.now().isoformat()})
    return {"detected_gaps": gaps, "reasoning_steps": steps}


def node_generate_summary(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    stats = state.get("class_stats", {})
    gaps = state.get("detected_gaps", [])

    prompt = f"""Buat ringkasan performa kuis kelas dalam bahasa Indonesia (3-5 kalimat).
Statistik: Mean={stats.get('mean',0)}, Median={stats.get('median',0)}, Below KKM={stats.get('pct_below_kkm',0)}%
Miskonsepsi: {json.dumps([g['misconception'] for g in gaps])}
Output teks ringkasan saja (bukan JSON)."""

    summary = call_llm_with_fallback("summary_generation", prompt)
    steps.append({"step": "generate_summary", "result": "Summary generated.",
                  "timestamp": datetime.now().isoformat()})
    return {"reasoning_steps": steps, "week_material_summary": summary}


def node_generate_remedial(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    gaps = state.get("detected_gaps", [])

    if not gaps:
        steps.append({"step": "generate_remedial", "result": "No gaps — no remedial needed.",
                      "timestamp": datetime.now().isoformat()})
        return {"remedial_slides": [], "remedial_generated": True, "reasoning_steps": steps}

    prompt = f"""Buat 5-8 slide remedial untuk mengatasi miskonsepsi berikut:
{json.dumps(gaps, indent=2)}

Output JSON array (tanpa fence):
[{{"slide_number":1,"title":"...","content":"...penjelasan perbaikan konsep...","key_points":["..."]}}]"""

    response = call_llm_with_fallback("remedial_generation", prompt)
    try:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        slides = json.loads(cleaned.strip())
    except (json.JSONDecodeError, IndexError):
        slides = [{"slide_number": 1, "title": "Remedial Overview",
                    "content": "Review materi yang perlu diperbaiki.", "key_points": []}]

    steps.append({"step": "generate_remedial",
                  "result": f"{len(slides)} remedial slides generated.",
                  "timestamp": datetime.now().isoformat()})
    return {"remedial_slides": slides, "remedial_generated": True, "reasoning_steps": steps}


def node_save_state(state: EducatorCopilotState) -> dict:
    steps = list(state.get("reasoning_steps", []))
    sid = state.get("session_id", generate_id())

    log_agent_decision(sid, "learning_cycle", "save_state",
                       f"Week {state.get('current_week', '?')}",
                       f"Scored {len(state.get('scored_students', []))} students, "
                       f"{len(state.get('detected_gaps', []))} gaps, "
                       f"{len(state.get('remedial_slides', []))} slides")

    conn = get_connection()
    try:
        # Save quiz analysis
        quiz_id = state.get("quiz_results", {}).get("quiz_id", generate_id())
        conn.execute(
            """INSERT OR REPLACE INTO quiz_analysis
               (analysis_id, quiz_id, class_stats, topic_performance, misconceptions, summary_text)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (generate_id(), quiz_id, json.dumps(state.get("class_stats", {})),
             json.dumps(state.get("error_rates", {})),
             json.dumps(state.get("detected_gaps", [])),
             state.get("week_material_summary", ""))
        )
        # Save remedial slides
        if state.get("remedial_slides"):
            conn.execute(
                """INSERT OR REPLACE INTO remedial_slides
                   (slide_id, quiz_id, course_id, for_week_number, slide_data)
                   VALUES (?, ?, ?, ?, ?)""",
                (generate_id(), quiz_id,
                 state.get("course_data", {}).get("course_id", ""),
                 state.get("current_week", 0),
                 json.dumps(state.get("remedial_slides", [])))
            )
        conn.commit()
    except Exception as e:
        print(f"[Learning Agent] Save error: {e}")
    finally:
        conn.close()

    steps.append({"step": "save_state", "result": "✅ Analysis saved to DB.",
                  "timestamp": datetime.now().isoformat()})
    return {"reasoning_steps": steps, "is_complete": True}


def build_learning_graph() -> StateGraph:
    g = StateGraph(EducatorCopilotState)
    g.add_node("load_context", node_load_context)
    g.add_node("score_responses", node_score_responses)
    g.add_node("aggregate_stats", node_aggregate_stats)
    g.add_node("detect_misconceptions", node_detect_misconceptions)
    g.add_node("prioritize_gaps", node_prioritize_gaps)
    g.add_node("generate_summary", node_generate_summary)
    g.add_node("generate_remedial", node_generate_remedial)
    g.add_node("save_state", node_save_state)

    g.set_entry_point("load_context")
    g.add_edge("load_context", "score_responses")
    g.add_edge("score_responses", "aggregate_stats")
    g.add_edge("aggregate_stats", "detect_misconceptions")
    g.add_edge("detect_misconceptions", "prioritize_gaps")
    g.add_edge("prioritize_gaps", "generate_summary")
    g.add_edge("generate_summary", "generate_remedial")
    g.add_edge("generate_remedial", "save_state")
    g.add_edge("save_state", END)
    return g


def run_learning_agent(quiz_data: dict, course_data: dict = None,
                       week: int = 0, material_summary: str = "") -> dict:
    app = build_learning_graph().compile()
    init = {
        "messages": [], "current_agent": "learning_cycle", "current_week": week,
        "session_id": str(uuid.uuid4())[:8], "institution_preset": "standard",
        "course_data": course_data or {}, "cpmk_list": [], "cpmk_slot_distribution": [],
        "week_skeleton": [], "rps_weeks": [], "weeks_approved": [],
        "needs_revision": False, "revision_count": 0,
        "quiz_results": quiz_data, "scored_students": [], "class_stats": {},
        "error_rates": {}, "detected_gaps": [], "remedial_slides": [],
        "remedial_generated": False, "week_material_summary": material_summary,
        "tool_calls_log": [], "reasoning_steps": [],
        "error_message": None, "is_complete": False,
    }
    return app.invoke(init)
