"""
Educator Copilot — Agent State Definition
==========================================
Defines the shared state TypedDict used by all LangGraph agents.
This is the single source of truth for data flowing through the graph.
"""

from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class EducatorCopilotState(TypedDict):
    """
    Shared state across all LangGraph nodes.

    Layer 1 — In-graph working memory (short-term, per session).
    Layer 2 — SQLite persistent memory is accessed via database_tool.
    """

    # ── Session Context ──────────────────────────────────────
    messages: Annotated[list, add_messages]  # LangGraph message history
    current_agent: str                       # "curriculum" | "learning_cycle"
    current_week: int                        # Week being processed (1–16)
    session_id: str                          # Unique session identifier

    # ── Institution Preset ───────────────────────────────────
    institution_preset: str                  # "itb" | "its_ub" | "ugm" | "standard"

    # ── Course Data (from Blok A–E form) ─────────────────────
    course_data: dict                        # Full form input from lecturer
    cpmk_list: list                          # Parsed list of CPMK objects
    cpmk_slot_distribution: list             # Bloom-weighted slot allocation

    # ── RPS State ────────────────────────────────────────────
    week_skeleton: list                      # Topic distribution skeleton (14 weeks)
    rps_weeks: list                          # Full 16-week RPS draft
    weeks_approved: list                     # List of approved week numbers
    needs_revision: bool                     # Whether validation found gaps
    revision_count: int                      # Number of revision iterations (max 2)

    # ── Quiz / Learning Cycle State ──────────────────────────
    quiz_results: dict                       # Raw quiz data being analyzed
    scored_students: list                    # Scored student results
    class_stats: dict                        # Aggregated class statistics
    error_rates: dict                        # Per-question error rates
    detected_gaps: list                      # Identified misconceptions
    remedial_slides: list                    # Generated remedial slide data
    remedial_generated: bool                 # Whether slides have been created
    week_material_summary: str               # Extracted text from week's PDF

    # ── Observability ────────────────────────────────────────
    tool_calls_log: list                     # Log of all tool invocations
    reasoning_steps: list                    # Step-by-step reasoning trace

    # ── Control Flow ─────────────────────────────────────────
    error_message: Optional[str]             # Error message if any
    is_complete: bool                        # Whether the agent has finished
