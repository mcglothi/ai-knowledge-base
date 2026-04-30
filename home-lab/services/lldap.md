---
tags: [lldap, ldap, authentik, truenas, identity, directory, babbage]
status: active
last_updated: 2026-04-03
---

# LLDAP (Lightweight LDAP)
**Last Updated:** 2026-04-03
**Summary:** Deployment and integration notes for LLDAP as the central identity directory for Authentik and TrueNAS.

## Overview
LLDAP is a simple LDAP server for user management, integrated with Authentik.

## Deployment
- **Host:** Babbage (10.10.10.10)
- **Port:** 17170 (Web), 3890 (LDAP)
- **Stack:** `/mnt/.ix-apps/app_mounts/dockge/stacks/lldap`
- **Database:** SQLite (`/mnt/Containers/LLDAP/users.db`)

## Configuration
- **Base DN:** `dc=home,dc=timmcg,dc=net`
- **Admin User:** `uid=admin,ou=people,dc=home,dc=timmcg,dc=net`
- **Service Account:** `uid=authentik,ou=people,dc=home,dc=timmcg,dc=net` (Member of `lldap_admin`)
- **Standardized Identity:** 
  - `mcglothi`: UID 1000, GID 2000 (Staff, LLDAP Admin)
  - `dekatria`: UID 1001, GID 2000 (Staff)
  - `authentik`: UID 2001, GID 2001
  - Note: GIDs were bumped from 20 to 2000+ to satisfy TrueNAS SCALE SSSD requirements (`min_id = 1000`).

## Integration: Authentik
- **Source Slug:** `lldap`
- **URI:** `ldap://lldap:3890` (Connected to `authentik_default` network)
- **Bind DN:** `uid=authentik,ou=people,dc=home,dc=timmcg,dc=net`
- **Bind Password:** [Stored in Vaultwarden: `PAT/LLDAP/svc_authentik`]
- **Status:** 🟢 Healthy / Syncing

## Integration: TrueNAS SCALE
- **Host:** Babbage (10.10.10.10)
- **Schema:** `RFC2307`
- **Attribute Maps:**
  - User: `objectClass=person`, `uidNumber=uidNumber`, `gidNumber=gidNumber`
  - Group: `objectClass=groupOfUniqueNames`, `gidNumber=gidNumber`, `uniqueMember=uniqueMember`
- **Status:** 🟢 Healthy (Users visible via `getent passwd`)
- **Known Issue:** Groups not appearing in `getent group` despite RFC2307 mapping.

## Maintenance
- Manual Sync: `sudo docker exec authentik-server-1 ak ldap_sync lldap`
- Reset Admin Password: `sudo docker exec lldap /app/lldap_set_password --base-url http://localhost:17170 --admin-username admin --admin-password <admin_pass> --username <user_to_reset> --password <new_pass>`

## Troubleshooting

### SSH Authentication Failures (TrueNAS)
- **Global Password Auth:** SSH password authentication was previously disabled globally on TrueNAS, which prevented LLDAP users from logging in via password even if SSSD was healthy. It was manually enabled at the system level.
- **Incomplete User Entries (SSSD):** SSH sessions were being rejected because LLDAP user entries were incomplete (missing home directory and shell mapping).
- **SSSD Attribute Mapping:** Fixed by manually updating the SSSD configuration on TrueNAS to correctly map LLDAP attributes (specifically `homeDirectory` and `loginShell`). LLDAP does not provide `modifyTimestamp`, so SSSD incremental updates should be handled with care or disabled if they cause sync loops.
