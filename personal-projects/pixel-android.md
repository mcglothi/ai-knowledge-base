---
context: personal
tags: [pixel, android, adb, wireless-adb, tailscale, phone, remote-control]
status: active
last_updated: 2026-02-23
---

# Pixel Android — Remote Control & Device Notes

**Last Updated:** 2026-02-23
**Summary:** Notes on the Pixel phone (daily driver), wireless ADB setup for remote control, and Android-specific gotchas discovered while configuring Tailscale.

---

## Device Info

| Item | Value |
|------|-------|
| Device | Google Pixel (daily driver) |
| OS | Android |
| Tailscale version | 1.94.2 |
| Tailscale node | `pixel` (100.64.0.2 on Headscale) |
| Wireless ADB IP | `10.10.140.4` (LAN IP — changes on DHCP renewal) |
| Wireless ADB port | **Changes every time wireless debugging is toggled or WiFi reconnects** — always re-check in Developer Options |

---

## Auto-Connect Scripts

### Pixel 10
**`~/code/pixel-connect.sh`** — scans ports 37000–44000 in parallel (50 at a time) and connects automatically. No manual port lookup needed.

```bash
~/code/pixel-connect.sh           # default IP 10.10.140.4
~/code/pixel-connect.sh 10.10.x.x  # override IP if DHCP changed it
```

### NVIDIA Shield (Living Room)
**`~/code/shield-connect.sh`** — connects to the fixed port (5555).

```bash
~/code/shield-connect.sh          # IP 10.10.174.255
```

## Wireless ADB Setup

Enable once in Developer Options (persists until toggled off):

1. **Enable Developer Options:** Settings → About Phone → tap Build Number 7 times
2. **Enable Wireless Debugging:** Settings → Developer Options → Wireless debugging → ON
3. **Pair a new device (first time):**
   - Tap "Pair device with pairing code" in the Wireless debugging menu
   - Note the pairing IP:port and 6-digit code
   - On laptop: `adb pair <ip>:<pairing-port>` then enter the code
4. **Connect (each session):**
   - Note the connection IP:port shown under "Wireless debugging" (different from pairing port)
   - `adb connect <ip>:<port>`
   - Confirm: `adb devices` — should show `<ip>:<port> device`

**Disconnect:**
```bash
adb disconnect 10.10.140.4:<port>
```

---

## Common ADB Commands

### Screenshot
```bash
adb -s 10.10.140.4:<port> shell screencap -p /sdcard/screen.png
adb -s 10.10.140.4:<port> pull /sdcard/screen.png /tmp/pixel_screen.png
# Then Read /tmp/pixel_screen.png to view it
```

### UI Dump (inspect elements)
```bash
adb -s 10.10.140.4:<port> shell uiautomator dump /sdcard/ui.xml
adb -s 10.10.140.4:<port> pull /sdcard/ui.xml /tmp/ui.xml
# Or read directly:
adb -s 10.10.140.4:<port> shell cat /sdcard/ui.xml
```

Parse with Python to find elements:
```python
import xml.etree.ElementTree as ET
xml = open('/tmp/ui.xml').read()
root = ET.fromstring(xml)
for elem in root.iter():
    text = elem.get('text','') or elem.get('content-desc','')
    if text:
        print(elem.get('class','?').split('.')[-1], repr(text),
              'checked=' + str(elem.get('checked')),
              'clickable=' + str(elem.get('clickable')),
              elem.get('bounds',''))
```

Filter by screen region (y range):
```python
parts = bounds.replace('][',',').replace('[','').replace(']','').split(',')
x1,y1,x2,y2 = int(parts[0]),int(parts[1]),int(parts[2]),int(parts[3])
if 1200 < y1 < 1500:  # filter by vertical position
    ...
```

### Tap an element
```bash
# Tap center of bounds [x1,y1][x2,y2]
adb -s 10.10.140.4:<port> shell input tap <cx> <cy>
```

