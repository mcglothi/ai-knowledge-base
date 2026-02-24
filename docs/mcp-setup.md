# MCP Server Setup

**Summary:** How to configure the GitHub MCP server so AI agents can read and write AIKB without a local clone.

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
