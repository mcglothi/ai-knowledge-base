# VM Lifecycle — VMDEPLOY & VMDECOM (ESGUnix)

**Last Updated:** 2026-04-21 (rev 2 — new stack design decisions added)
**Summary:** Full history, architecture, pain points, and future roadmap for the ESGUnix automated VM build and decommission system. Read this before touching any VMDEPLOY_* or VMDECOM_* playbook or planning a replacement.

---

## Background & History

These playbooks were written from scratch by Tim McGlothin. There was no predecessor automation — VM builds were a manual process before this work. The project began when LLBean migrated to Nutanix AHV (displacing VMware vCenter), and the goal was to automate the full lifecycle from survey input to a hardened, registered, monitored RHEL server.

The build runs as an AAP workflow — a chain of single-purpose playbooks that pass variables between each other via `ansible.builtin.set_stats`. This pattern emerged from the Ansible Tower era and was carried forward when Tower evolved into AAP. Several supporting task files in `org/esgunix/tasks/` predate the VMDEPLOY project entirely and were reused (not written for it). Some things remain in legacy locations because they are referenced by multiple AAP job templates and can't be reorganized without updating those templates.

The result is an organic, evolved codebase — not a greenfield design — and it shows in places. That context is important when reading the pain points below.

**Windows engineers are now shadowing this Unix work** and building a parallel Windows deploy workflow (`APP_Ansible_Prod_Windows/vm_deploy_v2/`). The Unix side is the reference implementation. A unified model covering both platforms is part of the future roadmap (see below).

---

## Repos

| Repo | Path | Scope |
|------|------|-------|
| `APP_Ansible_Prod_ESGUnix` | `~/code/APP_Ansible_Prod_ESGUnix/` | Unix/RHEL deploy + decom (this doc) |
| `APP_Ansible_Prod_Windows` | `~/code/APP_Ansible_Prod_Windows/` | Windows deploy (separate, shadowing Unix) |

---

## Nutanix API Context

When this was written, the Nutanix v1 API (`ntnx_vms` module) was the available interface. Nutanix has grown extremely fast — largely because Broadcom's VMware acquisition caused a massive price spike that is driving widespread migration to Nutanix — and their API surface has been a rapidly moving target. The `nutanix.ncp` v2 collection now exists (used by the Windows deploy), but migrating the Unix playbooks hasn't been prioritized given the velocity of Nutanix's changes. Migrating to v2 is a known roadmap item but requires careful timing against Nutanix releases.

---

## Current Architecture

### Deploy Workflow — Playbook Sequence

All playbooks run in AAP as a chained workflow. Variables flow between playbooks via `set_stats`.

| # | Playbook | Runs On | What It Does |
|---|----------|---------|--------------|
| 1 | `VMDEPLOY_VarMapping.yml` | localhost | Maps survey inputs → cluster, subnet, storage container, security group, image name |
| 2 | `VMDEPLOY_Infoblox.yml` | localhost | Allocates next available IP (excl. .1–.20), registers DNS A-record |
| 3 | `VMDEPLOY_CreateVM.yml` | localhost | Creates VM on Nutanix via v1 API; injects cloud-init for hostname/NIC config |
| 4 | `VMDEPLOY_WaitForSSH.yml` | localhost | Polls port 22 on new VM; 300s timeout |
| 5 | `VMDEPLOY_Satellite.yml` | new VM | Registers with Red Hat Satellite (`satcap.llbean.com`); enables repos; full package update |
| 6 | `VMDEPLOY_ConfigMgmt_Base.yml` | new VM | Imports 16 task files from `org/esgunix/tasks/` — base packages, Centrify AD join, NTP, SSH hardening, sudoers, service accounts, CrowdStrike config, etc. |
| 7 | `VMDEPLOY_BESClient_Setup.yml` | new VM | Installs IBM BigFix (BESAgent) endpoint security client |
| 8 | `VMDEPLOY_NessusAgent.yml` | new VM | Installs Tenable Nessus Agent; links to `sensor.cloud.tenable.com` |
| 9 | `VMDEPLOY_Crowdstrike.yml` | new VM | Installs CrowdStrike Falcon sensor; verifies CID |
| 10 | `VMDEPLOY_InventoryAdd.yml` | localhost | Registers host in AAP inventory "Linux - All Servers"; assigns OS/security/platform groups |
| 11 | `VMDEPLOY_Patch.yml` | new VM | Full `yum update`, creates `/etc/last_patched`, reboots |
| 12 | `VMDEPLOY_SendEmail.yml` | localhost | Notifies `technicalopscenter@llbean.com` + owner; includes VM details |

