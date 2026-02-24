# My Project

**Last Updated:** YYYY-MM-DD
**Summary:** [What this project is and its current status — answer "what is this and is it live?" in one sentence.]

> **This is an example project file.** Copy it to `projects/your-project.md` and replace with real content.
> Add a row to `_index.md` once filled in.

---

## Overview

[What the project does, who uses it, why it exists.]

**Stack:** [e.g. Python / FastAPI / PostgreSQL / Docker]
**Repo:** [e.g. `github.com/yourname/myproject`]
**Live at:** [URL if deployed]

---

## Access

```bash
# Clone
git clone https://github.com/yourname/myproject.git

# Run locally
cd myproject
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Credentials:**
- API key: `[Stored in YourSecretsManager: Projects/MyProject/API Key]`
- Database: `[Stored in YourSecretsManager: Projects/MyProject/DB Password]`

---

## Current State

- ✅ Core API endpoints working
- ✅ Deployed to production
- ⬜ Add rate limiting
- ⬜ Write integration tests
- ⚠️ Database connection pooling needs tuning under load

---

## Architecture

[Brief architecture description or diagram if useful.]

```
Client → Nginx → FastAPI → PostgreSQL
                         → Redis (cache)
```

---

## Environment

```bash
# Required environment variables
DATABASE_URL=postgresql://user:pass@localhost/mydb
REDIS_URL=redis://localhost:6379
SECRET_KEY=[Stored in YourSecretsManager: Projects/MyProject/Secret Key]
```

---

## Deployment

```bash
# Deploy via Docker Compose
docker compose -f docker-compose.prod.yml up -d
```

Hosted on: [e.g. a DigitalOcean Droplet / AWS EC2 t3.micro / Raspberry Pi]

---

## Gotchas & Pitfalls

- **Pydantic v2 breaking change:** `orm_mode` is now `model_config = ConfigDict(from_attributes=True)`. Don't use the old syntax.
- **PostgreSQL connection limit:** default is 100 connections; the app uses connection pooling (pool_size=5). Don't increase pool_size without checking the DB max_connections first.

---

## Outstanding Tasks

- [ ] Add rate limiting (token bucket, per IP)
- [ ] Write integration test suite
- [ ] Set up GitHub Actions CI

---

## Post-Mortems

### YYYY-MM-DD — Database connection exhaustion
- **What happened:** Prod went down, all DB connections used up
- **Root cause:** Missing connection pool configuration — app opened a new connection per request
- **Fix:** Added SQLAlchemy connection pooling with `pool_size=5, max_overflow=10`
- **Prevention:** Monitor active connections in Grafana; alert at 80% of max
