"""
Educator Copilot — Curriculum Agent (LangGraph Subgraph)
==========================================================
Generates a 16-week RPS using multi-step reasoning with Bloom alignment.
"""

import json
import uuid
from datetime import datetime

from langgraph.graph import StateGraph, END

from agents.state import EducatorCopilotState
from lib.llm_router import call_llm_with_fallback, get_model_name
from lib.template_presets import BLOOM_LEVELS
from tools.database import save_rps_week, save_course, log_agent_decision


def node_parse_input(state: EducatorCopilotState) -> dict:
    """Validate and normalize form input."""
    course_data = state.get("course_data", {})
    steps = list(state.get("reasoning_steps", []))

    required = ["name", "code", "credits", "cpl", "cpmk", "bahan_kajian",
                "teaching_methods", "assessment"]
    missing = [f for f in required if not course_data.get(f)]
    if missing:
        return {"error_message": f"Field belum lengkap: {', '.join(missing)}", "reasoning_steps": steps}

    assessment = course_data.get("assessment", [])
    total_weight = sum(a.get("weight", 0) for a in assessment)
    if abs(total_weight - 100) > 0.1:
        return {"error_message": f"Total bobot penilaian = {total_weight}%, harus 100%", "reasoning_steps": steps}

    cpmk_list = course_data.get("cpmk", [])
    if isinstance(cpmk_list, str):
        parsed = []
        for line in cpmk_list.strip().split("\n"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4:
                parsed.append({"code": parts[0], "description": parts[1],
                               "cpl_ref": parts[2], "bloom_level": parts[3].upper()})
            elif len(parts) >= 2:
                parsed.append({"code": parts[0], "description": parts[1],
                               "cpl_ref": "", "bloom_level": "C3"})
        cpmk_list = parsed

    steps.append({"step": "parse_input",
                  "result": f"Form valid. {len(cpmk_list)} CPMK.",
                  "timestamp": datetime.now().isoformat()})
    return {"cpmk_list": cpmk_list, "reasoning_steps": steps, "error_message": None}


def node_analyze_constraints(state: EducatorCopilotState) -> dict:
    """Calculate Bloom-weighted topic distribution."""
    cpmk_list = state.get("cpmk_list", [])
    steps = list(state.get("reasoning_steps", []))

    cpmk_slots = []
    for cpmk in cpmk_list:
        bloom = cpmk.get("bloom_level", "C3")
        weight = BLOOM_LEVELS.get(bloom, BLOOM_LEVELS["C3"])["weight"]
        cpmk_slots.append({"cpmk": cpmk["code"], "description": cpmk.get("description", ""),
                           "bloom_level": bloom, "bloom_weight": weight})

    total_weight = sum(c["bloom_weight"] for c in cpmk_slots)
    if total_weight > 0:
        for cs in cpmk_slots:
            cs["weeks_allocated"] = round(cs["bloom_weight"] / total_weight * 14, 1)

    steps.append({"step": "analyze_constraints",
                  "result": f"Total slot terbobot: {total_weight:.1f}. Distribusi 14 minggu selesai.",
                  "timestamp": datetime.now().isoformat()})
    return {"cpmk_slot_distribution": cpmk_slots, "reasoning_steps": steps}


def node_draft_skeleton(state: EducatorCopilotState) -> dict:
    """Map topics to 14 effective weeks."""
    course_data = state.get("course_data", {})
    cpmk_slots = state.get("cpmk_slot_distribution", [])
    steps = list(state.get("reasoning_steps", []))

    bahan = course_data.get("bahan_kajian", "")
    topics = [t.strip() for t in bahan.split("\n") if t.strip()] if isinstance(bahan, str) else bahan

    skeleton = []
    topic_idx = 0
    week_num = 0
    for cs in cpmk_slots:
        for _ in range(max(1, round(cs.get("weeks_allocated", 1)))):
            week_num += 1
            if week_num > 14:
                break
            topic = topics[topic_idx] if topic_idx < len(topics) else f"Topik {cs['cpmk']}"
            skeleton.append({"effective_week": week_num, "topic": topic,
                             "cpmk_ref": cs["cpmk"], "bloom_level": cs["bloom_level"]})
            topic_idx += 1
        if week_num > 14:
            break

    while len(skeleton) < 14:
        wn = len(skeleton) + 1
        t = topics[topic_idx] if topic_idx < len(topics) else "Topik tambahan"
        skeleton.append({"effective_week": wn, "topic": t,
                         "cpmk_ref": cpmk_slots[-1]["cpmk"] if cpmk_slots else "CPMK-1", "bloom_level": "C3"})
        topic_idx += 1

    steps.append({"step": "draft_skeleton",
                  "result": f"Skeleton {len(skeleton)} minggu dibuat.",
                  "timestamp": datetime.now().isoformat()})
    return {"week_skeleton": skeleton, "reasoning_steps": steps}


def node_generate_weeks(state: EducatorCopilotState) -> dict:
    """Generate content for each week via LLM."""
    course_data = state.get("course_data", {})
    skeleton = state.get("week_skeleton", [])
    steps = list(state.get("reasoning_steps", []))
    tool_log = list(state.get("tool_calls_log", []))

    rps_weeks = []
    eff_to_actual = {}
    actual = 1
    for eff in range(1, 15):
        if actual == 8:
            actual = 9
        eff_to_actual[eff] = actual
        actual += 1

    for i, skel in enumerate(skeleton):
        aw = eff_to_actual.get(i + 1, i + 1)
        prompt = f"""Kamu adalah asisten perancangan kurikulum perguruan tinggi Indonesia.
Buat konten RPS untuk SATU pertemuan:
MK: {course_data.get('name', '')} ({course_data.get('credits', 3)} SKS)
Minggu: {aw}/16 | Topik: {skel['topic']} | CPMK: {skel['cpmk_ref']} | Bloom: {skel['bloom_level']}
Metode: {course_data.get('teaching_methods', ['Ceramah'])}

Output JSON (tanpa fence):
{{"title":"...","description":"...","sub_cpmk":"...","learning_indicators":["..."],"teaching_method":"...","topics_covered":["..."],"student_activity":"...","references":["..."]}}"""

        response = call_llm_with_fallback("week_generation", prompt)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            week_data = json.loads(cleaned.strip())
        except (json.JSONDecodeError, IndexError):
            week_data = {"title": skel["topic"], "description": f"Pertemuan tentang {skel['topic']}",
                         "sub_cpmk": f"Sub-{skel['cpmk_ref']}", "learning_indicators": [],
                         "teaching_method": "Ceramah", "topics_covered": [skel["topic"]],
                         "student_activity": f"Mempelajari {skel['topic']}", "references": []}

        week_data.update({"week": aw, "type": "materi", "status": "draft",
                          "cpmk_ref": skel["cpmk_ref"], "bloom_level": skel["bloom_level"],
                          "time_tm": course_data.get("credits", 3) * 50})
        rps_weeks.append(week_data)
        tool_log.append({"week": aw, "tool": "llm", "model": get_model_name("week_generation")})

    rps_weeks.append({"week": 8, "type": "uts", "title": "Ujian Tengah Semester (UTS)",
                      "description": "Evaluasi capaian CPMK paruh pertama", "status": "draft",
                      "sub_cpmk": "", "learning_indicators": [], "teaching_method": "Ujian",
                      "topics_covered": [], "references": []})
    rps_weeks.append({"week": 16, "type": "uas", "title": "Ujian Akhir Semester (UAS)",
                      "description": "Evaluasi capaian CPMK keseluruhan", "status": "draft",
                      "sub_cpmk": "", "learning_indicators": [], "teaching_method": "Ujian",
                      "topics_covered": [], "references": []})
    rps_weeks.sort(key=lambda w: w["week"])

    steps.append({"step": "generate_weeks",
                  "result": f"{len(rps_weeks)} minggu generated.",
                  "timestamp": datetime.now().isoformat()})
    return {"rps_weeks": rps_weeks, "reasoning_steps": steps, "tool_calls_log": tool_log}


def node_validate_alignment(state: EducatorCopilotState) -> dict:
    """Validate CPMK coverage."""
    rps_weeks = state.get("rps_weeks", [])
    cpmk_list = state.get("cpmk_list", [])
    steps = list(state.get("reasoning_steps", []))

    covered = {w.get("cpmk_ref", "") for w in rps_weeks if w.get("cpmk_ref")}
    all_cpmk = {c["code"] for c in cpmk_list}
    missing = all_cpmk - covered
    needs_rev = len(missing) > 0

    steps.append({"step": "validate_alignment",
                  "result": f"Coverage: {len(covered)}/{len(all_cpmk)}. "
                            f"{'✅ OK' if not needs_rev else f'⚠️ Missing: {missing}'}",
                  "timestamp": datetime.now().isoformat()})
    return {"needs_revision": needs_rev, "revision_count": state.get("revision_count", 0),
            "reasoning_steps": steps}


def node_revise_if_needed(state: EducatorCopilotState) -> dict:
    """Fix alignment gaps."""
    rps_weeks = list(state.get("rps_weeks", []))
    cpmk_list = state.get("cpmk_list", [])
    steps = list(state.get("reasoning_steps", []))
    rev = state.get("revision_count", 0) + 1

    covered = {w.get("cpmk_ref", "") for w in rps_weeks}
    missing = list({c["code"] for c in cpmk_list} - covered)
    materi = [w for w in rps_weeks if w.get("type") == "materi"]

    for i, code in enumerate(missing):
        if i < len(materi):
            materi[-(i + 1)]["cpmk_ref"] = code

    steps.append({"step": f"revise (iter {rev})", "result": f"{len(missing)} CPMK remapped.",
                  "timestamp": datetime.now().isoformat()})
    return {"rps_weeks": rps_weeks, "revision_count": rev, "reasoning_steps": steps}


def node_finalize_rps(state: EducatorCopilotState) -> dict:
    """Save RPS to database."""
    course_data = state.get("course_data", {})
    rps_weeks = state.get("rps_weeks", [])
    steps = list(state.get("reasoning_steps", []))
    sid = state.get("session_id", str(uuid.uuid4())[:8])

    course_id = save_course(course_data)
    for w in rps_weeks:
        save_rps_week(course_id, w)

    log_agent_decision(sid, "curriculum", "finalize_rps",
                       f"Course: {course_data.get('name')}", f"{len(rps_weeks)} weeks saved",
                       model_used=get_model_name("week_generation"))

    steps.append({"step": "finalize_rps",
                  "result": f"✅ RPS saved. ID: {course_id}. {len(rps_weeks)} weeks.",
                  "timestamp": datetime.now().isoformat()})
    course_data["course_id"] = course_id
    return {"course_data": course_data, "reasoning_steps": steps, "is_complete": True}


def should_revise(state: EducatorCopilotState) -> str:
    if state.get("needs_revision") and state.get("revision_count", 0) < 2:
        return "revise_if_needed"
    return "finalize_rps"


def build_curriculum_graph() -> StateGraph:
    g = StateGraph(EducatorCopilotState)
    g.add_node("parse_input", node_parse_input)
    g.add_node("analyze_constraints", node_analyze_constraints)
    g.add_node("draft_skeleton", node_draft_skeleton)
    g.add_node("generate_weeks", node_generate_weeks)
    g.add_node("validate_alignment", node_validate_alignment)
    g.add_node("revise_if_needed", node_revise_if_needed)
    g.add_node("finalize_rps", node_finalize_rps)

    g.set_entry_point("parse_input")
    g.add_edge("parse_input", "analyze_constraints")
    g.add_edge("analyze_constraints", "draft_skeleton")
    g.add_edge("draft_skeleton", "generate_weeks")
    g.add_edge("generate_weeks", "validate_alignment")
    g.add_conditional_edges("validate_alignment", should_revise,
                            {"revise_if_needed": "revise_if_needed", "finalize_rps": "finalize_rps"})
    g.add_edge("revise_if_needed", "validate_alignment")
    g.add_edge("finalize_rps", END)
    return g


def run_curriculum_agent(course_data: dict, preset: str = "standard") -> dict:
    app = build_curriculum_graph().compile()
    init = {
        "messages": [], "current_agent": "curriculum", "current_week": 0,
        "session_id": str(uuid.uuid4())[:8], "institution_preset": preset,
        "course_data": course_data, "cpmk_list": [], "cpmk_slot_distribution": [],
        "week_skeleton": [], "rps_weeks": [], "weeks_approved": [],
        "needs_revision": False, "revision_count": 0,
        "quiz_results": {}, "scored_students": [], "class_stats": {},
        "error_rates": {}, "detected_gaps": [], "remedial_slides": [],
        "remedial_generated": False, "week_material_summary": "",
        "tool_calls_log": [], "reasoning_steps": [],
        "error_message": None, "is_complete": False,
    }
    return app.invoke(init)
