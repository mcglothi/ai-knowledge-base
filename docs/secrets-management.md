# Secrets Management

**Summary:** How to integrate AIKB with your secrets manager. AIKB never stores credentials — only references to them.

---

## The pattern

Every credential referenced in AIKB follows this format:

```markdown
[Stored in YourSecretsManager: Hierarchy/Of/Item/Name]
```

This tells a future agent (or human) exactly where to find the credential without exposing it in the repo. When an agent needs a credential, it reads the reference from AIKB and retrieves it from the secrets manager.

---

## Supported integrations

### 1Password

**Retrieve a secret:**
```bash
op read "op://Private/Item Name/field"
# or by UUID:
op read "op://vaultname/itemid/field"
```

**In AIKB files, reference as:**
```
[Stored in 1Password: Private/Service Name/API Key]
```

**Shell profile setup:**
```bash
# Add to ~/.zshrc or ~/.bashrc
export OP_ACCOUNT="your-account.1password.com"
```

**Tip:** Use the [1Password CLI (`op`)](https://developer.1password.com/docs/cli) for scripted access. Sign in once per session with `op signin`.

---

### Bitwarden (self-hosted or cloud)

**Retrieve a secret:**
```bash
BW_SESSION=$(bw unlock --raw)   # or use a cached session
bw get password "Item Name" --session "$BW_SESSION"
```

**In AIKB files, reference as:**
```
[Stored in Bitwarden: Item Name]
```

**Shell profile setup:**
```bash
# Unlock once and cache the session token
export BW_SESSION=$(bw unlock --raw)
```

**Tip:** Store `BW_SESSION` in a file with restricted permissions if you need it across shell sessions:
```bash
bw unlock --raw > ~/.bw_session && chmod 600 ~/.bw_session
```

---

### Vaultwarden (self-hosted Bitwarden-compatible)

Same CLI as Bitwarden. Configure the server URL:
```bash
bw config server https://your-vault-instance.example.com
bw login
```

**In AIKB files, reference as:**
```
[Stored in Vaultwarden: PAT/Service/Item Name]
```

---

### macOS Keychain

**Store a secret:**
```bash
security add-generic-password -a "$USER" -s "AIKB/Service/Item" -w "secret-value"
```

**Retrieve a secret:**
```bash
security find-generic-password -w -a "$USER" -s "AIKB/Service/Item"
```

**In AIKB files, reference as:**
```
[Stored in macOS Keychain: AIKB/Service/Item]
```

**Tip:** Use a consistent naming prefix (e.g. `AIKB/`) to keep your AIKB-related credentials organized.

---

### Environment variables

Suitable for credentials that are always available in your shell environment.

**Shell profile setup (do not commit this file):**
```bash
# In ~/.zshrc.local or ~/.profile.local (not tracked by dotfiles)
export MY_SERVICE_API_KEY="secret-value"
```

**In AIKB files, reference as:**
```
[Stored in environment: $MY_SERVICE_API_KEY]
```

**Tip:** Keep secrets out of your main dotfiles repo by using a separate, untracked include file.

---

### Secret scanning

Git offers a hook-based approach to prevent accidental credential commits. Consider tools like:
- [gitleaks](https://github.com/gitleaks/gitleaks) — scans for secrets in git history
- [detect-secrets](https://github.com/Yelp/detect-secrets) — pre-commit hook
- [trufflehog](https://github.com/trufflesecurity/trufflehog) — deep scan

Basic pre-commit check with gitleaks:
```bash
# Install
brew install gitleaks  # macOS
# or: go install github.com/gitleaks/gitleaks/v8@latest

# Add to AIKB as a pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks protect --staged --redact
EOF
chmod +x .git/hooks/pre-commit
```

---

## What to do if a secret is accidentally committed

1. **Rotate the credential immediately** — assume it's compromised regardless of repo visibility.
2. Remove it from git history:
   ```bash
   git filter-repo --path file-with-secret.md --invert-paths
   # or use BFG Repo Cleaner
   ```
3. Force-push the cleaned history (coordinate with anyone else who has cloned the repo).
4. Add the pattern to `.gitignore` or a pre-commit hook to prevent recurrence.
