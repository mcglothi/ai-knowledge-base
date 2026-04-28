#!/usr/bin/env python3
"""
Outlook email ingest: JSON export → distilled AIKB facts.
Heuristic-only: no LLM required.
"""

import json, re, sys, pathlib
from datetime import datetime, timezone
from collections import defaultdict

AIKB_ROOT = pathlib.Path("/home/tmcglothin/code/AIKB")
OUT_FILE   = AIKB_ROOT / "work/infra-intel-last30.md"
JSON_FILE  = pathlib.Path("/mnt/c/Temp/aikb_last30.json")

DAYS_BACK = 30

# ── noise filters ─────────────────────────────────────────────────────────────

NOISE_SUBJECTS = re.compile(
    r'(meeting invitation|accepted:|declined:|tentative:|calendar:|'
    r'out of office|automatic reply|unsubscribe|newsletter|noreply|'
    r'daily portland|weekly.*digest|your daily digest|workday inbox|'
    r'sea dogs|mother.?s day|deals on|subscribe to more|hsa work|'
    r'breaking news|breaking stories|discount programs|diy delight|'
    r'meaningful gifts|learn how to|register now:|simplify the way|'
    r'synchronization log|daily digest|shape the future of|'
    r'celebrate her|happening today.*coffee|one last reminder|'
    r'last chance to join|keynote.*redesigning|redesigning.*workforce)',
    re.IGNORECASE
)

NOISE_SENDERS = re.compile(
    r'(noreply|no-reply|donotreply|notifications?@|alerts?@|mailer-daemon|'
    r'discount.?programs|fidelity|myworkday\.com|beyondtrust|'
    r'cyberheistnews|knowbe4|appviewx\.com|bmc\.com|'
    r'daily.?portland|is.?news@|good shepherd|expedient|'
    r'cisco product|atlassian$)',
    re.IGNORECASE
)

# External vendor/marketing domains — block regardless of subject
NOISE_DOMAINS = re.compile(
    r'@(fidelity\.com|myworkday\.com|rubrik\.com|appviewx\.com|'
    r'path\.cisco\.com|cisco\.com|knowbe4\.com|cyberheistnews\.com|'
    r'bmc\.com|beyondtrust\.com|atlassian\.com|expedient\.com|'
    r'goodshepherdfoodbank\.org)',
    re.IGNORECASE
)

# ── signal classifiers ─────────────────────────────────────────────────────────

SIGNAL_RULES = {
    'incident': [
        r'\b(error|fail(ed|ure)?|down|outage|unreachable|crash(ed)?|issue|problem|alert|alarm|'
        r'warning|critical|oom|hung|panic|abort|timeout|unavailable|degraded|slow|latency)\b',
        r'\b(full|no space|disk|/boot|spool|journal)\b.{0,30}\b(full|0%|capacity|threshold)\b',
        r'\b(incident|INC|JSM|ticket|case|opened|escalat)\b',
    ],
    'action': [
        r"\b(action( item)?|TODO|will (fix|check|look|update|create|add|build|implement|deploy|patch|open|send))\b",
        r"\b(need(s)? to|should be|must be|please (check|fix|update|verify|confirm|review))\b",
        r"\b(assigned to|owner:|follow.?up|scheduled for|planned)\b",
    ],
    'resolved': [
        r"\b(fixed|resolved|done|complete(d)?|deployed|updated|patched|working|restored|back up|came up|looks good|all clear|closed|no longer)\b",
        r"\b(root cause|post.?mortem|post mortem|RCA)\b",
    ],
    'change': [
        r'\b(change|CHG|deploy(ment|ed)?|release|upgrade|migration|cutover|maintenance|'
        r'scheduled|window|planned)\b',
    ],
    'aap_job': [
        r'\b(AAP|Ansible|playbook|job (failed|succeeded|complete|error|running)|'
        r'execution environment|inventory)\b',
    ],
}
SIGNAL_RE = {k: [re.compile(p, re.IGNORECASE) for p in patterns]
             for k, patterns in SIGNAL_RULES.items()}

# ── infrastructure keyword groups ─────────────────────────────────────────────

INFRA_GROUPS = {
    'Nutanix': r'\b(nutanix|ahv|prism|ncc|cvm|acropolis|ntx-|aos|aos|lcm)\b',
    'Oracle / DBA': r'\b(oracle|asm|crsctl|afdload|rdbms|rac|oratab|ora\d+|lloracp|DBA)\b',
    'Patching': r'\b(patch(ing)?|/boot|kernel|yum|dnf|rpm|reboot|maintenance)\b',
    'Splunk': r'\b(splunk|indexer|forwarder|search head|hec)\b',
    'AAP / Ansible': r'\b(aap|ansible|playbook|tower|execution environment)\b',
    'Nutanix Storage / SAN': r'\b(ibm|flash(system)?|san|brocade|zoning|lun|wwn)\b',
    'Network': r'\b(arista|cisco|vlan|bgp|ospf|firewall|palo alto|f5|load.?balanc)\b',
    'JSM / ServiceNow': r'\b(jsm|jira|servicenow|snow|ITS-\d+|incident|ticket)\b',
    'GitHub / Copilot': r'\b(github|copilot|git|repo|pull.?request|workflow|actions)\b',
    'Windows / AVD': r'\b(windows|active.?directory|azure|avd|nerdio|intune|AAD)\b',
}
INFRA_RE = {k: re.compile(v, re.IGNORECASE) for k, v in INFRA_GROUPS.items()}


