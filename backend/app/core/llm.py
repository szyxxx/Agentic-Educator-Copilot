"""LLM provider routing.

`get_llm(task)` picks the first available provider from `LLM_PROVIDER_ORDER`
in `app.core.config`. Default order is OpenRouter (primary, multi-model) →
Anthropic direct (fallback) → Ollama (local last resort).

`task` is one of:
    "complex" — for grading, RPS drafting, anything that needs strong reasoning.
    "simple" — for MCQ generation, light extraction, fast/cheap reasoning.
"""

from __future__ import annotations

import logging
from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel

from app.core import config

log = logging.getLogger(__name__)

TaskKind = Literal["complex", "simple"]


# ---------------------------------------------------------------------------
# Provider builders
# ---------------------------------------------------------------------------


def _build_openrouter(task: TaskKind) -> BaseChatModel | None:
    if not config.OPENROUTER_API_KEY:
        return None
    try:
        # `langchain-openai` is the modern home for ChatOpenAI; fall back to
        # the community shim if the new package isn't installed.
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            from langchain_community.chat_models import ChatOpenAI  # type: ignore

        model = (
            config.OPENROUTER_MODEL_COMPLEX
            if task == "complex"
            else config.OPENROUTER_MODEL_SIMPLE
        )
        temperature = 0.2 if task == "complex" else 0.4

        # OpenRouter recommends an HTTP-Referer + X-Title pair for analytics.
        default_headers = {
            "HTTP-Referer": config.OPENROUTER_REFERER,
            "X-Title": config.OPENROUTER_TITLE,
        }
        return ChatOpenAI(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=config.OPENROUTER_API_KEY,
            model=model,
            temperature=temperature,
            default_headers=default_headers,
        )
    except Exception as e:  # pragma: no cover
        log.warning("[llm] OpenRouter init failed: %s", e)
        return None


def _build_anthropic(task: TaskKind) -> BaseChatModel | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    try:
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            log.info(
                "[llm] langchain-anthropic not installed; skipping native Anthropic. "
                "Install with `pip install langchain-anthropic` to enable."
            )
            return None

        model = (
            config.ANTHROPIC_MODEL_COMPLEX
            if task == "complex"
            else config.ANTHROPIC_MODEL_SIMPLE
        )
        temperature = 0.2 if task == "complex" else 0.4
        return ChatAnthropic(
            api_key=config.ANTHROPIC_API_KEY,
            model=model,
            temperature=temperature,
        )
    except Exception as e:  # pragma: no cover
        log.warning("[llm] Anthropic init failed: %s", e)
        return None


def _build_ollama(task: TaskKind) -> BaseChatModel | None:
    try:
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            from langchain_community.chat_models import ChatOllama  # type: ignore
        return ChatOllama(
            base_url=config.OLLAMA_BASE_URL,
            model=config.OLLAMA_MODEL,
            temperature=0.3 if task == "complex" else 0.5,
        )
    except Exception as e:  # pragma: no cover
        log.warning("[llm] Ollama init failed: %s", e)
        return None


_BUILDERS = {
    "openrouter": _build_openrouter,
    "anthropic": _build_anthropic,
    "ollama": _build_ollama,
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def get_llm(task: TaskKind = "complex") -> BaseChatModel:
    """Return the first configured chat model for the given task.

    Walks `LLM_PROVIDER_ORDER` and returns whichever provider is fully wired
    up. Raises RuntimeError only if every provider in the order is missing
    its credentials or runtime — that case usually means the dosen forgot
    to set up an .env file.
    """
    tried: list[str] = []
    for name in config.LLM_PROVIDER_ORDER:
        builder = _BUILDERS.get(name)
        if not builder:
            tried.append(f"{name}(unknown)")
            continue
        llm = builder(task)
        if llm is not None:
            log.info("[llm] using provider=%s task=%s", name, task)
            return llm
        tried.append(name)

    raise RuntimeError(
        "No LLM provider configured. Tried "
        + ", ".join(tried or ["(empty order)"])
        + ". Set at least one of OPENROUTER_API_KEY / ANTHROPIC_API_KEY, "
        "or run a local Ollama server."
    )
