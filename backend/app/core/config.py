"""Central config + .env loading.

Order of precedence for env values: OS env > `.env` next to the backend folder.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    # Walk up from this file to find the nearest .env (backend root or repo root).
    _here = Path(__file__).resolve()
    for candidate in [_here.parent.parent.parent, _here.parent.parent, _here.parent]:
        env_file = candidate / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            break
except Exception:  # pragma: no cover
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./educopilot.db")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# ---------------------------------------------------------------------------
# LLM provider configuration
# ---------------------------------------------------------------------------
#
# `LLM_PROVIDER_ORDER` is a comma-separated list. The first provider whose
# credentials/runtime are available wins. Default order:
#   1. openrouter  (cloud, multi-model — primary)
#   2. anthropic   (cloud, Claude direct — fallback when OpenRouter is down)
#   3. ollama      (local — last resort if both cloud routes are missing)

LLM_PROVIDER_ORDER = [
    p.strip().lower()
    for p in os.getenv("LLM_PROVIDER_ORDER", "openrouter,anthropic,ollama").split(",")
    if p.strip()
]

# OpenRouter (primary)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
).strip()
OPENROUTER_MODEL_COMPLEX = os.getenv(
    "OPENROUTER_MODEL_COMPLEX", "anthropic/claude-sonnet-4.5"
).strip()
OPENROUTER_MODEL_SIMPLE = os.getenv(
    "OPENROUTER_MODEL_SIMPLE", "anthropic/claude-haiku-4.5"
).strip()
OPENROUTER_REFERER = os.getenv(
    "OPENROUTER_REFERER", "http://localhost:3000"
).strip()
OPENROUTER_TITLE = os.getenv("OPENROUTER_TITLE", "EduCopilot").strip()

# Anthropic native (fallback)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL_COMPLEX = os.getenv(
    "ANTHROPIC_MODEL_COMPLEX", "claude-sonnet-4-5"
).strip()
ANTHROPIC_MODEL_SIMPLE = os.getenv(
    "ANTHROPIC_MODEL_SIMPLE", "claude-haiku-4-5"
).strip()

# Local fallback
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
