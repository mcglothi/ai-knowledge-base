---
context: personal-homelab
tags: [checklist, onboarding, dns, npm, ssl, vaultwarden, ansible, homepage, authentik, monitoring, new-service]
status: reference
last_updated: 2026-03-05
---

# New Service Onboarding Checklist

**Last Updated:** 2026-03-05
**Summary:** Steps required every time a new self-hosted service or container is added to the home lab.

---

## Checklist

### 1. Container / Deployment
- [ ] Create persistent storage directory on TrueNAS **before** deploying:
  ```bash
  ssh babbage "sudo mkdir -p /mnt/Containers/<ServiceName> && sudo chown -R apps:docker /mnt/Containers/<ServiceName>"
  ```
  Mount it in the compose file as: `- /mnt/Containers/<ServiceName>:/data` (or service-appropriate path)
- [ ] Create Dockge stack (or deploy as TrueNAS catalog app), referencing the volume above
- [ ] Confirm container is running and healthy
- [ ] Verify data is writing to `/mnt/Containers/<ServiceName>/` (not a container-local ephemeral volume)

### 2. DNS
- [ ] Add A/CNAME record in Pi-hole (primary: `10.10.0.2`) under `home.timmcg.net`
- [ ] Verify record propagates to secondary Pi-hole (`pihole2`, `10.10.0.22`)
- [ ] Test resolution: `nslookup <service>.home.timmcg.net`

### 3. Nginx Proxy Manager (NPM)
- [ ] Add proxy host in NPM (`npm.home.timmcg.net`)
  - Domain: `<service>.home.timmcg.net`
  - Forward to container IP/port
- [ ] Assign wildcard SSL cert (`*.home.timmcg.net`) on the proxy host
- [ ] Test HTTPS access from browser

### 4. Credentials
- [ ] Create Vaultwarden entry (folder: **Home Lab**)
  - Admin credentials
  - Any API keys or tokens
  - Naming: `<ServiceName> - Admin` or `PAT/<Service>/<Name>` for API keys

### 5. Authentik SSO (if applicable)
- [ ] Create Authentik application + provider
- [ ] Enable forward auth on NPM proxy host (or configure OIDC in the app)
- [ ] Test SSO login flow

### 6. Ansible
- [ ] Add host/service to the nightly patch playbook if it needs OS-level updates
- [ ] Add backup job if the service has stateful data
- [ ] Test playbook run against the new target

### 7. Homepage
- [ ] Add service card to Homepage (`homepage.home.timmcg.net`)
  - Name, URL, icon, description
  - API widget if the service exposes one (status/stats)

### 8. SSL / Certificate
- [ ] Confirm wildcard cert covers the subdomain (it should automatically)
- [ ] If a non-wildcard cert is needed, provision and add to NPM
- [ ] Update `_state.yaml` `ssl_certs` block with expiry date if a new cert was created

### 9. Monitoring (if applicable)
- [ ] Add Prometheus scrape target or exporter if the service exposes metrics
- [ ] Add Grafana dashboard or panel
- [ ] Set up alert rule for service-down condition

### 10. AIKB Documentation
- [ ] Create `home-lab/services/<service>.md` (copy from `_templates/service.md` if it exists)
- [ ] Add row to `home-lab/services/README.md`
- [ ] Add row to `_index.md` (Home Lab section)
- [ ] Add URL to `home-lab/infrastructure/access-reference.md`
- [ ] Update `_state.yaml` if any new pending items or SSL certs added
- [ ] If this is an AIKB runtime add-on, add/update extension manifest (`extension.yaml`) and list it in `_tools/extensions/README.md`
- [ ] If this service exposes APIs to agents, update `_agents/claude-code.md` and `_agents/codex.md` trigger/load guidance

---

## Quick Smoke Test

After completing the checklist, verify end-to-end:

1. Persistent storage exists and has content: `ssh babbage "ls -lah /mnt/Containers/<ServiceName>/"`
2. DNS resolves: `nslookup <service>.home.timmcg.net 10.10.0.2`
3. HTTPS loads without cert warning
4. Login works (local credentials or SSO)
5. Homepage card appears and links correctly
6. Ansible dry-run includes the new host/task without errors

---

## Notes

- All services run under `home.timmcg.net` with wildcard SSL managed by NPM on TrueNAS (`babbage`, `10.10.10.10`)
- Pi-hole is the authoritative DNS for `home.timmcg.net` — changes take effect immediately but both instances must be updated
- **Persistent storage root:** `/mnt/Containers/<ServiceName>/` — one directory per service, owned `apps:docker`. Never rely on Docker-managed volumes or container-local storage — data must survive container recreation.
- Dockge: `dockge.home.timmcg.net` — for custom compose stacks
- Ansible Semaphore: `ansible.home.timmcg.net` — schedule new jobs there
