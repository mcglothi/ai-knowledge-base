# Secrets Management
**Last Updated:** 2026-04-21
AIKB never stores credentials — only references: `[Stored in <Manager>: <Path/Name>]`

## 1Password
```bash
op read "op://Private/Item Name/field"
```
Reference: `[Stored in 1Password: Private/Service Name/API Key]`

## Bitwarden / Vaultwarden
```bash
BW_SESSION=$(cat ~/.bw_session)
bw get password "Item Name" --session "$BW_SESSION"
```
Reference: `[Stored in Bitwarden: Item Name]` or `[Stored in Vaultwarden: PAT/Service/Item Name]`
Vaultwarden server config: `bw config server https://your-vault.example.com && bw login`

## Delinea Secret Server
One-time init (per machine): `tss init --url https://your-server/SecretServer/ -r <RuleName> -k <onboarding-key>`
Retrieve: `tss secret --secret <id> --field password`
ID lookup: `personal/vaults/delinea.yaml` → friendly name → numeric ID
Reference: `[Stored in Delinea Secret Server: AWS Root Key (#123) / access-key-id]`
CLI: download from Delinea Downloads portal (no Homebrew formula). Python SDK: `pip install python-tss-sdk`.

## macOS Keychain
```bash
security add-generic-password -a "$USER" -s "AIKB/Service/Item" -w "secret-value"
security find-generic-password -w -a "$USER" -s "AIKB/Service/Item"
```
Reference: `[Stored in macOS Keychain: AIKB/Service/Item]`

## Environment Variables
```bash
# In ~/.zshrc.local or ~/.profile.local (untracked)
export MY_SERVICE_API_KEY="secret-value"
```
Reference: `[Stored in environment: $MY_SERVICE_API_KEY]`

## Secret Scanning
Prevent accidental commits:
- [gitleaks](https://github.com/gitleaks/gitleaks): `brew install gitleaks` → pre-commit: `gitleaks protect --staged --redact`
- [detect-secrets](https://github.com/Yelp/detect-secrets): pre-commit hook
- [trufflehog](https://github.com/trufflesecurity/trufflehog): deep history scan

## If a Secret is Committed
1. Rotate immediately — assume compromised.
2. `git filter-repo --path <file> --invert-paths` (or BFG Repo Cleaner)
3. Force-push cleaned history.
4. Add pattern to `.gitignore` or pre-commit hook.
