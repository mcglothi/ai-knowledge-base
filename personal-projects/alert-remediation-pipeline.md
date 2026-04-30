---
context: personal
tags: [hermes, alertmanager, prometheus, loki, ansible, automation, homelab]
last_updated: 2026-04-20
status: in-progress
⚠️ IN PROGRESS — Phase 3 active

---

# Alert-to-Remediation Pipeline
**Last Updated:** 2026-04-20
**Summary:** Deploy an AI-driven alert → triage → auto-remediation pipeline. Grafana fires alerts into Alertmanager (standalone Docker), Alertmanager webhooks to an Event Router, which enriches context from Loki/Prometheus and activates Hermes. Hermes selects from a curated Ansible playbook registry or escalates and drafts a new playbook for engineer review.

**Assigned To:** Hermes (Newton, LM Studio backend)
**Review:** Claude Code (post-deployment check)

---

## Environment Context

| Item | Value |
|------|-------|
| Newton (prototype Hermes host) | `newton` / `100.64.0.5`, macOS 26.4.1, LM Studio backend |
| Hopper (final Hermes host) | `10.10.10.200` / `hopper.home.timmcg.net`, Debian, Ollama `:11434` |
| Babbage (Docker host) | `10.10.10.10` / `babbage.home.timmcg.net` |
| SSH user for babbage/hopper | `svc_ansible` via `~/.ssh/svc_ansible` |
| Monitoring stack | Prometheus + Loki + Grafana — **TrueNAS native apps** on babbage |
| Ansible repo | `~/code/ansible/` (do not modify — separate lane) |
| Playbook repo (new) | `mcglothi/resolution-playbooks` (create if missing) |
| Remediation inventory | `~/code/resolution-playbooks/inventory/` (separate from main Ansible) |
| Secrets | Vaultwarden at `vault.home.timmcg.net` |
| Hermes model (Newton) | LM Studio at `http://localhost:1234/v1` |
| Hermes model (Hopper, future) | Ollama at `http://localhost:11434/v1`, model `qwen3-coder:30b` |

---

## Architecture

```
Grafana (TrueNAS app)
  │  Alert rule fires
  ▼
Alertmanager (standalone Docker on babbage :9093)
  │  Webhook route
  ▼
Event Router (Docker on babbage :8080)
  │  Enriched context (Loki logs + Prom metrics)
  ▼
Hermes webhook (Newton :7777 for prototype → Hopper :7777 long-term)
  │
  ├─── Manifest match → Execution Gateway (babbage :8090) → ansible-playbook
  │                                                         → ntfy: "auto-resolved"
  └─── No match → ntfy escalation + draft playbook → PR on resolution-playbooks
```

**Why Grafana → Alertmanager instead of Prometheus → Alertmanager:**
Prometheus and Grafana run as TrueNAS native apps. Editing the TrueNAS-managed `prometheus.yml` directly risks being overwritten by TrueNAS on app restart. Grafana has a built-in Alertmanager contact point that can POST to any Alertmanager endpoint — no Prometheus config surgery needed.

**Why Newton first, Hopper long-term:**
Newton has Hermes + LM Studio already running. Hopper is always-on Debian with Ollama. Prototype the full pipeline on Newton, then migrate the Hermes webhook + handle_alert script to Hopper by swapping the model endpoint and deploying via Docker.

---

## Before Starting

Register your AIKB session:

```bash
git -C /Users/mcglothi/code/AIKB pull && \
python3 /Users/mcglothi/code/AIKB/_tools/memory-pipeline/runtime_cli.py wake-up

python3 /Users/mcglothi/code/AIKB/_tools/memory-pipeline/runtime_cli.py claim-session \
  --agent "Hermes" --repo "AIKB" \
  --scope "homelab alert-remediation pipeline" \
  --task "Deploy Alertmanager → Event Router → Hermes webhook → Ansible gateway"
```

Add `⚠️ IN PROGRESS` to the top of this file. Replace with `✅` when done.

---

## Phase 1 — Discover Monitoring Stack on Babbage

**Goal:** Confirm TrueNAS app details, find where Grafana and Loki are reachable internally, note network names used by TrueNAS app containers.

