---
tags: [newton, jarvis, local-llm, model-routing, ollama, llama.cpp, mlx, voice, monetization, ai-top-atom, spark]
status: active
last_updated: 2026-04-22
---

# Newton Model Strategy
**Last Updated:** 2026-04-22
**Summary:** Active Newton-era local model portfolio for a 128 GB unified-memory Apple Silicon workstation, paired with `hopper` (Gigabyte AI Top Atom) as the primary always-on sidecar. Direction: use a routed fleet of Gemma 4 and Qwen 3.6 specialists, with AI Hub as the control plane and AIKB as the memory layer.

## Current State (2026-04-22)
- **Newton:** MBP M1 Max (128 GB) is fully docked with 140W PD and 10G networking via OWC/Sonnet stack. Acting as the primary Control Plane and Synthesis host.
- **Hopper:** Gigabyte AI Top Atom (GB10) is active as the high-throughput sidecar.
- **Interconnect:** Newton and Hopper are linked via Tailscale and local 10G/200G paths (optics pending for full 200G link).
- **Model Portfolio:** Transitioned from Gemma 3 / Qwen 3 to Gemma 4 and Qwen 3.6 as the new performance baseline.

## Core Decision
Newton is a **model host + router + eval lab**:
- one fast always-on orchestrator
- one coding specialist
- one strong general reasoning / research model
- one retrieval stack (embedding + reranker)
- one voice stack (STT + TTS)
- optional heavyweight long-context / multimodal lane for special jobs

## Recommended Model Lanes (v2 - April 2026)

### 1) Orchestrator / Fast Daily Driver
Primary target:
- `Gemma-4-e4b` (MoE) or `Phi-4-mini-instruct`

Use for:
- intent classification, first-pass planning, tool argument shaping.

### 2) Coding Specialist
Primary target:
- `Qwen-3.6-Coder-35B-A3B-Instruct` (MoE)

Use for:
- repo understanding, code edits, refactors, PR drafting.

### 3) General Research / Reasoning Specialist
Primary target:
- `Gemma-4-31b` or `Gemma-4-26b-a4b` (MoE)

Use for:
- synthesis across notes, research memos, AIKB-grounded briefings.

### 4) Retrieval Stack
Primary targets:
- `Qwen-3.6-Embedding-4B`
- `Qwen-3.6-Reranker-4B`

### 5) Voice (STT/TTS)
Primary target:
- `Whisper-v4-turbo` (if available) or `Whisper-large-v3-turbo`
- `Qwen-3.6-Audio-Chat` for native audio reasoning.

## Build Progress
- [x] Hardware Docking (Newton)
- [x] Hardware Bring-up (Hopper)
- [x] Initial Benchmark Harness (Locked 2026-04-22)
- [ ] Final Routed Model Portfolio Lock
- [ ] AI Hub v2 Routing Logic Integration

## Runtime Split
- `Ollama`: default operator-facing runtime and API surface; easiest AI Hub integration.
- `llama.cpp`: best path for hand-tuned GGUF quantized inference and benchmark discipline.
- `MLX / mlx-lm`: Apple-native lane for models that perform especially well in MLX form on Apple Silicon.
- `LM Studio`: comparison lab and quick compatibility check, not the canonical automation runtime.

## If A Spark-Class Sidecar Is Added
Adding a Spark-class sidecar such as the purchased `Gigabyte AI Top Atom` changes the system from a **single-node routed workstation** into a **two-node heterogeneous fabric**.

The main shift:
- `Newton` becomes the control plane, memory plane, and "deep work" box.
- `Spark` becomes the fast CUDA sidecar for always-on conversational work, batch throughput, and CUDA-native experiments.

### Revised Role Split
**Newton**
- AI Hub UI and operator console
- AIKB retrieval, reranking, and memory promotion
- long-context reasoning
- coding specialist lane
- slower high-value synthesis jobs
- canonical eval runner and model registry

**Spark**
- low-latency voice loop
- wake / interrupt / VAD / streaming orchestration
- fast agent handoff layer
- CUDA-native coder / research workers when throughput matters
- embeddings / reranking experiments that benefit from GPU batching
- background queues, summarization batches, and asynchronous workers

### Recommended Model Layout In A Two-Node System
Keep the "brains" distributed by role, not by naive model sharding.

**Resident on Spark**
- orchestrator / planner
- fast voice-facing model
- STT runtime
- optional fast coder worker for short code turns
- async batch workers

**Resident on Newton**
- primary coding specialist
- primary research/synthesis model
- retrieval stack tied closely to AIKB
- premium TTS lane
- heavyweight / long-context lane

### Flow Change
Without Spark:
`voice/text input -> Newton router -> model -> tools/memory -> response`

With Spark:
`voice/text input -> Spark front-door -> cheap local decision`

Then one of three routes:
1. `Spark handles it fully`
   Fast conversational turns, quick commands, simple voice replies, short summaries.