### Decommission Workflow — Playbook Sequence

| # | Playbook | Runs On | What It Does |
|---|----------|---------|--------------|
| 1 | `VMDECOM_InitialGuestCleanup.yml` | target VM | `subscription-manager unregister`; `adleave -f llbean.com` |
| 2 | `VMDECOM_InventoryRemove.yml` | localhost | Removes host from AAP via REST API (`DELETE /api/v2/hosts/{id}/`) |
| 3 | `VMDECOM_InfobloxCleanup.yml` | localhost | Deletes DNS A-record and reclaims IP in Infoblox |
| 4 | `VMDECOM_DeleteVM.yml` | localhost | Queries Nutanix v3 API for VM UUID; deletes with `ntnx_vms state: absent` |
| 5 | `VMDECOM_SendEmail.yml` | localhost | Notifies TOC + ESGUnix of removal from Nutanix, Infoblox, Satellite, AAP |

### Survey Inputs (AAP Job Survey)

| Variable | Type | Notes |
|----------|------|-------|
| `vm_hostname` | text | Hostname without domain |
| `os` | choice | Currently only `RHEL9` is wired up |
| `dc` | choice | `SWDC` or `BLDC` |
| `sec_zone` | choice | `Prod`, `Non-prod`, `CDE` |
| `network` | choice | Subnet in `10.x.x.0` format |
| `cpu_count` | integer | Free-form; no t-shirt guardrails |
| `memory_size` | integer (GB) | Free-form; no t-shirt guardrails |
| `platform` | text | Optional AAP group assignment |
| `owner_email` | text | CC'd on notification email |
| `patch_notes` | textarea | Included in notification |

### Infrastructure Endpoints

| System | Endpoint | Notes |
|--------|----------|-------|
| Nutanix Prism Central | `nutanix.llbean.com` | v1 API in deploy; v3 REST in decom UUID lookup |
| Infoblox (deploy) | `llb-gm-new.llbean.com` | Updated endpoint — replaces old `llb-gm-dns.llbean.com` |
| Infoblox (decom) | `llb-gm-dns.llbean.com` | **Still uses old endpoint — see Known Issues #1** |
| Red Hat Satellite | `satcap.llbean.com` | Activation key: `llb-rhel-satellite-base` |
| AAP Controller | `ans-pr-aap01.llbean.com` | Inventory: "Linux - All Servers" |
| SMTP | `mymail.llbean.com:25` | Plain SMTP, no TLS |
| Tenable | `sensor.cloud.tenable.com:443` | Nessus agent link target |

### Cluster & Network Mapping (hardcoded in VarMapping)

| DC | Cluster | Subnet prefix |
|----|---------|---------------|
| SWDC | `ntx-dc1-ahv01` | `dc1-ahv01-{network}` |
| BLDC | `ntx-dc2-ahv01` | `dc2-ahv01-{network}` |

Storage containers follow naming pattern: `SC-{dc1|dc2}-ahv01-{prod|nonprod}`

---

## What ConfigMgmt_Base Does

`VMDEPLOY_ConfigMgmt_Base.yml` is the heaviest playbook — it imports 16 task files from `org/esgunix/tasks/` sequentially:

`fixes.yml` → `subscription_manager.yml` → `yum_repos.yml` → `yum_repos_server_specific.yml` → `base_packages.yml` → `centrify.yml` → `chrony.yml` → `sshd.yml` → `network.yml` → `logrotate.yml` → `users_local_service_accounts.yml` → `root_user_mods.yml` → `sudoers.yml` → `operations_files.yml` → `custom_facts.yml` → `crowdstrike.yml`

These task files predate VMDEPLOY and are shared with other playbooks (patching, ESGUNIX_* base config). They were not written for VM deploy specifically — they are the general-purpose RHEL hardening and config tasks. They also maintain **excluded host lists** for Oracle and Beumer servers that skip most tasks.