```bash
# List running containers related to monitoring
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 \
  "docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}' | grep -iE 'grafana|prometheus|loki|alert'"

# Find the Docker network TrueNAS apps use
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 \
  "docker inspect \$(docker ps -q --filter name=grafana | head -1) --format '{{json .NetworkSettings.Networks}}' | python3 -m json.tool"
```

**Document:**
- Container names for Grafana, Prometheus, Loki
- Their internal Docker network name (you'll need this to put Alertmanager on the same network)
- Internal service hostnames (e.g. `prometheus`, `loki`, or full container names)
- Grafana URL (likely `http://babbage.home.timmcg.net:3000` or similar)

**Checkpoint:**
```bash
python3 /Users/mcglothi/code/AIKB/_tools/memory-pipeline/runtime_cli.py capture \
  --agent "Hermes" --type observation \
  --project "personal-projects/alert-remediation-pipeline.md" \
  --summary "Monitoring containers: <names>. Docker network: <name>. Grafana URL: <url>. Loki internal: <host:port>."
```

---

## Phase 2 — Deploy Alertmanager (Standalone Docker)

**Goal:** Run Alertmanager as a standalone Docker container on babbage, on the same network as the TrueNAS monitoring apps. Configure it to route all alerts to the Event Router.

### 2a. Create config directory and alertmanager.yml

```bash
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 "sudo mkdir -p /opt/alertmanager"
```

Write `/opt/alertmanager/alertmanager.yml` on babbage:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'instance', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: event-router

receivers:
  - name: event-router
    webhook_configs:
      - url: 'http://alert-router:8080/webhook'
        send_resolved: true

inhibit_rules:
  - source_matchers: [severity="critical"]
    target_matchers: [severity="warning"]
    equal: ['alertname', 'instance']
```

### 2b. Write compose file for standalone stack

Create `/opt/alertmanager/compose.yaml` on babbage. Replace `<MONITORING_NETWORK>` with the network name discovered in Phase 1:

```yaml
services:
  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - /opt/alertmanager:/etc/alertmanager
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://babbage.home.timmcg.net:9093'
    networks:
      - monitoring_net

  alert-router:
    image: alert-router:latest
    container_name: alert-router
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - alert_router_data:/data
    environment:
      - HERMES_WEBHOOK_URL=http://newton.home.timmcg.net:7777/alert
      - LOKI_URL=http://<LOKI_CONTAINER_NAME>:3100
      - PROMETHEUS_URL=http://<PROMETHEUS_CONTAINER_NAME>:9090
    networks:
      - monitoring_net

  exec-gateway:
    image: exec-gateway:latest
    container_name: exec-gateway
    restart: unless-stopped
    ports:
      - "8090:8090"
    volumes:
      - /opt/resolution-playbooks:/playbooks:ro
      - /opt/remediation-inventory:/ansible/inventory:ro
    environment:
      - PLAYBOOK_REPO_PATH=/playbooks
      - ANSIBLE_INVENTORY=/ansible/inventory/hosts.yml
      - GATEWAY_TOKEN_FILE=/run/secrets/gateway_token
    networks:
      - monitoring_net

  ntfy:
    image: binwiederhier/ntfy:latest
    container_name: ntfy
    restart: unless-stopped
    ports:
      - "8120:80"
    volumes:
      - ntfy_data:/var/cache/ntfy
    command: serve
    environment:
      - NTFY_BASE_URL=http://babbage.home.timmcg.net:8120
      - NTFY_CACHE_FILE=/var/cache/ntfy/cache.db
    networks:
      - monitoring_net

volumes:
  alertmanager_data:
  alert_router_data:
  ntfy_data:

networks:
  monitoring_net:
    external: true
    name: <MONITORING_NETWORK>   # ← replace with actual network name from Phase 1
```

**Note:** `alert-router` and `exec-gateway` images are built in Phases 4 and 6. Start only `alertmanager` and `ntfy` now:

```bash
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 \
  "cd /opt/alertmanager && docker compose up -d alertmanager ntfy"

# Verify
curl -s http://10.10.10.10:9093/-/healthy
curl -s http://10.10.10.10:8120/v1/health
```

---

## Phase 3 — Configure Grafana Alerting → Alertmanager

**Goal:** Add Alertmanager as a contact point in Grafana, write alert rules for disk/memory/host, and route all alerts through Alertmanager.

### 3a. Add Alertmanager contact point in Grafana

1. Open Grafana UI (URL from Phase 1)
2. Navigate to **Alerting → Contact points → Add contact point**
3. Type: **Alertmanager**
4. URL: `http://alertmanager:9093` (internal Docker network name) or `http://10.10.10.10:9093` if cross-network
5. Save and test — you should see a test alert appear in Alertmanager UI at `http://10.10.10.10:9093`

**Alternative via Grafana API** (if you prefer scripting):
```bash
curl -s -X POST http://10.10.10.10:3000/api/v1/provisioning/contact-points \
  -H "Content-Type: application/json" \
  -u admin:<password> \
  -d '{
    "name": "alertmanager",
    "type": "alertmanager",
    "settings": {
      "url": "http://10.10.10.10:9093",
      "basicAuthUser": "",
      "basicAuthPassword": ""
    }
  }'
```

Get the Grafana admin password from Vaultwarden:
```bash
BW_SESSION=$(cat ~/.bw_session)
bw get password "homelab/grafana-admin" --session "$BW_SESSION"
```

### 3b. Set Alertmanager as the default contact point

Grafana Alerting → Notification policies → Edit root policy → set contact point to `alertmanager`.

### 3c. Create alert rules in Grafana

Navigate to **Alerting → Alert rules → New alert rule**. Create one rule per category. Use Grafana's query builder against the Prometheus datasource.

**Disk Space High** (Warning):
- Query: `(node_filesystem_avail_bytes{mountpoint!~"/boot.*"} / node_filesystem_size_bytes) * 100`
- Condition: `IS BELOW 15`
- For: `5m`
- Labels: `severity=warning`, `alertname=DiskSpaceHigh`

**Disk Space Critical**:
- Same query, threshold `5`, for `2m`, `severity=critical`, `alertname=DiskSpaceCritical`

**Memory High**:
- Query: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- Condition: `IS ABOVE 90`
- For: `10m`
- Labels: `severity=warning`, `alertname=MemoryHigh`

**Host Unreachable**:
- Query: `up`
- Condition: `IS BELOW 1`
- For: `3m`
- Labels: `severity=critical`, `alertname=HostUnreachable`

**Note on node_exporter:** The disk/memory rules require node_exporter running on target hosts. Check if it's already scraping: `curl -s http://10.10.10.10:9090/api/v1/targets | python3 -m json.tool | grep node`. If not present, note this as a follow-up — the host rules can still be set up now.

---

## Phase 4 — Build and Deploy the Event Router

**Goal:** FastAPI service on babbage that receives Alertmanager webhooks, enriches them with Loki logs and Prometheus metrics, then POSTs to Hermes.

### 4a. Create build directory on babbage

```bash
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 "sudo mkdir -p /opt/alert-router"
```

### 4b. Write the app files

Write the following to babbage at `/opt/alert-router/`:

**`main.py`**:
```python
from fastapi import FastAPI, Request
from datetime import datetime, timezone
import httpx, sqlite3, json, os

app = FastAPI()
DB_PATH = "/data/events.db"
HERMES_WEBHOOK = os.environ.get("HERMES_WEBHOOK_URL", "")
LOKI_URL = os.environ.get("LOKI_URL", "http://loki:3100")
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "http://prometheus:9090")

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        received_at TEXT,
        alertname TEXT,
        severity TEXT,
        host TEXT,
        status TEXT,
        raw TEXT,
        enriched TEXT
    )""")
    con.commit(); con.close()

init_db()

async def enrich(alert: dict) -> dict:
    labels = alert.get("labels", {})
    host = labels.get("instance", labels.get("host", "unknown")).split(":")[0]
    alertname = labels.get("alertname", "unknown")
    enriched = {"alert": alert, "loki_logs": [], "prom_metrics": {}}

    async with httpx.AsyncClient(timeout=10) as client:
        # Last 15 min of logs for this host
        try:
            end = int(datetime.now(timezone.utc).timestamp() * 1e9)
            start = end - int(15 * 60 * 1e9)
            r = await client.get(f"{LOKI_URL}/loki/api/v1/query_range", params={
                "query": f'{{host=~"{host}"}}',
                "start": start, "end": end, "limit": 100
            })
            if r.status_code == 200:
                for stream in r.json().get("data", {}).get("result", []):
                    for _, line in stream.get("values", []):
                        enriched["loki_logs"].append(line)
        except Exception as e:
            enriched["loki_logs"] = [f"[loki error: {e}]"]

        # Relevant Prometheus metric snapshot
        try:
            metric_map = {
                "DiskSpaceHigh": f'node_filesystem_avail_bytes{{instance=~"{host}.*"}}',
                "DiskSpaceCritical": f'node_filesystem_avail_bytes{{instance=~"{host}.*"}}',
                "MemoryHigh": f'node_memory_MemAvailable_bytes{{instance=~"{host}.*"}}',
                "HostUnreachable": f'up{{instance=~"{host}.*"}}',
            }
            q = metric_map.get(alertname)
            if q:
                r = await client.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": q})
                if r.status_code == 200:
                    enriched["prom_metrics"] = r.json().get("data", {})
        except Exception as e:
            enriched["prom_metrics"] = {"error": str(e)}

    return enriched

@app.post("/webhook")
async def receive_alert(request: Request):
    body = await request.json()
    alerts = body.get("alerts", [])
    for alert in alerts:
        labels = alert.get("labels", {})
        enriched = await enrich(alert)
        con = sqlite3.connect(DB_PATH)
        con.execute(
            "INSERT INTO events (received_at,alertname,severity,host,status,raw,enriched) VALUES (?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(),
             labels.get("alertname","unknown"), labels.get("severity","unknown"),
             labels.get("instance", labels.get("host","unknown")),
             alert.get("status","unknown"), json.dumps(alert), json.dumps(enriched))
        )
        con.commit(); con.close()

        if HERMES_WEBHOOK:
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    await client.post(HERMES_WEBHOOK, json=enriched)
            except Exception as e:
                print(f"[router] Hermes webhook failed: {e}")

    return {"received": len(alerts)}

@app.get("/events")
def list_events(limit: int = 50):
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT id,received_at,alertname,severity,host,status FROM events ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    con.close()
    return [{"id":r[0],"received_at":r[1],"alertname":r[2],
             "severity":r[3],"host":r[4],"status":r[5]} for r in rows]
```

**`requirements.txt`**:
```
fastapi
uvicorn
httpx
```

**`Dockerfile`**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 4c. Build and deploy

```bash
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 \
  "cd /opt/alertmanager && docker compose build alert-router && \
   docker compose up -d alert-router && docker compose ps"
```

### 4d. Verify

```bash
# Send synthetic webhook
curl -s -X POST http://10.10.10.10:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"alerts":[{"labels":{"alertname":"DiskSpaceHigh","severity":"warning","instance":"babbage:9100"},"status":"firing","annotations":{"summary":"Test","description":"Disk test"}}]}'

curl -s http://10.10.10.10:8080/events | python3 -m json.tool | head -20
```

---

## Phase 5 — Resolution Playbooks Repository

**Goal:** Create the playbook registry on GitHub. Separate remediation Ansible inventory lives here too, isolated from the main Ansible lanes.

### 5a. Create the repo

```bash
gh repo create mcglothi/resolution-playbooks --private \
  --description "Approved Ansible remediation playbooks for automated alert resolution"
cd ~/code && git clone git@github.com:mcglothi/resolution-playbooks.git
cd resolution-playbooks
```

### 5b. Create directory structure

```
resolution-playbooks/
├── manifest.yaml
├── inventory/
│   └── hosts.yml          ← remediation-only inventory (separate from ~/code/ansible/)
├── approved/
│   ├── disk_cleanup_old_logs.yml
│   ├── disk_cleanup_docker.yml
│   └── container_healthcheck.yml
└── drafts/
    └── .gitkeep
```

**`inventory/hosts.yml`** — remediation targets only:
```yaml
all:
  vars:
    ansible_user: svc_ansible
    ansible_ssh_private_key_file: ~/.ssh/svc_ansible
    ansible_become: true
    ansible_become_method: sudo
  hosts:
    babbage:
      ansible_host: 10.10.10.10
    turing:
      ansible_host: 10.10.10.50
    hopper:
      ansible_host: 10.10.10.200
    farnsworth:
      ansible_host: 10.10.10.100
```

**`manifest.yaml`**:
```yaml
version: "1"
playbooks:
  - id: disk_cleanup_old_logs
    path: approved/disk_cleanup_old_logs.yml
    description: Remove log files older than 30 days from /var/log
    triggers:
      - alertname: DiskSpaceHigh
      - alertname: DiskSpaceCritical
    preconditions: []
    tags: []
    risk_level: low
    status: approved

  - id: disk_cleanup_docker
    path: approved/disk_cleanup_docker.yml
    description: Prune unused Docker images, stopped containers, and dangling volumes
    triggers:
      - alertname: DiskSpaceHigh
      - alertname: DiskSpaceCritical
    preconditions: []
    tags: []
    risk_level: low
    status: approved

  - id: container_healthcheck
    path: approved/container_healthcheck.yml
    description: Report container status and recent logs — read-only, no changes made
    triggers:
      - alertname: ContainerDown
    preconditions: []
    tags: [read_only]
    risk_level: none
    status: approved
```

**`approved/disk_cleanup_old_logs.yml`**:
```yaml
---
- name: Clean old log files
  hosts: "{{ target_hosts }}"
  become: true
  gather_facts: false
  tasks:
    - name: Find log files older than 30 days
      find:
        paths: /var/log
        age: 30d
        recurse: true
        patterns: "*.log,*.log.*,*.gz"
      register: old_logs

    - name: Remove old log files
      file:
        path: "{{ item.path }}"
        state: absent
      loop: "{{ old_logs.files }}"
      when: old_logs.matched > 0

    - name: Report
      debug:
        msg: "Removed {{ old_logs.matched }} log files"
```

**`approved/disk_cleanup_docker.yml`**:
```yaml
---
- name: Prune Docker resources
  hosts: "{{ target_hosts }}"
  become: true
  gather_facts: false
  tasks:
    - name: Prune unused Docker images, containers, and dangling volumes
      command: docker system prune -f
      register: prune_result

    - name: Report
      debug:
        msg: "{{ prune_result.stdout }}"
```

**`approved/container_healthcheck.yml`**:
```yaml
---
- name: Report container status (read-only)
  hosts: "{{ target_hosts }}"
  become: true
  gather_facts: false
  vars:
    container_name: "{{ target_container | default('unknown') }}"
  tasks:
    - name: Get container status
      command: >
        docker inspect --format
        '{{ '{{' }}.State.Status{{ '}}' }} healthy={{ '{{' }}.State.Health.Status{{ '}}' }}'
        "{{ container_name }}"
      register: status
      ignore_errors: true

    - name: Get recent logs
      command: docker logs --tail 50 "{{ container_name }}"
      register: recent_logs
      ignore_errors: true

    - name: Report
      debug:
        msg:
          - "Container: {{ container_name }}"
          - "Status: {{ status.stdout | default('not found') }}"
          - "Recent stderr: {{ recent_logs.stderr_lines[-20:] | default([]) }}"
```

### 5c. Commit and push

```bash
cd ~/code/resolution-playbooks
git add .
git commit -m "Initial playbook registry: manifest, inventory, 3 approved playbooks"
git push origin main
```

### 5d. Clone to babbage for gateway access

```bash
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 \
  "git clone git@github.com:mcglothi/resolution-playbooks.git /opt/resolution-playbooks && \
   mkdir -p /opt/remediation-inventory && \
   cp /opt/resolution-playbooks/inventory/hosts.yml /opt/remediation-inventory/"
```

---

## Phase 6 — Build and Deploy the Execution Gateway

**Goal:** Trusted API gateway — Hermes POSTs `{playbook_id, target_hosts, extra_vars}`. Gateway validates against manifest, enforces tag restrictions, runs ansible-playbook.

### 6a. Create build directory

```bash
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 "sudo mkdir -p /opt/exec-gateway"
```

### 6b. Write the service

**`main.py`**:
```python
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import subprocess, yaml, os

app = FastAPI()

PLAYBOOK_REPO = os.environ.get("PLAYBOOK_REPO_PATH", "/playbooks")
ANSIBLE_INVENTORY = os.environ.get("ANSIBLE_INVENTORY", "/ansible/inventory/hosts.yml")
GATEWAY_TOKEN = os.environ.get("GATEWAY_TOKEN", "")

RESTRICTED_TAGS = {"requires_restart", "requires_reboot"}

class ExecuteRequest(BaseModel):
    playbook_id: str
    target_hosts: str
    extra_vars: dict = {}
    authorized_tags: list[str] = []

def load_manifest() -> list[dict]:
    with open(f"{PLAYBOOK_REPO}/manifest.yaml") as f:
        return yaml.safe_load(f).get("playbooks", [])

def find_playbook(playbook_id: str) -> dict | None:
    return next((p for p in load_manifest()
                 if p["id"] == playbook_id and p["status"] == "approved"), None)

@app.post("/execute")
def execute(req: ExecuteRequest, x_gateway_token: str = Header(default="")):
    if GATEWAY_TOKEN and x_gateway_token != GATEWAY_TOKEN:
        raise HTTPException(403, "Invalid gateway token")

    playbook = find_playbook(req.playbook_id)
    if not playbook:
        raise HTTPException(404, f"Playbook '{req.playbook_id}' not found or not approved")

    blocked = RESTRICTED_TAGS & set(playbook.get("tags", []))
    if blocked and not blocked.issubset(set(req.authorized_tags)):
        raise HTTPException(403, f"Playbook has restricted tags {blocked} — explicit authorization required")

    playbook_path = os.path.join(PLAYBOOK_REPO, playbook["path"])
    if not os.path.exists(playbook_path):
        raise HTTPException(500, f"Playbook file missing: {playbook_path}")

    extra_vars = {**req.extra_vars, "target_hosts": req.target_hosts}
    cmd = [
        "ansible-playbook", playbook_path,
        "-i", ANSIBLE_INVENTORY,
        "--extra-vars", yaml.dump(extra_vars),
        "--limit", req.target_hosts,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    return {
        "playbook_id": req.playbook_id,
        "target_hosts": req.target_hosts,
        "return_code": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-2000:],
        "success": result.returncode == 0
    }

@app.get("/playbooks")
def list_playbooks():
    return load_manifest()
```

**`requirements.txt`**:
```
fastapi
uvicorn
pyyaml
```

**`Dockerfile`**:
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y ansible git openssh-client && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
```

### 6c. Set gateway token in Vaultwarden

Add a Vaultwarden entry `homelab/exec-gateway-token` with a random token (e.g. `openssl rand -hex 32`). Retrieve it:

```bash
BW_SESSION=$(cat ~/.bw_session)
GATEWAY_TOKEN=$(bw get password "homelab/exec-gateway-token" --session "$BW_SESSION")
echo $GATEWAY_TOKEN  # verify it retrieved
```

Pass the token to the compose environment. Write it to `/opt/alertmanager/.env` on babbage (not committed to git):
```
EXEC_GATEWAY_TOKEN=<token>
```

Update the `exec-gateway` service in `compose.yaml`:
```yaml
    environment:
      - GATEWAY_TOKEN=${EXEC_GATEWAY_TOKEN}
```

### 6d. Build and deploy

```bash
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 \
  "cd /opt/alertmanager && docker compose build exec-gateway && \
   docker compose up -d exec-gateway && docker compose ps"
```

### 6e. Verify

```bash
# List approved playbooks
curl -s http://10.10.10.10:8090/playbooks | python3 -m json.tool

# Test read-only playbook
curl -s -X POST http://10.10.10.10:8090/execute \
  -H "Content-Type: application/json" \
  -H "X-Gateway-Token: $GATEWAY_TOKEN" \
  -d '{"playbook_id":"container_healthcheck","target_hosts":"babbage","extra_vars":{"target_container":"alertmanager"}}' \
  | python3 -m json.tool
```

---

## Phase 7 — Configure Hermes Webhook on Newton

**Goal:** Register a Hermes webhook subscription on Newton that activates Hermes when the Event Router POSTs an enriched alert. Hermes reasons about the alert, calls the execution gateway or escalates.

### 7a. Write the Hermes prompt template

Write `~/code/alert-pipeline/alert_prompt.md` on Newton:

```markdown
You are an infrastructure remediation agent. An alert has fired in the homelab.

## Alert Context
- **Alert name:** {{ alert.labels.alertname }}
- **Host:** {{ alert.labels.instance }}
- **Severity:** {{ alert.labels.severity }}
- **Status:** {{ alert.status }}
- **Description:** {{ alert.annotations.description }}

## Recent Logs (last 15 lines from Loki)
{{ loki_logs | last(15) | join('\n') }}

## Current Metrics
{{ prom_metrics | tojson }}

## Available Playbooks
{{ manifest | tojson }}

## Your Task
1. Analyze the alert and logs to confirm root cause.
2. Check the available playbooks list above for a matching playbook (match on `triggers[].alertname`).
3. If a match exists:
   - Call the execution gateway: POST http://10.10.10.10:8090/execute
   - Header: X-Gateway-Token: {{ env.EXEC_GATEWAY_TOKEN }}
   - Body: {"playbook_id": "<id>", "target_hosts": "<host>", "extra_vars": {}}
   - Report the result via ntfy: POST http://babbage.home.timmcg.net:8120/homelab-alerts
4. If no match exists:
   - Send escalation to ntfy with alert summary and reason no playbook matched
   - Draft an Ansible playbook to address this alert type (idempotent, no reboots/restarts)
   - Commit the draft to ~/code/resolution-playbooks/drafts/<alertname>_draft.yml
   - Create a branch `hermes/draft-<alertname>-<date>` and open a PR on mcglothi/resolution-playbooks

Rules for any playbook you draft:
- Must be idempotent
- No reboots, no service restarts unless explicitly tagged `requires_restart`
- hosts must use variable: hosts: "{{ target_hosts }}"
- Keep it minimal — one job, one purpose
```

### 7b. Check hermes webhook subscribe syntax

Run this first and note the exact flags:
```bash
hermes webhook subscribe --help
```

Then register the subscription. The general form is likely:
```bash
hermes webhook subscribe \
  --name "alert-handler" \
  --route "/alert" \
  --port 7777 \
  --prompt-file ~/code/alert-pipeline/alert_prompt.md
```

Adjust flags to match what `hermes webhook subscribe --help` shows. Key things to pass:
- The route path (`/alert`)
- The port (`7777`)
- The prompt (either inline or as a file reference)
- Any env vars needed by the prompt (`EXEC_GATEWAY_TOKEN`)

Verify the subscription was registered:
```bash
hermes webhook list
```

### 7c. Test the webhook directly

```bash
hermes webhook test alert-handler \
  --data '{"alert":{"labels":{"alertname":"DiskSpaceHigh","severity":"warning","instance":"babbage:9100"},"status":"firing","annotations":{"description":"/ has less than 15% free"}},"loki_logs":["test log line"],"prom_metrics":{}}'
```

### 7d. Make it persistent (launchd on Newton)

Write `~/Library/LaunchAgents/net.timmcg.hermes-alert-webhook.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>net.timmcg.hermes-alert-webhook</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/hermes</string>
        <string>webhook</string>
        <string>subscribe</string>
        <!-- adjust args to match what --help shows -->
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>EXEC_GATEWAY_TOKEN</key>
        <string>REPLACE_WITH_TOKEN</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/mcglothi/logs/hermes-webhook.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/mcglothi/logs/hermes-webhook.err</string>
</dict>
</plist>
```

**Note:** Replace `REPLACE_WITH_TOKEN` with the actual token fetched from Vaultwarden. Retrieve it at plist-write time:
```bash
BW_SESSION=$(cat ~/.bw_session)
GATEWAY_TOKEN=$(bw get password "homelab/exec-gateway-token" --session "$BW_SESSION")
# Then substitute into the plist before writing
```

```bash
mkdir -p ~/logs
launchctl load ~/Library/LaunchAgents/net.timmcg.hermes-alert-webhook.plist
launchctl list | grep hermes
```

---

## Phase 8 — End-to-End Test

**Goal:** Fire a real alert path and verify every hop.

### 8a. Trigger via Alertmanager API

```bash
curl -s -X POST http://10.10.10.10:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "DiskSpaceHigh",
      "severity": "warning",
      "instance": "babbage:9100"
    },
    "annotations": {
      "summary": "Disk space low on babbage",
      "description": "/ has less than 15% free — test alert"
    },
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }]'
```

### 8b. Verify each hop in order

```bash
# 1. Alertmanager received and routed it
curl -s http://10.10.10.10:9093/api/v2/alerts | python3 -m json.tool | grep alertname

