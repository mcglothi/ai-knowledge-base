---
context: personal
---
# Project: Dream Vault (Somnium / Remnant)
**Last Updated:** 2026-04-04
**Status:** ✅ DESIGN PHASE (In-Progress)
**Summary:** A dedicated bedside AI device (physical box) for private, local dream recording, interpretation, and long-term analysis.

---

## 1. The Core Concept
A phone-free, single-purpose hardware device on the nightstand. One-tap to record dream recollections upon waking. No cloud, no apps, just a private "Vault" for the subconscious.

### Naming Ideas
- **Somnium:** Scientific, secure, high-end "vault" vibe.
- **Remnant:** Poetic, human, focused on catching "fragments" before they fade.
- **Noctua:** The watchful "owl" on the nightstand.
- **DreamDial:** Emphasizes the physical interaction.

---

## 2. Key Differentiation (The "Vault" Angle)
Unlike current dream apps that process data in the cloud (OpenAI/Gemini APIs), this product is **100% Local-First**.

- **Hardware:** Based on **Raspberry Pi 5** (utilizing the Modem Dream Recorder open-source shell/hardware list).
- **Intelligence:** 
  - **Whisper.cpp (Tiny):** Local transcription.
  - **Llama 3.2 (1B/3B):** Local interpretation.
  - **ChromaDB / SQLite-VSS:** Local vector database for long-term memory.
- **Security:** Air-gapped capable. Your most private thoughts never touch a server.

---

## 3. High-Signal Features
### A. The Personal Lexicon
The AI "learns" the user's personal symbols.
- Example: "Lobster = Father" (overriding generic "Snake = Enemy" interpretations).
- Correlates with waking-life context to build a private dictionary of your mind.

### B. The Celestial Context
Integrated offline astrology engine (`Skyfield`).
- Maps dreams to Moon Phases, Retrogrades, and Transits.
- Correlates emotional "vividness" with the "Dream Sky."

### C. The Global Lens Dial
Interpretation from multiple world philosophies:
- **Hindu (Swapna Shastra):** Symbols as omens and prophecy.
- **Buddhist (Milam):** Lucidity and "Emptying" the dream as a rehearsal for the Bardo.
- **Indigenous (Vision Quest):** Searching for guardian spirit "allies."
- **Zulu (Amadlozi):** Ancestral visits and family-tree health.
- **Islamic (Ru'ya):** Categorizing "True" prophecy vs. psychological noise.
- **Mayan (Nagual):** Tracking your spirit companion’s health.

---

## 4. Next Steps
1.  **Hardware Prototyping:** Validating local LLM performance (Llama 3.2 1B/3B) on Pi 5.
2.  **UI Design:** Designing the "Global Dial" and "Long-term Analysis" dashboard.
3.  **Local Lexicon Logic:** Defining the vector-mapping strategy for "Lobster = Dad" overrides.

---
*Created during a Gemini CLI session on April 4, 2026.*