CAT_PRIORITY = ['incident', 'resolved', 'change', 'aap_job', 'action', 'info']

def classify(text):
    cats = []
    for cat, patterns in SIGNAL_RE.items():
        if any(p.search(text) for p in patterns):
            cats.append(cat)
    return cats or ['info']

def primary_cat(cats):
    for c in CAT_PRIORITY:
        if c in cats:
            return c
    return 'info'


def infra_group(subj, body):
    combined = (subj or '') + ' ' + (body or '')[:500]
    groups = []
    for grp, pat in INFRA_RE.items():
        if pat.search(combined):
            groups.append(grp)
    return groups or ['General']


def truncate(text, n=220):
    return text[:n] + ('…' if len(text) > n else '')


def clean_body(body):
    if not body: return ''
    # Strip reply chains (common patterns)
    body = re.sub(r'\n+From:.*?Subject:.*?\n', '\n', body, flags=re.DOTALL)
    body = re.sub(r'\nOn .{10,80} wrote:\n', '\n', body)
    body = re.sub(r'-{3,}.*', '', body, flags=re.DOTALL)  # strip ---Original Message---
    body = re.sub(r'\s+', ' ', body)
    return body.strip()[:600]


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    if not JSON_FILE.exists():
        print(f"Outlook JSON not found at {JSON_FILE} — skipping")
        sys.exit(0)

    with open(JSON_FILE, encoding='utf-8-sig') as f:
        emails = json.load(f)

    print(f"Loaded {len(emails)} emails from Outlook export")

    # Filter noise
    signal_emails = []
    for e in emails:
        subj = e.get('Subject', '')
        sender_addr = e.get('SenderEmailAddress', '')
        sender_name = e.get('SenderName', '') or sender_addr
        if NOISE_SUBJECTS.search(subj): continue
        if NOISE_SENDERS.search(sender_addr) or NOISE_SENDERS.search(sender_name): continue
        if NOISE_DOMAINS.search(sender_addr): continue
        body = clean_body(e.get('Body', ''))
        cats = classify(subj + ' ' + body)
        groups = infra_group(subj, body)
        signal_emails.append({
            'date': e.get('ReceivedTime', '')[:16],
            'from': sender_name[:40],
            'subject': subj[:120],
            'body_snippet': body[:300],
            'cats': cats,
            'groups': groups,
        })

    ratio = len(signal_emails) / len(emails) if emails else 0
    print(f"  {len(signal_emails)} signal emails after noise filter ({ratio:.0%} pass-through)")
    if ratio > 0.5:
        print(f"  WARNING: pass-through rate {ratio:.0%} — noise filter may be too permissive")

    # Group by infra category
    by_group = defaultdict(list)
    for e in signal_emails:
        for grp in e['groups']:
            by_group[grp].append(e)

    # Generate report
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        "# Infra Intelligence — Email Last 30 Days",
        f"**Generated:** {now}  **Source:** Outlook (local COM scrape)",
        "",
        f"**Stats:** {len(emails)} raw emails → {len(signal_emails)} signal emails",
        "",
    ]

    CAT_LABELS = {
        'incident':  '🔴 Incidents / Issues',
        'resolved':  '✅ Resolved',
        'action':    '📋 Action Items',
        'change':    '🔧 Changes / Deployments',
        'aap_job':   '⚙️ AAP Job Activity',
        'info':      '💬 Notable',
    }

    for grp in sorted(by_group.keys()):
        emails = sorted(by_group[grp], key=lambda x: x['date'])[-40:]  # last 40 per group
        if not emails: continue

        lines.append(f"## {grp} ({len(emails)} emails)\n")

        # Sub-group by primary category only (prevents duplicate entries)
        buckets = defaultdict(list)
        for e in emails:
            buckets[primary_cat(e['cats'])].append(e)

        for cat in ['incident','resolved','action','change','aap_job','info']:
            items = buckets.get(cat, [])
            if not items: continue
            lines.append(f"**{CAT_LABELS[cat]}**")
            for e in items[-15:]:
                subj = e['subject']
                snippet = e['body_snippet'][:180] if e['body_snippet'] != subj else ''
                lines.append(f"- `{e['date']}` **{e['from']}** — {subj}")
                if snippet:
                    lines.append(f"  > {snippet}")
            lines.append("")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text('\n'.join(lines))
    print(f"Written: {OUT_FILE} ({len(lines)} lines)")


if __name__ == '__main__':
    main()
