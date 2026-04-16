#!/usr/bin/env python3
# =============================================================================
# AIKB TUI Installer
# Personalizes agent instruction files with your GitHub username, repo name,
# and local path after you've cloned the template.
#
# Usage: ./install.sh (which calls this script)
# =============================================================================

import os
import sys
import subprocess
import platform
import socket
import json
from pathlib import Path
from datetime import datetime, timezone

# ── Dependency Bootstrap (Phase 0) ───────────────────────────────────────────
REQUIRED = {"rich": "rich", "questionary": "questionary"}

missing = []
for pkg, import_name in REQUIRED.items():
    try:
        __import__(import_name)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"\nAIKB needs {', '.join(missing)} to run the installer.")
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

# Now we can import rich and questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary

console = Console()

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

# ── Main Application ─────────────────────────────────────────────────────────
def main():
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
        choices=[
            "Claude Code",
            "Gemini CLI",
            "OpenCode",
            "Cursor",
            "ChatGPT (web)",
            "Gemini (web)",
            "Grok",
            "Codex CLI",
        ],
        validate=lambda x: True if len(x) > 0 else "Select at least one tool"
    ).ask()

    web_tools = {"ChatGPT (web)", "Gemini (web)", "Grok"}
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
        choices=[
            "1Password",
            "Bitwarden / Vaultwarden",
            "macOS Keychain",
            "Environment variables (.env / shell profile)",
            "Skip for now"
        ],
        default="Skip for now"
    ).ask()

    secrets_map = {
        "1Password": ("1Password", 'op read "op://Private/ITEM_NAME/credential"'),
        "Bitwarden / Vaultwarden": ("Bitwarden", 'bw get password "PAT/<Service>/<Name>" --session "$BW_SESSION"'),
        "macOS Keychain": ("macOS Keychain", 'security find-generic-password -w -a "$USER" -s "ITEM_NAME"'),
        "Environment variables (.env / shell profile)": ("Environment variables", 'echo "$MY_SECRET_VAR"'),
        "Skip for now": ("your secrets manager", "[see your secrets manager documentation]")
    }

    secrets_manager, secrets_retrieve = secrets_map[secrets_choice]

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

    # Phase 8: Execution with Progress
    steps = [
        "Substituting placeholders in agent files",
        "Updating _index.md",
        "Scaffolding personal profile files",
        "Saving configuration to .aikb-config.d/",
        "Adding upstream remote",
        "Creating initial commit",
        "Configuring AI tools"
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Step 1: Substitutions
        task1 = progress.add_task(f"[1/{len(steps)}] {steps[0]}", total=1)
        agents_dir = Path("_agents")

        subs = {
            "{{GITHUB_USERNAME}}": github_username,
            "{{REPO_NAME}}": repo_name,
            "{{REPO_URL}}": repo_url,
            "{{REPO_SSH}}": repo_ssh,
            "{{LOCAL_PATH}}": local_path,
            "{{CODE_ROOT}}": code_root,
            "{{PRIMARY_HOSTNAME}}": hostname,
            "{{OS}}": os_friendly,
            "{{SECRETS_MANAGER}}": secrets_manager,
            "{{SECRETS_RETRIEVE}}": secrets_retrieve,
        }

        def apply_subs(src, dest):
            content = src.read_text()
            for k, v in subs.items():
                content = content.replace(k, v)
            dest.write_text(content)

        for tmpl in agents_dir.glob("*.md"):
            apply_subs(tmpl, tmpl)

        agents_md = Path("AGENTS.md")
        if agents_md.exists():
            apply_subs(agents_md, agents_md)

        progress.update(task1, advance=1, description=f"[1/{len(steps)}] {steps[0]} [green]✓[/green]")

        # Step 2: _index.md
        task2 = progress.add_task(f"[2/{len(steps)}] {steps[1]}", total=1)
        index_md = Path("_index.md")
        if index_md.exists():
            content = index_md.read_text()
            content = content.replace("{{GITHUB_USERNAME}}", github_username).replace("{{REPO_NAME}}", repo_name)
            index_md.write_text(content)
        progress.update(task2, advance=1, description=f"[2/{len(steps)}] {steps[1]} [green]✓[/green]")

        # Step 3: Scaffolding
        task3 = progress.add_task(f"[3/{len(steps)}] {steps[2]}", total=1)
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
                content = example_dev.read_text().replace("my-macbook", hostname)
                readme_path.write_text(content)

        machine_profile = dev_env_dir / f"{hostname}.md"
        if not machine_profile.exists():
            template_machine = Path("_templates/machine-profile.md")
            if template_machine.exists():
                content = template_machine.read_text().replace("[hostname]", hostname)
                machine_profile.write_text(content)
        progress.update(task3, advance=1, description=f"[3/{len(steps)}] {steps[2]} [green]✓[/green]")

        # Step 4: Saving config
        task4 = progress.add_task(f"[4/{len(steps)}] {steps[3]}", total=1)
        config_dir = Path(".aikb-config.d")
        config_dir.mkdir(exist_ok=True)
        (config_dir / "GITHUB_USERNAME").write_text(github_username)
        (config_dir / "REPO_NAME").write_text(repo_name)
        (config_dir / "REPO_URL").write_text(repo_url)
        (config_dir / "REPO_SSH").write_text(repo_ssh)
        (config_dir / "LOCAL_PATH").write_text(local_path)
        (config_dir / "CODE_ROOT").write_text(code_root)
        (config_dir / "PRIMARY_HOSTNAME").write_text(hostname)
        (config_dir / "OS").write_text(os_friendly)
        (config_dir / "SECRETS_MANAGER").write_text(secrets_manager)
        (config_dir / "SECRETS_RETRIEVE").write_text(secrets_retrieve)
        progress.update(task4, advance=1, description=f"[4/{len(steps)}] {steps[3]} [green]✓[/green]")

        # Step 5: Upstream remote
        task5 = progress.add_task(f"[5/{len(steps)}] {steps[4]}", total=1)
        subprocess.run(["git", "remote", "add", "upstream", "https://github.com/mcglothi/ai-knowledge-base.git"], stderr=subprocess.DEVNULL)
        
        # Initialize template sync state
        try:
            subprocess.run(["git", "fetch", "upstream", "--quiet"], stderr=subprocess.DEVNULL)
            upstream_sha = subprocess.check_output(["git", "rev-parse", "upstream/main"], stderr=subprocess.DEVNULL).decode().strip()
            if upstream_sha:
                state_file = config_dir / "template-sync-state.json"
                stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                payload = {
                    "last_checked_utc": stamp,
                    "last_seen_upstream_sha": upstream_sha,
                    "last_applied_upstream_sha": upstream_sha,
                    "check_interval_days": 7,
                }
                state_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        except:
            pass
            
        progress.update(task5, advance=1, description=f"[5/{len(steps)}] {steps[4]} [green]✓[/green]")

        # Step 6: Initial commit
        task6 = progress.add_task(f"[6/{len(steps)}] {steps[5]}", total=1)
        subprocess.run(["git", "add", "-A"])
        subprocess.run(["git", "commit", "-m", f"chore: personalize AIKB for {github_username}", "--allow-empty"], stdout=subprocess.DEVNULL)
        progress.update(task6, advance=1, description=f"[6/{len(steps)}] {steps[5]} [green]✓[/green]")

        # Step 7: Configuring tools
        task7 = progress.add_task(f"[7/{len(steps)}] {steps[6]}", total=1)

        # Claude Code
        if "Claude Code" in selected_tools:
            claude_dir = Path.home() / ".claude"
            claude_dir.mkdir(exist_ok=True)
            claude_dest = claude_dir / "CLAUDE.md"
            claude_src = Path("_agents/claude-code.md")
            if claude_src.exists():
                claude_dest.write_text(claude_src.read_text())

        # Gemini CLI
        if "Gemini CLI" in selected_tools:
            gemini_dir = Path.home() / ".gemini"
            gemini_dir.mkdir(exist_ok=True)
            gemini_dest = gemini_dir / "GEMINI.md"
            gemini_src = Path("_agents/gemini-cli.md")
            if not gemini_src.exists(): # fallback for naming variations
                 gemini_src = Path("_agents/gemini.md")
            if gemini_src.exists():
                gemini_dest.write_text(gemini_src.read_text())

        # OpenCode
        if "OpenCode" in selected_tools:
            opencode_config = Path.home() / ".config/opencode/opencode.json"
            opencode_src = Path(local_path) / "_agents/opencode.md"
            if not opencode_config.parent.exists():
                opencode_config.parent.mkdir(parents=True, exist_ok=True)

            config_data = {}
            if opencode_config.exists():
                try:
                    config_data = json.loads(opencode_config.read_text())
                except:
                    pass

            instructions = config_data.get("instructions", [])
            if str(opencode_src) not in instructions:
                instructions.append(str(opencode_src))
                config_data["instructions"] = instructions
                opencode_config.write_text(json.dumps(config_data, indent=2))

        progress.update(task7, advance=1, description=f"[7/{len(steps)}] {steps[6]} [green]✓[/green]")

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
    main()
