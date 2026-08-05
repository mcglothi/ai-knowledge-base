#!/usr/bin/env python3
# =============================================================================
# AIKB TUI Installer
# Personalizes agent instruction files with your GitHub username, repo name,
# and local path after you've cloned the template.
#
# Usage: ./install.sh (which calls this script)
# =============================================================================

import argparse
import os
import re
import sys
import subprocess
import platform
import socket
import json
from pathlib import Path
from datetime import datetime, timezone

# ── Shared setup vocabulary ──────────────────────────────────────────────────
# Defined at module level so the interactive TUI and the non-interactive/agent
# path stay in lockstep — there is exactly one list of tools and one secrets map.

TOOL_CHOICES = [
    "Claude Code",
    "Gemini CLI",
    "OpenCode",
    "Cursor",
    "ChatGPT (web)",
    "Gemini (web)",
    "Grok",
    "Codex CLI",
]

WEB_TOOLS = {"ChatGPT (web)", "Gemini (web)", "Grok"}

SECRETS_MAP = {
    "1Password": ("1Password", 'op read "op://Private/ITEM_NAME/credential"'),
    "Bitwarden / Vaultwarden": ("Bitwarden", 'bw get password "PAT/<Service>/<Name>" --session "$BW_SESSION"'),
    "Delinea Secret Server": ("Delinea Secret Server", 'tss secret --secret <id> --field password  # id via personal/vaults/delinea.yaml'),
    "macOS Keychain": ("macOS Keychain", 'security find-generic-password -w -a "$USER" -s "ITEM_NAME"'),
    "Environment variables (.env / shell profile)": ("Environment variables", 'echo "$MY_SECRET_VAR"'),
    "Skip for now": ("your secrets manager", "[see your secrets manager documentation]"),
}

CONFIG_SCHEMA = {
    "github_username": "string  (required) — your GitHub username",
    "repo_name": "string  (default: AIKB) — name of your private AIKB repo",
    "local_path": "string  (default: cwd) — absolute path to this clone",
    "hostname": "string  (default: this machine's short hostname)",
    "secrets_manager": f"string  (default: 'Skip for now') — one of: {list(SECRETS_MAP)}",
    "tools": f"list of strings (required, >=1) — any of: {TOOL_CHOICES}",
    "setup_search": "bool  (default: false) — run _tools/aikb-search/setup.sh after install",
    "install_stop_hook": "bool  (default: false) — register the session stop hook for Claude Code",
    "commit": "bool  (default: true) — create the initial personalization commit",
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="install.py",
        description="Personalize this AIKB clone. Runs an interactive TUI by default; "
                    "use --config/--non-interactive to drive it from a script or an AI agent.",
    )
    p.add_argument("--config", metavar="PATH",
                   help="JSON file of setup answers. Implies --non-interactive. Use '-' to read stdin.")
    p.add_argument("--non-interactive", action="store_true",
                   help="Never prompt. Requires --config, or --defaults to accept every default.")
    p.add_argument("--defaults", action="store_true",
                   help="With --non-interactive, fill any unspecified field from auto-discovery.")
    p.add_argument("--print-schema", action="store_true",
                   help="Print the --config JSON schema and exit. Needs no dependencies.")
    p.add_argument("--dry-run", action="store_true",
                   help="With --non-interactive, resolve and print the config without writing anything.")
    return p.parse_args(argv)


ARGS = parse_args()
NON_INTERACTIVE = ARGS.non_interactive or ARGS.config is not None

# --print-schema must work on a bare clone with nothing installed, so it is
# handled before any third-party import is attempted.
if ARGS.print_schema:
    print(json.dumps(CONFIG_SCHEMA, indent=2, ensure_ascii=False))
    sys.exit(0)

# ── Dependency Bootstrap (Phase 0) ───────────────────────────────────────────
# questionary is only needed to ask questions, so the non-interactive path does
# not require it. rich is presentation-only and degrades to plain text, which
# keeps the agent-driven path runnable on a stdlib-only Python.
REQUIRED = {"rich": "rich"} if NON_INTERACTIVE else {"rich": "rich", "questionary": "questionary"}

missing = []
for pkg, import_name in REQUIRED.items():
    try:
        __import__(import_name)
    except ImportError:
        missing.append(pkg)