# 2. Event Router received and stored it
curl -s http://10.10.10.10:8080/events | python3 -m json.tool | head -30

# 3. Hermes webhook was activated (check hermes logs / launchd output)
tail -20 ~/logs/hermes-webhook.log

# 4. Execution gateway was called
ssh -i ~/.ssh/svc_ansible svc_ansible@10.10.10.10 "docker logs exec-gateway --tail 20"

# 5. ntfy notification arrived
# Check phone/browser at http://babbage.home.timmcg.net:8120/homelab-alerts
```

Expected result: ntfy notification saying "Auto-resolved: DiskSpaceHigh — ran disk_cleanup_old_logs on babbage"

### 8c. Test the escalation path (no-match alert)

```bash
curl -s -X POST http://10.10.10.10:9093/api/v2/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {"alertname": "UnknownServiceFailure", "severity": "critical", "instance": "babbage:9100"},
    "annotations": {"summary": "Unknown failure", "description": "Test of escalation path"},
    "startsAt": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }]'
```

Expected result:
- ntfy notification: escalation + "no playbook found"
- A new draft PR on `mcglothi/resolution-playbooks` for `UnknownServiceFailure`

---

## Phase 9 — AIKB Update + Closeout

When all phases are ✅:

1. Update this file: set status to `done`, remove `⚠️ IN PROGRESS`
2. Update `home-lab/infrastructure/living-atlas.yaml`: add `alertmanager`, `alert-router`, `exec-gateway`, `ntfy` services
3. Update `home-lab/infrastructure/servers.md`: add port reference table for new services
4. Add `resolution-playbooks` to `_index.md`
5. Note Newton→Hopper migration as a follow-up pending item in `_state.yaml`
6. Capture closeout:

```bash
python3 /Users/mcglothi/code/AIKB/_tools/memory-pipeline/runtime_cli.py closeout \
  --phrase "pipeline deploy complete"