2. `Spark enriches then forwards to Newton`
   Best for coding, AIKB-grounded research, long reasoning, and anything needing local memory/state.
3. `Spark runs async side work while Newton handles primary answer`
   Best for prefetch, indexing, background summarization, repo scans, and proactive jobs.

### Best Practical Pattern
Do **not** start with split inference of one prompt across both machines.

Start with:
- **role-specialized routing**
- **background job queues**
- **speculative prefetch**
- **optional prefill/decode experiments only after baseline value is proven**

This keeps the architecture useful even if interconnect performance is only "good enough" rather than amazing.

### Day-0 Bring-Up Bias For The AI Top Atom
Before the broader two-node design is attempted, the sidecar should earn trust with a very small first scope:
- stable power and network
- remote shell access
- one known-good local model runtime
- one simple health signal / heartbeat
- no required dependency on it for Newton day-to-day work yet

If it can stay online cleanly during the Texas trip window, it graduates from "new hardware" to "trusted always-on agent foothold."

### Service Layout Change
Single-node services become:
1. `router-edge` on Spark
   Handles ingress, voice session state, fast routing, and cheap-first policy.
2. `router-core` on Newton
   Handles deep routing, memory-aware decisions, approvals, and high-value escalations.
3. `job-queue`
   Shared queue for async work, summaries, repo scans, benchmark jobs, and proactive tasks.
4. `model-registry`
   Must now track `host`, `runtime`, `warm_state`, `queue_affinity`, and measured handoff latency.
5. `telemetry`
   Must track per-host latency, network overhead, and whether Spark saved time or just added hops.

### What Improves Immediately
- voice latency
- concurrency
- background task throughput
- ability to keep a fast model hot without competing with big Newton jobs
- room to experiment with CUDA-native stacks without destabilizing the main workstation

### What Gets More Complex
- scheduling and queueing
- network transport and retry logic
- memory/source consistency between hosts
- benchmark discipline
- operational complexity if you try split-inference too early

### Recommendation
If you add Spark, treat it first as:
- a **front-of-house low-latency node**
- an **async worker pool**
- a **CUDA experiment box**

Do **not** make it the canonical memory/control plane.

Newton should remain the trusted center of gravity because that is where your operator console, AIKB grounding, coding context, and monetizable workflow logic naturally live.

## How Valuable A Second Spark Would Be
Short version: **moderately valuable for concurrency and experimentation, highly valuable only if your workflow becomes genuinely multi-agent or very-large-model centric.**

### Where A Second Spark Is Worth Real Money
- running several agent workers at once without fighting for the same device
- local batch jobs: summarization queues, indexing, eval sweeps, transcript processing
- CUDA-native coding/research workers in parallel with a separate voice/front-door stack
- larger-model experiments that exceed the comfort zone of a single Spark
- proving out TensorRT-LLM / vLLM / SGLang distributed layouts before bigger hardware buys

### Where It Is Less Valuable Than It Sounds
- single-user interactive coding if Newton is already your main coding box
- AIKB-grounded research flows that are bottlenecked more by retrieval/tooling than raw token generation
- simple voice assistant use where one Spark already keeps the edge stack hot
- naive "cluster two boxes so everything gets twice as fast" expectations

### Practical Read
For your workflow, the second Spark is **not** the next best dollar before the first Spark proves useful.

After one Spark exists, the second Spark becomes attractive if one of these is true:
1. you routinely want voice + coding + background jobs all running at once
2. you want a dedicated always-hot worker pool for asynchronous monetizable jobs
3. you are actively testing distributed inference / fine-tuning as a strategic capability
4. you need larger CUDA-native model capacity than one Spark comfortably provides

### What The 200G Link Actually Changes
The 200 Gb/s ConnectX-7 link makes a two-Spark setup much more credible than normal homelab Ethernet clustering for:
- tensor-parallel larger-model inference
- distributed fine-tuning
- fast inter-node collectives
- lower-overhead multi-node experiments

But it does **not** erase all distributed-inference costs.

Even NVIDIA’s own guidance says scaling is best when inter-node communication is minimized, and less efficient when workloads require frequent layer-by-layer synchronization. So the 200G link is most valuable when it lets you do:
- bigger models
- more concurrent workers
- better TPOT on supported distributed stacks

It is less magical for:
- lots of tiny chat requests
- retrieval-heavy workflows
- anything dominated by tools, I/O, or human think time

### My Recommendation
- `Newton only`: highest value per dollar at the start
- `Newton + 1 Spark`: strongest next step for real workflow improvement
- `Newton + 2 Sparks`: worth it when you are intentionally building a local multi-agent service fabric, not just a better personal chatbot

If the goal is daily personal leverage, the second Spark is a **phase-2 multiplier**.
If the goal is building a revenue-producing local AI platform with concurrency, job queues, and service tiers, the second Spark becomes much more defensible.

