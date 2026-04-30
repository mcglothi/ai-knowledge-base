---
tags: [unmanic, transcoding, plex, hevc, nvidia, babbage]
hosts: [babbage]
last_updated: 2026-04-05
---

# Unmanic
**Last Updated:** 2026-04-05
**Summary:** Media optimization service for transcoding library files to efficient formats.

## Configuration
- **Host:** babbage (TrueNAS SCALE)
- **Path:** `/mnt/Containers/Unmanic/.unmanic`
- **Library Path:** `/library/video/movies` -> `/mnt/Data/Media/video/movies`
- **Hardware Acceleration:** NVIDIA GPU (NVENC) enabled.

## Optimization Strategy (Set 2026-04-05)
- **Plugin:** `video_transcoder` (replaced legacy H265 plugin to enable force-transcoding).
- **Target Codec:** HEVC (H265).
- **Target Bitrate:** 15 Mbps (aiming for 12-15GB file sizes for 4K content).
- **Resolution:** Source (preserves 4K but compresses heavily).
- **Force Transcode:** Enabled (processes files even if already in HEVC to meet bitrate target).

## Observations
- **4K Dominance:** ~52% of the movie library is 4K.
- **Buffering Issue:** Files >20GB were causing remote streaming bottlenecks.
- **Radarr Profile:** Currently using a single "Any" profile that prefers high-bitrate 4K.
- **Recommendation:** Future work should include a 1080p-only profile in Radarr for non-essential movies to reduce initial download sizes.
