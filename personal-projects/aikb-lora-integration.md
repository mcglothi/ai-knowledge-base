---
context: personal
---
# AIKB LoRA Integration
**Last Updated:** 2026-03-25
**Status:** 🔬 Planning
**Summary:** Implementation of a nightly LoRA (Low-Rank Adaptation) fine-tuning pipeline to align local models with AIKB knowledge, now repositioned behind a nightly "dream cycle" that consolidates memory before any training run.

---

## Objective
Enable a "Dreaming" phase for Kyloch/AIKB where nightly memory consolidation produces a clean training candidate set, and LoRA fine-tuning becomes an optional downstream step. This reduces direct training on noisy sessions, keeps RAG authoritative for facts, and improves personal alignment for repeated workflows and defaults.

## Updated Positioning

LoRA is no longer the first nightly memory job.
The order should be:

1. runtime ingest
2. proposal harvest and review
3. nightly dream-cycle consolidation
4. optional LoRA fine-tuning on the dream outputs
5. model packaging and serving

This keeps raw session residue, assistant chatter, and unresolved contradictions out of the adapter dataset.

## Roadmap

### 1. Dream-Cycle Outputs as Training Inputs
- [x] Create `_tools/memory-pipeline/dream_cycle.py`
- [ ] Emit structured daily outputs for facts, procedures, preferences, and rejected/noisy candidates.
- [ ] Add trainability labels: `trainable`, `retrieve_only`, `reject`.
- [ ] Preserve evidence pointers back to runtime events, proposal ids, and canonical file paths.

### 2. Data Generation Pipeline (LoRA Extraction)
- [ ] Create `_tools/memory-pipeline/extract_lora_dataset.py`
- [ ] Convert dream-cycle outputs into task-oriented JSONL records.
- [ ] Implement Markdown-to-QA pair extraction logic only for approved/trainable facts.
- [ ] Implement runbook-to-procedural-instruction extraction.
- [ ] Implement preference/default extraction for stable operator habits.
- [ ] Output standardized `dataset.jsonl`.

### 3. Nightly Fine-tuning (MLX/Unsloth)
- [ ] Setup MLX-based training script on `tesla` (M1 Mac).
- [ ] Setup Unsloth-based training script on `feynman` (NVIDIA GPU).
- [ ] Implement nightly trigger (cron/LaunchAgent).
- [ ] Gate training on minimum dataset quality thresholds from the dream cycle.
- [ ] Monitor VRAM/Unified Memory usage during training.

### 4. Model Lifecycle & Serving
- [ ] Implement automatic merge of LoRA adapters with base model.
- [ ] Automate GGUF quantization (llama.cpp/mlx).
- [ ] Automate Ollama model creation (`ollama create jarvis-aikb`).
- [ ] Implement zero-downtime reload for local agents.

## Implementation Notes
- **Base Models:** qwen2.5:7b, llama3.1:8b.
- **Compute:** Prefer `tesla` for low-power nightly training; use `feynman` for speed/larger models.
- **Persistence:** Store nightly adapters in `_runtime/lora/adapters/`.
- **Authority boundary:** AIKB markdown + Memory Core retrieval remain the source of truth. LoRA should bias defaults, phrasing, routing, and repeated procedures, not replace retrieval for current facts.
- **Safety boundary:** Never train directly on `new` proposals, raw runtime events, or unresolved contradictions.

## Recommended First Slice

Before any training code lands, build the dream-cycle MVP:

- read runtime events for the last 24 hours
- read Memory Core proposals grouped by status
- read canonical AIKB diffs for the same window
- emit a markdown dream summary plus structured JSONL outputs
- score the day on quality: noise rejected, contradictions found, trainable examples produced

If that output looks clean for several nights in a row, then add `extract_lora_dataset.py` and start with a small MLX adapter run on `tesla`.
