"""
Educator Copilot — LLM Router & Cost Optimization
====================================================
Tiered model routing: heavy tasks → Sonnet/GPT-4o, light tasks → Haiku/mini.
Automatic fallback to Ollama for offline operation.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Model Maps ──────────────────────────────────────────────────

TASK_MODEL_MAP = {
    # Heavy tasks → smart model
    "rps_generation":       "claude-sonnet-4-20250514",
    "essay_scoring":        "claude-sonnet-4-20250514",
    # Light tasks → cheap model
    "material_review":      "claude-haiku-4-20250414",
    "pg_misconception":     "claude-haiku-4-20250414",
    "remedial_generation":  "claude-haiku-4-20250414",
    "reference_search":     "claude-haiku-4-20250414",
    "week_generation":      "claude-haiku-4-20250414",
    "summary_generation":   "claude-haiku-4-20250414",
}

OLLAMA_MODEL_MAP = {
    "rps_generation":       "mistral:7b",
    "essay_scoring":        "mistral:7b",
    "material_review":      "llama3.2:3b",
    "pg_misconception":     "llama3.2:3b",
    "remedial_generation":  "llama3.2:3b",
    "reference_search":     "llama3.2:3b",
    "week_generation":      "llama3.2:3b",
    "summary_generation":   "llama3.2:3b",
}


def get_llm(task: str, force_local: bool = False):
    """
    Get the appropriate LLM for a given task.
    Uses tiered routing: heavy tasks get smarter models, light tasks get cheaper ones.
    Falls back to Ollama if FORCE_LOCAL_LLM is set or if API keys are missing.
    """
    if force_local or os.getenv("FORCE_LOCAL_LLM", "").lower() == "true":
        try:
            from langchain_community.llms import Ollama
            model = OLLAMA_MODEL_MAP.get(task, "llama3.2:3b")
            return Ollama(model=model)
        except ImportError:
            raise RuntimeError("Ollama not available. Install: pip install ollama")

    # Try Anthropic first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key.startswith("sk-ant"):
        try:
            from langchain_anthropic import ChatAnthropic
            model = TASK_MODEL_MAP.get(task, "claude-haiku-4-20250414")
            return ChatAnthropic(
                model=model,
                api_key=api_key,
                max_retries=2,
                timeout=60,
            )
        except ImportError:
            pass

    # Try OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.startswith("sk-"):
        try:
            from langchain_openai import ChatOpenAI
            # Map Anthropic model names to OpenAI equivalents
            openai_map = {
                "claude-sonnet-4-20250514": "gpt-4o",
                "claude-haiku-4-20250414": "gpt-4o-mini",
            }
            anthropic_model = TASK_MODEL_MAP.get(task, "claude-haiku-4-20250414")
            model = openai_map.get(anthropic_model, "gpt-4o-mini")
            return ChatOpenAI(model=model, api_key=openai_key, max_retries=2)
        except ImportError:
            pass

    # Fallback to Ollama
    try:
        from langchain_community.llms import Ollama
        model = OLLAMA_MODEL_MAP.get(task, "llama3.2:3b")
        return Ollama(model=model)
    except ImportError:
        raise RuntimeError(
            "No LLM available. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, "
            "or install Ollama for local inference."
        )


def call_llm_with_fallback(task: str, prompt: str) -> str:
    """
    Call LLM with automatic fallback chain:
    1. Primary (Anthropic/OpenAI based on env)
    2. Fallback to Ollama local
    """
    try:
        llm = get_llm(task, force_local=False)
        response = llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"[LLM Router] Primary failed ({e}), falling back to Ollama...")
        try:
            llm = get_llm(task, force_local=True)
            response = llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e2:
            return f"[ERROR] All LLM backends failed: {e2}"


def get_model_name(task: str) -> str:
    """Get the model name that would be used for a task (for logging)."""
    if os.getenv("FORCE_LOCAL_LLM", "").lower() == "true":
        return OLLAMA_MODEL_MAP.get(task, "llama3.2:3b")
    return TASK_MODEL_MAP.get(task, "claude-haiku-4-20250414")
