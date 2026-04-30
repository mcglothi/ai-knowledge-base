---
tags: [feynman, denon, samsung, cec, hdmi, esp32, avr, tv, automation, startup, shutdown, av]
status: in-progress
last_updated: 2026-02-27
---

# Workstation AV Control (feynman)

**Last Updated:** 2026-02-27
**Summary:** Plan and command reference for automating workstation AV startup/shutdown behavior.
**Host:** feynman
**Status:** ⚠️ IN PROGRESS — ESP32 CEC bridge not yet built/flashed

---

## Overview

Automate startup and shutdown of the AV devices attached to feynman workstation:

| Device | Control Method | Status |
|--------|---------------|--------|
| Denon AVR-X1100W receiver | HTTP API (LAN) | ✅ Working |
| Samsung UN55JU6700 55" TV | ESP32 CEC bridge (planned) | 🔨 Building |

Goal: single startup/shutdown script that powers both devices on/off in sequence.

---

## Denon AVR-X1100W

**IP:** `10.10.198.166`
**Control:** HTTP GET commands to the Denon iPhoneApp API — no auth required.

### Key Commands

```bash
# Power
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?PWON"
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?PWSTANDBY"

# Volume (0–99)
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?MV45"
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?MVUP"
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?MVDOWN"

# Mute
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?MUON"
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?MUOFF"

# Input select
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?SIPC"   # PC
curl "http://10.10.198.166/goform/formiPhoneAppDirect.xml?SIBD"   # Blu-ray

# Status query
curl "http://10.10.198.166/goform/formMainZone_MainZoneXmlStatus.xml"
```

---

## Samsung UN55JU6700

**IP:** `10.10.147.109`
**WiFi MAC:** `24:4B:03:37:51:64`
**Network:** WiFi (2.4/5GHz)
**Anynet+ (HDMI-CEC):** Enabled

### Network API (port 8001 — works while TV is on)

```bash
# Device info
curl http://10.10.147.109:8001/api/v2/

# Key commands via samsungtvws Python library
pip install samsungtvws
```

```python
from samsungtvws import SamsungTVWS
tv = SamsungTVWS('10.10.147.109')
tv.send_key('KEY_POWER')
tv.send_key('KEY_VOLUP')
```

**Limitation:** Network API cannot cold-wake the TV from fully off — CEC required for power-on.

### Wake-on-LAN

WoL is supported on this model but **unreliable over WiFi** (adapter sleeps when TV is off). If TV is ever wired via ethernet, WoL becomes viable:
```bash
wakeonlan 24:4B:03:37:51:64
```

---

## ESP32 CEC Bridge

### Why

- feynman has a GTX 1080 Ti — NVIDIA's Linux driver does **not** expose CEC (`/dev/cec*` absent)
- CEC bus is active on all HDMI ports simultaneously — no inline passthrough needed
- Plug into any spare HDMI port on the TV

### Hardware

| Part | Detail |
|------|--------|
| ESP32 dev board | ESP-WROOM-32 (DOIT DevKit V1 clone, CP2102 USB-UART, AMS1117-3.3V reg) |
| HDMI cable (scrap) | Cut one end — only pins 13 and 17 are used |
| 330Ω resistor | CEC line protection |
| USB power | Powered from feynman USB port (on when PC is on) |

### Wiring

```
HDMI male plug
  pin 13 (CEC) ──[330Ω]──── GPIO5  (D5, right side of board)
  pin 17 (GND) ──────────── GND
  all others   ── unconnected
```

**HDMI pin 13 location** (Type A male, face-on):
```
 ┌─────────────────────────────┐
 │ 19 17 15 [13] 11  9  7  5  3  1 │  ← top row (odd), pin 13 = 4th from left
 │    18 16  14  12 10  8  6  4  2 │  ← bottom row (even)
 └─────────────────────────────┘
```

**GPIO pin note:** Avoid GPIO 6–11 (internal flash), 34–39 (input-only), 0/2/12/15 (boot-strap). GPIO5 is safe.

**If TV doesn't respond:** Pull HDMI pin 19 (HPD) high via 10kΩ resistor to 3.3V to fake a connected display. Samsung JU series typically doesn't require this.

### Firmware Plan

Arduino framework (ESP-IDF compatible). Dependencies:
- [`johnboiles/arduino-cec`](https://github.com/johnboiles/arduino-cec) — bit-bang CEC on GPIO5
- `ESPAsyncWebServer` — HTTP API

Endpoints:
```
POST http://cec-bridge.local/power/on     → CEC ImageViewOn to TV (addr 0)
POST http://cec-bridge.local/power/off    → CEC Standby to TV (addr 0)
GET  http://cec-bridge.local/status       → alive check
```

mDNS hostname: `cec-bridge.local`

### Flash Setup (feynman)

```bash
# Arduino CLI or PlatformIO
pacman -S python-pip
pip install esptool

# Board: ESP32 Dev Module
# Upload speed: 921600
# Port: /dev/ttyUSB0 (CP2102 — auto-loaded on Arch, no driver install needed)
```

---

## Startup / Shutdown Script (planned)

Location: `~/bin/av-start` and `~/bin/av-stop`

```bash
#!/bin/bash
# av-start — power on workstation AV

# 1. Power on Denon AVR
curl -s "http://10.10.198.166/goform/formiPhoneAppDirect.xml?PWON"
sleep 2

# 2. Set volume to working level
curl -s "http://10.10.198.166/goform/formiPhoneAppDirect.xml?MV45"

# 3. Power on Samsung TV via CEC bridge
curl -s -X POST "http://cec-bridge.local/power/on"

echo "AV started"
```

```bash
#!/bin/bash
# av-stop — power off workstation AV

curl -s -X POST "http://cec-bridge.local/power/off"
sleep 1
curl -s "http://10.10.198.166/goform/formiPhoneAppDirect.xml?PWSTANDBY"

echo "AV stopped"
```

---

## To-Do

- [ ] Build ESP32 CEC bridge hardware (solder pin 13 + GND to GPIO5)
- [ ] Flash ESP32 firmware (arduino-cec + AsyncWebServer)
- [ ] Test CEC power on/off to TV
- [ ] Write and test `av-start` / `av-stop` scripts
- [ ] Optionally wire to system suspend/resume via systemd hooks
