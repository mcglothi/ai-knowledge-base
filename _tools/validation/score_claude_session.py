#!/usr/bin/env python3
from pathlib import Path
import argparse, json, re, sys

ap=argparse.ArgumentParser(description='Score a Claude session JSONL for v2 behavior signals')
ap.add_argument('--session-file', required=True)
args=ap.parse_args()

p=Path(args.session_file)
if not p.exists():
    print('ERROR: session file not found')
    sys.exit(2)

lines=p.read_text(errors='ignore').splitlines()
text='\n'.join(lines)

checks={
 'im_send_used': r'runtime_cli\.py im send|--mirror-sent',
 'token_playbook_loaded': r'docs/playbooks/token-economy\.md',
 'closeout_playbook_loaded': r'docs/playbooks/closeout\.md',
 'mindmeld_playbook_loaded': r'docs/playbooks/cross-agent-mind-meld\.md',
 'git_playbook_loaded': r'docs/playbooks/git-checkpointing\.md',
 'wrap_phrase_seen': r'lets wrap up|let\'s wrap up|lets shut down|let\'s shut down',
}

score=0
max_score=len(checks)
results={}
for k,pat in checks.items():
    ok=bool(re.search(pat,text,re.I))
    results[k]=ok
    score += 1 if ok else 0

status='PASS' if results['im_send_used'] and results['token_playbook_loaded'] and results['closeout_playbook_loaded'] else 'WARN'
print(f'SESSION_SCORE: {score}/{max_score}')
print(f'STATUS: {status}')
for k,v in results.items():
    print(f'- {k}: {"OK" if v else "MISSING"}')
