---
context: personal
tags: [apf, certificates, ec2, mariadb, s3, ocr, tesseract, php, bacb, lookup, aws, ssh, bastion, database, t2-micro, dns, dkim, spf]
hosts: [ec2-apf-cert]
services: [mariadb, apache]
last_updated: 2026-04-13
---

# APF: Certificate Registry — Reference

**Last Updated:** 2026-04-13
**Summary:** Standalone certificate lookup system on EC2 t2.micro (ip-10-0-20-83). 64,451 certs in MariaDB + S3. Tabbed web UI (BACB / Email / Name). OCR enrichment COMPLETE (99.8% coverage). Added send.registery DNS records.

---

## DNS Records (Route 53)

Managed in hosted zone `Z01249502BI1HFSPUUYK4` (autismpartnershipfoundation.org).

| Type | Host/Name | Value |
|------|-----------|-------|
| TXT  | `resend._domainkey.registery` | `p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5lyFdfxebJ/YSCz+8aQnhNAIg5UjlkGmCAYREt9icVqNpvX86d5BEcXxvjwaD6VInftHGSMwgwyExEMqtCGPbQid7jpmNdhW04sOXXzzBjmvFQHqbUM3VcCEmjyMDWNTwoxLK6ZyWVF040hZDxTKrNo/+LuyjSsPCz6Mf0PzBiwIDAQAB` |
| MX   | `send.registery` | `10 feedback-smtp.us-east-1.amazonses.com` |
| TXT  | `send.registery` | `v=spf1 include:amazonses.com ~all` |

---

## Application

- **Lookup UI:** https://myadmin.autismpartnershipfoundation.org/verify/lookup_enhanced.php
- **Legacy UI:** `.../verify/lookup.php` (BACB number only — kept alongside)
- **App path:** `/var/www/html/verify/`
- **Config:** `/var/www/config.php`

---

## SSH Access (two-hop via bastion)

### Preferred: `APF` alias in `~/.ssh/config`

```bash
ssh APF                          # interactive shell on web server
scp /tmp/file.php APF:/tmp/      # copy files
ssh APF "sudo command"           # run command
```

`~/.ssh/config` entry (on feynman):
```
Host apf-jump-host
  HostName 52.39.99.191          # ⚠ bastion gets a new public IP on each start
  User ec2-user
  IdentityFile ~/tmcglothin-apf-prod.pem

Host APF
  HostName 10.0.20.83
  User ec2-user
  IdentityFile ~/tmcglothin-apf-prod.pem
  ProxyCommand ssh -q -W %h:%p apf-jump-host
```

### Finding the current bastion IP

The bastion gets a new public IP on every restart. To find it (requires AWS CLI + credentials):

```bash
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].[Tags[?Key==`Name`].Value | [0], PrivateIpAddress, PublicIpAddress, State.Name]' \
  --output table
```

On feynman this is aliased as `apf-inst`. On other machines run the full command above.

**Workflow when bastion IP has changed:**
1. Run the command above — find the public IP of `Bastion / apf-prod-bastion-*`
2. Update `apf-jump-host` HostName in `~/.ssh/config`
3. `ssh APF` works again

### Instances (current)

| Name | Instance ID | Private IP | Public IP | Notes |
|------|-------------|------------|-----------|-------|
| phpmyadmin | `i-054376b6d8751b8cb` | `10.0.20.83` | none | Web server, t2.micro |
| Bastion | `i-0bd90d7263a1dfaae` | `10.0.10.243` | `52.39.99.191` (changes on restart) | t2.nano, RUNNING |

- **SSH key:** `~/tmcglothin-apf-prod.pem`
- **Web root:** `/var/www/html/verify/`

**Pitfalls:**
- **Bastion public IP changes on restart** — run `apf-inst` to confirm current IP, then update `~/.ssh/config` `apf-jump-host` HostName.
- **Never `pkill -f <pattern>` over SSH** — the pattern matches the bash process in the SSH command itself, killing the session. Use `kill <PID>`.
- `</dev/null` redirect required for nohup processes to survive SSH disconnect.

---

## Database

- **Engine:** MariaDB 10.2.38 (localhost on EC2)
- **DB:** `apf_certificates` / **User:** `cert_user` / **Pass:** `[Stored in Vaultwarden: APF MariaDB]`
- **Auth:** socket-only (`cert_user@localhost`). TCP connections (e.g. SSH tunnel to 127.0.0.1) are denied. Root MySQL password unknown.
- **Workaround for remote writes:** generate SQL files locally, SCP to `/tmp/`, apply via `mysql < file.sql` over SSH.

