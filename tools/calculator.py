"""
Educator Copilot — Quiz Calculator Tool
=========================================
Calculates class statistics from quiz scores.
"""

import statistics
from langchain_core.tools import tool


@tool
def quiz_calculator_tool(scores: list[float]) -> dict:
    """
    Menghitung statistik distribusi skor kuis kelas.
    Input: list skor semua mahasiswa (0–100).
    Output: mean, median, std_dev, min, max, pct_below_kkm.
    """
    if not scores:
        return {
            "mean": 0, "median": 0, "std_dev": 0,
            "min": 0, "max": 0, "pct_below_kkm": 0,
            "count": 0,
        }

    kkm = 60
    return {
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "std_dev": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
        "min": min(scores),
        "max": max(scores),
        "pct_below_kkm": round(sum(1 for s in scores if s < kkm) / len(scores) * 100, 1),
        "count": len(scores),
    }


def calculate_error_rates(scored_students: list, answer_key: dict, question_mapping: dict) -> dict:
    """Calculate per-question error rates and map to topics/Sub-CPMK."""
    error_rates = {}
    total_students = len(scored_students)
    if total_students == 0:
        return error_rates

    for q in answer_key:
        wrong_count = sum(1 for s in scored_students if q in s.get("wrong_questions", []))
        error_rates[q] = {
            "error_rate": round(wrong_count / total_students * 100, 1),
            "wrong_count": wrong_count,
            "total_students": total_students,
            "topic": question_mapping.get(q, {}).get("topic", "Unknown"),
            "sub_cpmk": question_mapping.get(q, {}).get("sub_cpmk", ""),
        }
    return error_rates


def get_problematic_questions(error_rates: dict, threshold: float = 40.0) -> dict:
    """Filter questions with error rate above threshold (default 40%)."""
    return {q: v for q, v in error_rates.items() if v["error_rate"] > threshold}
