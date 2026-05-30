import operator
import json
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from app.core.llm import get_llm


class QuizState(TypedDict):
    material_content: str       # Konten materi (PDF/teks)
    course_id: str
    week_number: int
    quiz_type: str              # "multiple_choice" | "essay" | "mixed"
    difficulty_level: str       # "easy" | "medium" | "hard" | "adaptive"
    num_questions: int
    generated_questions: List[dict]
    answer_key: List[dict]
    validated: bool
    messages: Annotated[list, operator.add]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _split_counts(quiz_type: str, total: int) -> tuple[int, int]:
    """Return (mcq_count, essay_count) based on quiz_type and the requested total."""
    total = max(1, int(total or 1))
    if quiz_type == "multiple_choice":
        return total, 0
    if quiz_type == "essay":
        return 0, total
    # "mixed" — split roughly in half, MCQ taking the larger share when odd
    mcq = (total + 1) // 2
    return mcq, total - mcq


def _extract_json_array(text: str) -> list:
    """Best-effort JSON-array extraction from a possibly noisy LLM response."""
    if not text:
        return []
    cleaned = text.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start < 0 or end <= start:
        return []
    try:
        parsed = json.loads(cleaned[start:end])
        return parsed if isinstance(parsed, list) else []
    except Exception as e:
        print(f"[quiz_agent] JSON parse error: {e}")
        return []


def _strip_inline_options(question: str) -> str:
    """Remove inline options that some LLMs leak into the question text.

    The model occasionally writes "...?  A. opt1 B. opt2 C. opt3 D. opt4" into
    `question` even though it also fills `options` separately. We chop the
    text starting at the earliest place an option marker appears.
    """
    import re

    if not question:
        return question
    # Match "A.", "A)", " a.", " (A)" etc. that look like an MCQ option marker
    # preceded by whitespace or a sentence-ending punctuation.
    pattern = re.compile(
        r"(?:(?<=\s)|(?<=[?!.]))\(?[A-Da-d][\.\)]\s",
    )
    match = pattern.search(question)
    if not match:
        return question.strip()
    # Only strip if at least 2 markers are present (real giveaway), otherwise
    # the question may legitimately reference "A." for some other reason.
    if len(pattern.findall(question)) < 2:
        return question.strip()
    return question[: match.start()].rstrip(" ?.!,;:") + "?"


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def parse_material_node(state: QuizState):
    print("Parsing material...")
    return {}


def lo_node(state: QuizState):
    print("Identifying Learning Objectives (CPMK)...")
    return {}


def generate_mcq_node(state: QuizState):
    """Generate MCQs as a single batched LLM call so we honor num_questions."""
    quiz_type = state.get("quiz_type") or "mixed"
    if quiz_type not in ("multiple_choice", "mixed"):
        return {}

    mcq_count, _ = _split_counts(quiz_type, state.get("num_questions") or 1)
    if mcq_count <= 0:
        return {}

    print(f"Generating {mcq_count} Multiple Choice Questions...")
    llm = get_llm("simple")
    material = (state.get("material_content") or "")[:4000]

    prompt = f"""
    Anda adalah penyusun soal kuis akademik. Berdasarkan materi berikut:
    \"\"\"{material}\"\"\"

    Buat {mcq_count} soal pilihan ganda berbahasa Indonesia.
    Tingkat kesulitan: {state.get('difficulty_level')}.
    Setiap soal harus berbeda topik/sudut pandang dan menguji pemahaman, bukan hafalan.

    ATURAN PENTING:
    - Kolom "question" HANYA berisi pertanyaan tanpa daftar opsi.
    - JANGAN menyalin "A.", "B.", "C.", "D." atau teks opsi ke dalam "question".
    - Opsi ditulis hanya di kolom "options".
    - "correct_answer" hanya berisi salah satu dari "A", "B", "C", "D".

    Output HARUS berupa JSON array murni (tanpa markdown, tanpa teks lain).
    Setiap elemen array adalah objek dengan struktur PERSIS:
    {{
        "id": "Q001",
        "type": "multiple_choice",
        "bloom_level": "understand",
        "question": "pertanyaan tanpa opsi",
        "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
        "correct_answer": "B",
        "explanation": "penjelasan singkat",
        "weight": 10
    }}

    Gunakan id Q001, Q002, ... berurutan. Hanya outputkan JSON array.
    """
    try:
        res = llm.invoke(prompt)
        items = _extract_json_array(res.content)
    except Exception as e:
        print(f"[quiz_agent] Error generating MCQ: {e}")
        items = []

    # Sanitize and pad/trim to mcq_count
    clean: list[dict] = []
    for i, q in enumerate(items[:mcq_count]):
        if not isinstance(q, dict):
            continue
        q.setdefault("id", f"Q{i + 1:03d}")
        q["type"] = "multiple_choice"
        q.setdefault("weight", 10)
        if "question" in q and isinstance(q["question"], str):
            q["question"] = _strip_inline_options(q["question"])
        if "options" in q and isinstance(q["options"], dict):
            clean.append(q)

    return {"generated_questions": (state.get("generated_questions") or []) + clean}