### `certificate_registry` — 64,451 rows

```sql
id               INT PK
bacb_number      VARCHAR(50) UNIQUE   -- e.g. "BACB1000309"
s3_key           VARCHAR(255)         -- e.g. "certificate_\t1117334.jpg"  ← LITERAL TAB!
s3_bucket        VARCHAR(100)         -- "apf-certs"
first_name       VARCHAR(100)         -- Populated by OCR enrichment
last_name        VARCHAR(100)         -- Populated by OCR enrichment
user_email       VARCHAR(255)
course_start_date DATE
course_end_date   DATE
updated_at        DATETIME ON UPDATE CURRENT_TIMESTAMP
```

### `course_completions` — 495,842 rows (imported from `wordpress_users_reference.csv`)

```sql
id         INT PK
wp_user_id INT                     INDEX
email      VARCHAR(255)            INDEX
first_name VARCHAR(100)
last_name  VARCHAR(100)            INDEX (last_name, first_name)
start_date DATE
end_date   DATE                    INDEX
```

### `certificate_lookups` — audit log of all search queries

---

## CRITICAL: S3 Key Contains a Literal TAB

Every key in `apf-certs` has a **literal TAB character** between `certificate_` and the BACB number:

```
certificate_\t1117334.jpg        ← actual key
certificate_\tBACB1000309.jpg    ← actual key
```

- The `s3_key` column stores this tab literally.
- **Always pass the raw DB value** — PHP `escapeshellarg()` handles it correctly.
- **Never construct the key manually.**
- In bash: `"certificate_"$'\t'"1117334.jpg"`
- `aws s3 ls s3://apf-certs/` shows the tab as whitespace in terminal output.

---

## S3 Bucket

- **Bucket:** `apf-certs` (us-west-2) — 64,451 certificate JPGs (~30 GB)
- **Backup bucket:** `apf-migration-backups-2026` — 290,566 certificate PDFs (48 GB) + DB backups

---

## Application Files

```
/var/www/html/verify/
├── index.php                           # Certificate generation (with registry logging)
├── index.php.backup-20260204           # Original backup
├── lookup.php                          # BACB number lookup (legacy, keep alongside)
├── lookup_enhanced.php                 # Tabbed UI: BACB / Email / Name
├── test_lookup.php                     # CLI lookup tool
├── test_registry.php                   # DB connection test
├── enrich_certs_ocr.php                # EC2 OCR enrichment (single worker, slow)
├── launch_ocr.sh                       # Safe single-worker launcher
├── import_completions.php              # One-time CSV import (already run)
├── migrate_certificates_optimized.php  # S3 discovery & WP data extraction
├── import_all_certificates.php         # Certificate import script
├── s3_certificates_cache.json          # S3 data cache (17 MB, 65,727 certs)
├── certificate_mapping.csv             # Certificate list (65,718 rows)
├── wordpress_users_reference.csv       # RBT course users (495,842)
└── vendor/                             # Composer (AWS SDK)
```

### Lookup UI tabs (`lookup_enhanced.php`)
- **Tab 1:** BACB Number — existing single-cert lookup
- **Tab 2:** Email — searches both `certificate_registry.user_email` + `course_completions.email`
- **Tab 3:** Name — searches both tables; masks email as `jo***@gmail.com` on multi-match (privacy)

---

## OCR Enrichment Pipeline

Populates `first_name` / `last_name` in `certificate_registry` by running Tesseract on the JPG certs.

### Certificate Template (all 64,451 certs use this layout)
```
[First Last] [BACB_artifact]
Name of RBT Applicant:   RBT Applicant BACB ID:
[MM-DD-YYYY]  [MM-DD-YYYY]
Training Start Date:     Training End Date:
```

### Local Multi-Worker Approach — COMPLETE ✅

**Final status:** 12 Python workers finished 2026-02-20. 64,040 records enriched locally and imported to EC2.

**Key implementation details:**
- `OMP_THREAD_LIMIT=1` on each Tesseract call — prevents CPU contention.
- SQL-file approach used instead of SSH tunnel.
- Results imported via `/tmp/apf_ocr/import_ocr_results.sh`.

**Performance:** ~0.39/s per worker × 12 = ~4.7 certs/sec total.

**Final Verification:**
```sql
SELECT
  COUNT(*) AS total,
  SUM(first_name IS NOT NULL) AS enriched,
  SUM(first_name IS NULL AND s3_key IS NOT NULL) AS still_null
FROM certificate_registry;
-- Result: 64,451 total, 64,336 enriched, 115 still_null (99.8% coverage)
```

