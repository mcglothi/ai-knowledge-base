#!/usr/bin/env python3
"""
Teams message ingest: LevelDB → distilled AIKB facts.
Heuristic-only: no LLM required.
"""

import ccl_chromium_reader.ccl_chromium_indexeddb as idb
import pathlib, json, re, sys
from datetime import datetime, timezone
from collections import defaultdict

AIKB_ROOT = pathlib.Path("/home/tmcglothin/code/AIKB")
LDB_PATH = pathlib.Path("/mnt/c/Temp/teams_leveldb")
OUT_FILE = AIKB_ROOT / "work/teams-intel-last30.md"
CONV_NAMES_CACHE = pathlib.Path("/tmp/teams_conv_names.json")

DAYS_BACK = 30

# ── noise filters ─────────────────────────────────────────────────────────────
NOISE_PATTERNS = [
    r'^[\U0001F000-\U0001FFFF\U00002600-\U000027FF\s\+\!\?\.]+$',  # pure emoji
    r'^\s*(ok|lol|haha|👍|👎|✅|❌|😂|🙂|thx|thanks!?|np|sure|got it|sounds good|will do)\s*$',
    r'^(be back|brb|afk|omw)\b',
    r'^\d{10,}\s+8:orgid:',  # meeting roster junk
    r'^8:orgid:[a-f0-9-]+\s+\w',  # user-list junk (from meeting records)
]
NOISE_RE = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS]

# ── signal classifiers ─────────────────────────────────────────────────────────
SIGNAL_RULES = {
    'incident': [
        r'\b(error|fail(ed|ure)?|down|outage|unreachable|crash(ed)?|issue|problem|alert|alarm|warning|critical|oom|OOM|hung|hangs?|panic|abort|timeout)\b',
        r'\b(not starting|not coming up|not running|service unavailable|connection refused)\b',
        r'\b(full|no space|disk|/boot|spool|journal)\b.{0,30}\b(full|0%|capacity)\b',
    ],
    'action': [
        # Require infra/project context word within 80 chars to avoid casual chat
        r"\b(I('ll| will)|going to|working on|will (check|look|fix|update|create|build|implement|deploy))\b.{0,80}\b(server|host|vm|playbook|ansible|script|cluster|node|service|ticket|patch|deploy|config|cert|dns|port|volume|disk|lun|job|alert|monitor|repo|pipeline)\b",
        r"\b(need(s)? to|plan(ning)? to)\b.{0,80}\b(server|host|vm|playbook|ansible|script|cluster|node|service|ticket|patch|deploy|config|cert|dns|port|volume|disk|lun|job|alert)\b",
        r"\b(TODO|action item|follow.?up|assigned to|owner:)\b",
        r"\b(please|can you|could you)\b.{0,40}\b(check|look|fix|update|verify|confirm|send|create)\b",
    ],
    'resolved': [
        r"\b(fixed|resolved|done|complete(d)?|deployed|updated|patched|working now|back up|came up|looks good|all clear)\b",
        r"\b(ticket (is |has been )?(closed|resolved)|case closed|root cause)\b",
    ],
    'decision': [
        r"\b(decided|agreed|going with|switching to|migrating to|approved|confirmed|will use|chose|chosen)\b",
        r"\b(roadmap|milestone|target date|scheduled for|planned for)\b",
    ],
    'knowledge': [
        r"\b(root cause|because|turns out|found (out|that)|the (issue|problem|fix) (is|was)|KB \d+|article|workaround)\b",
        r"\b(command|playbook|script|procedure|steps?|runbook|documentation)\b.{0,40}\b(is|are|was|should)\b",
    ],
}
SIGNAL_RE = {k: [re.compile(p, re.IGNORECASE) for p in patterns] for k, patterns in SIGNAL_RULES.items()}

# ── helper functions ───────────────────────────────────────────────────────────