def generate_essay_node(state: QuizState):
    """Generate essay questions as one batched LLM call."""
    quiz_type = state.get("quiz_type") or "mixed"
    if quiz_type not in ("essay", "mixed"):
        return {}

    _, essay_count = _split_counts(quiz_type, state.get("num_questions") or 1)
    if essay_count <= 0:
        return {}

    # Continue numbering after any MCQs that were already produced
    starting_index = len(state.get("generated_questions") or []) + 1

    print(f"Generating {essay_count} Essay Questions...")
    llm = get_llm("complex")
    material = (state.get("material_content") or "")[:4000]

    prompt = f"""
    Anda adalah penyusun soal esai akademik. Berdasarkan materi berikut:
    \"\"\"{material}\"\"\"

    Buat {essay_count} soal esai berbahasa Indonesia yang membutuhkan analisis dan argumentasi.
    Tingkat kesulitan: {state.get('difficulty_level')}.
    Setiap soal harus berbeda fokus dan tidak duplikatif.

    Output HARUS berupa JSON array murni (tanpa markdown, tanpa teks lain).
    Setiap elemen array adalah objek dengan struktur PERSIS:
    {{
        "id": "Q{starting_index:03d}",
        "type": "essay",
        "bloom_level": "analyze",
        "question": "pertanyaan esai",
        "rubric": {{
            "excellent": "kriteria nilai 90-100",
            "good": "kriteria nilai 70-89",
            "satisfactory": "kriteria nilai 50-69",
            "needs_improvement": "kriteria nilai 0-49"
        }},
        "max_score": 30
    }}

    Gunakan id Q{starting_index:03d}, Q{starting_index + 1:03d}, ... berurutan. Hanya outputkan JSON array.
    """
    try:
        res = llm.invoke(prompt)
        items = _extract_json_array(res.content)
    except Exception as e:
        print(f"[quiz_agent] Error generating Essay: {e}")
        items = []

    clean: list[dict] = []
    for i, q in enumerate(items[:essay_count]):
        if not isinstance(q, dict):
            continue
        q.setdefault("id", f"Q{starting_index + i:03d}")
        q["type"] = "essay"
        q.setdefault("max_score", 30)
        clean.append(q)

    return {"generated_questions": (state.get("generated_questions") or []) + clean}


def answer_key_node(state: QuizState):
    print("Generating Answer Key & Rubrics...")
    keys = []
    for q in state.get("generated_questions", []):
        if q.get("type") == "essay":
            keys.append({"id": q.get("id"), "answer": q.get("rubric")})
        else:
            keys.append({"id": q.get("id"), "answer": q.get("correct_answer")})
    return {"answer_key": keys}


def validate_node(state: QuizState):
    print("Validating Quiz Questions...")
    return {"validated": True}


def route_after_validation(state: QuizState):
    if state.get("validated"):
        return "finalize_quiz"
    return "finalize_quiz"


def finalize_node(state: QuizState):
    print("Finalizing Quiz...")
    return {}


def build_quiz_graph():
    graph = StateGraph(QuizState)

    graph.add_node("parse_material", parse_material_node)
    graph.add_node("identify_learning_objectives", lo_node)
    graph.add_node("generate_mcq", generate_mcq_node)
    graph.add_node("generate_essay", generate_essay_node)
    graph.add_node("generate_answer_key", answer_key_node)
    graph.add_node("validate_questions", validate_node)
    graph.add_node("finalize_quiz", finalize_node)

    graph.set_entry_point("parse_material")
    graph.add_edge("parse_material", "identify_learning_objectives")
    graph.add_edge("identify_learning_objectives", "generate_mcq")
    graph.add_edge("generate_mcq", "generate_essay")
    graph.add_edge("generate_essay", "generate_answer_key")
    graph.add_edge("generate_answer_key", "validate_questions")

    graph.add_conditional_edges(
        "validate_questions",
        route_after_validation,
        {
            "finalize_quiz": "finalize_quiz"
        }
    )
    graph.add_edge("finalize_quiz", END)

    return graph.compile()
