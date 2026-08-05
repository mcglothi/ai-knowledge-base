#!/usr/bin/env python3
"""AIKB doctor — validate the installation and print an integration matrix.

Run directly or via `runtime_cli.py doctor`. Exits non-zero when any check
FAILs; WARNs are informational (degraded but functional).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"

REQUIRED_DIRS = [
    "_runtime/events",
    "_runtime/candidates",
    "_runtime/im",
    "_agents",
    "docs/playbooks",
]

CORE_SCRIPTS = [
    "_tools/memory-pipeline/ingest_runtime.py",
    "_tools/memory-pipeline/build_candidates.py",
    "_tools/memory-pipeline/memory_search.py",
    "_tools/memory-pipeline/runtime_cli.py",
    "_tools/memory-pipeline/redaction.py",
    "_tools/aikb-search/server.py",
]

PLAYBOOKS = [
    "docs/playbooks/im.md",
    "docs/playbooks/token-economy.md",
    "docs/playbooks/closeout.md",
    "docs/playbooks/git-checkpointing.md",
]


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    # Actionable remedy, surfaced in --json so an agent can self-correct.
    fix: str = ""


def check_python() -> Check:
    version = sys.version_info
    if version >= (3, 10):
        return Check("python", OK, f"{version.major}.{version.minor}.{version.micro}")
    return Check("python", FAIL, f"{version.major}.{version.minor} < 3.10")


def check_paths() -> list[Check]:
    checks = []
    for rel in REQUIRED_DIRS:
        path = ROOT / rel
        checks.append(Check(f"dir {rel}", OK if path.is_dir() else FAIL, str(path) if not path.is_dir() else ""))
    for rel in CORE_SCRIPTS:
        path = ROOT / rel
        checks.append(Check(f"script {rel}", OK if path.is_file() else FAIL))
    for rel in PLAYBOOKS:
        path = ROOT / rel
        checks.append(Check(f"playbook {rel}", OK if path.is_file() else WARN, "" if path.is_file() else "missing"))
    return checks


def check_event_write() -> Check:
    """Round-trip an event through the real capture path, then remove it."""
    sentinel_date = "1999-12-31"
    out_file = ROOT / "_runtime" / "events" / f"{sentinel_date}.ndjson"
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "_tools" / "memory-pipeline" / "ingest_runtime.py"),
                "--agent", "doctor",
                "--session-id", "doctor",
                "--type", "observation",
                "--project", "general",
                "--summary", "doctor write test",
                "--promote-hint", "ignore",
                "--date", sentinel_date,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return Check("event write", FAIL, (proc.stderr or proc.stdout).strip()[:200])
        payload = out_file.read_text(encoding="utf-8").strip().splitlines()
        json.loads(payload[-1])
        return Check("event write", OK)
    except Exception as exc:  # noqa: BLE001 — doctor must not crash on any check
        return Check("event write", FAIL, str(exc)[:200])
    finally:
        if out_file.exists():
            out_file.unlink()


def check_keyword_search() -> Check:
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "_tools" / "memory-pipeline" / "memory_search.py"),
                "--query", "readme overview",
                "--limit", "1",
                "--no-semantic",
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return Check("keyword search", FAIL, (proc.stderr or proc.stdout).strip()[:200])
        json.loads(proc.stdout)
        return Check("keyword search", OK)
    except Exception as exc:  # noqa: BLE001
        return Check("keyword search", FAIL, str(exc)[:200])


def check_semantic_backend() -> Check:
    try:
        import sentence_transformers  # noqa: F401

        return Check("semantic backend (memory_search)", OK)
    except ImportError:
        return Check(
            "semantic backend (memory_search)",
            WARN,
            "sentence-transformers not importable; hybrid mode silently degrades to keyword",
        )


def check_mcp_search_venv() -> Check:
    venv_python = ROOT / "_tools" / "aikb-search" / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return Check(
            "aikb-search venv",
            WARN,
            "no venv — run _tools/aikb-search/setup.sh to enable the MCP search server",
        )
    proc = subprocess.run(
        [str(venv_python), "-c", "import fastembed, fastmcp"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return Check("aikb-search venv", FAIL, "venv exists but fastembed/fastmcp missing")
    return Check("aikb-search venv", OK)


def check_search_index() -> Check:
    db = ROOT / "_tools" / "aikb-search" / "aikb_index.db"
    if db.exists():
        return Check("search index", OK, f"{db.stat().st_size // 1024} KiB")
    return Check("search index", WARN, "not built yet — auto-builds on first MCP search")


def check_git() -> list[Check]:
    checks = []
    if not shutil.which("git"):
        return [Check("git", FAIL, "git not on PATH")]
    inside = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if inside.returncode != 0:
        return [Check("git repo", FAIL, "AIKB root is not a git repository")]
    checks.append(Check("git repo", OK))
    remotes = subprocess.run(
        ["git", "-C", str(ROOT), "remote"], capture_output=True, text=True
    ).stdout.strip()
    checks.append(
        Check("git remote", OK if remotes else WARN, "" if remotes else "no remote — sync across machines unavailable")
    )
    return checks


def check_onboarding() -> list[Check]:
    """Is *setup* finished? Distinct from the runtime-health checks above.

    These are the questions an agent needs answered to know what is left to do
    on a fresh clone, and to verify its own work after running the installer.
    Each carries a `fix` so the answer is actionable without extra lookup.
    """
    checks: list[Check] = []

    config_dir = ROOT / ".aikb-config.d"
    configured = config_dir.is_dir() and (config_dir / "GITHUB_USERNAME").exists()
    checks.append(
        Check(
            "installer run",
            OK if configured else FAIL,
            "" if configured else "no .aikb-config.d/ — run install.sh (or install.py --config)",
            fix="python3 install.py --print-schema",
        )
    )

    # Unsubstituted placeholders mean a partial or failed personalization.
    stale: list[str] = []
    targets = list((ROOT / "_agents").rglob("*.md"))
    for extra in ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", "_index.md"):
        p = ROOT / extra
        if p.exists():
            targets.append(p)
    for path in targets:
        try:
            if "{{" in path.read_text(encoding="utf-8"):
                stale.append(str(path.relative_to(ROOT)))
        except (OSError, UnicodeDecodeError):
            continue
    checks.append(
        Check(
            "placeholders substituted",
            OK if not stale else FAIL,
            "" if not stale else f"{len(stale)} file(s) still contain {{{{...}}}}: {', '.join(sorted(stale)[:3])}",
            fix="rerun the installer, or ./sync.sh to re-apply saved config",
        )
    )

    profile = ROOT / "personal" / "profile.md"
    if not profile.exists():
        checks.append(Check("profile filled in", FAIL, "personal/profile.md missing", fix="ask the operator the onboarding interview questions"))
    else:
        text = profile.read_text(encoding="utf-8", errors="ignore")
        placeholder = ("[TODO" in text) or ("[Your " in text) or ("Software engineer with 8 years" in text)
        checks.append(
            Check(
                "profile filled in",
                WARN if placeholder else OK,
                "still contains example/placeholder text" if placeholder else "",
                fix="ask the operator the onboarding interview questions, then rewrite personal/profile.md",
            )
        )

    dev_env = ROOT / "personal" / "dev-environment"
    machines = [p for p in dev_env.glob("*.md") if p.name != "README.md"] if dev_env.is_dir() else []
    checks.append(
        Check(
            "machine profile",
            OK if machines else WARN,
            f"{len(machines)} machine profile(s)" if machines else "no per-machine profile yet",
            fix="cp _templates/machine-profile.md personal/dev-environment/<hostname>.md",
        )
    )

    # Which agent front-ends are actually wired up on this machine.
    wired = []
    if (Path.home() / ".claude" / "CLAUDE.md").exists():
        wired.append("claude-code")
    if (Path.home() / ".gemini" / "GEMINI.md").exists():
        wired.append("gemini-cli")
    if (Path.home() / ".config" / "opencode" / "opencode.json").exists():
        wired.append("opencode")
    checks.append(
        Check(
            "agent files installed",
            OK if wired else WARN,
            ", ".join(wired) if wired else "no agent instruction files found in $HOME",
            fix="rerun the installer and select your tools",
        )
    )

    settings = Path.home() / ".claude" / "settings.json"
    hooked = False
    if settings.exists():
        try:
            hooked = "aikb-session-stop.sh" in settings.read_text(encoding="utf-8")
        except OSError:
            hooked = False
    checks.append(
        Check(
            "session stop hook",
            OK if hooked else WARN,
            "" if hooked else "not registered — session context is not captured automatically",
            fix="see docs/stop-hook-setup.md",
        )
    )

    return checks


def deep_check_hints() -> list[str]:
    hints = []
    for rel, label in [
        ("_tools/health-check.py", "host health"),
        ("_tools/combined-health-check.sh", "combined infra health"),
        ("_tools/validation/run_v2_trial.sh", "agent instruction validation"),
    ]:
        if (ROOT / rel).exists():
            hints.append(f"{rel}  ({label})")
    return hints


def main() -> int:
    args = sys.argv[1:]
    as_json = "--json" in args
    onboarding_only = "--onboarding" in args

    if onboarding_only:
        checks = check_onboarding()
    else:
        checks = [check_python()]
        checks.extend(check_paths())
        checks.append(check_event_write())
        checks.append(check_keyword_search())
        checks.append(check_semantic_backend())
        checks.append(check_mcp_search_venv())
        checks.append(check_search_index())
        checks.extend(check_git())
        checks.extend(check_onboarding())

    if as_json:
        fails = [c for c in checks if c.status == FAIL]
        warns = [c for c in checks if c.status == WARN]
        payload = {
            "root": str(ROOT),
            "ok": not fails,
            "summary": {
                "total": len(checks),
                "ok": len(checks) - len(fails) - len(warns),
                "warn": len(warns),
                "fail": len(fails),
            },
            "checks": [
                {"name": c.name, "status": c.status, "detail": c.detail, "fix": c.fix}
                for c in checks
            ],
            "next_actions": [
                {"name": c.name, "status": c.status, "fix": c.fix}
                for c in checks
                if c.status in (FAIL, WARN) and c.fix
            ],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1 if fails else 0

    width = max(len(c.name) for c in checks) + 2
    print(f"AIKB doctor — {ROOT}")
    print()
    for check in checks:
        icon = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}[check.status]
        detail = f"  — {check.detail}" if check.detail else ""
        print(f"  {icon} {check.name.ljust(width)} {check.status}{detail}")

    fails = [c for c in checks if c.status == FAIL]
    warns = [c for c in checks if c.status == WARN]
    print()
    print(f"{len(checks)} checks: {len(checks) - len(fails) - len(warns)} ok, {len(warns)} warn, {len(fails)} fail")

    actionable = [c for c in checks if c.status in (FAIL, WARN) and c.fix]
    if actionable:
        print("\nSuggested next steps:")
        for check in actionable:
            print(f"  - {check.name}: {check.fix}")

    hints = deep_check_hints()
    if hints:
        print("\nDeeper checks available on this instance:")
        for hint in hints:
            print(f"  - {hint}")

    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