def strip_html(text):
    if not text: return ''
    if isinstance(text, bytes): text = text.decode('utf-8', errors='replace')
    text = re.sub(r'<[^>]+>', ' ', str(text))
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def ms_to_dt(ms):
    try: return datetime.fromtimestamp(float(ms)/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
    except: return str(ms)

def is_noise(text):
    if len(text) < 15: return True
    for pat in NOISE_RE:
        if pat.match(text): return True
    return False

def classify(text):
    cats = []
    for cat, patterns in SIGNAL_RE.items():
        if any(p.search(text) for p in patterns):
            cats.append(cat)
    return cats or ['info']

def truncate(text, n=200):
    return text[:n] + ('…' if len(text) > n else '')


# ── load Teams data ────────────────────────────────────────────────────────────

def load_messages(cutoff_ms):
    wrapped = idb.WrappedIndexDB(LDB_PATH)

    SKIP_TYPES = {
        'Event/Call','ThreadActivity/AddMember','ThreadActivity/DeleteMember',
        'ThreadActivity/MemberJoined','Event/CallRecording','ThreadActivity/TopicUpdate',
        'ThreadActivity/MemberLeft','Event/CallStarted','Event/CallEnded',
    }

    messages = []
    seen_ids = set()

    for db_id_num in [9, 1012]:
        try:
            db = wrapped[db_id_num]
            for store_name in db.object_store_names:
                store = db.get_object_store_by_name(store_name)
                for rec in store.iterate_records():
                    try:
                        val = rec.value
                        if not isinstance(val, dict): continue
                        conv_id = val.get('conversationId', '')
                        for msg_key, msg in val.get('messageMap', {}).items():
                            if not isinstance(msg, dict): continue
                            ts = (msg.get('originalArrivalTime') or
                                  msg.get('clientArrivalTime') or
                                  val.get('latestDeliveryTime', 0))
                            if float(ts or 0) < cutoff_ms: continue
                            mtype = msg.get('messageType') or msg.get('messagetype') or ''
                            if mtype in SKIP_TYPES: continue
                            content = strip_html(msg.get('content', ''))
                            if is_noise(content): continue
                            # Skip pure numeric/ID junk
                            if re.match(r'^[\d\s:@orgid\-]+$', content): continue
                            msg_id = msg.get('id', '') or msg_key
                            if msg_id in seen_ids: continue
                            seen_ids.add(msg_id)
                            sender = (msg.get('imDisplayName') or
                                      msg.get('fromDisplayNameInToken') or
                                      (f"{msg.get('fromGivenNameInToken','')} "
                                       f"{msg.get('fromFamilyNameInToken','')}").strip() or
                                      str(msg.get('creator', 'Unknown')))
                            if isinstance(sender, bytes):
                                sender = sender.decode('utf-8', errors='replace')
                            messages.append({
                                'ts': ms_to_dt(ts),
                                'ts_raw': float(ts or 0),
                                'conv_id': conv_id,
                                'sender': str(sender).strip() or 'Unknown',
                                'content': content,
                                'cats': classify(content),
                            })
                    except: pass
        except: pass

    return sorted(messages, key=lambda x: x['ts_raw'])


def load_conv_names():
    try:
        wrapped = idb.WrappedIndexDB(LDB_PATH)
        names = {}
        for db_id_num in [8, 7]:
            try:
                db = wrapped[db_id_num]
                for store_name in db.object_store_names:
                    store = db.get_object_store_by_name(store_name)
                    for rec in store.iterate_records():
                        try:
                            val = rec.value
                            if not isinstance(val, dict): continue
                            cid = (val.get('id') or val.get('threadId') or
                                   val.get('conversationId', ''))
                            name = (val.get('displayName') or
                                    val.get('threadProperties', {}).get('topic') or
                                    val.get('name') or '')
                            if isinstance(name, bytes):
                                name = name.decode('utf-8', errors='replace')
                            if cid and name:
                                names[str(cid)] = str(name)
                        except: pass
            except: pass
        with open(CONV_NAMES_CACHE, 'w') as f:
            json.dump(names, f)
        return names
    except:
        if CONV_NAMES_CACHE.exists():
            with open(CONV_NAMES_CACHE) as f:
                return json.load(f)
        return {}


# ── report generation ──────────────────────────────────────────────────────────

INFRA_CHANNEL_KEYS = [
    'unix','nutanix','toc','server','storage','network','splunk','vmware',
    'ansible','arista','patch','cluster','oracle','dba','cisco','infra',
    'linux','windows','deploy','incident','monitoring','alert','esg',
]

AI_CHANNEL_KEYS = ['ai nerd','copilot','claude','llm','ai ','chatgpt']

def channel_is_relevant(name):
    n = name.lower()
    return any(k in n for k in INFRA_CHANNEL_KEYS + AI_CHANNEL_KEYS)


def render_channel(display_name, msgs):
    """Render a distilled summary section for one channel."""
    lines = []
    msgs_s = sorted(msgs, key=lambda x: x['ts_raw'])
    date_range = f"{msgs_s[0]['ts'][:10]} → {msgs_s[-1]['ts'][:10]}"
    signal_msgs = [m for m in msgs if 'info' not in m['cats'] or any(
        c in m['cats'] for c in ('incident','action','resolved','decision','knowledge'))]

    lines.append(f"### {display_name}")
    lines.append(f"**{len(msgs)} messages** · {date_range} · "
                 f"{len(signal_msgs)} signal msgs\n")

    # Group into categories
    buckets = defaultdict(list)
    for m in msgs_s:
        for cat in m['cats']:
            buckets[cat].append(m)

    CAT_LABELS = {
        'incident':  '🔴 Incidents / Issues',
        'resolved':  '✅ Resolved / Complete',
        'action':    '📋 Action Items',
        'decision':  '🏛 Decisions',
        'knowledge': '💡 Knowledge / Findings',
        'info':      '💬 Notable Exchanges',
    }

    order = ['incident','resolved','action','decision','knowledge','info']
    any_signal = False

    for cat in order:
        items = buckets.get(cat, [])
        if not items: continue
        # Limit info to last 10, others to last 20
        limit = 10 if cat == 'info' else 20
        items = items[-limit:]
        lines.append(f"**{CAT_LABELS[cat]}**")
        for m in items:
            sender = m['sender'][:30]
            content = truncate(m['content'], 220)
            lines.append(f"- `{m['ts']}` **{sender}:** {content}")
        lines.append("")
        any_signal = True

    if not any_signal:
        # Show last 5 as info fallback
        lines.append("**💬 Recent**")
        for m in msgs_s[-5:]:
            lines.append(f"- `{m['ts']}` **{m['sender'][:30]}:** {truncate(m['content'], 180)}")
        lines.append("")

    return lines


def generate_report(messages, conv_names):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    cutoff = datetime.fromtimestamp(
        (min(m['ts_raw'] for m in messages)/1000 if messages else 0),
        tz=timezone.utc).strftime('%Y-%m-%d')

    lines = [
        "# Teams Intelligence — Last 30 Days",
        f"**Generated:** {now}  **Period:** {cutoff} → today  "
        f"**Source:** Local Teams cache",
        "",
        f"**Stats:** {len(messages)} signal messages extracted from Teams local cache",
        "",
    ]

    convs = defaultdict(list)
    for m in messages:
        convs[m['conv_id']].append(m)

    # ── Channel volume table ──────────────────────────────────────────────────
    lines.append("## Channel Volume (Top 20)\n")
    lines.append("| # | Channel | Msgs | Signal | Last Active |")
    lines.append("|---|---------|------|--------|-------------|")
    row = 0
    for cid, msgs in sorted(convs.items(), key=lambda x: -len(x[1])):
        if row >= 20: break
        signal = len([m for m in msgs if 'info' not in m['cats']])
        if signal == 0: continue  # skip zero-signal channels
        cname = conv_names.get(cid, '')
        if not cname or cname.startswith('19:'): cname = '(Direct/Meeting)'
        last = sorted(msgs, key=lambda x: x['ts_raw'])[-1]['ts'][:10]
        row += 1
        lines.append(f"| {row} | {cname} | {len(msgs)} | {signal} | {last} |")
    lines.append("")

    # ── Infrastructure channels ───────────────────────────────────────────────
    lines.append("## Infrastructure Channels\n")
    for cid, msgs in sorted(convs.items(), key=lambda x: -len(x[1])):
        cname = conv_names.get(cid, '')
        if not channel_is_relevant(cname): continue
        if len(msgs) < 5: continue
        lines += render_channel(cname, msgs)

    # ── Today ─────────────────────────────────────────────────────────────────
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    today_msgs = [m for m in messages if m['ts'].startswith(today_str)]
    if today_msgs:
        lines.append(f"## Today ({today_str})\n")
        today_convs = defaultdict(list)
        for m in today_msgs:
            today_convs[m['conv_id']].append(m)
        for cid, msgs in sorted(today_convs.items(), key=lambda x: -len(x[1])):
            cname = conv_names.get(cid, '')
            if not cname or cname.startswith('19:'): cname = '(Direct/Meeting)'
            lines.append(f"### {cname} ({len(msgs)} msgs)")
            for m in sorted(msgs, key=lambda x: x['ts_raw']):
                cats = ','.join(c for c in m['cats'] if c != 'info')
                tag = f" `[{cats}]`" if cats else ''
                lines.append(
                    f"- `{m['ts']}` **{m['sender'][:25]}:**{tag} "
                    f"{truncate(m['content'], 180)}")
            lines.append("")

    return '\n'.join(lines)


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    if not LDB_PATH.exists():
        print("Teams LDB not found — skipping Teams ingest")
        sys.exit(0)

    cutoff_ms = (datetime.now(timezone.utc).timestamp() - DAYS_BACK * 86400) * 1000

    print(f"Loading Teams messages (last {DAYS_BACK} days)...")
    messages = load_messages(cutoff_ms)
    print(f"  {len(messages)} signal messages loaded")

    print("Loading conversation names...")
    conv_names = load_conv_names()
    print(f"  {len(conv_names)} conversations named")

    print("Generating report...")
    report = generate_report(messages, conv_names)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(report)
    print(f"  Written: {OUT_FILE} ({len(report)} chars, {len(report.splitlines())} lines)")


if __name__ == '__main__':
    main()
