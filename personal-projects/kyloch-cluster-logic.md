---
context: personal
---
# Kyloch Phase 1.5: Heterogeneous Cluster Logic
**Status:** Technical Design
**Last Updated:** 2026-03-21

## The "Split-Phase" Inference Strategy
- **Node A (DGX Spark / CUDA):** **Prefill (PP) Specialist.**
  - Handles the compute-heavy "reading" of large prompts/AIKB docs.
  - Generates the initial KV Cache at high TFLOPS.
- **Node B (Mac M5 Max / Unified Memory):** **Decode (TG) Specialist.**
  - Receives the KV Cache over 10GbE/25GbE.
  - Handles token generation at high memory bandwidth (400GB/s+).

## The KV Cache Bottleneck Mitigation
- **Avoid "Double Quantization":** Keep KV Cache at FP16 or FP8 to prevent accuracy "cliffs" in RAG/Memory tasks.
- **Prompt Caching (Prefix Caching):** Pre-compute and pin static context (System Prompt + AIKB Index) on both nodes to minimize delta transfer.
- **Network Goal:** 25GbE Thunderbolt-to-QSFP adapter to bring 10GB cache transfer under 4 seconds.

## Resident Model Allocation (The "Model Zoo")
| Model | Tier | Location | RAM/VRAM |
| :--- | :--- | :--- | :--- |
| **Whisper (STT)** | Real-time | Spark (CUDA) | 2GB |
| **Phi-4 (Router)** | Always-on | Spark (VRAM) | 10GB |
| **Llama-70B (Expert)** | Deep-thought | Mac (Unified) | 42GB |
| **Qwen-32B (Coder)** | Specialist | Spark (VRAM) | 20GB |

## Scaling Path (The "Fabric" Transition)
1. **Queue-based Tasking:** Implement Redis-backed tasking between nodes (Spark -> Queue -> Mac).
2. **LoRA Fine-tuning:** Nightly "Dreaming" phase where Kyloch fine-tunes on the day's interactions to improve personal alignment.
3. **Identity-as-a-Service:** Host local, air-gapped inference for B2B/Legal/Medical workloads to fund hardware expansion.
