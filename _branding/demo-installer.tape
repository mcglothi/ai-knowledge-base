Output _branding/demo-installer.gif

# ⚠ RE-RENDERING WARNING
# This tape runs ./install.sh for real — it will write to ~/.claude/CLAUDE.md,
# ~/.gemini/GEMINI.md, and create a git commit in the current directory.
# Always re-render from a throwaway clone, never from your live AIKB:
#
#   git clone https://github.com/YOUR_USERNAME/AIKB.git /tmp/aikb-demo
#   cd /tmp/aikb-demo
#   vhs _branding/demo-installer.tape

Set BackgroundColor "#0C1522"
Set ForegroundColor "#F6F1E9"
Set FontFamily "JetBrains Mono"
Set FontSize 14
Set Width 1000
Set Height 600
Set Padding 20
Set TypingSpeed 40ms

# Start in the repo root
Type "cd ~/code/AIKB && ./install.sh"
Sleep 500ms
Enter
Sleep 3s

# Welcome screen — "Ready to begin?"
# questionary confirm prompt — press Enter to accept default (Y)
Enter
Sleep 1s

# Platform check passes, prereqs table renders
Sleep 2s

# Persona selection — checkbox prompt
# Claude Code is first item, already focused — press Space to select it
Space
Sleep 300ms
# Arrow down to Gemini CLI
Down
Sleep 200ms
Space
Sleep 300ms
# Press Enter to confirm
Enter
Sleep 1s

# Web tools note appears and fades — brief pause
Sleep 1s

# Configuration section
# GitHub username — type "jane"
Type "jane"
Enter
Sleep 500ms

# Repo name — press Enter (default: AIKB)
Enter
Sleep 500ms

# Local path — press Enter (default: current dir)
Enter
Sleep 500ms

# Hostname — press Enter (default: dev-box)
Enter
Sleep 1s

# Secrets manager — arrow down to "Skip for now" (it's the last item, default)
Enter
Sleep 1s

# Review summary panel renders
Sleep 2s

# "Proceed with setup?" — Enter to confirm
Enter
Sleep 1s

# Progress steps animate one by one
Sleep 5s

# Tool configuration — Claude Code and Gemini CLI
Sleep 2s

# Next steps panel
Sleep 3s

# "Run orientation?" — press N
Type "n"
Enter
Sleep 500ms

# "Run feature tour?" — press N
Type "n"
Enter
Sleep 1s

# "Happy building." — hold on final screen
Sleep 3s
