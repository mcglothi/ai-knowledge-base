#!/usr/bin/env python3
"""
AIKB Microsoft Copilot Studio Adapter (MVP)

Local HTTP facade for Copilot Studio custom connectors.

Endpoints:
- POST /health
- POST /copilot/remember
- POST /copilot/recall
- POST /copilot/context-pack

Auth modes (env):
- AIKB_AUTH_MODE=none (default)
- AIKB_AUTH_MODE=api_key (requires header: x-api-key)
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

# Make AIKB search modules importable
AIKB_ROOT = Path(__file__).resolve().parents[2]
AIKB_SEARCH_DIR = AIKB_ROOT / "_tools" / "aikb-search"
sys.path.insert(0, str(AIKB_SEARCH_DIR))

from indexer import DB_PATH, build_index  # type: ignore
from search import search as aikb_search_impl  # type: ignore

EVENTS_DIR = AIKB_ROOT / "_runtime" / "events"

SECRET_HINTS = ("password", "api_key", "apikey", "token", "secret", "private key")


@dataclass
class Config:
    host: str
    port: int
    auth_mode: str
    api_key: str
    tenant_default: str
    project_default: str


CFG = Config(
    host=os.getenv("AIKB_ADAPTER_HOST", "127.0.0.1"),
    port=int(os.getenv("AIKB_ADAPTER_PORT", "8787")),
    auth_mode=os.getenv("AIKB_AUTH_MODE", "none").strip().lower(),
    api_key=os.getenv("AIKB_API_KEY", ""),
    tenant_default=os.getenv("AIKB_TENANT_ID", "default-tenant"),
    project_default=os.getenv("AIKB_PROJECT_ID", "general"),
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ensure_index() -> None:
    if not DB_PATH.exists():
        build_index(verbose=False)


def mk_event_id() -> str:
    n = now_utc()
    return f"evt_{n.strftime('%Y%m%d_%H%M%S_%f')}_{uuid4().hex[:6]}"


def write_event(event: dict[str, Any]) -> Path:
    n = now_utc()
    out_file = EVENTS_DIR / f"{n.strftime('%Y-%m-%d')}.ndjson"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=True) + "\n")
    return out_file


def sanitize_text(v: str) -> str:
    return re.sub(r"\s+", " ", (v or "").strip())


def build_context_pack(results: list[dict[str, Any]], max_bullets: int = 5) -> dict[str, Any]:
    bullets: list[str] = []
    snippets: list[str] = []

    for r in results[:max_bullets]:
        file_ = r.get("file", "")
        section = r.get("section", "")
        excerpt = sanitize_text(str(r.get("excerpt", "")))
        bullets.append(f"{file_} § {section}: {excerpt[:140]}")
        snippets.append(f"[{file_} § {section}] {excerpt}")

    if bullets:
        summary = "Relevant prior context found in AIKB memory/search results."
    else:
        summary = "No high-confidence prior context found."

    context_text = "\n".join([f"- {b}" for b in bullets])
    token_estimate = max(1, int(len(context_text.split()) * 1.35))

    return {
        "summary": summary,
        "bullet_context": bullets,
        "context_text": context_text,
        "token_estimate": token_estimate,
        "sources": [
            {
                "file": r.get("file", ""),
                "section": r.get("section", ""),
                "score": r.get("score", 0),
                "date": r.get("date", ""),
            }
            for r in results[:max_bullets]
        ],
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "AIKB-MSCS-Adapter/0.1"

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            raise ValueError("Invalid JSON body")

    def _send(self, code: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _check_auth(self) -> bool:
        if CFG.auth_mode == "none":
            return True
        if CFG.auth_mode == "api_key":
            supplied = self.headers.get("x-api-key", "")
            return bool(CFG.api_key) and supplied == CFG.api_key
        return False

    def do_GET(self) -> None:
        if self.path == "/health":
            return self._send(
                200,
                {
                    "status": "ok",
                    "service": "aikb-mscs-adapter",
                    "version": "0.1.0",
                    "auth_mode": CFG.auth_mode,
                    "db_index_present": DB_PATH.exists(),
                },
            )
        self._send(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if not self._check_auth() and self.path != "/health":
            return self._send(401, {"error": "unauthorized", "message": "Missing/invalid credentials"})

        try:
            if self.path == "/health":
                return self._send(200, {"status": "ok"})

            if self.path == "/copilot/remember":
                req = self._read_json()
                text = sanitize_text(str(req.get("text", "")))
                if not text:
                    return self._send(400, {"error": "bad_request", "message": "text is required"})
                if any(h in text.lower() for h in SECRET_HINTS):
                    return self._send(
                        400,
                        {
                            "error": "secret_detected",
                            "message": "Potential secret detected. Store credentials in a vault and reference by name.",
                        },
                    )

                tenant_id = str(req.get("tenant_id") or CFG.tenant_default)
                project_id = str(req.get("project_id") or CFG.project_default)
                agent_id = str(req.get("agent_id") or "copilot-studio")
                user_id = str(req.get("user_id") or "unknown")
                tags = req.get("tags") or []
                if not isinstance(tags, list):
                    tags = []

                event = {
                    "id": mk_event_id(),
                    "ts_utc": now_utc().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "session_id": f"mscs-{now_utc().strftime('%Y%m%d%H%M%S')}",
                    "agent": agent_id,
                    "type": str(req.get("type") or "observation"),
                    "project": project_id,
                    "summary": text,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "tags": tags,
                    "source": str(req.get("source") or "copilot_studio"),
                    "sensitivity": str(req.get("pii_level") or "normal"),
                    "promote_hint": str(req.get("promote_hint") or "candidate"),
                    "evidence": [],
                }
                out_file = write_event(event)
                return self._send(
                    200,
                    {
                        "status": "accepted",
                        "event_id": event["id"],
                        "stored_at": event["ts_utc"],
                        "file": str(out_file.relative_to(AIKB_ROOT)),
                    },
                )

            if self.path == "/copilot/recall":
                req = self._read_json()
                query = sanitize_text(str(req.get("query", "")))
                if not query:
                    return self._send(400, {"error": "bad_request", "message": "query is required"})

                top_k = int(req.get("limit", 5))
                top_k = 1 if top_k < 1 else 10 if top_k > 10 else top_k

                ensure_index()
                rows = aikb_search_impl(query, top_k=top_k, include_related=True)

                # Optional lightweight post-filtering by tag tokens
                filters = req.get("filters") or {}
                tags_any = filters.get("tags_any") if isinstance(filters, dict) else None
                min_conf = filters.get("min_confidence") if isinstance(filters, dict) else None

                results = []
                for i, r in enumerate(rows, 1):
                    score = float(r.get("score", 0.0))
                    if isinstance(min_conf, (int, float)) and score < float(min_conf):
                        continue

                    text = sanitize_text(str(r.get("excerpt", "")))
                    if isinstance(tags_any, list) and tags_any:
                        joined = f"{r.get('file','')} {r.get('section','')} {text}".lower()
                        if not any(str(t).lower() in joined for t in tags_any):
                            continue

                    results.append(
                        {
                            "memory_id": f"mem_{i}",
                            "text": text,
                            "score": score,
                            "timestamp": r.get("date", ""),
                            "tags": [],
                            "file": r.get("file", ""),
                            "section": r.get("section", ""),
                        }
                    )

                return self._send(200, {"results": results})

            if self.path == "/copilot/context-pack":
                req = self._read_json()
                query = sanitize_text(str(req.get("query", "")))
                if not query:
                    return self._send(400, {"error": "bad_request", "message": "query is required"})

                top_k = int(req.get("limit", 5))
                top_k = 1 if top_k < 1 else 10 if top_k > 10 else top_k

                ensure_index()
                rows = aikb_search_impl(query, top_k=top_k, include_related=True)
                pack = build_context_pack(rows, max_bullets=top_k)
                return self._send(200, pack)

            return self._send(404, {"error": "not_found"})

        except ValueError as ve:
            return self._send(400, {"error": "bad_request", "message": str(ve)})
        except Exception as e:
            return self._send(500, {"error": "internal_error", "message": str(e)})


def main() -> None:
    httpd = ThreadingHTTPServer((CFG.host, CFG.port), Handler)
    print(
        f"AIKB MSCS adapter listening on http://{CFG.host}:{CFG.port} "
        f"(auth_mode={CFG.auth_mode})"
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
