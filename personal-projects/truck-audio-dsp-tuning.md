---
context: personal
tags: [truck-audio, car-audio, helix, dsp, rew, audiofrog, sundown-audio, ford-f150, tuning]
last_updated: 2026-03-31
---

# Truck Audio DSP Tuning
**Last Updated:** 2026-03-31
**Summary:** Ongoing personal tuning project for the 2017 Ford F-150 Platinum audio system: HELIX DSP Pro Mk2, active 3-way front stage, dual SD-3 10-inch subs, a three-preset retune strategy for driver/passenger/balanced listening, and a longer-term concept for a custom onboard AI-driven DSP/source platform.

## System Snapshot
- **Vehicle:** 2017 Ford F-150 Platinum with stock Sync 3 head unit retained
- **DSP:** HELIX DSP Pro Mk2
- **Sub stage:** Sundown Audio 1500 W amplifier on two Sundown Audio SD-3 10-inch subs
- **Front stage amps:** two Zapco Studio 500 W amplifiers
- **Front stage speakers:** Audiofrog GS690 door midbass, Audiofrog GB25 midrange, Audiofrog GB10 tweeter
- **Installation notes:** GS690s are mounted low in sealed, fully sound-deadened doors; GB25 and GB10 are mounted high in 3D-printed dash pods for stage height
- **Sources:** Spotify from phone plus a 2 TB drive with uncompressed music via USB into Sync 3

## Tuning Workflow Used So Far
- Start with physical distance measurements from each driver to the center of the head position and use those as initial delay values
- Measure each single driver with pink noise while moving the mic gently between left and right ear positions to create a localized spatial average
- Measure key driver combinations afterward: adjacent band handoffs and full left/right front-stage blends
- Import measurements into REW and use them to refine delay, phase/polarity, crossover points, and PEQ
- Target a JBL-style house curve with slightly more brightness and a little more sub bass
- Avoid boosting narrow dips aggressively; prefer peak reduction and then listening-based refinement

## Project Goal
Move from a single strong driver-seat tune to a more intentional three-preset system:

1. **Driver SQ**
   Best imaging, stage focus, and tonal balance for the driver seat.
2. **Passenger SQ**
   Full passenger-seat tune measured from that position instead of simply mirroring driver delays.
3. **Social / Balanced**
   A cabin-friendly preset with reduced time-alignment bias, broader EQ moves, and better tonal consistency across multiple seats.

## Current Planning Decisions
- Do fresh passenger-seat measurements rather than flipping driver delay values
- Create a third preset that intentionally reduces or removes aggressive left/right time alignment for a more shared listening experience
- Keep crossover, polarity, and delay decisions separate from EQ decisions during each tuning round
- Use the work Windows 11 laptop as the likely HELIX programming machine; keep REW measurements and analysis flexible across Mac/Windows

## Starting Crossover Plan
These are starting points only and should be validated by measurement and listening:

- **Sub -> GS690:** 70 Hz LR24
- **GS690 -> GB25:** 250 to 315 Hz LR24, with 280 Hz as a likely compromise starting point
- **GB25 -> GB10:** 3.2 kHz LR24

### Notes Behind The Starting Points
- Keep the GS690 low enough in frequency to avoid losing stage height to the doors
- Let the dash-mounted GB25 carry more lower-midrange information than a typical low-door midbass / high-dash mid handoff would
- Keep the GB10 handoff conservative at first for protection and easier blending

## Measurement Plan For The Next Retune
- Save/export the current known-good driver preset before making structural changes
- Rebuild or validate the driver-seat tune with structured single-driver and combination measurements
- Re-measure the passenger seat from scratch
- Build the balanced preset from multiple measurement positions across the front row instead of from a single head position

## Open Questions
- Whether 250 Hz, 280 Hz, or 315 Hz is the best GS690-to-GB25 handoff in this truck once stage height and GB25 strain are compared directly
- Whether 63 Hz, 70 Hz, or 80 Hz is the best sub-to-midbass handoff in the actual enclosure/door environment
- How much time alignment should remain in the balanced preset before the image collapses less than desired

## Next Steps
- Build a repeatable worksheet for all three presets
- Define a fixed measurement naming scheme for REW captures
- Compare crossover sets systematically instead of moving one value at a time ad hoc
- Document listening tracks and decision criteria for stage height, blend, strain, and bass localization

## Longer-Term Concept: Custom Onboard AI DSP
- Long-range idea is to replace or sit in front of the current source/DSP path with a custom onboard compute platform such as a Jetson Orin Nano or similar embedded system
- The platform would act as the primary source, likely with mobile-router plus 5G connectivity for streaming, local storage, and a full web UI for advanced tuning and system management
- Fixed microphones installed near the listening positions, likely in the driver and passenger headrests, would enable repeatable seat-specific measurement and adaptive correction
- A simple physical feedback interface with hard buttons would allow fast in-car rating after tracks, while optional voice memos would let the user describe subjective issues such as bass level, harshness, raspiness, or stage problems
- The longer-term software goal is an onboard AI agent that combines objective measurements with subjective feedback and gradually improves tuning in a controlled, versioned, reversible way
- This does not appear to exist as a mainstream aftermarket product yet; adjacent OEM/Tier-1 capabilities exist, but the full objective-plus-subjective adaptive loop still looks open as a personal R&D direction
