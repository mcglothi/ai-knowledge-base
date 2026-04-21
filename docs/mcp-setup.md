# MCP Server Setup
**Last Updated:** 2026-04-21
GitHub MCP server gives agents direct repo access — useful without a local AIKB clone.

## Prerequisites
Node.js 18+ · `npx` available · GitHub PAT with `repo` scope

## Step 1 — Create GitHub PAT
GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
- Name: `AIKB MCP Token` · Expiry: 1 year
- Repository access: only `your-username/AIKB`
- Permissions: Contents → Read and write

Store in secrets manager: `[Stored in YourSecretsManager: PAT/GitHub/AIKB MCP Token]`
```bash
echo "your_token_here" > ~/.aikb_token && chmod 600 ~/.aikb_token
```

## Step 2 — Add to Claude Code
```bash
claude mcp add github-aikb \
  -e GITHUB_TOKEN=$(cat ~/.aikb_token) \
  -- npx -y @modelcontextprotocol/server-github
claude mcp list  # verify
```

## Step 3 — Add to Gemini CLI
```bash
gemini mcp add github-aikb \
  -e GITHUB_TOKEN=$(cat ~/.aikb_token) \
  -- npx -y @modelcontextprotocol/server-github
```

## Step 4 — Verify
Start a session and ask: "Read README.md from my AIKB repo (your-username/AIKB)."

## Security
- Fine-grained PAT scoped to AIKB repo only. Never classic tokens with broad `repo` scope.
- `~/.aikb_token` excluded by `.gitignore`. Never commit it.
- Rotate token if exposed. Set calendar reminder for expiry.

## MCP Auto-Discovery
Registry at `_tools/mcp-registry.yaml`. When agent writes an environmental fact (e.g. "org uses PagerDuty"), it checks registry for a matching MCP server.
On match: mention in conversation + log to `_pending_approvals.md` (type: mcp-discovery, priority: low).
`status: wanted` entries = tools with no MCP server yet, tracked as ecosystem gaps.
Add entries:
```yaml
- keywords: ["MyTool", "mytool.io"]
  mcp_name: "mytool-mcp"
  install: "npm install mytool-mcp"
  capabilities: [what it can do]
  status: community
```

## Revoke
GitHub → Settings → Developer settings → Personal access tokens → delete `AIKB MCP Token` → generate new → reconfigure.

## Troubleshooting
- "Permission denied" → PAT needs Contents read/write on AIKB repo.
- "Repository not found" → confirm repo name and PAT access.
- MCP not starting → `node --version` (need 18+) · try `npx @modelcontextprotocol/server-github` manually.
- Can read but not write → PAT missing write permission.
