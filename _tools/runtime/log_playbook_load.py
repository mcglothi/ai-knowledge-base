#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse, json

p = argparse.ArgumentParser(description='Log L2 playbook load events for observability')
p.add_argument('--agent', required=True)
p.add_argument('--playbook', required=True)
p.add_argument('--trigger', required=True)
p.add_argument('--session-id', default='')
p.add_argument('--note', default='')
args = p.parse_args()

root = Path(__file__).resolve().parents[2]
outdir = root / '_runtime' / 'events'
outdir.mkdir(parents=True, exist_ok=True)
fn = outdir / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.ndjson"

record = {
    'ts_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'type': 'playbook_load',
    'agent': args.agent,
    'playbook': args.playbook,
    'trigger': args.trigger,
    'session_id': args.session_id,
    'note': args.note,
}
with fn.open('a', encoding='utf-8') as f:
    f.write(json.dumps(record) + '\n')
print(f'logged: {fn}')
