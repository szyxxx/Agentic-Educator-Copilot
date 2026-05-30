"""LLM-backed grading for a single student submission.

Inputs (`GradingState`):
    quiz_id, student_id, nim, student_answers, questions, answer_key

`student_answers` is a flat dict `{question_id: answer}` produced when the
educator imports a CSV row. MCQ entries are single uppercase letters and
essay entries are free text.

The agent grades MCQs deterministically (string match against the correct
answer), then asks the LLM to score essay answers using the rubric. The
result includes per-question feedback, an overall feedback string, the total
score (0-100), and a list of weak topics inferred from missed questions.
"""

import json
import operator
from typing import Annotated, List, TypedDict

from langgraph.graph import END, StateGraph

from app.core.llm import get_llm


class GradingState(TypedDict):
    quiz_id: str
    student_id: str
    nim: str
    questions: List[dict]
    answer_key: List[dict]
    student_answers: dict
    mcq_scores: List[dict]
    essay_scores: List[dict]
    total_score: float
    feedback_per_question: List[dict]
    overall_feedback: str
    weak_topics: List[str]
    messages: Annotated[list, operator.add]


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def grade_mcq_node(state: GradingState):
    print("Grading MCQ answers...")
    questions = state.get("questions") or []
    answers = state.get("student_answers") or {}

    scores: list[dict] = []
    for q in questions:
        if q.get("type") != "multiple_choice":
            continue
        weight = float(q.get("weight") or 10)
        correct = (q.get("correct_answer") or "").strip().upper()
        picked = str(answers.get(q.get("id"), "") or "").strip().upper()

        if picked and correct and picked == correct:
            scores.append({"id": q.get("id"), "score": weight, "correct": True, "picked": picked})
        else:
            scores.append(
                {
                    "id": q.get("id"),
                    "score": 0.0,
                    "correct": False,
                    "picked": picked or "(kosong)",
                }
            )
    return {"mcq_scores": scores}


def grade_essay_node(state: GradingState):
    print("Grading Essay answers with AI...")
    questions = state.get("questions") or []
    essays = [q for q in questions if q.get("type") == "essay"]
    if not essays:
        return {"essay_scores": []}

    answers = state.get("student_answers") or {}
    items_for_llm = []
    for q in essays:
        student_answer = str(answers.get(q.get("id"), "") or "").strip()
        if not student_answer:
            student_answer = "(tidak dijawab)"
        items_for_llm.append(
            {
                "id": q.get("id"),
                "question": q.get("question"),
                "rubric": q.get("rubric") or {},
                "max_score": float(q.get("max_score") or 30),
                "student_answer": student_answer[:1500],
            }
        )

    prompt = f"""
    Anda adalah penilai esai akademik. Nilai jawaban mahasiswa berikut sesuai rubrik.
    Untuk setiap soal, output JSON murni dengan struktur:
    {{
        "id": "Q...",
        "score": float (0..max_score, ikuti rubrik),
        "feedback": "feedback singkat untuk mahasiswa"
    }}

    Output keseluruhan adalah JSON ARRAY. Hanya keluarkan JSON, tanpa markdown.

    Data:
    {json.dumps(items_for_llm, ensure_ascii=False)}
    """

    try:
        llm = get_llm("complex")
        resp = llm.invoke(prompt)
        raw = (resp.content or "").replace("```json", "").replace("```", "").strip()
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start < 0 or end <= start:
            raise ValueError("LLM response without JSON array")
        parsed = json.loads(raw[start:end])
    except Exception as e:
        print(f"[grading] essay LLM failed: {e}")
        # Fallback — give 0 with a generic note
        parsed = [
            {
                "id": q.get("id"),
                "score": 0.0,
                "feedback": "Gagal menilai otomatis. Mohon dinilai manual.",
            }
            for q in essays
        ]

    score_map = {p.get("id"): p for p in parsed if isinstance(p, dict)}
    out = []
    for q in essays:
        max_score = float(q.get("max_score") or 30)
        info = score_map.get(q.get("id"), {})
        score = float(info.get("score") or 0.0)
        score = max(0.0, min(score, max_score))
        out.append(
            {
                "id": q.get("id"),
                "score": score,
                "feedback": info.get("feedback", ""),
                "max_score": max_score,
            }
        )
    return {"essay_scores": out}


def aggregate_node(state: GradingState):
    print("Aggregating scores...")
    mcq = state.get("mcq_scores") or []
    essay = state.get("essay_scores") or []
    questions = state.get("questions") or []

    earned = sum(item.get("score", 0.0) for item in mcq) + sum(
        item.get("score", 0.0) for item in essay
    )
    max_total = sum(
        float(q.get("weight") or 10) if q.get("type") == "multiple_choice" else float(q.get("max_score") or 30)
        for q in questions
    )
    if max_total <= 0:
        return {"total_score": 0.0}
    pct = earned / max_total * 100.0
    return {"total_score": round(pct, 1)}


def feedback_node(state: GradingState):
    print("Generating personalized feedback...")
    total = state.get("total_score") or 0
    mcq = state.get("mcq_scores") or []
    essay = state.get("essay_scores") or []

    correct_mcq = sum(1 for m in mcq if m.get("correct"))
    weak_essay = [e.get("id") for e in essay if e.get("score", 0) < (e.get("max_score", 30) * 0.6)]

    bits = [f"Skor total {total} dari 100."]
    if mcq:
        bits.append(f"MCQ benar {correct_mcq}/{len(mcq)}.")
    if weak_essay:
        bits.append(f"Soal esai yang perlu diperdalam: {', '.join(weak_essay)}.")
    elif essay:
        bits.append("Jawaban esai sudah memadai.")

    return {"overall_feedback": " ".join(bits)}


def weak_topics_node(state: GradingState):
    print("Identifying learning gaps...")
    questions = state.get("questions") or []
    mcq = state.get("mcq_scores") or []
    essay = state.get("essay_scores") or []

    weak: list[str] = []
    for q in questions:
        qid = q.get("id")
        if any(m.get("id") == qid and not m.get("correct") for m in mcq):
            weak.append(q.get("question", qid)[:80])
        for e in essay:
            if e.get("id") == qid and e.get("score", 0) < (e.get("max_score", 30) * 0.6):
                weak.append(q.get("question", qid)[:80])
    seen, out = set(), []
    for t in weak:
        if t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= 5:
            break
    return {"weak_topics": out}


def save_results_node(state: GradingState):
    return {}


def build_grading_graph():
    graph = StateGraph(GradingState)

    graph.add_node("grade_mcq", grade_mcq_node)
    graph.add_node("grade_essay", grade_essay_node)
    graph.add_node("aggregate_scores", aggregate_node)
    graph.add_node("generate_feedback", feedback_node)
    graph.add_node("identify_weak_topics", weak_topics_node)
    graph.add_node("save_results", save_results_node)

    graph.set_entry_point("grade_mcq")
    graph.add_edge("grade_mcq", "grade_essay")
    graph.add_edge("grade_essay", "aggregate_scores")
    graph.add_edge("aggregate_scores", "generate_feedback")
    graph.add_edge("generate_feedback", "identify_weak_topics")
    graph.add_edge("identify_weak_topics", "save_results")
    graph.add_edge("save_results", END)

    return graph.compile()
