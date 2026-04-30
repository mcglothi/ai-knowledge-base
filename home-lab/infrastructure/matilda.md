---
context: personal-homelab
tags: [matilda, laptop, dell-precision, rtx-2000, kate]
last_updated: 2026-04-24
---

# Machine Profile: Matilda

**Last Updated:** 2026-04-24
**Summary:** Dell Precision laptop (model 15/17), Kate's machine. NVIDIA RTX 2000 mobile (8GB VRAM) — capable of running 4-bit 7B-class local models.

---

## Identity

| Field | Value |
|-------|-------|
| Hostname | `matilda` (TBD — assign on network) |
| Owner | Kate |
| Form factor | Dell Precision (model 15 or 17) |
| GPU | NVIDIA RTX 2000 Mobile (8GB VRAM) |
| System RAM | 32 GB |
| Role | Portable workstation / local-LLM inference node |

---

## GPU Notes

**NVIDIA RTX 2000 Mobile (8GB VRAM)** — Ada Lovelace architecture, workstation-class.

- **4-bit 7B models:** ~4.5GB weights → leaves ~3.5GB for KV cache (~4K context comfortably)
  - Qwen 2.5 Coder 7B Q4_K_M — recommended pick
  - Mistral 7B variants
- **4-bit 3B models:** ~2GB weights → leaves ~6GB for context (10K+ tokens)
  - Qwen 2.5 3B, Llama 3.2 3B — fast inference
- **9B models at 4-bit:** ~6GB weights → tight, short context only
  - Gemma 2 9B Q4_K_M — edge case, may swap to CPU

**Not feasible on this GPU:**
- 13B+ models even at 4-bit (will OOM or swap)
- Any model at FP16 (weights alone exceed VRAM)

---

## Notes

- System RAM (32GB) is sufficient for most local model workflows — the GPU VRAM is the bottleneck, not system memory.
- When this machine comes online on the home network, assign a static IP and add to `servers.md`.
