"""Structured local-model calls, with one bounded repair attempt.

Cloud providers retain their original call options and single-call behavior.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from langchain_ollama import ChatOllama
from pydantic import TypeAdapter

log = logging.getLogger(__name__)


def invoke_json(
    llm: Any,
    prompt: str,
    *,
    adapter: TypeAdapter,
    validate: Callable[[Any], None] | None = None,
    temperature: float | None = None,
    seed: int | None = None,
) -> Any:
    """Return decoded JSON; validate/retry/schema/options apply only to Ollama."""
    local = isinstance(llm, ChatOllama)
    schema = adapter.json_schema()
    model = llm
    if local:
        updates = {}
        if temperature is not None:
            updates["temperature"] = temperature
        if seed is not None:
            updates["seed"] = seed
        model = llm.model_copy(update=updates)
    attempts = 2 if local else 1
    current_prompt = prompt
    for attempt in range(attempts):
        try:
            response = model.invoke(current_prompt, **({"format": schema} if local else {}))
            metadata = getattr(response, "response_metadata", {}) or {}
            if local:
                log.info("[ollama-json] attempt=%s done_reason=%s prompt_tokens=%s output_tokens=%s eval_ns=%s total_ns=%s", attempt + 1, metadata.get("done_reason"), metadata.get("prompt_eval_count"), metadata.get("eval_count"), metadata.get("eval_duration"), metadata.get("total_duration"))
                if metadata.get("done_reason") == "length":
                    raise ValueError("Keluaran terpotong: tambah OLLAMA_NUM_CTX/OLLAMA_NUM_PREDICT atau ringkas masukan")
            text = response.content
            if not isinstance(text, str):
                raise ValueError("Konten JSON bukan teks")
            if local:
                # Grammar-constrained local output must be a complete JSON document.
                data = json.loads(text)
                data = adapter.dump_python(adapter.validate_python(data, strict=True), mode="json")
                if validate is not None:
                    validate(data)
            else:
                # Preserve the tolerant parser used by the existing cloud paths.
                text = text.replace("```json", "").replace("```", "").strip()
                left, right = ("[", "]") if schema.get("type") == "array" else ("{", "}")
                start, end = text.find(left), text.rfind(right) + 1
                if start < 0 or end <= start:
                    raise ValueError("LLM tidak mengembalikan JSON yang diminta")
                data = json.loads(text[start:end])
            return data
        except Exception as error:
            if attempt + 1 == attempts:
                raise ValueError(f"Keluaran JSON LLM gagal setelah {attempts} percobaan") from error
            log.warning("[ollama-json] retry after %s: %s", type(error).__name__, str(error).splitlines()[0][:200])
            # Do not feed untrusted generated content or validation input back to the model.
            reason = str(error).splitlines()[0][:200] if type(error) is ValueError else "Struktur atau tipe data JSON tidak memenuhi skema."
            current_prompt = prompt + f"\nPerbaiki hasil sebelumnya: {reason}. Keluarkan satu dokumen JSON lengkap sesuai skema, ringkas setiap teks, isi seluruh item yang diminta, tanpa markdown."
    raise AssertionError("unreachable")