**The Satellite playbook** (`VMDEPLOY_Satellite.yml`) does extensive defensive cleanup before registering: it checks whether the host is registered to Red Hat CDN vs Satellite, removes any Katello packages/files, and re-installs the CA certificate from scratch. This pattern was reused from an existing server onboarding/remediation playbook. It is intentionally defensive because these playbooks originally also ran against existing servers in unknown registration states, not just fresh VMs.

---

## Known Pain Points & Technical Debt

### Critical / Operational Risk

**1. Infoblox endpoint mismatch (deploy vs. decom)**
VMDEPLOY_Infoblox.yml uses `llb-gm-new.llbean.com`. VMDECOM_InfobloxCleanup.yml still uses `llb-gm-dns.llbean.com`. If the old endpoint is retired, decom will silently succeed but DNS records and IPs will remain registered permanently. Needs to be aligned.

**2. No rollback / partial failure recovery**
If the workflow fails at any point, there is no automated cleanup path. Partial failure scenarios and their residue:
- Fails at CreateVM → orphaned Infoblox IP/DNS, no VM
- Fails at WaitForSSH → VM exists but unmanaged (not in Satellite, AAP, or any security tool)
- Fails mid-ConfigMgmt_Base → VM partially hardened, in unknown state
- Fails at InventoryAdd → fully configured VM that AAP can't target

Manual intervention required in all cases. No cleanup/rollback playbook exists.

**3. Logic bug in `fixes.yml`**
A condition checks `ansible_distribution_major_version == '8' AND ansible_distribution_major_version == '9'` — logically impossible, always false. The Python symlink removal task never executes on RHEL 8 or 9. Should use `or`.

**4. Hardcoded credentials in plaintext**
- `org/esgunix/tasks/centrify.yml`: AD join accounts `srvrjoin`/`C0nnecti0n` and `srvrjoinv`/`xPWZnd#23+lT#hL` are in plaintext
- `VMDEPLOY_NessusAgent.yml`: Nessus API key `1d151977cbb9866f4b0ed191399fa48ee0b44893696490d3b696703dc776a07c` is in plaintext
- `org/esgunix/tasks/users_local_service_accounts.yml`: password hash for `svc-sn-unix` exposed

These should be in Ansible Vault.

### Design / Technical Debt

**5. Nutanix v1 API (`ntnx_vms`)**
The deploy playbooks use the legacy v1 Nutanix module. The Windows deploy already uses `nutanix.ncp` v2. Nutanix's API has been rapidly evolving due to massive market growth following the Broadcom/VMware acquisition. Migration to v2 is a known roadmap item — timing should be coordinated against Nutanix platform releases.

**6. Cloud-init inline YAML in CreateVM**
The cloud-init config is written as an inline Jinja2 string in the playbook. It hardcodes:
- Network interface name: `System ens3` (breaks if NIC naming differs)
- DNS servers: `10.122.248.14 172.21.249.14`
- Gateway: derived by regex (strips last octet, appends `.1`)
No YAML validation; failures are opaque.

**7. Complex shell parsing in Satellite.yml**
Subscription state is detected via a multi-stage `grep | awk | grep -oP` pipeline against `subscription-manager config` output. Fragile if subscription-manager output format changes between RHEL releases.

**8. RHEL9-only support in VarMapping**
`VMDEPLOY_VarMapping.yml` only has `image_name` and `OS_group` mappings for RHEL9. Selecting any other OS leaves those variables undefined; downstream playbooks fail with opaque errors. RHEL8 was presumably supported at some point.

**9. No t-shirt sizing**
CPU and memory are raw free-form integers in the survey. Nothing prevents a user from requesting 64 vCPUs or 1 GB RAM. Standardized sizes (S/M/L) are planned for the new stack.

**10. `set_stats` variable passing is Tower/AAP-specific**
The mechanism for threading variables between chained playbooks only works inside AAP workflows. Playbooks cannot be run independently for testing without mocking prior stages. Not portable outside AAP.

**11. Decom is incomplete**
The decom workflow cleans up: Satellite, Active Directory, AAP inventory, Infoblox, Nutanix. It does **not** clean up: IBM BigFix, Nessus Agent, CrowdStrike Falcon, Omnicenter monitoring. Those systems self-expire stale agents, which is acceptable for now but not ideal. Proper decom cleanup for all systems is on the roadmap.

