#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path
from collections import defaultdict

LOG = Path.home()/'.gemini'/'tmp'/'code'/'logs.json'

if not LOG.exists():
    print('GEMINI SCORE: FAIL')
    print(f'ERROR: missing {LOG}')
    sys.exit(2)

arr = json.loads(LOG.read_text())
if not isinstance(arr, list):
    print('GEMINI SCORE: FAIL')
    print('ERROR: logs.json is not a list')
    sys.exit(2)

sess = defaultdict(list)
for r in arr:
    sid = r.get('sessionId')
    if sid:
        sess[sid].append(r)

def latest_ts(recs):
    return max((x.get('timestamp','') for x in recs), default='')

items = sorted(sess.items(), key=lambda kv: latest_ts(kv[1]), reverse=True)
if not items:
    print('GEMINI SCORE: FAIL')
    print('ERROR: no sessions found')
    sys.exit(2)

# pick most recent session with at least 4 user prompts
target_sid, recs = items[0]
messages = [r.get('message','') for r in recs if isinstance(r.get('message'), str)]
joined = '\n'.join(messages).lower()

checks = {
    'im_prompt': any(k in joined for k in ['jot this down','leave yourself a note','note for next time']),
    'token_prompt': 'token-economy.md' in joined or 'compact/compress should trigger' in joined,
    'cross_agent_prompt': 'consensus items' in joined and 'next 3 actions' in joined,
    'closeout_prompt': any(k in joined for k in ["let's wrap up",'lets wrap up'])
}

score = sum(1 for v in checks.values() if v)

print(f'GEMINI SESSION: {target_sid}')
print(f'RECORDS: {len(recs)}')
print('CHECKS:')
for k,v in checks.items():
    print(f'- {k}: {"PASS" if v else "FAIL"}')

if score == 4:
    print('GEMINI SCORE: PASS (prompt-path coverage)')
    sys.exit(0)
elif score >= 3:
    print('GEMINI SCORE: PARTIAL (most prompts captured; verify response transcript separately)')
    sys.exit(0)
else:
    print('GEMINI SCORE: FAIL')
    sys.exit(1)
