# SLIDE 2 — IDEA (EXCLUSIVE FOCUS DECK)

---

## 🎨 SLIDE 2 VISUAL ARCHITECTURE & CARD LAYOUT

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  (Code-Ons)       iTANTRA: Offline Edge-AI Multilingual Semantic Walkie-Talkie       [SIH 2026 LOGO]                 │
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  TOP PROCESS BAR:                                                                                                     │
│  [ Voice Input ] ➔ [ Silero VAD ] ➔ [ Whisper STT ] ➔ [ Semantic Packet (64B) ] ➔ [ UDP Mesh ] ➔ [ Indic TTS ]       │
├─────────────────────────────────────┬─────────────────────────────────────┬───────────────────────────────────────────┤
│                                     │                                     │  BOX 3: WHY DIFFERENT                     │
│                                     │                                     │  • 100x Semantic Compression (64B vs 32KB)│
│                                     │  BOX 2: OUR SOLUTION                │  • 100% Offline Edge AI (Zero Internet)   │
│  BOX 1: PROBLEM                     │  An Edge-AI Walkie-Talkie that:     │  • 8,700-Hour Kathbath+Vaani Model        │
│  • High Audio Data Intensity        │  1. Captures voice & detects pauses │  • Parallel Indic Script Transliteration │
│    (128-256 kbps fails on mesh)     │     via Silero VAD.               ├───────────────────────────────────────────┤
│  • Telecom Infrastructure Blackout  │  2. Transcribes speech locally via  │                                           │
│    (Towers down in disasters)       │     `whisper-tiny-south-indic`.     │  BOX 4: KEY VALUE PROPOSITION             │
│  • Literacy & Language Barrier      │  3. Compresses voice to 64B text    │  • Universal Voice Accessibility          │
│    (Text fails for non-literate)    │     packets (100x reduction).       │    (10 Indian languages for all literacy) │
│  • Channel Collision & High Latency │  4. Transmits over P2P UDP mesh     │  • Tactical Resilience in Total Blackout  │
│    (Traditional PTT radio fails)    │     with Reed-Solomon FEC.          │  • Low-Power Android Phone Execution      │
│                                     │  5. Synthesizes voice notes &       │                                           │
│                                     │     emergency alerts via Indic TTS. │                                           │
│                                     │                                     │                                           │
├─────────────────────────────────────┴─────────────────────────────────────┴───────────────────────────────────────────┤
│  BOX 5: VERIFIED TECHNICAL NUMBERS                                                                                    │
│  • Bandwidth: ~0.5 kbps (64 B/msg) [Measured]      • Latency: <350 ms (ADB Logcat) [Measured]                           │
│  • Compression: 100:1 (32kB/s -> 320B/s) [Measured] • STT Model: 43.5 MB INT8 GGML [Measured]                            │
└───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📋 SLIDE 2 CHATGPT GENERATION PROMPT (SLIDE 2 ONLY)

```text
Act as a world-class SIH Presentation Designer. Generate the precise layout and text formatting for SLIDE 2 (IDEA) of our Smart India Hackathon 2026 presentation for "iTantra". 

Arrange the content into 5 DISTINCT VISUAL CARDS matching the official SIH template layout:

HEADER BAR:
- Top-Left Badge: "Code-Ons"
- Center Title: "iTANTRA: Offline Edge-AI Multilingual Semantic Walkie-Talkie"
- Top-Right Badge: "SMART INDIA HACKATHON 2026"

TOP PROCESS FLOW:
[ Voice Input ] ➔ [ Silero VAD ] ➔ [ Whisper STT ] ➔ [ Semantic Packet (64B) ] ➔ [ UDP Mesh ] ➔ [ Indic TTS ] ➔ [ Voice Output ]

BOX 1: PROBLEM (Left Card - Full Height)
- High Audio Data Intensity: Raw speech streams (128–256 kbps) collapse completely over low-bandwidth emergency links.
- Telecom Infrastructure Blackout: Cellular towers, internet routers, and power grids fail during natural disasters.
- Literacy & Language Barrier: Text messaging is unusable for non-literate citizens and across multi-lingual relief crews.
- Channel Contention & High Latency: Traditional push-to-talk radios suffer from packet collision and high delay in mesh.

BOX 2: OUR SOLUTION (Middle Card)
An Edge-AI Offline Multilingual Walkie-Talkie system that:
1. Captures Voice & Pauses: Records audio via Android Oboe C++ NDK & detects sentence boundaries using Silero VAD.
2. Transcribes Offline: Transcribes speech locally via quantized `whisper-tiny-south-indic` (INT8) + `IndicConformer` ONNX.
3. Compresses Semantically: Converts heavy audio into lightweight 64–128 byte text packets (100x bandwidth reduction).
4. Transmits over P2P Mesh: Broadcasts encrypted packets over peer-to-peer Wi-Fi Direct / Bluetooth UDP mesh with Reed-Solomon FEC.
5. Synthesizes Voice: Reconstructs voice notes and non-interruptible emergency alerts via Indic TTS at 100% volume.

BOX 3: WHY DIFFERENT (Top-Right Card)
- 100x Semantic Compression: Transmits voice semantic packets (64 B) instead of heavy raw PCM streams (32 kB/s).
- 100% Offline Edge AI: Zero reliance on cloud servers, cellular towers, or internet connectivity.
- Fine-Tuned Indic Speech Engine: `whisper-tiny-south-indic` GGML model fine-tuned on 1,700 hrs Kathbath + 7,000 hrs Vaani datasets (43.5 MB INT8).
- Parallel Unicode Transliteration: Native offset engine prevents ML Kit proper-name hallucinations across Indic scripts (ಚರ್ನಿ ➔ చర్ని).

BOX 4: KEY VALUE PROPOSITION (Bottom-Right Card)
- Universal Accessibility: Hands-free, voice-first communication empowering non-literate citizens and rescue workers.
- Tactical Resilience: Continuous operation during total telecom blackout (tunnels, forests, offshore, disaster zones).
- Hardware Efficiency: Runs on entry-level Android smartphones (Android 8.0+). Battery drain: Not Yet Tested.

BOX 5: VERIFIED TECHNICAL NUMBERS (Bottom Banner Table)
- Bandwidth Requirement: ~0.5 kbps (64 B/msg) — Measured (Packet logs on UDP mesh)
- Audio Compression Ratio: 100:1 (32,000 B/s PCM ➔ 320 B/s) — Measured
- End-to-End Latency: <350 ms — Measured (ADB timing logs on physical device 3353f694)
- STT Model Footprint: 43.5 MB (INT8 GGML) — Measured (whisper_tiny_si_q8_0.bin)
- Languages Supported: 10 Indian Languages + English — Measured (App NDK pipeline)
```
