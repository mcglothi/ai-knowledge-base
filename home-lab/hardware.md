---
tags: [hardware, raspberry-pi, opensoak, undervoltage, power, home-lab, newton, sonnet, 10gbe]
hosts: [opensoak, newton]
last_updated: 2026-04-22
---

# Home Lab — Hardware Issues

**Last Updated:** 2026-04-22
**Summary:** Tracking file for active hardware faults and physical reliability risks in the home lab.
**Purpose:** Track physical hardware problems, failures, and known hardware quirks across all home lab devices.

---

## Newton — Sonnet 10G SFP+ Link Negotiation

**Device:** Newton (`10.10.110.110` / `newton10g`)
**Status:** ✅ RESOLVED — Replacement HiFiber optics installed; configured as static secondary 10G path
**Discovered:** 2026-04-22
**Resolved:** 2026-04-24

### Symptoms
- Sonnet Solo 10G SFP+ Thunderbolt 3 Edition is connected through the OWC Thunderbolt 5 Hub.
- macOS sees the OWC hub at 80 Gb/s and the Sonnet adapter at 40 Gb/s Thunderbolt.
- macOS sees the Aquantia AQC107 NIC with `Maximum Link Speed: 10 Gb/s`.
- Current known-good Ethernet state is `10Gbase-T <full-duplex,flow-control>` on `en8`, static IP `10.10.110.110`.
- Gateway pings over `en8` at 1G were clean: 0% packet loss, roughly 0.3 ms average.
- Forcing `10Gbase-T <full-duplex,flow-control>` with `networksetup -setMedia en8 10Gbase-T full-duplex flow-control` with original Finisar optics caused instability.
- **Verification (2026-04-24):** After installing the replacement HiFiber `SFP-10G-SR` transceivers, `en8` linked at `10Gbase-T <full-duplex,flow-control>` automatically. Pings to gateway `10.10.0.1` and Hopper `10.10.145.26` show 0% loss and ~0.25 ms latency. Newton is now fully integrated into the 10G lab backbone.

### Current Assessment
The 10G path is fully operational. The HiFiber/OEM-style `SFP-10G-SR` optics are the correct match for this hardware stack. No further troubleshooting required.

### Comparison: Feynman Known-Good 10G Fiber
- Feynman 10G NIC is an Intel X710 SFP+ card (`i40e`, `enp2s0f0np0`) on USW-Aggregation port 2.
- UniFi reports port 2 at `speed: 10000` with MAC `6c:fe:54:1c:61:80`.
- Linux EEPROM read shows Feynman uses an `OEM` `SFP-10G-SR` module, 10G Base-SR, LC, 850nm, with clean optical diagnostics.
- The known-good Feynman modules were later identified operationally as HiFiber-branded optics; order the same brand/spec for Newton.
- This comparison led to the fix: Newton succeeded after moving the Feynman-style `OEM SFP-10G-SR` optics to the Sonnet setup. A follow-up test with the new Newton cable confirmed the cable was not the fault.

### Recovery Commands
If the link is physically changed and macOS gets stuck inactive:
```bash
networksetup -setMedia en8 autoselect
sleep 3
networksetup -setMedia en8 10Gbase-T full-duplex flow-control
networksetup -getMedia en8
ifconfig en8
ping -c 10 -S 10.10.110.110 10.10.0.1
```

Restore 1G baseline if needed:
   ```bash
networksetup -setMedia en8 1000baseT full-duplex
```

---

## OpenSoak Pi — Undervoltage / Power Supply

**Device:** Raspberry Pi 4 (`opensoak`, 10.10.169.191)
**Status:** ⚠️ ACTIVE — Pi currently throttled
**Discovered:** 2026-02-24 (via log review)

### Symptoms
- `vcgencmd get_throttled` returns `0x50005`:
  - Bit 0: Under-voltage **currently active**
  - Bit 2: ARM frequency capped (throttled) **currently active**
  - Bits 16, 18: Historical under-voltage and throttling recorded
- **275,584** undervoltage kernel events logged (all-time) — long-running issue
- Dense burst Feb 23 16:59–18:15 (~60+ events in ~75 min)
- Last logged event: `Feb 23 18:15:09 opensoak kernel: hwmon hwmon1: Undervoltage detected!`

### Impact
- Pi 4 CPU running at reduced frequency (performance degraded)
- App services (`opensoak.service`, `opensoak-frontend.service`) remain running — no crashes caused by undervoltage
- **Risk:** SD card corruption is possible if voltage dips become severe (writes during brownout)

### Root Cause
Likely underpowered USB power supply or resistive cable. Pi 4 requires **5V / 3A** minimum (15W); a USB-C PSU that negotiates only 5V/2A or uses a thin cable will trigger this.

### Fix
Replace the power supply with one of:
- Official Raspberry Pi 4 USB-C PSU (5.1V / 3A)
- Any quality 5V/3A USB-C adapter with a short, thick cable

**Do not use:** cheap USB chargers, phone chargers, or long/thin USB-C cables.

### Verification (after swap)
```bash
ssh -i ~/.ssh/id_rsa mcglothi@10.10.169.191
vcgencmd get_throttled
# Want: throttled=0x0 (or 0x50000 if historical bits remain but no active bits)
```

To clear historical bits (optional, for a clean reading after hardware fix):
```bash
# Not directly clearable via vcgencmd — requires reboot
sudo reboot
# Then re-check
vcgencmd get_throttled
# Should be 0x0 if power is stable
```

---

## Device Inventory

| Device | Model | Location | Power | Notes |
|--------|-------|----------|-------|-------|
| opensoak | Raspberry Pi 4 | Hot tub enclosure | USB-C (unknown PSU) | ⚠️ Undervoltage issue |
