#!/usr/bin/env python3
"""
sidecar.py — local Ollama offload helper for AIKB pipeline scripts.

Routes LLM calls to a local or LAN Ollama instance (sidecar, workstation,
or localhost) to offload grunt-work scoring and drafting from frontier models.

Configuration via environment variables (all optional):

    AIKB_SIDECAR_URL      Ollama base URL (default: http://localhost:11434)
    AIKB_SIDECAR_SCORING_MODEL   Fast model for scoring/classification
                                  (default: gemma3:4b)
    AIKB_SIDECAR_BRIEFING_MODEL  Model for wake-up synthesis
                                  (default: gemma3:4b)
    AIKB_SIDECAR_DRAFTING_MODEL  Model for patch drafting — can be larger
                                  (default: qwen2.5-coder:7b)

Falls back gracefully to None when the sidecar is unreachable,
allowing callers to fall back to rule-based behavior without crashing.

Usage:
    from sidecar import ask, available, score_event, draft_patch

    result = ask("Summarise this...", model=BRIEFING_MODEL)
    if result is None:
        # Sidecar unreachable — use rule-based fallback
        ...

Rename this file to sidecar.py if you prefer a host-neutral name.
"""

from __future__ import annotations

import json
import os
import urllib.request
from urllib.error import URLError

# ---------------------------------------------------------------------------
# Configuration — override via environment variables
# ---------------------------------------------------------------------------

SIDECAR_URL: str = os.environ.get("AIKB_SIDECAR_URL", "http://localhost:11434")

# Model assignments. Use small/fast models on the hot path (scoring, briefing);
# larger models only for fully-async work (patch drafting).
SCORING_MODEL: str = os.environ.get("AIKB_SIDECAR_SCORING_MODEL", "gemma3:4b")
BRIEFING_MODEL: str = os.environ.get("AIKB_SIDECAR_BRIEFING_MODEL", "gemma3:4b")
DRAFTING_MODEL: str = os.environ.get("AIKB_SIDECAR_DRAFTING_MODEL", "qwen2.5-coder:7b")

_CONNECT_TIMEOUT = 3   # seconds — fast fail when sidecar unreachable
_READ_TIMEOUT = 120    # seconds — allow time for larger models

# Cached availability per process (avoids repeated probes)
_sidecar_available: bool | None = None


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def available(force_check: bool = False) -> bool:
    """Return True if the sidecar Ollama API is reachable."""
    global _sidecar_available
    if _sidecar_available is None or force_check:
        try:
            req = urllib.request.Request(f"{SIDECAR_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=_CONNECT_TIMEOUT):
                pass
            _sidecar_available = True
        except Exception:
            _sidecar_available = False
    return _sidecar_available


def ask(
    prompt: str,
    model: str = BRIEFING_MODEL,
    system: str = "",
    timeout: int = _READ_TIMEOUT,
) -> str | None:
    """
    Send a prompt to the sidecar and return the response text.

    Returns None if the sidecar is unreachable or the call fails — callers
    should fall back to rule-based behavior in that case.

    Args:
        prompt:  The user prompt.
        model:   Ollama model tag. Defaults to BRIEFING_MODEL.
        system:  Optional system prompt.
        timeout: Total request timeout in seconds.
    """
    if not available():
        return None

    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system

    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{SIDECAR_URL}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            return body.get("response", "").strip() or None
    except (URLError, json.JSONDecodeError, KeyError):
        return None


# ---------------------------------------------------------------------------
# Task-specific helpers
# ---------------------------------------------------------------------------

def score_event(summary: str, project: str) -> float | None:
    """
    Ask the sidecar to score an event's promotion worthiness (0.0–1.0).

    Returns None if the sidecar is unavailable — caller should use rule-based score.
    """
    prompt = (
        f"Rate the following knowledge-base event on a scale from 0.0 to 1.0 for "
        f"whether it describes a durable, factual change that a future AI agent "
        f"should know about. 1.0 = definitely promote, 0.0 = ephemeral noise.\n\n"
        f"Project: {project}\n"
        f"Event: {summary}\n\n"
        f"Reply with only a single decimal number between 0.0 and 1.0. No explanation."
    )
    result = ask(prompt, model=SCORING_MODEL, timeout=30)
    if result is None:
        return None
    try:
        score = float(result.strip().split()[0])
        return max(0.0, min(1.0, score))
    except (ValueError, IndexError):
        return None


def draft_patch(
    target_file_content: str,
    proposed_change: str,
    context: str = "",
) -> str | None:
    """
    Ask the sidecar to draft a markdown patch for a candidate.

    Returns the drafted text, or None if the sidecar is unavailable.
    """
    system = (
        "You are an editor for a personal AI knowledge base written in Markdown. "
        "Your job is to produce a minimal, accurate edit to the target document. "
        "Output only the new or changed content — do not repeat unchanged sections. "
        "Be concise and factual. Do not add speculation."
    )
    prompt = (
        f"Target document:\n{target_file_content[:4000]}\n\n"
        f"Proposed change: {proposed_change}\n"
        + (f"Additional context: {context}\n" if context else "")
        + "\nDraft the minimal markdown addition or edit needed:"
    )
    return ask(prompt, model=DRAFTING_MODEL, system=system, timeout=90)


def summarize_for_wakeup(events_text: str, state_summary: str) -> str | None:
    """
    Ask the sidecar to synthesize a wake-up briefing from recent events and state.

    Returns a short markdown briefing, or None if the sidecar is unavailable
    (caller should fall back to template-based wake-up output).
    """
    system = (
        "You are a briefing assistant for a personal AI knowledge base. "
        "Produce exactly 3 terse bullets for a session-start briefing from the provided "
        "events and system state. Focus on what changed, what is blocked, and what needs "
        "attention next. Keep each bullet under 14 words. Be specific. Do not add a title, "
        "intro, or speculation."
    )
    prompt = (
        f"System state:\n{state_summary}\n\n"
        f"Recent events:\n{events_text}\n\n"
        "Session-start briefing:"
    )
    return ask(prompt, model=BRIEFING_MODEL, system=system, timeout=60)
