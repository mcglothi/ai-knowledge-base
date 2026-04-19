# MCP Server Setup

**Last Updated:** 2026-04-19
**Summary:** How to configure MCP servers for AIKB, including the GitHub MCP for remote access and the auto-discovery loop that surfaces new MCP opportunities as you document your environment.

---

## What the MCP server does

The GitHub MCP server (`@modelcontextprotocol/server-github`) gives agents direct access to a GitHub repo via API. With it configured, an agent can:
- Read any file in your AIKB repo
- Create and update files (each write becomes a commit)
- Search across files

This is useful when you're on a machine without a local AIKB clone — a cloud IDE, a new laptop, a friend's machine, etc.

---

## Prerequisites

- Node.js 18+ and `npx` available
- A GitHub Personal Access Token (PAT) with `repo` scope
- Claude Code or Gemini CLI installed

---

## Step 1 — Create a GitHub PAT

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click **Generate new token**
3. Set:
   - **Token name:** `AIKB MCP Token`
   - **Expiration:** 1 year (or your preference)
   - **Repository access:** Only select `your-username/AIKB`
   - **Permissions:** Contents → Read and write
4. Click **Generate token** and copy it immediately

**Store the token in your secrets manager** — you won't be able to see it again.

```
[Stored in YourSecretsManager: PAT/GitHub/AIKB MCP Token]
```

Then save a local copy for MCP server use (this file is not committed — see `.gitignore`):
```bash
echo "your_token_here" > ~/.aikb_token
chmod 600 ~/.aikb_token
```

Alternatively, set it as an environment variable in your shell profile:
```bash
export AIKB_GITHUB_TOKEN="your_token_here"
```

---

## Step 2 — Add the MCP server to Claude Code

```bash
claude mcp add github-aikb \
  -e GITHUB_TOKEN=$(cat ~/.aikb_token) \
  -- npx -y @modelcontextprotocol/server-github
```

Or if using an environment variable:
```bash
claude mcp add github-aikb \
  -e GITHUB_TOKEN="$AIKB_GITHUB_TOKEN" \
  -- npx -y @modelcontextprotocol/server-github
```

Verify it was added:
```bash
claude mcp list
```

---

## Step 3 — Add the MCP server to Gemini CLI

```bash
gemini mcp add github-aikb \
  -e GITHUB_TOKEN=$(cat ~/.aikb_token) \
  -- npx -y @modelcontextprotocol/server-github
```

---

## Step 4 — Verify the connection

Start a new Claude Code or Gemini CLI session and ask:
```
Read the file README.md from my AIKB repo (your-username/AIKB).
```

The agent should read and display the file contents.

---

## Security considerations

- **PAT scope:** Use fine-grained tokens scoped to only the AIKB repo with Contents read/write. Avoid classic tokens with broad `repo` scope.
- **Token storage:** `~/.aikb_token` is excluded by `.gitignore`. Never commit it. Never set `GITHUB_TOKEN` system-wide in a shared environment.
- **Token rotation:** Rotate the token if it's ever exposed. GitHub will also notify you of leaked tokens if they appear in a public repo.
- **Expiry:** Set token expiry to match your rotation cadence. A calendar reminder is useful.

---

---

## MCP auto-discovery

AIKB includes a registry of known MCP servers at `_tools/mcp-registry.yaml`. When an agent writes an environmental fact about a tool or platform — "org uses PagerDuty for alerting", "we use Infoblox for IPAM" — it checks the registry for a matching MCP server.

**When a match is found**, the agent:
1. Mentions it in conversation: *"Noted. There's an MCP server for PagerDuty — want me to add it to your setup?"*
2. Logs a low-priority item to `_pending_approvals.md` so it's not forgotten if you're mid-task

**Example approval entry:**
```
| 2026-04-19 | Claude Code | env discovery | pagerduty-mcp available — org uses PagerDuty for alerting | mcp-discovery | pending |
```

**Trigger conditions** — agents check the registry when:
- Writing a new environmental fact to any AIKB file
- You ask: *"are there any MCP servers we should be using?"*
- Wake-up surfaces a tool mention in `_state.yaml` or `_index.md` without a matching configured MCP

**No duplicate suggestions** — agents skip tools already listed in your MCP configuration.

### Registry entries marked `wanted`

Some registry entries have `status: wanted` — these are tools where no MCP server exists yet, but one would be useful. They're tracked as ecosystem gaps. If you build one, submit it upstream.

### Adding entries to the registry

```yaml
- keywords: ["MyTool", "mytool.io"]
  mcp_name: "mytool-mcp"
  install: "npm install mytool-mcp"
  capabilities:
    - what the MCP can do
  status: community
```

Contributions to `_tools/mcp-registry.yaml` that are tool-agnostic belong in the public template at `mcglothi/ai-knowledge-base`.

---

## Revoking access

If your token is compromised:
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Find and delete the `AIKB MCP Token`
3. Generate a new one and reconfigure

---

## Troubleshooting

**"Permission denied" errors**
→ Check that the PAT has Contents read/write on the AIKB repo specifically.

**"Repository not found"**
→ Confirm the repo name and that the PAT has access to it. The repo must be the one the agent was configured to access.

**MCP server not starting**
→ Ensure Node.js 18+ is installed: `node --version`. Try running the server manually: `npx @modelcontextprotocol/server-github`

**Agent can read but not write**
→ Check the PAT permissions — write access requires Contents → Read and write (not just Read).