### Swipe / Scroll
```bash
# Scroll up (swipe from bottom to top)
adb -s 10.10.140.4:<port> shell input swipe 540 400 540 100 300

# Multiple swipes to reach bottom:
for i in 1 2 3 4 5; do adb -s <device> shell input swipe 540 400 540 100 300; done
```

### Back button
```bash
adb -s 10.10.140.4:<port> shell input keyevent KEYCODE_BACK
```

### Home button
```bash
adb -s 10.10.140.4:<port> shell input keyevent KEYCODE_HOME
```

### Type text
```bash
adb -s 10.10.140.4:<port> shell input text "yourtext"
# WARNING: Android IME auto-capitalizes first character.
# Special chars (&, /, :) may need URL encoding or multiple steps.
# For URLs: type deliberately, e.g. "https" may become "Https" — usually OK for URL schemes.
```

### Open a URL in browser
```bash
adb -s 10.10.140.4:<port> shell am start -a android.intent.action.VIEW -d 'http://nas.home.timmcg.net'
```

### Launch an app by package
```bash
adb -s 10.10.140.4:<port> shell monkey -p com.tailscale.ipn -c android.intent.category.LAUNCHER 1
```

---

## Gotchas

- **ADB port changes** every time wireless debugging is toggled off/on or the phone reconnects to WiFi. Always re-check the current port in Developer Options before connecting.
- **UIAutomator only captures visible elements** — if the screen has a scrollable list, only what's currently in view appears in the dump. Scroll and re-dump to find items further down.
- **`ping` on Android ADB shell bypasses VPN DNS** — `ping nas.home.timmcg.net` will fail with "unknown host" even when Tailscale split DNS is correctly configured. App-level DNS (browser, etc.) routes through the VPN stack correctly.
- **Auto-capitalization** on text input: the first character typed via `adb shell input text` gets capitalized by the Android IME. Work around by accounting for it (e.g., `Https://` instead of `https://` — URL schemes are case-insensitive).
- **`screencap` with multiple displays** emits a warning ("Multiple displays found") but works fine — it uses the primary display.
- **ADB text with special characters** (`&`, `?`, `#`, spaces) needs escaping or quoting. Use `'single quotes'` in the shell command.

---

## Tailscale on Android (v1.94.x)

### Custom server setup (7-tap trick doesn't work on 1.94.x)
1. Open Tailscale → Settings → Accounts → tap **⋮ menu** (top-right)
2. Tap **"Use an alternate server"**
3. Enter the custom URL (e.g., `https://hs.timmcg.net`)
4. Tap **Add account** — browser opens with `headscale nodes register` command

### Subnet routing (accept-routes equivalent)
Settings → **Subnet routing** → opens sub-screen "Subnet routes" → enable **"Use Tailscale subnets"**

This is required to reach `10.10.x.x` addresses via truenas-scale's advertised subnet.

### Split DNS behavior on Android
- The `home.timmcg.net` split DNS route is **not displayed** in Tailscale → Settings → DNS settings (only arpa reverse-DNS routes appear in the UI)
- Split DNS IS applied at the app level — browsers and other apps resolve `*.home.timmcg.net` correctly via Pi-hole
- Confirmed: `nas.home.timmcg.net` loads TrueNAS, `grafana.home.timmcg.net` redirects to Authentik SSO

### Node registration via ADB (when browser flow leaves app "logged out")
After the browser-based registration, the Tailscale app may stay in a logged-out state but the node IS registered server-side. Wait a few seconds and the app usually syncs. If not, the node is still active — check with `sudo headscale node list` on the server.

### Node registered as "localhost"
When connecting via ADB input (custom server URL typed manually), the node may register with hostname `localhost`. Rename with:
```bash
sudo headscale nodes rename --identifier <id> <new-name>
```

---

## See Also

- [`personal-projects/headscale-gcp.md`](headscale-gcp.md) — Headscale setup, pre-auth keys, full node list
- [`home-lab/infrastructure/network-dns.md`](../home-lab/infrastructure/network-dns.md) — Pi-hole split DNS details