**12. Email is the only notification and audit trail**
No ticketing integration. No structured output beyond email to TOC and owner. No ability to query "what VMs were built last week" from automation data.

**13. Excluded hosts lists**
Multiple hardcoded exclusion lists in the config management tasks (~40 Oracle servers, a few others). These drift silently and require manual maintenance.

**14. Typo in decom email**
`VMDECOM_SendEmail.yml` subject line: "Decommisioned" (missing one 's').

---

## AAP Workflow IDs

| Workflow | ID |
|----------|----|
| VM Build | 1098 |
| VM Decom | 1100 |

---

## Future Direction

### Near-term (improvements to current stack)
- Fix Infoblox endpoint mismatch between deploy and decom
- Fix logic bug in `fixes.yml` (`and` → `or`)
- Migrate credentials to Delinea Secret Server (see new stack design below)
- Migrate Nutanix API to v2 (`nutanix.ncp`)
- Add RHEL8 back to VarMapping (or explicitly document it as unsupported)
- Proper decom cleanup for BigFix, Nessus, CrowdStrike, and Omnicenter
- Add a cleanup/rollback playbook for failed partial deployments

---

## New Stack Design

**Goal:** Full integrated self-service VM request and decom via Jira Service Management (JSM), with AAP as the trusted execution backbone.

### User Model

Two entry points, one execution path:

```
Regular user (JSM)                  Engineer (AAP direct)
  → request form                      → job template
  → management approval               → no approval needed
  → AAP trigger on approval           │
         └──────────────┬─────────────┘
                        ▼
                  AAP Workflow
              (same playbooks either way)
```

JSM is new at LLBean (recently migrated from ServiceNow) — mostly greenfield. The JSM team and the AAP engineering team are different groups, so each layer is owned separately.

Primary self-service use case: **temporary dev/experiment VMs**. Larger or specialized builds (SQL, Oracle, infrastructure) go directly to engineering via AAP, not JSM.

### T-shirt Sizing

Owned entirely by JSM — the JSM request form presents S/M/L and maps to resolved integers before triggering AAP. AAP receives `cpu_count` and `memory_size` as integers; it has no knowledge of sizing labels. This allows the JSM team to adjust sizes based on user feedback without any AAP changes.

Approximate starting sizes (not final):

| Label | vCPU | RAM |
|-------|------|-----|
| S | 2 | 4 GB |
| M | 4 | 8 GB |
| L | 8 | 16 GB |

Engineers submitting directly to AAP supply raw integers.

### Playbook Architecture — `import_playbook` + natural variable flow

**Replace `set_stats` with a single master playbook** that `import_playbook`s each sub-playbook in sequence. Variables set via `set_fact` on `localhost` in any play are available to all subsequent plays without tunneling through AAP workflow artifacts.

The new VM is added to in-memory inventory via `add_host` after creation. Remote plays target the `new_vms` group and access infra vars from `hostvars['localhost']` where needed.

```
VMDEPLOY_Main.yml          ← single AAP job template
  import_playbook: VarMapping.yml
  import_playbook: Infoblox.yml
  import_playbook: CreateVM.yml       ← add_host here
  import_playbook: WaitForSSH.yml
  import_playbook: Satellite.yml
  import_playbook: ConfigMgmt_Base.yml
  import_playbook: Agents.yml         ← consolidate BES + Nessus + CrowdStrike
  import_playbook: InventoryAdd.yml
  import_playbook: Patch.yml
  import_playbook: Notify.yml
```

**Tradeoff acknowledged:** moving from 12 separate job templates to 1 means you lose the AAP workflow UI's ability to restart from a specific failed step. Accepted — a failed build should be rolled back and retried cleanly, not resumed mid-flight. The rollback mechanism handles cleanup automatically.

Individual sub-playbooks remain standalone files. The master playbook is the orchestrator.

Decom follows the same pattern:

```
VMDECOM_Main.yml
  import_playbook: GuestCleanup.yml     (Satellite unregister + AD leave)
  import_playbook: BigFixCleanup.yml    ← new
  import_playbook: NessusCleanup.yml    ← new
  import_playbook: CrowdstrikeCleanup.yml ← new
  import_playbook: OmnicenterCleanup.yml  ← new
  import_playbook: InventoryRemove.yml
  import_playbook: InfobloxCleanup.yml  (fix endpoint)
  import_playbook: DeleteVM.yml         (v2 API)
  import_playbook: Notify.yml
```

