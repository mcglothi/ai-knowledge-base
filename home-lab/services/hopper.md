---
context: personal-homelab
tags: [hopper, gb10, gigabyte-ai-top-atom, local-llm, nvidia, home-lab, llama-server]
hosts: [hopper]
last_updated: 2026-04-27
---

# Hopper — GB10 Sidecar
**Last Updated:** 2026-04-27
**Summary:** Gigabyte AI Top Atom sidecar dedicated to local LLM inference. Following the Phase 2 migration, all agent services and UI wrappers have been moved to Turing. Hopper now serves only as a high-performance compute node.

**Host:** hopper
**IP:** 10.10.10.200

## Current State (Inference-Only)
- Host reachable on LAN as `hopper.home.timmcg.net` (`10.10.10.200`).
- GPU visible via `nvidia-smi` as `NVIDIA GB10` with driver `580.142` and CUDA `13.0`.
- **llama-server-gemma431.service:** Primary inference lane running `gemma-4-31b-dense-q8-llamacpp` on `http://10.10.10.200:8012/v1`.
- **node-exporter:** Monitoring metrics available on `http://10.10.10.200:9100/metrics`.
- **Ollama:** Container still present but idling (no models resident) to free GPU for native `llama.cpp` lanes.

## Migrated Services (Moved to Turing)
- **Open WebUI:** Formerly on `:8081`, now running on Turing as a Dockge stack (`:3002`).
- **Hermes Agent:** Formerly a user systemd service, now running on Turing as a Dockge stack (`:9119`, `:8642`).
- **MCPO Bridges:** `aikb-memory-mcpo` and `github-aikb-mcpo` moved to Turing.
- **NemoClaw:** Sandbox execution moved to OpenShell cluster on Turing.

## Native llama.cpp Lane
- **Model:** `gemma-4-31b-dense-q8-llamacpp`
- **Endpoint:** `http://10.10.10.200:8012/v1`
- **Config:** `--n_gpu_layers -1`, `--n_ctx 32768`, `--flash_attn True`, `--cache True`
- **Status:** Primary backend for Open WebUI and Hermes.

---

## Deployment History
- **2026-04-27:** Phase 2 Migration complete. Hopper decommissioned as a service host; remains inference compute only.
- **2026-04-24:** Gema 4 31B Dense Q8 cutover via rebuilt native `llama-cpp-python` with CUDA 13.0 support.
- **2026-04-21:** Initial native `llama.cpp` lane setup for Qwen 3.6 for Hermes.
