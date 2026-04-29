# AIKB Adapter: Microsoft Copilot Studio (Scaffold)

Status: scaffold

This directory is reserved for the Microsoft Copilot Studio adapter.

Planned facade endpoints:
- POST /copilot/remember
- POST /copilot/recall
- POST /copilot/context-pack
- POST /copilot/feedback (optional)

Notes:
- Keep translation layer thin (map directly to AIKB core primitives)
- Keep enterprise controls reusable where possible (tenant scope, PII hooks, audit)
