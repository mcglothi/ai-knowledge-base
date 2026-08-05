#!/usr/bin/env python3
"""Shared secret redaction for memory capture paths.

Two layers:
  1. redact_text() — regex patterns for known credential shapes. On match the
     credential is replaced with [REDACTED:<name>] and capture proceeds.
  2. hint_words() — advisory substring hints ("password", "token", ...). These
     produce a warning only; they are far too noisy to block on ("the token
     refresh bug was fixed" is a legitimate memory).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # anthropic_key must precede openai_key: sk-ant-... also matches the sk- pattern
    ("anthropic_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_pat", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("github_fine_grained", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b", re.IGNORECASE)),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "password_assignment",
        re.compile(r"(?i)\b(password|passwd|pwd)\s*[:=]\s*\S+"),
    ),
    (
        "credential_assignment",
        re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\s*[:=]\s*[A-Za-z0-9._/+-]{8,}"),
    ),
]

HINT_WORDS = ("password", "api_key", "apikey", "token", "secret", "private key")


@dataclass
class RedactionResult:
    text: str
    redactions: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)


def redact_text(text: str) -> RedactionResult:
    """Redact known credential shapes; report advisory hint words separately."""
    redactions: list[str] = []
    result = text
    for name, pattern in PATTERNS:
        if pattern.search(result):
            redactions.append(name)
            result = pattern.sub(f"[REDACTED:{name}]", result)
    lowered = result.lower()
    hints = [hint for hint in HINT_WORDS if hint in lowered]
    return RedactionResult(text=result, redactions=redactions, hints=hints)


def hint_words(text: str) -> list[str]:
    lowered = text.lower()
    return [hint for hint in HINT_WORDS if hint in lowered]
