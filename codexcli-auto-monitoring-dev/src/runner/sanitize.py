from __future__ import annotations

import re
from typing import Any


_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(Authorization:\s*Bearer\s+)[^\s]+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9._-]{16,}"), r"\1***"),
    (re.compile(r"(CODEX_API_KEY=)[^\s]+"), r"\1***"),
    (re.compile(r"([A-Z0-9_]*API_KEY=)[^\s]+"), r"\1***"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"), "sk-***"),
]


def sanitize_text(text: str) -> str:
    out = text
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}
    return value

