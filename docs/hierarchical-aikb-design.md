# Hierarchical AI Knowledge Base (AIKB) Design

## 1. Core Concept: Engine vs. Store Separation

Currently, the AIKB bundles the "Engine" (`_tools`, `_templates`, `_agents`) with the "Store" (the `.md` knowledge files, `_runtime/`, `_state.yaml`). 

To make this hierarchical and modular, we must **decouple the Engine from the Store**.

*   **Global Engine (Installed Once):** The tools and templates are installed in a central location (e.g., `~/.aikb/core/` or `/usr/local/aikb/`).
*   **Local Stores (Installed Everywhere):** A user creates a "Local Store" by dropping a marker file (e.g., `.aikb-root` or just initializing `_runtime/` and `_state.yaml`) into any directory (e.g., `~/work/` or `~/personal/project-a/`).

## 2. Context Bubbling (The "Nearest Scope" Principle)

When an agent (like Gemini CLI) is launched inside a subdirectory (e.g., `~/work/project-a/src/`), the system needs to know which AIKB to use.

1.  **Upward Discovery:** The AIKB CLI wrapper walks *up* the directory tree from `$PWD`.
2.  **Binding:** The first directory it finds containing `.aikb-root` becomes the active `$AIKB_ROOT`.
3.  **Isolation:** The agent only has access to the `$AIKB_ROOT` and its children. It does not know about sibling or parent AIKBs.

This guarantees that an agent launched in `~/personal/` won't hallucinate work-related server IPs, and vice-versa.

## 3. The Union View (The "Parent Sees All" Principle)

If a user installs an AIKB at `~/` (Parent) and also has AIKBs at `~/work/` and `~/personal/` (Children), the Parent should be able to query the Children.

We modify the semantic indexer (`_tools/aikb-search/indexer.py`) and search tools to handle this:

1.  **Boundary Detection:** When the indexer walks the filesystem (e.g., using `rglob`), if it encounters a directory with its own `.aikb-root`, it stops recursing into it *by default* to maintain isolation.
2.  **Aggregation Mode:** If the indexer is run from the Parent AIKB (or with a `--recursive` flag), it continues into the Child AIKBs.
3.  **Scope Tagging:** When indexing a Child AIKB from the Parent, the indexer automatically prepends a scope tag (e.g., `[work]` or `[personal]`) to the chunks based on the subdirectory name. 
4.  **Result:** When you search from the Parent, you get results from everywhere, clearly labeled by their origin.

## 4. Addressing Redundancy

By decoupling the Engine, a Local AIKB directory drops from containing dozens of files down to just:

```text
~/work/
├── .aikb-root       # The marker file
├── _index.md        # Local domain overview
├── _state.yaml      # Local incident/status tracking
└── _runtime/        # Local event logs and memories
```

No more copied Python scripts, shell hooks, or template markdown files. 

## 5. Implementation Steps

1.  **The Wrapper Script:** Create a global `aikb` bash script that implements the "walk up and find `.aikb-root`" logic and exports `$AIKB_ROOT`.
2.  **Path Updates:** Update all Python scripts in `_tools/` to read `os.environ.get("AIKB_ROOT")` instead of hardcoding `Path(__file__).parents[2]`.
3.  **Indexer Update:** Update `indexer.py`'s `rglob` logic to respect `.aikb-root` boundaries, and add the `--recursive` flag for the Parent union view.
4.  **Agent Context:** Update the `wake-up` scripts and `GEMINI.md` instructions to inform the agent of its current bounded scope.
