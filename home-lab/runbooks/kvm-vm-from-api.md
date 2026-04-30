---
context: personal-homelab
tags: [truenas, kvm, vm, ansible, debian, cloud-image, runbook, api]
hosts: [truenas, babbage]
last_updated: 2026-03-01
---

# Runbook: Provision a KVM VM on TrueNAS SCALE via API

**Last Updated:** 2026-03-01
**Summary:** Repeatable API-first runbook for provisioning Debian KVM VMs on TrueNAS and preparing Ansible access.
**Derived from:** turing AI hub VM deployment (full post-mortem in `home-lab/services/turing.md`)
**Platform:** TrueNAS SCALE Electric Eel (24.10+)

This runbook documents the complete process for provisioning a new KVM VM on TrueNAS SCALE via the REST API, installing Debian via cloud image, and making it Ansible-reachable — without touching the UI or interactive console.

---

## Prerequisites

| Item | Value / Location |
|------|-----------------|
| TrueNAS API key | Vaultwarden: `PAT/TrueNAS/svc_claude` — must have `allowlist: [{"method":"*","resource":"*"}]` |
| Debian 13 cloud image | `/mnt/VMs/ISOs/debian-13-generic-amd64.qcow2` on babbage (or re-download) |
| Target IP | Assign a static IP in the 10.10.0.0/16 range |
| SSH key for svc_ansible | `~/.ssh/svc_ansible/id_ed25519` (feynman) or `~/.ssh/svc_claude` (other machines) |

**If re-downloading the cloud image:**
```bash
sudo curl -sL -o /mnt/VMs/ISOs/debian-13-generic-amd64.qcow2 \
  https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2
# Verify: should be ~400-450 MB
```

---

## Step 1 — Create the VM body

```bash
API="https://nas.home.timmcg.net/api/v2.0"
KEY="<api_key_from_vaultwarden>"

curl -sk -X POST "$API/vm" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<vm_name>",
    "description": "<description>",
    "vcpus": 4,
    "memory": 8192,
    "bootloader": "UEFI",
    "autostart": true,
    "time": "LOCAL",
    "ensure_display_device": true
  }'
```

Note the `id` in the response — this is `VM_ID`.

**Electric Eel API change:** `devices` is no longer accepted in `POST /vm`. You must add them separately (see steps 2-4).

---

## Step 2 — Add DISK device (creates zvol)

```bash
VM_ID=<id_from_step_1>
ZVOL_NAME="VMs/<vm_name>"   # must be under the VMs pool

curl -sk -X POST "$API/vm/device" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"vm\": $VM_ID,
    \"dtype\": \"DISK\",
    \"attributes\": {
      \"type\": \"VIRTIO\",
      \"create_zvol\": true,
      \"zvol_name\": \"$ZVOL_NAME\",
      \"zvol_volsize\": 53687091200
    }
  }"
# 53687091200 = 50 * 1024 * 1024 * 1024 (50 GB)
```

---

## Step 3 — Add NIC device

```bash
NIC="eno1"   # confirmed only UP physical NIC on babbage

curl -sk -X POST "$API/vm/device" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"vm\": $VM_ID,
    \"dtype\": \"NIC\",
    \"attributes\": {
      \"type\": \"VIRTIO\",
      \"nic_attach\": \"$NIC\"
    }
  }"
```

TrueNAS VMs use macvtap (`type='direct' mode='bridge'`) — the VM gets its own MAC and appears directly on the LAN. The VM does NOT need a traditional Linux bridge.

---

## Step 4 — Trigger udev for zvol symlink

After zvol creation, the `/dev/zvol/VMs/<vm_name>` symlink does not exist until udev processes the new block device:

```bash
ssh 10.10.10.10 "sudo udevadm trigger --subsystem-match=block"
# Wait ~5 seconds
ssh 10.10.10.10 "ls -la /dev/zvol/VMs/"
# Should show the new zvol symlink
```

