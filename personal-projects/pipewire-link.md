---
tags: [pipewire, audio, feynman, systemd, linux, usb, dac, sound]
hosts: [feynman]
last_updated: 2026-02-19
---

# pipewire-link
**Last Updated:** 2026-02-19
**Summary:** Bash script to automatically link specific PipeWire audio sources to sinks. feynman only.

## Environment Requirements
- **Machine:** `feynman` only — tied to specific USB audio hardware physically attached to that machine
- **Tools:** `pw-link` (PipeWire), `systemctl`
- **Platform:** Linux / systemd

## Overview
Ensures a persistent connection between a specific USB PnP Audio Device and a HiFimeDIY DAC, which may otherwise need manual re-linking after re-plugging or restarts.

## Components
- **Script:** `/home/mcglothi/code/pipewire-link/setup_pipewire_link.sh`
- **Service:** `/home/mcglothi/code/pipewire-link/pipewire-link.service` (Runs script on startup/session)

## Source/Sink Configuration
- **Source:** `alsa_input.usb-0c76_USB_PnP_Audio_Device-00.iec958-stereo`
- **Sink:** `alsa_output.usb-HiFimeDIY_SA9227_USB_Audio-01.iec958-stereo`