### EC2 Single-Worker (slow fallback — currently KILLED)
- Script: `enrich_certs_ocr.php` | Launch: `launch_ocr.sh` (nohup + `</dev/null`)
- Log: `/tmp/ocr.log` | Throughput: ~0.38/s
- **NEVER run more than 1 worker on t2.micro** — 4 workers → OOM → MariaDB crash → required `aws ec2 reboot-instances`
  - OOM breakdown: 4× PHP (~64MB) + 4× Tesseract (~150MB) + MariaDB (~300MB) + Apache = exceeded 970MB

---

## Key Dependencies (version-pinned)

| Component | Version | Where | Notes |
|-----------|---------|-------|-------|
| Tesseract OCR (EC2) | 3.04.00 | EC2 t2.micro via EPEL/yum | Slow (~2s/cert); only 1 worker safe on t2.micro |
| Tesseract OCR (local) | 5.5.2 | Local dev machine | 3–5× faster than v3; used for 12-worker local approach |
| MariaDB | 10.2.38 | EC2 t2.micro | Socket-auth only for `cert_user` |
| Python venv | pymysql 1.1.2 | `/tmp/ocr_venv` | Required for local OCR script DB writes |
| AWS SDK (PHP) | via Composer | `/var/www/html/verify/vendor/` | Required for S3 downloads in PHP scripts |

---

## Incidents & Post-Mortems

### Feb 2026 — OOM Crash (4 Tesseract Workers on t2.micro)
- **What happened:** Launched 4 parallel PHP OCR workers on the EC2 t2.micro; instance ran out of memory, MariaDB crashed, all prepared statements became invalid.
- **Root cause:** 4× PHP (~64 MB each) + 4× Tesseract (~150 MB each) + MariaDB (~300 MB) + Apache exceeded 970 MB total RAM.
- **Fix:** `aws ec2 reboot-instances --instance-ids i-054376b6d8751b8cb --region us-west-2`. Added `ping(reconnect=True)` before each DB write to survive connection drops.
- **Prevention:** Hard rule — never run more than 1 Tesseract worker on the t2.micro. Switched to local 8-worker approach on dev machine instead.

### Feb 2026 — MariaDB Connection Timeout During OCR
- **What happened:** PHP OCR script's DB connection silently timed out while Tesseract was processing (2+ second pause per cert), causing `Error while sending STMT_EXECUTE packet` on write.
- **Root cause:** MySQL `wait_timeout` expired during long Tesseract calls.
- **Fix:** Added `$conn->ping()` with reconnect logic inside every `dbUpdate()` call before executing the write.
- **Prevention:** Always ping/reconnect before writes in any long-running batch script with pauses between operations.

### Feb 2026 — `pkill -f` Killed SSH Session
- **What happened:** Running `ssh ... 'pkill -f enrich_certs_ocr.php'` over SSH terminated the SSH session itself.
- **Root cause:** `pkill -f` matches against the full command line of all processes. The bash process running the SSH command had the pattern string in its command line.
- **Fix:** Used `kill <PID>` instead.
- **Prevention:** Never use `pkill -f <pattern>` over SSH when the pattern string could appear anywhere in the SSH command itself. Always use `kill <PID>`.

---

## Operations Quick Reference

```bash
# Check MariaDB health
sudo systemctl status mariadb

# Test DB connection
mysql -u cert_user -p[Stored in Vaultwarden: APF MariaDB] apf_certificates -e "SELECT COUNT(*) FROM certificate_registry;"

# Test lookup
cd /var/www/html/verify && php test_lookup.php 1117334

# Enrichment status
mysql -u cert_user -p[Stored in Vaultwarden: APF MariaDB] apf_certificates -e "
  SELECT
    SUM(first_name IS NOT NULL) AS enriched,
    SUM(first_name IS NULL AND s3_key IS NOT NULL) AS remaining
  FROM certificate_registry;"

# Weekly backup
mysqldump -u cert_user -p[Stored in Vaultwarden: APF MariaDB] apf_certificates | gzip \
  > /tmp/cert_registry_$(date +%Y%m%d).sql.gz
aws s3 cp /tmp/cert_registry_$(date +%Y%m%d).sql.gz \
  s3://apf-migration-backups-2026/registry-backups/
```

## Rollback Options

| Scenario | Action |
|----------|--------|
| App issue | `cp index.php.backup-20260204 index.php` |
| DB corruption | Drop/recreate table, re-run `import_all_certificates.php` (~30 min) |
| Complete rebuild | Install MariaDB, restore dump, copy app files (~2–3 hours) |