**If you skip this step:** VM start fails with "DISK device not available".

---

## Step 5 — Write cloud image to zvol

Do NOT start the VM yet. Write the cloud image first.

```bash
# On babbage (SSH as mcglothi or root):
ZVOL="/dev/zvol/VMs/<vm_name>"

sudo qemu-img convert -O raw \
  /mnt/VMs/ISOs/debian-13-generic-amd64.qcow2 \
  $ZVOL

# Verify: should write ~3 GiB virtual size to the zvol
# The remaining space (up to 50 GB) is claimed by the partition on first boot
```

---

## Step 6 — Configure the VM image before first boot

Mount the root partition via loopback and configure the OS.

**⚠️ Critical: TrueNAS zvol uses 16K physical block size.** Standard partition tools (`parted`, `sfdisk`, `fdisk`) fail with "Unknown error 512" (EIO) when opening `/dev/zd0` for write. Always use `losetup` with a byte offset.

### 6a — Mount the root partition

```bash
# Root partition (partition 1) starts at sector 262144
# Byte offset = 262144 × 512 = 134,217,728

sudo losetup -o 134217728 /dev/loop2 /dev/zd0
sudo mount -t ext4 /dev/loop2 /mnt/vm-root
```

If `/dev/loop2` is already in use: `sudo losetup -d /dev/loop2` first, or use a different loop number.

### 6b — Set hostname

```bash
echo "<vm_name>" | sudo tee /mnt/vm-root/etc/hostname

sudo tee /mnt/vm-root/etc/hosts > /dev/null <<EOF
127.0.0.1 localhost
127.0.1.1 <vm_name>

::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
EOF
```

### 6c — Configure static networking

```bash
sudo tee /mnt/vm-root/etc/systemd/network/10-<vm_name>.network > /dev/null <<EOF
[Match]
Name=en*

[Network]
Address=<ip>/16
Gateway=10.10.0.1
DNS=10.10.0.2
DNS=10.10.0.3
EOF
```

**⚠️ Use /16, not /24.** All homelab hosts are on 10.10.0.0/16. Gateway 10.10.0.1 is unreachable from a /24 subnet.

### 6d — Enable SSH password auth (for initial access)

```bash
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' \
  /mnt/vm-root/etc/ssh/sshd_config
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' \
  /mnt/vm-root/etc/ssh/sshd_config
```

**Note:** Edit the main `sshd_config` directly, not a drop-in. Debian cloud image has `Include /etc/ssh/sshd_config.d/*.conf` at the top. In OpenSSH, `Include` is processed first, so drop-in settings load before the main file — but first-match wins, and main file's `no` would override drop-in `yes`. Editing the main file is definitive.

### 6e — Disable cloud-init (prevents re-initialization on reboot)

```bash
# Mark cloud-init as disabled
sudo touch /mnt/vm-root/etc/cloud/cloud-init.disabled

# Or remove cloud-init entirely (can do via apt after first boot)
```

If you want cloud-init for this specific deployment:
- Put seed files at `/mnt/vm-root/var/lib/cloud/seed/nocloud/`
- Add `/mnt/vm-root/etc/cloud/cloud.cfg.d/99-nocloud.cfg` with `datasource_list: [NoCloud, None]`
- **Do NOT use `chpasswd.list` with pre-hashed `$6$...` passwords** — cloud-init treats them as plaintext and double-hashes them. Use `users[].hashed_passwd:` instead.

### 6f — Set root password directly in shadow

```bash
# Generate hash
NEW_HASH=$(openssl passwd -6 '<password>')

# Replace root entry in shadow file
sudo python3 -c "
import re, sys
shadow = open('/mnt/vm-root/etc/shadow').read()
shadow = re.sub(r'^(root:)[^:]*(:.*)', r'\g<1>${NEW_HASH}\g<2>', shadow, flags=re.MULTILINE)
open('/mnt/vm-root/etc/shadow', 'w').write(shadow)
print('root password updated')
"
```

