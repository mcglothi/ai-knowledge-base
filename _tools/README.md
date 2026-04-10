# AIKB Intelligence Tools

This directory contains optional scripts to automate the retrieval and structuring of your AI Knowledge Base.

## Tools Overview

### 1. Ambient Context Injection (`ambient_ask.sh`)
This is a lightweight wrapper for your favorite AI CLI tool (e.g., `gemini`, `claude`). It intercept your prompt, scans your AIKB for the top 3 most relevant facts, and injects them silently as an `<ambient_context>` block before launching the agent.

**Usage:**
```bash
./_tools/memory-pipeline/ambient_ask.sh gemini "How do I connect to the production server?"
```

### 2. Temporal Knowledge Graph (`build_temporal_graph.py`)
This script generates a JSON knowledge graph of your entire repository. It extracts entities like IP addresses, hostnames, and tool names, and tracks their relationship to specific files and dates.

**Usage:**
```bash
python3 ./_tools/memory-pipeline/build_temporal_graph.py --out ./_runtime/graphs/my-graph.json
```

### 3. Semantic Search (`memory_search.py`)
A fast, hybrid search tool that combines keyword matching with optional semantic reranking. It is used internally by `ambient_ask.sh` but can be run standalone to find specific sections of your AIKB.

**Usage:**
```bash
python3 ./_tools/memory-pipeline/memory_search.py --query "ssh keys" --limit 5
```

## Advanced Automation (Reference)

For more advanced automation (like LLM-powered triage and auto-merging of facts), see the reference implementation scripts in the internal AIKB repository or adapt the following logic:

- **Auto-Triage:** Use a local model (via Ollama) to score new events and decide if they should be `approved` or `rejected`.
- **Fact Supersession:** Before merging a new fact, search for existing context and determine if the new fact should `replace` or `append` to the existing knowledge.
