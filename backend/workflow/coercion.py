"""Shared numeric-string coercion helpers for messy LLM-extracted values."""
import re
from typing import Optional


def coerce_numeric_string(v) -> Optional[float]:
    """Best-effort coercion of messy extracted number strings into a clean float."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    raw_str = str(v).lower()
    for token in ("kgs", "kg", "nos.", "nos", "sqm", "cum", "mt", "%", "φ"):
        raw_str = raw_str.replace(token, "")
    raw_str = raw_str.replace(",", "").strip().rstrip(".")
    if not raw_str:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", raw_str)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None
