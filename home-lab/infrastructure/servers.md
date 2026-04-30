---
tags: [truenas, babbage, turing, farnsworth, hopper, servers, ips, 10.10.10.10, svc_ansible, ssh, workstations, feynman, tesla, raspberry-pi, opensoak, baird, cecmate, esp32, cec, iot]
hosts: [truenas, babbage, turing, farnsworth, hopper, pihole, pihole2, opensoak, tesla, feynman, matilda, baird]
last_updated: 2026-04-24
---

# Server & Host Inventory
**Last Updated:** 2026-04-24
**Summary:** Canonical host inventory with roles, addressing, and key operational notes across the home lab.

## Management
- **router**: UDM Pro (10.10.0.1). Primary gateway and DHCP server.

## TrueNAS Ecosystem
- **truenas / babbage**: Primary Storage & App Server (10.10.10.10).
  - Agent Accounts: `svc_gemini`, `svc_claude`, `svc_codex` (authorized keys verified 2026-04-10).
  - svc_ansible SSH: works. Dedicated key generated on tesla at `~/.ssh/svc_ansible`.
  - svc_ansible sudo: `svc_ansible ALL=(ALL) NOPASSWD:ALL` in `/etc/sudoers`.
- **turing**: Ubuntu 24.04 VM on babbage (10.10.10.50).
  - Primary AI Hub surface hosting `operator-console` (:3001).
  - Agent Accounts: `svc_gemini`, `svc_claude`, `svc_codex` (all with sudo NOPASSWD).
  - svc_ansible SSH: authorized for agent keys and dedicated `svc_ansible` key.
- **farnsworth**: Secondary server / test environment (10.10.10.100).

## Dedicated Infrastructure
- **hopper**: Gigabyte AI Top Atom / GB10 local-LLM sidecar (10.10.10.200).
  - Reachable on LAN as `hopper.home.timmcg.net`.
  - GPU confirmed via `nvidia-smi` as `NVIDIA GB10`.
  - Ollama serving on `:11434`; initial test model is `qwen2.5:7b`.
  - Open WebUI running as a user service on `:8080`.
- **pihole**: Primary DNS (Container on TrueNAS).
- **pihole2**: Secondary DNS (Raspberry Pi - 10.10.0.22).
- **opensoak**: Hot Tub Controller (Raspberry Pi - 10.10.169.191).

## IoT / Embedded Devices
- **baird**: Office TV CEC Controller — CECmate v1 (ESP32-WROOM-32, 10.10.199.178, static).
  - HDMI CEC on GPIO21 (10kΩ pull-up to 3.3V), GND, connected to HDMI2 on Samsung office TV.
  - Samsung ~55" 4K, model code 3135, mfg week 42 2014. Anynet+ must be enabled.
  - Firmware: ESPHome 2026.2.2. Config: ~/esphome/tv-cec.yaml on Arch desktop.
  - Web UI: http://baird.home.timmcg.net (buttons only — REST API crashes ESP32, use native API).
  - CLI: ~/esphome/baird.py via ~/esphome-venv/bin/python3 (uses aioesphomeapi port 6053).
  - OTA: port 3232. API encryption key in ~/esphome/secrets.yaml.
  - Source repo: mcglothi/cecmate (rename from esphome-configs).

## Workstations
- **newton**: MacBook Pro M5 Max (10.10.187.116 / 100.64.0.6). Primary workstation.
  - **Connection Priority:** Always prefer `newton10g` (`10.10.110.110`) when docked.
  - Fallback logic: `newton10g` (Docked 10G) -> `newton` (Wi-Fi/DHCP) -> `100.64.0.6` (Tailscale).
  - MAC 10G: `00:30:93:12:5e:58` (en8) — used for UDM reservation.
  - Roles: Primary Agent Orchestrator, Synthesis Host, local-LLM (LM Studio).
- **tesla**: MacBook Pro M1 13" (10.10.190.57). Primary mobile development machine. Always on WiFi — no wired NIC.
  - WoL: standard magic packet not supported over WiFi. M1 sleep keeps efficiency cores active.
  - ⬜ Untested: `ssh tesla` from feynman while tesla is asleep — may wake it if "Wake for network access" is enabled (System Settings → Battery → Options).
- **feynman**: Arch Linux desktop (10.10.145.26). Primary development machine (x86_64).
  - MAC 1G: `e0:d5:5e:2b:c6:e2` (enp0s31f6)
  - MAC 10G: `6c:fe:54:1c:61:80` (enp2s0f0np0) — **use this for WoL**
  - WoL tools: Newton has Homebrew `wakeonlan` 0.42; Feynman has Arch `wol` 0.7.1. Tesla should also carry `wakeonlan` as the macOS workstation baseline.
  - Preferred wake command from Newton or Tesla: `wakeonlan 6c:fe:54:1c:61:80`
  - WoL relay fallback: `ssh truenas "python3 -c \"import socket; mac='6cfe541c6180'; magic=bytes.fromhex('ff'*6+mac*16); s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1); s.sendto(magic,('<broadcast>',9))\"` (`wakeonlan` not installed on TrueNAS)
- **matilda**: Dell Precision laptop (Kate's machine). NVIDIA RTX 2000 Mobile (8GB VRAM), 32GB RAM.
  - GPU capable of running 4-bit 7B models (Qwen 2.5 Coder 7B recommended).
  - Full profile: [`home-lab/infrastructure/matilda.md`](matilda.md)
  - Pending: assign hostname, IP, and add to network when brought online.