if missing:
    if NON_INTERACTIVE:
        # Never block an unattended run on a prompt; try quietly, then degrade.
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    else:
        print(f"\nAIKB needs {', '.join(missing)} to run the installer.")
        if not sys.stdin.isatty():
            print(
                "\nNo interactive terminal detected.\n"
                "  • To install dependencies yourself:  pip install " + " ".join(missing) + "\n"
                "  • To run without a terminal at all:  python3 install.py --print-schema\n"
                "    then:                              python3 install.py --config setup.json\n"
            )
            sys.exit(1)
        ans = input("Install them now with pip? [Y/n]: ").strip().lower()
        if ans in ("", "y"):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet"] + missing)
                print("Done. Restarting installer...\n")
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except subprocess.CalledProcessError:
                print(f"Error: Failed to install dependencies. Try running: pip install {' '.join(missing)}")
                sys.exit(1)
        else:
            print("Run: pip install " + " ".join(missing))
            sys.exit(1)


class _PlainConsole:
    """Minimal stand-in for rich.Console so --non-interactive needs no deps."""

    _MARKUP = re.compile(r"\[/?[a-zA-Z0-9 _#=.,()-]*\]")

    def print(self, *args, **kwargs):
        for a in args:
            print(self._MARKUP.sub("", str(a)) if isinstance(a, str) else a)
        if not args:
            print()


try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
    RICH_OK = True
except ImportError:
    console = _PlainConsole()
    RICH_OK = False

if not NON_INTERACTIVE:
    import questionary

# ── Platform Detection (Phase 2) ─────────────────────────────────────────────
def detect_platform():
    system = platform.system()
    if system == "Windows":
        return "windows-native"
    elif system == "Linux":
        try:
            with open("/proc/version") as f:
                content = f.read().lower()
                if "microsoft" in content or "wsl" in content:
                    cwd = os.getcwd()
                    if cwd.startswith("/mnt/"):
                        return "wsl-wrong-fs"
                    return "wsl"
        except Exception:
            pass
        return "linux"
    elif system == "Darwin":
        return "macos"
    return "unknown"

# ── Prerequisite Checks (Phase 3) ────────────────────────────────────────────
def check_prerequisites():
    results = []
    git_found = False
    try:
        git_ver = subprocess.check_output(["git", "--version"]).decode().strip().split()[-1]
        results.append(("git", f"✓ {git_ver}", ""))
        git_found = True
    except:
        results.append(("git", "✗ missing", "Required for AIKB"))

    results.append(("python3", f"✓ {platform.python_version()}", ""))

    gh_found = False
    try:
        gh_ver = subprocess.check_output(["gh", "--version"]).decode().strip().split("\n")[0].split()[-1]
        results.append(("gh (GitHub CLI)", f"✓ {gh_ver}", "Optional — enables one-command repo creation"))
        gh_found = True
    except:
        results.append(("gh (GitHub CLI)", "✗ missing", "Optional"))

    return results, git_found, gh_found

