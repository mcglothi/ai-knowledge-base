---
context: personal
---
# Goose-AIKB Integration

**Status:** 🔬 Researching
**Owner:** Kyloch / mcglothi
**Tags:** goose, aikb, mcp, automation, orchestration, recipes

## Overview
Integration of the **Goose AI Agent** (goose-docs.ai) into the AIKB ecosystem. The goal is to leverage Goose's native MCP support and "Recipes" to automate AIKB maintenance and cross-service orchestration.

## Objectives
- [ ] **MCP Bridge:** Expose AIKB core tools (`aikb_search`, `runtime_cli.py`) as an MCP server for Goose.
- [ ] **Standard Recipes:** Create Goose Recipes for `wake-up`, `closeout`, and `compression` workflows.
- [ ] **Local Execution:** Configure Goose to use `Hopper` (Ollama) for low-latency/private AIKB maintenance tasks.
- [ ] **Identity Alignment:** Align Goose's persona with `DAIDENTITY.md` and your existing agent voice.

## Workflow Integration
- **Platform:** Run Goose on `Newton` (MacBook Pro workstation).
- **Model Routing:** 
  - Local tasks (Hopper/Ollama) for tagging and linting.
  - Frontier tasks (Claude/Gemini) for complex synthesis and roadmap updates.

## Next Steps
1. [ ] Install Goose on Newton.
2. [ ] Prototype a YAML Recipe for the AIKB `wake-up` ritual.
3. [ ] Research Goose's MCP server configuration to bridge with existing Python scripts.

## Related
- [`personal-projects/project-kyloch.md`](project-kyloch.md)
- [`home-lab/infrastructure/mcp-management.md`](../home-lab/infrastructure/mcp-management.md)
- [`AGENTS.md`](../AGENTS.md)
