---
context: personal-homelab
tags: [pdf, fosgail, service, babbage, tool]
status: active
last_updated: 2026-04-25
---

# Fosgail (PDF Manipulation)

**Fosgail** is a rebranded fork of Stirling-PDF, providing a complete web-based PDF manipulation suite with enhanced AI features.

## Deployment Details
- **Host:** babbage (10.10.10.10)
- **Container Name:** `fosgail`
- **Port:** 30090
- **URL:** [https://pdf.home.timmcg.net](https://pdf.home.timmcg.net)
- **Source:** `/Users/mcglothi/code/fosgail`
- **Config Path:** `/mnt/Containers/fosgail/configs`

## Features
- **Make Fillable:** Automatically detects visual form fields (text boxes, checkboxes) and overlays interactive AcroForm widgets.
- **Dark Mode:** Built-in theme toggle with a "Rainbow Mode" easter egg (10 rapid clicks).
- **No Auth:** Currently configured with `security.enableLogin: false` for internal use.

## Maintenance
To rebuild and update:
```bash
cd /Users/mcglothi/code/fosgail
rsync -avz --exclude 'node_modules' --exclude '.git' --exclude 'build' --exclude '.gradle' . babbage:/tmp/fosgail-build/
ssh babbage "cd /tmp/fosgail-build && sudo docker build -t fosgail:latest -f docker/embedded/Dockerfile ."
cd /mnt/Containers/fosgail && sudo docker compose up -d
```