# ── Configuration Discovery ──────────────────────────────────────────────────
def discover_config():
    config = {
        "github_username": "",
        "repo_name": "AIKB",
        "local_path": os.getcwd(),
        "hostname": socket.gethostname().split(".")[0],
    }

    try:
        origin_url = subprocess.check_output(["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL).decode().strip()
        import re
        # Match git@github.com:username/repo.git or https://github.com/username/repo(.git)
        match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)(\.git)?$', origin_url)
        if match:
            config["github_username"] = match.group(1)
            config["repo_name"] = match.group(2)
    except:
        pass

    if not config["github_username"]:
        try:
            gh_user = subprocess.check_output(["gh", "api", "user", "--jq", ".login"], stderr=subprocess.DEVNULL).decode().strip()
            config["github_username"] = gh_user
        except:
            pass

    return config


# ── Setup Execution (shared by the TUI and the non-interactive path) ─────────
# Everything that actually changes the filesystem lives here, so the interactive
# installer and an AI agent driving --config perform byte-identical work.

def resolve_config(raw: dict, discovered: dict, plat: str) -> dict:
    """Fill defaults, validate, and derive every value setup needs.

    Raises ValueError with an actionable message on bad input — the agent path
    depends on failing loudly rather than silently writing empty strings.
    """
    cfg = dict(raw or {})

    cfg.setdefault("github_username", discovered.get("github_username", ""))
    cfg.setdefault("repo_name", discovered.get("repo_name", "AIKB"))
    cfg.setdefault("local_path", discovered.get("local_path", os.getcwd()))
    cfg.setdefault("hostname", discovered.get("hostname", ""))
    cfg.setdefault("secrets_manager", "Skip for now")
    cfg.setdefault("tools", [])
    cfg.setdefault("setup_search", False)
    cfg.setdefault("install_stop_hook", False)
    cfg.setdefault("commit", True)

    unknown = set(cfg) - set(CONFIG_SCHEMA)
    if unknown:
        raise ValueError(f"unknown config key(s): {sorted(unknown)}. Run --print-schema for the accepted keys.")

    for field in ("github_username", "repo_name", "local_path", "hostname"):
        if not str(cfg.get(field) or "").strip():
            raise ValueError(f"'{field}' is required and could not be auto-discovered — set it in --config.")

    if cfg["secrets_manager"] not in SECRETS_MAP:
        raise ValueError(f"secrets_manager must be one of {list(SECRETS_MAP)} (got {cfg['secrets_manager']!r})")

    if not isinstance(cfg["tools"], list) or not cfg["tools"]:
        raise ValueError(f"'tools' must be a non-empty list; choose from {TOOL_CHOICES}")
    bad_tools = [t for t in cfg["tools"] if t not in TOOL_CHOICES]
    if bad_tools:
        raise ValueError(f"unknown tool(s): {bad_tools}. Valid choices: {TOOL_CHOICES}")

    cfg["repo_url"] = f"https://github.com/{cfg['github_username']}/{cfg['repo_name']}"
    cfg["repo_ssh"] = f"git@github.com:{cfg['github_username']}/{cfg['repo_name']}.git"
    cfg["code_root"] = str(Path(cfg["local_path"]).parent) + "/"
    cfg["os_friendly"] = (
        "macOS" if plat == "macos"
        else "Linux" if plat in ("linux", "wsl", "wsl-wrong-fs")
        else plat
    )
    cfg["secrets_manager_label"], cfg["secrets_retrieve"] = SECRETS_MAP[cfg["secrets_manager"]]
    return cfg


SETUP_STEPS = [
    "Substituting placeholders in agent files",
    "Updating _index.md",
    "Scaffolding personal profile files",
    "Saving configuration to .aikb-config.d/",
    "Adding upstream remote",
    "Creating initial commit",
    "Configuring AI tools",
    "Optional components (search, stop hook)",
]


def apply_setup(cfg: dict, step):
    """Perform the setup. `step(i, label)` is called as each step completes."""
    subs = {
        "{{GITHUB_USERNAME}}": cfg["github_username"],
        "{{REPO_NAME}}": cfg["repo_name"],
        "{{REPO_URL}}": cfg["repo_url"],
        "{{REPO_SSH}}": cfg["repo_ssh"],
        "{{LOCAL_PATH}}": cfg["local_path"],
        "{{CODE_ROOT}}": cfg["code_root"],
        "{{PRIMARY_HOSTNAME}}": cfg["hostname"],
        "{{OS}}": cfg["os_friendly"],
        "{{SECRETS_MANAGER}}": cfg["secrets_manager_label"],
        "{{SECRETS_RETRIEVE}}": cfg["secrets_retrieve"],
    }

    def apply_subs(path: Path):
        content = path.read_text()
        for k, v in subs.items():
            content = content.replace(k, v)
        path.write_text(content)

    # 1 — placeholder substitution.
    # Recursive: v2 overlays and shared L1 files live in subdirectories
    # (_agents/v2/, _agents/shared/) and must be personalized too.
    for tmpl in Path("_agents").rglob("*.md"):
        apply_subs(tmpl)
    for extra in (Path("AGENTS.md"), Path("CLAUDE.md"), Path(".github/copilot-instructions.md")):
        # sync.sh personalizes these too; the installer must match it.
        if extra.exists():
            apply_subs(extra)
    step(1, SETUP_STEPS[0])

    # 2 — _index.md
    index_md = Path("_index.md")
    if index_md.exists():
        content = index_md.read_text()
        content = content.replace("{{GITHUB_USERNAME}}", cfg["github_username"]).replace(
            "{{REPO_NAME}}", cfg["repo_name"]
        )
        index_md.write_text(content)
    step(2, SETUP_STEPS[1])

    # 3 — scaffold personal files
    hostname = cfg["hostname"]
    profile_path = Path("personal/profile.md")
    if not profile_path.exists():
        example_profile = Path("example/personal/profile.md")
        if example_profile.exists():
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(example_profile.read_text())

    dev_env_dir = Path("personal/dev-environment")
    dev_env_dir.mkdir(parents=True, exist_ok=True)
    readme_path = dev_env_dir / "README.md"
    if not readme_path.exists():
        example_dev = Path("example/personal/dev-environment.md")
        if example_dev.exists():
            readme_path.write_text(example_dev.read_text().replace("my-macbook", hostname))

    machine_profile = dev_env_dir / f"{hostname}.md"
    if not machine_profile.exists():
        template_machine = Path("_templates/machine-profile.md")
        if template_machine.exists():
            machine_profile.write_text(template_machine.read_text().replace("[hostname]", hostname))
    step(3, SETUP_STEPS[2])

    # 4 — persist config for sync.sh
    config_dir = Path(".aikb-config.d")
    config_dir.mkdir(exist_ok=True)
    for key, value in (
        ("GITHUB_USERNAME", cfg["github_username"]),
        ("REPO_NAME", cfg["repo_name"]),
        ("REPO_URL", cfg["repo_url"]),
        ("REPO_SSH", cfg["repo_ssh"]),
        ("LOCAL_PATH", cfg["local_path"]),
        ("CODE_ROOT", cfg["code_root"]),
        ("PRIMARY_HOSTNAME", hostname),
        ("OS", cfg["os_friendly"]),
        ("SECRETS_MANAGER", cfg["secrets_manager_label"]),
        ("SECRETS_RETRIEVE", cfg["secrets_retrieve"]),
    ):
        (config_dir / key).write_text(value)
    step(4, SETUP_STEPS[3])

    # 5 — upstream remote + template-sync state
    subprocess.run(
        ["git", "remote", "add", "upstream", "https://github.com/mcglothi/ai-knowledge-base.git"],
        stderr=subprocess.DEVNULL,
    )
    try:
        subprocess.run(["git", "fetch", "upstream", "--quiet"], stderr=subprocess.DEVNULL)
        upstream_sha = subprocess.check_output(
            ["git", "rev-parse", "upstream/main"], stderr=subprocess.DEVNULL
        ).decode().strip()
        if upstream_sha:
            stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            (config_dir / "template-sync-state.json").write_text(
                json.dumps(
                    {
                        "last_checked_utc": stamp,
                        "last_seen_upstream_sha": upstream_sha,
                        "last_applied_upstream_sha": upstream_sha,
                        "check_interval_days": 7,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
    except Exception:
        pass
    step(5, SETUP_STEPS[4])

    # 6 — initial commit
    if cfg["commit"]:
        subprocess.run(["git", "add", "-A"])
        subprocess.run(
            ["git", "commit", "-m", f"chore: personalize AIKB for {cfg['github_username']}", "--allow-empty"],
            stdout=subprocess.DEVNULL,
        )
    step(6, SETUP_STEPS[5])

    # 7 — write agent config files
    tools = cfg["tools"]
    if "Claude Code" in tools:
        claude_dir = Path.home() / ".claude"
        claude_dir.mkdir(exist_ok=True)
        src = Path("_agents/claude-code.md")
        if src.exists():
            (claude_dir / "CLAUDE.md").write_text(src.read_text())

    if "Gemini CLI" in tools:
        gemini_dir = Path.home() / ".gemini"
        gemini_dir.mkdir(exist_ok=True)
        src = Path("_agents/gemini-cli.md")
        if not src.exists():  # fallback for naming variations
            src = Path("_agents/gemini.md")
        if src.exists():
            (gemini_dir / "GEMINI.md").write_text(src.read_text())

    if "OpenCode" in tools:
        opencode_config = Path.home() / ".config/opencode/opencode.json"
        opencode_src = Path(cfg["local_path"]) / "_agents/opencode.md"
        opencode_config.parent.mkdir(parents=True, exist_ok=True)
        config_data = {}
        if opencode_config.exists():
            try:
                config_data = json.loads(opencode_config.read_text())
            except Exception:
                pass
        instructions = config_data.get("instructions", [])
        if str(opencode_src) not in instructions:
            instructions.append(str(opencode_src))
            config_data["instructions"] = instructions
            opencode_config.write_text(json.dumps(config_data, indent=2))
    step(7, SETUP_STEPS[6])

    # 8 — optional components
    notes = []
    if cfg["setup_search"]:
        search_setup = Path("_tools/aikb-search/setup.sh")
        if search_setup.exists():
            rc = subprocess.run(["bash", str(search_setup)]).returncode
            notes.append("search: installed" if rc == 0 else f"search: setup.sh exited {rc}")
        else:
            notes.append("search: _tools/aikb-search/setup.sh not found")
    if cfg["install_stop_hook"]:
        notes.append(install_stop_hook(cfg))
    step(8, SETUP_STEPS[7])
    return notes


def install_stop_hook(cfg: dict) -> str:
    """Register the AIKB session stop hook in ~/.claude/settings.json.

    Merges into any existing settings rather than overwriting them, and is a
    no-op if an AIKB stop hook is already registered.
    """
    settings = Path.home() / ".claude" / "settings.json"
    command = f"bash {cfg['local_path']}/_tools/memory-pipeline/aikb-session-stop.sh"
    try:
        settings.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if settings.exists():
            try:
                data = json.loads(settings.read_text())
            except json.JSONDecodeError:
                return f"stop hook: {settings} is not valid JSON — left untouched"
        hooks = data.setdefault("hooks", {})
        stop = hooks.setdefault("Stop", [])
        if any("aikb-session-stop.sh" in json.dumps(entry) for entry in stop):
            return "stop hook: already registered"
        stop.append({"matcher": "", "hooks": [{"type": "command", "command": command}]})
        settings.write_text(json.dumps(data, indent=2) + "\n")
        return "stop hook: registered"
    except Exception as exc:
        return f"stop hook: failed ({exc})"


def run_non_interactive():
    """Entry point for scripted/agent-driven setup."""
    raw = {}
    if ARGS.config:
        try:
            text = sys.stdin.read() if ARGS.config == "-" else Path(ARGS.config).read_text()
            raw = json.loads(text)
        except FileNotFoundError:
            console.print(f"[red]Config file not found:[/red] {ARGS.config}")
            sys.exit(1)
        except json.JSONDecodeError as exc:
            console.print(f"[red]Config file is not valid JSON:[/red] {exc}")
            sys.exit(1)
    elif not ARGS.defaults:
        console.print(
            "[red]--non-interactive requires --config PATH (or --defaults).[/red]\n"
            "Run 'python3 install.py --print-schema' to see the accepted fields."
        )
        sys.exit(1)

    plat = detect_platform()
    if plat == "windows-native":
        console.print("[red]AIKB requires WSL on Windows. See docs/windows-wsl.md[/red]")
        sys.exit(1)

    try:
        cfg = resolve_config(raw, discover_config(), plat)
    except ValueError as exc:
        console.print(f"[red]Invalid config:[/red] {exc}")
        sys.exit(1)

    shown = {k: v for k, v in cfg.items() if k in CONFIG_SCHEMA}
    console.print("Resolved configuration:")
    console.print(json.dumps(shown, indent=2, ensure_ascii=False))

    if ARGS.dry_run:
        console.print("\n[yellow]--dry-run: nothing was written.[/yellow]")
        return

    total = len(SETUP_STEPS)
    notes = apply_setup(cfg, lambda i, label: console.print(f"  [{i}/{total}] {label}"))

    console.print("\nSetup complete.")
    for note in notes:
        console.print(f"  - {note}")

    manual = [t for t in cfg["tools"] if t in WEB_TOOLS or t == "Cursor"]
    if manual:
        console.print(
            "\nStill needs a manual paste (these tools have no config file):\n  "
            + "\n  ".join(f"{t} -> _agents/{TOOL_FILE_HINT.get(t, '')}" for t in manual)
        )
    console.print("\nNext: git push origin main")


TOOL_FILE_HINT = {
    "ChatGPT (web)": "chatgpt.md",
    "Gemini (web)": "gemini.md",
    "Grok": "grok.md",
    "Cursor": "cursor.md",
}


# ── Main Application ─────────────────────────────────────────────────────────
def main():
    # The TUI needs a real terminal. Without one, questionary's prompts either
    # raise EOFError or silently return empty answers — which would personalize
    # every file with blank values. Fail early with a usable alternative instead.
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        console.print(
            "[red]This installer needs an interactive terminal.[/red]\n\n"
            "It looks like you are running from a script, a pipe, or an AI agent.\n"
            "Use the non-interactive path instead:\n\n"
            "  1. python3 install.py --print-schema        # see the accepted fields\n"
            "  2. write your answers to setup.json\n"
            "  3. python3 install.py --config setup.json --dry-run\n"
            "  4. python3 install.py --config setup.json\n\n"
            "Or accept every auto-discovered default:\n"
            "  python3 install.py --non-interactive --defaults --config setup.json\n"
        )
        sys.exit(1)

    # Phase 1: Welcome Screen
    console.print(Panel.fit(
        "[bold blue]AIKB Setup[/bold blue]\n[blue]AI Knowledge Base — Unified Memory[/blue]",
        border_style="blue", padding=(1, 4)
    ))

    console.print(Panel(
        "Welcome! This installer will set up AIKB — a private Git repo\n"
        "that becomes your AI's long-term memory.\n\n"
        "After setup, every agent you configure (Claude Code, Gemini,\n"
        "ChatGPT, Cursor, etc.) will read from this repo at session start.\n"
        "It knows your projects, your preferences, and decisions from past\n"
        "sessions — without you re-explaining them.\n\n"
        "[bold cyan]What this script does:[/bold cyan]\n"
        "  ✦ Personalize your agent instruction files with your details\n"
        "  ✦ Wire up whichever AI tools you use\n"
        "  ✦ Create a committed, push-ready repo\n\n"
        "[dim]Time to complete: ~3 minutes[/dim]",
        title="[bold]About AIKB[/bold]", border_style="cyan"
    ))

    if not questionary.confirm("Ready to begin?", default=True).ask():
        console.print("[yellow]Aborted.[/yellow]")
        sys.exit(0)

    # Phase 2: Platform Detection
    plat = detect_platform()
    if plat == "windows-native":
        console.print(Panel(
            "⚠  [bold yellow]Windows Detected[/bold yellow]\n\n"
            "AIKB requires a Unix-compatible shell environment.\n"
            "On Windows, that means WSL (Windows Subsystem for Linux).\n\n"
            "Full setup guide: docs/windows-wsl.md\n"
            "(or: https://github.com/mcglothi/ai-knowledge-base/blob/main/docs/windows-wsl.md)\n\n"
            "[bold cyan]Quickstart:[/bold cyan]\n"
            "  1. Open PowerShell as Administrator\n"
            "  2. Run: [bold]wsl --install[/bold]\n"
            "  3. Reboot, open the new Ubuntu app\n"
            "  4. Come back here and re-run this script inside the WSL terminal",
            border_style="yellow"
        ))
        sys.exit(1)
    elif plat == "wsl-wrong-fs":
        console.print(Panel(
            "⚠  [bold yellow]WSL detected, but you're on the Windows filesystem (/mnt/...)[/bold yellow]\n\n"
            "This will cause slow Git performance and potential permission issues.\n"
            "AIKB works best when cloned inside WSL's own filesystem.\n\n"
            "[bold cyan]Recommended fix:[/bold cyan]\n"
            "  cd ~\n"
            "  git clone https://github.com/YOUR_USERNAME/AIKB.git ~/code/AIKB\n"
            "  cd ~/code/AIKB\n"
            "  python3 install.py\n\n"
            "You can continue here, but performance may be degraded.",
            border_style="yellow"
        ))
        if not questionary.confirm("Continue anyway?", default=False).ask():
            sys.exit(0)
    elif plat == "wsl":
        console.print("[green]✓ Running in WSL — full compatibility confirmed[/green]")
    elif plat in ("macos", "linux"):
        console.print(f"[green]✓ Platform: {plat.replace('macos', 'macOS').capitalize()} — good to go[/green]")
    else:
        console.print("[yellow]⚠ Unknown platform — continuing anyway[/yellow]")

    # Phase 3: Prerequisites Check
    results, git_found, gh_found = check_prerequisites()
    table = Table(title="Checking prerequisites...", box=None)
    table.add_column("Tool", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Note", style="dim")
    for r in results:
        table.add_row(*r)
    console.print(table)

    if not git_found:
        console.print("[red]✗ git is required but not installed. Install it and re-run.[/red]")
        sys.exit(1)

    # Phase 4: Persona Selection
    console.print("\n─── [bold]Which tools do you use?[/bold] ────────────────────────────────────\n")
    console.print(
        "AIKB can be wired into multiple AI tools at once. Tell us which\n"
        "ones you use and we'll configure each of them automatically.\n\n"
        "[dim](Arrow keys to move, Space to select, Enter to confirm)[/dim]\n"
    )

    selected_tools = questionary.checkbox(
        "Which AI tools do you use? (select all that apply)",
        choices=TOOL_CHOICES,
        validate=lambda x: True if len(x) > 0 else "Select at least one tool"
    ).ask()

    web_tools = WEB_TOOLS
    if any(tool in web_tools for tool in selected_tools):
        console.print(
            "\n[dim]Note: ChatGPT, Gemini (web), and Grok require a one-time\n"
            "manual paste into their Settings. We'll show you exactly what\n"
            "to do at the end of setup.[/dim]\n"
        )

    # Phase 5: Configuration
    console.print("\n─── [bold]Your Configuration[/bold] ─────────────────────────────────────────\n")
    console.print(
        "These values personalize the agent instruction files so agents\n"
        "know your repo location, your username, and your machine. Most\n"
        "are pre-filled from your Git config — just press Enter to accept.\n"
    )

    discovered = discover_config()

    # GitHub Username
    console.print(Panel(
        "Your public GitHub username. This is used to construct the URL\n"
        "for your AIKB repo (github.com/YOU/AIKB) so agents can reference\n"
        "it and the MCP server can find it.",
        title="GitHub Username", border_style="dim"
    ))
    github_username = questionary.text("GitHub username:", default=discovered["github_username"]).ask()
    if not github_username:
        console.print("[red]GitHub username is required.[/red]")
        sys.exit(1)

    # Repo Name
    console.print(Panel(
        "The name of your AIKB repo on GitHub. Leave as 'AIKB' unless\n"
        "you named it something different when you created it.",
        title="Repo Name", border_style="dim"
    ))
    repo_name = questionary.text("Repo name:", default=discovered["repo_name"]).ask()

    # Local Clone Path
    console.print(Panel(
        "Where this repo lives on your machine. Agents use this path to\n"
        "find and commit to your AIKB when running locally.",
        title="Local Path", border_style="dim"
    ))
    local_path = questionary.text("Local clone path:", default=discovered["local_path"]).ask()

    # Hostname
    console.print(Panel(
        "A short name for this machine (e.g. 'my-macbook', 'work-laptop').\n"
        "AIKB uses this to track which machine a setup was done on, and\n"
        "to create a machine profile file in personal/dev-environment/.",
        title="Hostname", border_style="dim"
    ))
    hostname = questionary.text("Primary machine hostname:", default=discovered["hostname"]).ask()

    # Phase 6: Secrets Manager
    console.print("\n─── [bold]Credential Retrieval (Optional)[/bold] ───────────────────────────\n")
    console.print(Panel(
        "AIKB stores references to credentials (like API keys, tokens)\n"
        "by name rather than value. The agent instruction files include\n"
        "a snippet showing agents HOW to retrieve a credential when they\n"
        "need one.\n\n"
        "This is optional and only affects comments in the generated\n"
        "files — no credentials are collected or stored.",
        border_style="dim"
    ))

    secrets_choice = questionary.select(
        "Which password manager do you use? (skip if unsure)",
        choices=list(SECRETS_MAP),
        default="Skip for now"
    ).ask()

    secrets_manager, secrets_retrieve = SECRETS_MAP[secrets_choice]

    # Optional core components the installer can wire up for you.
    console.print("\n─── [bold]Optional Components[/bold] ────────────────────────────────────────\n")
    setup_search = questionary.confirm(
        "Set up local search now? (builds the index — this is how agents recall memory)",
        default=True
    ).ask()
    install_hook = False
    if "Claude Code" in selected_tools:
        install_hook = questionary.confirm(
            "Register the session stop hook for Claude Code? (auto-captures context at session end)",
            default=True
        ).ask()

    # Phase 7: Review & Confirm
    repo_url = f"https://github.com/{github_username}/{repo_name}"
    repo_ssh = f"git@github.com:{github_username}/{repo_name}.git"
    code_root = str(Path(local_path).parent) + "/"
    os_friendly = "macOS" if plat == "macos" else "Linux" if plat in ("linux", "wsl", "wsl-wrong-fs") else plat

    console.print("\n─── [bold]Configuration Summary[/bold] ──────────────────────────────────────\n")
    summary = f"""[bold]GitHub username[/bold]  :  {github_username}
[bold]Repo name[/bold]        :  {repo_name}
[bold]Repo URL[/bold]         :  {repo_url}
[bold]Local path[/bold]       :  {local_path}
[bold]Hostname[/bold]         :  {hostname}
[bold]Secrets manager[/bold]  :  {secrets_manager}

[bold]Tools to configure:[/bold]
"""
    for tool in selected_tools:
        summary += f"    • {tool}\n"

    console.print(Panel(summary.strip(), border_style="green"))

    if not questionary.confirm("Proceed with setup?", default=True).ask():
        console.print("[yellow]Aborted.[/yellow]")
        sys.exit(0)

    # Phase 8: Execution — delegates to the same apply_setup() the
    # non-interactive/agent path uses, so both do byte-identical work.
    try:
        cfg = resolve_config(
            {
                "github_username": github_username,
                "repo_name": repo_name,
                "local_path": local_path,
                "hostname": hostname,
                "secrets_manager": secrets_choice,
                "tools": selected_tools,
                "setup_search": bool(setup_search),
                "install_stop_hook": bool(install_hook),
            },
            discovered,
            plat,
        )
    except ValueError as exc:
        console.print(f"[red]Invalid configuration:[/red] {exc}")
        sys.exit(1)

    total = len(SETUP_STEPS)
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"[1/{total}] {SETUP_STEPS[0]}", total=total)

        def report(i, label):
            progress.update(task, advance=1, description=f"[{i}/{total}] {label} [green]\u2713[/green]")

        notes = apply_setup(cfg, report)

    for note in notes:
        console.print(f"  [dim]{note}[/dim]")

    # Phase 10: Next Steps
    console.print("\n─── [bold]Setup Complete[/bold] ─────────────────────────────────────────────\n")
    console.print("✓ AIKB is configured and committed locally.\n")

    next_steps = """[bold cyan]Next: push to GitHub[/bold cyan]
    git push origin main

[bold cyan]Then fill in two files (agents ask questions until these exist):[/bold cyan]
    • personal/profile.md       — your background, skills, stack
    • personal/dev-environment/{hostname}.md  — tools on this machine

Both files have been created with commented placeholders.
Open them and fill in the sections marked with [TODO].
"""
    console.print(next_steps.format(hostname=hostname))

    # Web tools manual steps
    selected_web = [t for t in selected_tools if t in web_tools]
    if selected_web:
        console.print("\n─── [bold]Manual Steps for Web AI Tools[/bold] ─────────────────────────────\n")
        if "ChatGPT (web)" in selected_web:
            console.print("[bold]ChatGPT:[/bold]\n    Settings → Customize ChatGPT → Custom Instructions\n    Paste the contents of: [dim]_agents/chatgpt.md[/dim]\n")
        if "Gemini (web)" in selected_web:
            console.print("[bold]Gemini (web):[/bold]\n    Settings → Custom Instructions\n    Paste the contents of: [dim]_agents/gemini.md[/dim]\n")
        if "Grok" in selected_web:
            console.print("[bold]Grok:[/bold]\n    Customize Grok → System Prompt\n    Paste the contents of: [dim]_agents/grok.md[/dim]\n")
        console.print("[dim]You'll also need to paste _index.md at the start of each session\n(web tools can't read your repo directly).[/dim]\n")

    if "Cursor" in selected_tools:
        console.print("\n─── [bold]Manual Step for Cursor[/bold] ─────────────────────────────────────\n")
        console.print("Cursor Settings → Cursor Settings → Rules → User Rules\nPaste the contents of: [dim]_agents/cursor.md[/dim]\n")

    if "Codex CLI" in selected_tools:
        console.print("\n─── [bold]Codex CLI[/bold] ──────────────────────────────────────────────────\n")
        console.print("Sync AGENTS.md to all your project repos:\n    cd {local_path}\n    ./sync-agents.sh --dry-run   # preview\n    ./sync-agents.sh             # apply\n".format(local_path=local_path))

    console.print("\n─── [bold]Learn More[/bold] ─────────────────────────────────────────────────\n")
    if questionary.confirm("Run a 4-minute orientation? (explains the concepts)", default=False).ask():
        subprocess.run(["bash", "_tools/tutorial.sh"])

    if questionary.confirm("Run the feature tour? (live walkthrough of commands)", default=False).ask():
        subprocess.run(["bash", "_tools/feature-tour.sh"])

    console.print("\n[bold green]Happy building.[/bold green]")

if __name__ == "__main__":
    if NON_INTERACTIVE:
        run_non_interactive()
    else:
        main()
