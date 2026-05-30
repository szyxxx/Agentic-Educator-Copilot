"""Coercion helpers for institutional RPS values.

The API and the AI agent both call into these helpers so legacy / sloppy
inputs (free-text CPMK strings, mismatched bahan kajian, out-of-range
reference indices) get normalized the same way everywhere.

Each helper is pure and deterministic so it can be unit-tested in
isolation. Keep them dependency-free aside from stdlib.
"""

from __future__ import annotations

import re
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Bahan Kajian
# ---------------------------------------------------------------------------


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _levenshtein(a: str, b: str) -> int:
    """Iterative Levenshtein distance — small enough for our use, no deps."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ch_a in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, ch_b in enumerate(b, start=1):
            curr[j] = min(
                curr[j - 1] + 1,
                prev[j] + 1,
                prev[j - 1] + (0 if ch_a == ch_b else 1),
            )
        prev = curr
    return prev[-1]


def coerce_bahan_kajian(value: Any, allowed: list[str]) -> str:
    """Normalize a single bahan kajian value against the allowed list.

    Rules:
      1. Empty / None → empty string.
      2. Case-insensitive verbatim match → return the canonical entry.
      3. Closest match by Levenshtein distance ≤ 3 → return that entry.
      4. Otherwise → empty string.
    """
    text = (str(value) if value is not None else "").strip()
    if not text or not allowed:
        return ""

    # Case-insensitive verbatim
    norm_text = _norm(text)
    for entry in allowed:
        if _norm(entry) == norm_text:
            return entry

    # Fuzzy fallback within distance 3
    best_entry: str = ""
    best_dist = 4  # strictly < 4 means within 3
    for entry in allowed:
        dist = _levenshtein(_norm(entry), norm_text)
        if dist < best_dist:
            best_dist = dist
            best_entry = entry
    return best_entry if best_dist <= 3 else ""


# ---------------------------------------------------------------------------
# CPMK number
# ---------------------------------------------------------------------------


def coerce_cpmk_number(value: Any, list_len: int) -> int | None:
    """Coerce a CPMK reference into an integer in [1, list_len], or None.

    Accepts ints directly. For strings, the first integer found in the
    string is used (so "CPMK-2" and "2" both resolve to 2, "CPMK-1, CPMK-3"
    resolves to 1 — the institutional template only allows one CPMK per row).
    """
    if value is None or list_len <= 0:
        return None
    if isinstance(value, bool):
        return None  # bool is a subclass of int, exclude explicitly
    if isinstance(value, int):
        return value if 1 <= value <= list_len else None
    if isinstance(value, float):
        if not value.is_integer():
            return None
        n = int(value)
        return n if 1 <= n <= list_len else None
    text = str(value or "").strip()
    if not text:
        return None
    match = re.search(r"\d+", text)
    if not match:
        return None
    n = int(match.group(0))
    return n if 1 <= n <= list_len else None


# ---------------------------------------------------------------------------
# Reference indices
# ---------------------------------------------------------------------------


def coerce_reference_indices(
    values: Any, list_len: int
) -> tuple[list[int], bool]:
    """Coerce a list of reference indices to ints in [1, list_len].

    Returns `(indices, had_invalid)` where `had_invalid` is True if any
    incoming value was dropped because it was non-integer or out of range.
    Order is preserved; duplicates are removed.
    """
    if values is None or list_len <= 0:
        if values:
            return [], True
        return [], False

    raw_iter: Iterable[Any]
    if isinstance(values, (list, tuple, set)):
        raw_iter = list(values)
    elif isinstance(values, str):
        # Parse "1, 3, 8" etc.
        raw_iter = [piece for piece in re.split(r"[,;]\s*", values) if piece.strip()]
    else:
        raw_iter = [values]

    out: list[int] = []
    seen: set[int] = set()
    had_invalid = False
    for item in raw_iter:
        n: int | None = None
        if isinstance(item, bool):
            had_invalid = True
            continue
        if isinstance(item, int):
            n = item
        elif isinstance(item, float):
            if item.is_integer():
                n = int(item)
        else:
            text = str(item or "").strip()
            if not text:
                continue
            m = re.search(r"\d+", text)
            if m:
                n = int(m.group(0))
        if n is None or not (1 <= n <= list_len):
            had_invalid = True
            continue
        if n in seen:
            continue
        seen.add(n)
        out.append(n)
    return out, had_invalid