### 6g — Unmount

```bash
sudo sync
sudo umount /mnt/vm-root
sudo losetup -d /dev/loop2
```

---

## Step 7 — Start the VM

```bash
curl -sk -X POST "$API/vm/id/$VM_ID/start" \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
# Expect 200 or 204
```

**Note the endpoint:** `/vm/id/{id}/start` — not `/vm/{id}/start`.

Wait ~30 seconds for boot, then verify:

```bash
ping -c 3 <vm_ip>
ssh root@<vm_ip>   # or mcglothi@<vm_ip>
```

---

## Step 8 — Deploy svc_ansible

If bootstrap_svc_account.yml targets `hosts: home` (not the new VM's group), run manually:

```bash
ssh root@<vm_ip> bash -s <<'ENDSSH'
groupadd -f svc_ansible
id svc_ansible &>/dev/null || useradd -m -g svc_ansible -s /bin/bash svc_ansible
mkdir -p /home/svc_ansible/.ssh
chmod 700 /home/svc_ansible/.ssh
cat > /home/svc_ansible/.ssh/authorized_keys <<'ENDKEYS'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN5Nb6/Nvc7iyrTxN0S+NBTI+3a9IjetB1QYO5JYxjFh svc_ansible@home.timmcg.net
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN6tdEC9dKYlOBozlVEe7cfb7pKdjnVfjF/XlBQqtu4Y mcglothi@tesla
ENDKEYS
chmod 600 /home/svc_ansible/.ssh/authorized_keys
chown -R svc_ansible:svc_ansible /home/svc_ansible/.ssh
echo 'svc_ansible ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/svc_ansible
chmod 440 /etc/sudoers.d/svc_ansible
ENDSSH
```

---

## Step 9 — Verify Ansible connectivity

```bash
# Using svc_claude key (works from tesla; svc_ansible key only on feynman)
SSH_AUTH_SOCK="" ansible -i ai/inventory.ini <vm_name> \
  -m ping \
  --private-key ~/.ssh/svc_claude
```

Expected: `<vm_name> | SUCCESS => {"ping": "pong"}`

---

## Step 10 — Verify apt / internet access

Before running any setup playbooks:

```bash
ssh svc_ansible@<vm_ip> "cat /etc/resolv.conf"
ssh svc_ansible@<vm_ip> "ping -c 2 8.8.8.8"
ssh svc_ansible@<vm_ip> "ping -c 2 deb.debian.org"
ssh svc_ansible@<vm_ip> "sudo apt update"
```

If `ping 8.8.8.8` fails: macvtap routing issue — check gateway reachability.
If `ping deb.debian.org` fails but IP ping works: DNS issue — check `/etc/resolv.conf`.
If both work but apt fails: check for proxy config or firewall rules.

---

## Step 11 — Run Ansible playbooks

```bash
cd ~/code/ansible

# Install Docker, Dockge, Node, claude CLI, gemini CLI
ansible-playbook -i ai/inventory.ini ai/setup_turing.yml

# Deploy ttyd + code-server compose stacks
ansible-playbook -i ai/inventory.ini ai/deploy_ai_services.yml

# Add DNS entries to Pi-hole
ansible-playbook -i ai/inventory.ini ai/update_pihole_dns.yml

# Create NPM proxy hosts (needs vault_npm_user + vault_npm_password)
ansible-playbook -i ai/inventory.ini ai/configure_npm_proxy.yml

# Add to Homepage dashboard
ansible-playbook -i ai/inventory.ini ai/update_homepage.yml
```

---

## Step 12 — Fix NPM Proxy Connectivity (macvtap isolation)

macvtap VMs are reachable from the LAN but **NOT from the TrueNAS host itself**. NPM runs on babbage/TrueNAS, so proxy hosts to any macvtap VM return 502 by default.

Fix: create a `macvlan` interface on babbage (one-time, covers all macvtap VMs):

```bash
# On babbage (run once; applies to all macvtap VMs)
sudo ip link add macvlan0 link eno1 type macvlan mode bridge
sudo ip addr add 10.10.10.11/16 dev macvlan0
sudo ip link set macvlan0 up
```

Then add a specific route for each VM:
```bash
# Per VM — add route to VM's IP via macvlan0
sudo ip route add <vm_ip>/32 dev macvlan0 src 10.10.10.11
```

To persist across reboots, create `/etc/systemd/system/macvlan-turing.service`:
```ini
[Unit]
Description=macvlan bridge for turing VM (macvtap isolation workaround)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c '\
  ip link show macvlan0 2>/dev/null || ip link add macvlan0 link eno1 type macvlan mode bridge; \
  ip addr show macvlan0 | grep -q 10.10.10.11 || ip addr add 10.10.10.11/16 dev macvlan0; \
  ip link set macvlan0 up; \
  ip route show | grep -q <vm_ip> || ip route add <vm_ip>/32 dev macvlan0 src 10.10.10.11'

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now macvlan-turing.service
```

---

## Known Pitfalls (Electric Eel / TrueNAS 24.10)

| Pitfall | Detail | Fix |
|---------|--------|-----|
| `devices` field rejected in POST /vm | Electric Eel requires two-step creation | Add devices via POST /vm/device after VM creation |
| API key allowlist | Empty `allowlist: []` = deny everything | Use `[{"method":"*","resource":"*"}]` |
| `filesystem/stat` 422 "Not a string" | Endpoint expects positional string, not JSON object | Skip or use SSH instead |
| Display type VNC invalid | Must use SPICE with password | Omit display device; `ensure_display_device: true` handles it |
| udev symlink missing | /dev/zvol/... not created until udev runs | `sudo udevadm trigger --subsystem-match=block` |
| API key regeneration | `sudo -n midclt call api_key.create '{"name":"...","allowlist":[{"method":"*","resource":"*"}]}'` | Run on babbage directly |
| Start endpoint path | `/vm/id/{id}/start` not `/vm/{id}/start` | Use correct path |

---

## SSH Gotchas

| Issue | Fix |
|-------|-----|
| sshpass exit code 5 (OpenSSH 10) | Add `-v` flag; better: use key-based auth instead |
| SSH MaxAuthTries exceeded | `SSH_AUTH_SOCK="" ssh -o IdentitiesOnly=yes -i ~/.ssh/keyfile ...` |
| ControlMaster stale socket | Use IP address instead of hostname, or add `-o ControlMaster=no -o ControlPath=none` |
| svc_ansible key only on feynman | Use `~/.ssh/svc_claude` from other machines; update inventory `ansible_ssh_private_key_file` |

---

## Optional: Create a Gold Image

After a VM is fully configured, capture it as a gold image for future deployments:

```bash
# 1. Cleanly halt the VM
ssh svc_ansible@<vm_ip> "sudo systemctl poweroff"
# Wait ~30s

# 2. Capture compressed image
sudo qemu-img convert -O qcow2 -c /dev/zvol/VMs/<vm_name> \
  /mnt/VMs/ISOs/debian-13-gold-$(date +%Y%m%d).qcow2

# 3. Deploy from gold image to a new VM:
#    - Create new zvol via API (Steps 1-4 above)
#    - sudo qemu-img convert -O raw /mnt/VMs/ISOs/debian-13-gold-YYYYMMDD.qcow2 /dev/zvol/VMs/<new_vm>
#    - Mount + update /etc/hostname, /etc/hosts, /etc/systemd/network/
#    - Start VM — svc_ansible auth works immediately (keys baked in)
#    - Run: ssh-keygen -A  (regenerate unique host keys)
```

Full gold image strategy: `home-lab/services/turing.md` → Gold Images section.