### Error Handling — block/rescue with automatic rollback

Wrap the full deploy in a `block/rescue/always`. On any failure, the rescue triggers cleanup logic that mirrors the decom. The rollback task list is written once and shared between rollback and decom.

```yaml
- block:
    - import_tasks: provision_infra.yml   # Infoblox + Nutanix
    - import_tasks: configure_vm.yml      # all remote plays
  rescue:
    - import_tasks: rollback.yml          # delete VM, remove DNS, log failure
  always:
    - import_tasks: report_result.yml     # success or failure notification
```

### Nutanix — Templates + v2 API + Storage Container Targeting

**Move from image clones to templates.** Reasons:
1. Templates are easier to keep current (patch the template, redeploy)
2. Image clones prevent disk extension on the resulting VM (confirmed on Windows side, assumed true for RHEL)
3. The v2 API (`nutanix.ncp`) provides per-disk `storage_container_reference.ext_id` — this should allow deploying directly into `SC-dc1-ahv01-prod` (etc.) without the current manual post-creation migration

**The storage container problem** is a known gap in the current stack. VMs deploy into the default storage container and require manual migration to the correct named container. The v2 API disk config is the expected solution path — needs a spike to confirm. The commented-out UUID lookup in the current `VMDEPLOY_CreateVM.yml` shows this was attempted and not completed.

Target pattern for v2 VM creation:
1. Look up storage container UUID by name (`SC-{dc}-ahv01-{prod|nonprod}`)
2. Specify that UUID in the disk config at creation time
3. No post-creation migration

### Secrets — Delinea Secret Server (unified)

**Current problem:** each AAP job template has a different credential configured (Infoblox template gets Infoblox cred, Nutanix template gets Nutanix cred, etc.). Fragmented, and rotating a credential means updating both SS and AAP.

**New pattern:** one custom AAP credential type that injects the SS API token as an environment variable. All secrets fetched programmatically via the `community.general.tss` lookup plugin (already used in the codebase). Single credential on the master job template.

```yaml
# At the top of the master playbook (or a dedicated secrets-fetch play):
- set_fact:
    centrify_password: "{{ lookup('community.general.tss',
                           ss_centrify_secret_id,
                           base_url=ss_base_url,
                           token=lookup('env', 'SECRET_SERVER_TOKEN'))
                           | json_query('items[?slug==`password`].itemValue | [0]') }}"
    nessus_api_key:    "{{ lookup('community.general.tss', ss_nessus_secret_id, ...) }}"
```

Credential rotation is done in Delinea SS only — AAP and playbooks are untouched. This replaces both the current fragmented AAP credentials pattern and the hardcoded plaintext values in `centrify.yml` and `NessusAgent.yml`.

### Open Technical Questions / Spikes Needed

1. **Nutanix v2 + storage container targeting** ⬅ NEEDS SPIKE: Confirm `ntnx_vms_v2` supports `storage_container_reference.ext_id` at VM creation/clone time and that it works with template-based deploys. Nutanix API has been a moving target — verify against current `nutanix.ncp` collection version and online docs. This is a design blocker: if v2 can't solve the storage container problem at creation time, the no-post-migration premise breaks and the architecture needs adjustment.
2. **Template vs image in v2**: Confirm the exact module/parameter for deploying from a Nutanix template (`ntnx_vm_templates_v2`?) vs. image clone. Both platforms (Unix + Windows) need this.
3. ~~**`add_host` + SSH bootstrap**~~: **RESOLVED** — `svc-ansible` SSH key is baked into all baseline images and templates. `add_host` dynamic inventory works cleanly; no bootstrap step needed. The `import_playbook` architecture is unblocked on this point.
4. **`community.general.tss` + AAP custom credential type**: Design the custom credential type YAML for injecting the SS token. Confirm `tss` plugin version compatibility with current EE Python environment.
5. **JSM → AAP trigger mechanism**: When JSM approval fires, how does it trigger the AAP job template? AAP REST API webhook? Jira automation rule? This is the JSM team's problem to solve but the AAP API endpoint and credential need to be defined.