git -C /Users/mcglothi/code/AIKB add . && \
git -C /Users/mcglothi/code/AIKB commit -m "AI Update: alert-remediation-pipeline.md — v1 deployment complete on Newton" && \
git -C /Users/mcglothi/code/AIKB push origin main
```

---

## Newton → Hopper Migration (Follow-up)

After the prototype is validated on Newton, migrate Hermes to Hopper:

1. The Event Router `HERMES_WEBHOOK_URL` env var changes from `newton.home.timmcg.net:7777` → `hopper.home.timmcg.net:7777`
2. Deploy Hermes on Hopper — swap LM Studio (`localhost:1234/v1`) for Ollama (`localhost:11434/v1`, model `qwen3-coder:30b`)
3. Register the same webhook subscription on Hopper
4. Set up as a systemd service on Hopper (not launchd — it's Debian)
5. Update `/opt/alertmanager/compose.yaml` with new `HERMES_WEBHOOK_URL` and restart alert-router
6. Decommission the launchd agent on Newton

---

## Blockers / Open Questions (Hermes: flag these, don't guess)

- [ ] Exact `hermes webhook subscribe` flag names — run `hermes webhook subscribe --help` and adjust Phase 7 accordingly
- [ ] Hermes binary path for launchd plist — run `which hermes` on Newton
- [ ] Whether Grafana and Alertmanager can reach each other by container name (Phase 3) — may need to use `10.10.10.10:9093` instead of `alertmanager:9093` if they're on separate Docker networks
- [ ] node_exporter presence — verify before expecting disk/memory rules to fire real data
- [ ] Grafana admin password in Vaultwarden — confirm the entry name matches what's stored

---

## Review Checklist for Claude Code

After Hermes completes, report back with:

- [ ] All 4 services running (`docker ps` on babbage: alertmanager, alert-router, exec-gateway, ntfy)
- [ ] Grafana contact point test passes (Alertmanager receives test alert)
- [ ] Event Router correctly enriches events (show sample `/events` output)
- [ ] Gateway enforces tag restrictions (attempt a fake `requires_restart` playbook — should get 403)
- [ ] Hermes webhook subscription confirmed active (`hermes webhook list`)
- [ ] End-to-end test result (matching alert path)
- [ ] Escalation path test result (non-matching alert → PR created)
- [ ] Draft PR URL from the escalation test
- [ ] No credentials in any committed file
