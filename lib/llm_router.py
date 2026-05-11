"""
Educator Copilot — LLM Router & Cost Optimization
====================================================
Tiered model routing: heavy tasks → gemma4:e4b/GPT-4o, light tasks → Haiku/mini.
Automatic fallback to Ollama for offline operation.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Model Maps ──────────────────────────────────────────────────

HEAVY_MODEL = os.getenv("LLM_HEAVY_MODEL")
LIGHT_MODEL = os.getenv("LLM_LIGHT_MODEL", "claude-haiku-4-20250414")

TASK_MODEL_MAP = {
    # Heavy tasks → smart model
    "rps_generation":       HEAVY_MODEL,
    "essay_scoring":        HEAVY_MODEL,
    "quiz_generation":      HEAVY_MODEL,
    # Light tasks → cheap model
    "material_review":      LIGHT_MODEL,
    "pg_misconception":     LIGHT_MODEL,
    "remedial_generation":  LIGHT_MODEL,
    "reference_search":     LIGHT_MODEL,
    "week_generation":      LIGHT_MODEL,
    "summary_generation":   LIGHT_MODEL,
}

OLLAMA_MODEL_MAP = {
    "rps_generation":       "gemma4:e4b",
    "essay_scoring":        "gemma4:e4b",
    "quiz_generation":      "gemma4:e4b",
    "material_review":      "gemma4:e4b",
    "pg_misconception":     "gemma4:e4b",
    "remedial_generation":  "gemma4:e4b",
    "reference_search":     "gemma4:e4b",
    "week_generation":      "gemma4:e4b",
    "summary_generation":   "gemma4:e4b",
}


def get_llm(task: str, force_local: bool = False):
    """
    Get the appropriate LLM for a given task.
    Uses tiered routing: heavy tasks get smarter models, light tasks get cheaper ones.
    Falls back to Ollama if FORCE_LOCAL_LLM is set or if API keys are missing.
    """
    if force_local or os.getenv("FORCE_LOCAL_LLM", "").lower() == "true":
        try:
            from langchain_ollama import OllamaLLM
            model = OLLAMA_MODEL_MAP.get(task, "gemma4:e4b")
            return OllamaLLM(model=model)
        except ImportError:
            raise RuntimeError("Ollama not available. Install: pip install langchain-ollama")

    # Try OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    # Fallback if user placed OpenRouter key in ANTHROPIC_API_KEY
    anth_key = os.getenv("ANTHROPIC_API_KEY")
    if not openrouter_key and anth_key and anth_key.startswith("sk-or-"):
        openrouter_key = anth_key

    if openrouter_key and openrouter_key.startswith("sk-or-"):
        try:
            from langchain_openai import ChatOpenAI
            
            # Use the model defined in TASK_MODEL_MAP. If it's a legacy Anthropic model name, map it to a valid OpenRouter model.
            legacy_or_map = {
                "claude-gemma4:e4b-4-20250514": "anthropic/claude-3.5-sonnet",
                "claude-haiku-4-20250414": "anthropic/claude-3-haiku",
            }
            raw_model = TASK_MODEL_MAP.get(task, LIGHT_MODEL)
            model = legacy_or_map.get(raw_model, raw_model)
            
            return ChatOpenAI(
                model=model,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=2,
            )
        except ImportError:
            pass

    # Try Anthropic
    if anth_key and anth_key.startswith("sk-ant"):
        try:
            from langchain_anthropic import ChatAnthropic
            model = TASK_MODEL_MAP.get(task, LIGHT_MODEL)
            return ChatAnthropic(
                model=model,
                api_key=anth_key,
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
                "claude-gemma4:e4b-4-20250514": "gpt-4o",
                "claude-haiku-4-20250414": "gpt-4o-mini",
            }
            anthropic_model = TASK_MODEL_MAP.get(task, LIGHT_MODEL)
            model = openai_map.get(anthropic_model, "gpt-4o-mini")
            return ChatOpenAI(model=model, api_key=openai_key, max_retries=2)
        except ImportError:
            pass

    # Fallback to Ollama
    try:
        from langchain_ollama import OllamaLLM
        model = OLLAMA_MODEL_MAP.get(task, "gemma4:e4b")
        return OllamaLLM(model=model)
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
        return OLLAMA_MODEL_MAP.get(task, "gemma4:e4b")
    return TASK_MODEL_MAP.get(task, LIGHT_MODEL)
