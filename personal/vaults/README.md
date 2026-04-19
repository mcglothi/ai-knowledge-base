# personal/vaults/

**Last Updated:** 2026-04-19
**Summary:** Vault-specific ID registries. Maps numeric or opaque secret IDs to human-readable names so agents can look up secrets by name rather than by ID.

---

## Why this exists

Some secret managers (notably Delinea Secret Server) identify secrets by numeric ID rather than by path or name. Without a lookup table, every AIKB reference must manually include both the friendly name and the ID, and agents can't resolve names on their own.

Files in this folder act as an index: agent loads the file, looks up a name, gets the ID, retrieves the secret.

---

## Files

| File | Vault |
|------|-------|
| `delinea.yaml` | Delinea Secret Server (formerly Thycotic) |

---

## How agents use this

When the operator says "get the Ansible Vault Password from Delinea":

1. Agent reads `personal/vaults/delinea.yaml`
2. Finds `name: "Ansible Vault Password"` → `id: 300`, `field: password`
3. Runs `tss secret --secret 300 --field password`
4. Returns the value — operator never needed to know the ID

When writing a new AIKB credential reference, agents use the registry to auto-populate the ID:
```
[Stored in Delinea: Ansible Vault Password (#300) / password]
```

---

## Adding new secrets

Add an entry to `delinea.yaml`:

```yaml
- id: 999
  name: "Descriptive Friendly Name"
  field: password        # the tss field name — usually password, username, or a custom field
  category: infra        # aws | vcs | infra | db | api | other
  notes: "Optional context — rotate date, team, linked service"
```

Never add secret values. IDs and field names only.

---

## Extending to other vaults

If you use a vault that also identifies secrets by opaque ID (e.g. CyberArk), follow the same pattern:

```
personal/vaults/cyberark.yaml
```

Use `_templates/vault-registry-template.yaml` as a starting point.