## Service Topology
Use AI Hub as the user-facing control plane and build a thin local router service behind it.

Recommended services:
1. `router-api`
   Routes prompts by task, latency budget, privacy level, and confidence.
2. `model-registry`
   Tracks installed models, quantization, runtime, warm/cold status, benchmark notes.
3. `eval-runner`
   Replays standard tasks and records quality/latency/cost metrics.
4. `memory-retrieval`
   Embedding + reranker + chunking for AIKB and repo data.
5. `voice-gateway`
   Streaming STT, interruption handling, TTS output, wake-mode policies.
6. `usage-meter`
   Per-lane token/time/job accounting so the stack can become billable, not just cool.

## Routing Policy v1
- Default to local.
- Start every request in a cheap lane.
- Escalate only on evidence:
  - code task -> coding specialist
  - long synthesis / research -> research specialist
  - retrieval-heavy query -> retrieval + reasoning pair
  - voice -> STT + orchestrator + optional specialist + TTS
  - giant context / multimodal -> heavyweight lane
- Frontier API fallback stays available for high-value misses, but must be explicit and logged.

## Quantization / Sizing Heuristic
- Resident models: 0.6B to 8B
- Daily specialists: 12B to 30B class, preferably MoE where quality-per-active-parameter is strong
- Heavy lane: only one at a time, loaded intentionally

The practical Newton goal is not "largest model that fits." The goal is:
- 1 instant lane
- 2 dependable specialist lanes
- retrieval always available
- voice always available
- one optional power lane

## Revenue-Oriented Scaffolding
The first money-making version should sell **repeatable outcomes**, not generic chat.

Best initial productizable lanes:
1. Coding copilot for your own consulting/client work
   - repo intake
   - bug triage
   - patch drafting
   - changelog / PR / deployment notes
2. Research briefings
   - compare tools/vendors
   - summarize docs and transcripts
   - generate operator-facing recommendations
3. Voice ops assistant
   - home-lab briefings
   - mobile/desk voice command center
   - personal productivity flows
4. AIKB-backed knowledge worker
   - project memory
   - status briefs
   - decision logs
   - client-context recall

These are much closer to a job-replacement engine than a single chat box because they create:
- saved time
- reusable workflows
- audit trails
- service tiers

## Build Order
### Phase A — Before Newton arrives
- Finalize benchmark matrix for orchestrator / coder / research / voice / retrieval lanes.
- Add AI Hub concept of `task_type` and `route_reason`.
- Define a canonical local model registry file.

### Phase B — Newton week one
- Install runtimes: `Ollama`, `llama.cpp`, `mlx-lm`.
- Load one candidate per lane, not ten.
- Capture latency, throughput, quality notes for your real workflows.

### Phase C — First monetizable system
- Add usage logging and job IDs.
- Add saved workflow templates in AI Hub.
- Add one billing-friendly surface:
  - "briefing run"
  - "repo audit"
  - "research packet"

### Phase D — Replace labor, not just API spend
- Turn your own recurring work into routable jobs first.
- Measure hours saved per week.
- Only then package the best lanes for outside users or clients.

## Initial Candidate Matrix
| Lane | Primary | Backup |
|------|---------|--------|
| Orchestrator | Phi-4-mini-instruct | Gemma 3 4B |
| Coding | Qwen3-Coder-30B-A3B-Instruct | current Qwen coder lane via Ollama until upgraded |
| Research | Mistral-Small-3.1-24B-Instruct | Gemma 3 12B |
| Retrieval | Qwen3-Embedding-4B + Qwen3-Reranker-4B | 0.6B variants for lighter always-on use |
| STT | whisper-large-v3-turbo + faster-whisper | distil-whisper-large-v3 for English-fast mode |
| TTS | Qwen3-TTS 0.6B | Qwen3-TTS 1.7B |
| Heavy lane | Llama 4 Scout | future large local checkpoint after baseline benchmarks |

## Sources
- Gemma 3 model card: https://huggingface.co/google/gemma-3-4b-it
- Gemma 3 model card: https://huggingface.co/google/gemma-3-12b-it
- Phi-4-mini-instruct model card: https://huggingface.co/microsoft/Phi-4-mini-instruct
- Mistral Small 3.1 model card: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
- Qwen3-Coder-30B-A3B-Instruct model card: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct
- Qwen3-Embedding-4B model card: https://huggingface.co/Qwen/Qwen3-Embedding-4B
- Qwen3-Reranker-4B model card: https://huggingface.co/Qwen/Qwen3-Reranker-4B
- Llama 4 Scout model card: https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct
- Whisper large-v3-turbo model card: https://huggingface.co/openai/whisper-large-v3-turbo
- Faster-Whisper README: https://github.com/SYSTRAN/faster-whisper
- Qwen3-TTS README: https://github.com/QwenLM/Qwen3-TTS
