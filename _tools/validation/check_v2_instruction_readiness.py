#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path('.').resolve()

required_files = {
    'core': ROOT / '_agents/shared/core-min.md',
    'session': ROOT / '_agents/shared/session-min.md',
    'overlay_claude': ROOT / '_agents/v2/claude-code.overlay.md',
    'overlay_codex': ROOT / '_agents/v2/codex.overlay.md',
    'overlay_gemini': ROOT / '_agents/v2/gemini-cli.overlay.md',
    'pb_im': ROOT / 'docs/playbooks/im.md',
    'pb_token': ROOT / 'docs/playbooks/token-economy.md',
    'pb_closeout': ROOT / 'docs/playbooks/closeout.md',
    'pb_git': ROOT / 'docs/playbooks/git-checkpointing.md',
    'pb_mindmeld': ROOT / 'docs/playbooks/cross-agent-mind-meld.md',
    'dispatch': ROOT / '_agents/v2/dispatch.yaml',
    'handoff_schema': ROOT / 'docs/schemas/handoff-contract-v1.md',
}

line_limits = {
    'core': 15,
    'overlay_claude': 25,
    'overlay_codex': 25,
    'overlay_gemini': 25,
}

required_core_phrases = [
    '[MANDATE] Be precise; do not invent facts or tool results.',
    '[MANDATE] Do not expose secrets/credentials in outputs or commits.',
    'Compact triggers:',
    'Use dispatch table to load only required L2 playbooks.',
    'On wrap-up phrase: run closeout checklist and report status.',
]

required_overlay_phrases = [
    'AIKB root: ${AIKB_ROOT}',
    'runtime_cli: python3 ${AIKB_ROOT}/_tools/memory-pipeline/runtime_cli.py',
    'Preserve IM fuzzy trigger phrases',
    # Vendor-neutral: the concrete manager is filled in from
    # .aikb-config.d/SECRETS_MANAGER at install/sync time.
    'Credential fallback order:',
    'Credential retrieval:',
    'Credential safety: never echo secret values or pass them as CLI arguments.',
    'Startup health check: verify L2 playbook paths exist and are readable.',
    'Core version expected: v2.0',
]

required_overlay_compact = {
    'overlay_claude': 'Compact keyword: /compact',
    'overlay_codex': 'Compact keyword: /compact',
    'overlay_gemini': 'Compact keyword: /compress',
}


def count_rule_lines(path: Path) -> int:
    lines = path.read_text().splitlines()
    return sum(1 for l in lines if l.strip().startswith('- '))


def check_file_exists_readable(path: Path) -> bool:
    return path.exists() and path.is_file() and path.stat().st_size >= 0


def contains_all(text: str, phrases):
    return [p for p in phrases if p not in text]


errors = []
warnings = []

# 1) Presence/readability
for key, fp in required_files.items():
    if not check_file_exists_readable(fp):
        errors.append(f'MISSING: {key} -> {fp}')

if errors:
    print('V2 READINESS: FAIL')
    for e in errors:
        print(f'ERROR: {e}')
    sys.exit(1)

# 2) Line budgets
for key, limit in line_limits.items():
    fp = required_files[key]
    n = count_rule_lines(fp)
    if n > limit:
        errors.append(f'LINE_BUDGET_EXCEEDED: {key} has {n} bullet lines (limit {limit})')
    else:
        print(f'OK: {key} line budget {n}/{limit}')

# 3) Core content
core_text = required_files['core'].read_text()
for m in contains_all(core_text, required_core_phrases):
    errors.append(f'CORE_MISSING_PHRASE: {m}')

# 4) Overlay content
for key in ['overlay_claude', 'overlay_codex', 'overlay_gemini']:
    txt = required_files[key].read_text()
    for m in contains_all(txt, required_overlay_phrases):
        errors.append(f'{key}_MISSING_PHRASE: {m}')
    expected_compact = required_overlay_compact[key]
    if expected_compact not in txt:
        errors.append(f'{key}_MISSING_COMPACT_KEYWORD: {expected_compact}')

# 5) Session min sections
session_text = required_files['session'].read_text()
for phrase in ['Startup Health Check', 'During Session', 'Closeout']:
    if phrase not in session_text:
        errors.append(f'SESSION_MIN_MISSING_SECTION: {phrase}')

# 6) Playbook sanity
for key in ['pb_im', 'pb_token', 'pb_closeout', 'pb_git', 'pb_mindmeld']:
    txt = required_files[key].read_text()
    if not txt.lstrip().startswith('# '):
        errors.append(f'{key}_INVALID_HEADING')
    if 'When to Load' not in txt:
        warnings.append(f'{key}_MISSING_WHEN_TO_LOAD')

# 7) Dispatch registry sanity
dispatch_text = required_files['dispatch'].read_text()
for phrase in ['rules:', 'id: im', 'id: token-economy', 'id: closeout', 'id: git-checkpointing', 'id: cross-agent-mind-meld']:
    if phrase not in dispatch_text:
        errors.append(f'DISPATCH_MISSING: {phrase}')

# 8) Handoff schema sanity
handoff_text = required_files['handoff_schema'].read_text()
for phrase in ['Handoff Contract v1', 'Required Fields', 'next_actions', 'rollback']:
    if phrase not in handoff_text:
        errors.append(f'HANDOFF_SCHEMA_MISSING: {phrase}')

if errors:
    print('V2 READINESS: FAIL')
    for e in errors:
        print(f'ERROR: {e}')
    for w in warnings:
        print(f'WARN: {w}')
    sys.exit(2)

print('V2 READINESS: PASS')
for w in warnings:
    print(f'WARN: {w}')
