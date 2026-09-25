# SLIDE 4 — FEASIBILITY AND VIABILITY (WITH CPU & POWER METRICS)

---

## 🎨 SLIDE 4 VISUAL CARD LAYOUT (WITH HARDWARE PERFORMANCE DIAGNOSTICS)

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  (Code-Ons)                                   FEASIBILITY AND VIABILITY                              [SIH 2026 LOGO]  │
├───────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────┤
│  TOP-LEFT CARD (60% Width): RISK ASSESSMENT & MITIGATION          │  TOP-RIGHT CARD (40% Width): OPERATIONAL          │
│  ┌─────────────────────────────────────────────────────────────┐  │  FEASIBILITY & HARDWARE OVERHEAD                  │
│  │ Risk: Limited RAM & CPU on Low-Cost Phones                  │  │  ┌─────────────────────────────────────────────┐  │
│  │ ➔ Solution: 8-bit Model Quantization + C++ Native Execution │  │  │ • Target Hardware: Android 8.0+ budget      │  │
│  │                                                             │  │  │   handsets (price N/Y/T).                   │  │
│  │ Risk: Packet Loss over Wireless Emergency Links             │  │  │ • CPU Usage: live in-app diag panel         │  │
│  │ ➔ Solution: Reed-Solomon RS(255,223) FEC + UDP Retry Queue  │  │  │   Not Yet Tested as an average.             │  │
│  │                                                             │  │  │ • Power Draw: Not Yet Tested.               │  │
│  │ Risk: Name Distortion Across Languages                      │  │  │   No mA figure printed.                     │  │
│  │ ➔ Solution: PivotTranslator Parallel Indic Unicode Engine   │  │  │ • RAM: app PSS, live in panel.              │  │
│  │                                                             │  │  │ • 100% Offline: Zero cell/cloud reliance.   │  │
│  │ Risk: Signal Overlap in Multi-Device Mesh                   │  │  └─────────────────────────────────────────────┘  │
│  │ ➔ Solution: Time-Division Sender Queue + SenderID Headers   │  ├───────────────────────────────────────────────────┤
│  └─────────────────────────────────────────────────────────────┘  │  BOTTOM-RIGHT CARD (40% Width): ECONOMIC          │
├─────────────────────────────────────┬─────────────────────────────┤  APPROACH & VIABILITY                             │
│  BOTTOM-LEFT CARD: EMPIRICAL        │  PROVEN DATASETS & SPECS    │  ┌─────────────────────────────────────────────┐  │
│  FIELD MEASUREMENTS                 │  • Kathbath (1,700 hrs)     │  │ • Capex: replaces radio hardware            │  │
│  ┌────────────────────────────────┐ │  • Vaani (7,000 hrs)        │  │   with existing handsets; N/Y/T.            │  │
│  │ • STT CER: 0.03–0.34           │ │  • Silero VAD (2.3 MB)      │  │ • Opex Savings: 100x payload compression    │  │
│  │ • Decode 0.4–4.4 s / 3.0 s     │ │  • Android Oboe NDK         │  │   (32 kB/s -> 0.32 kB/s text payload).      │  │
│  │ • Payload ≤38 B ≈0.5 kbps      │ │  • ChaCha20-Poly1305 AEAD   │  │ • Market Size: $18.4 Billion in 2024        │  │
│  │ • STT Model Footprint: 43.5 MB │ │  • Wi-Fi Direct Mesh        │  │   ($34.8 Billion by 2030 @ 11.2% CAGR).     │  │
│  │ • Mesh latency <350 ms         │ │                             │  │ • Revenue Streams: B2G NDRF/Defense, B2B    │  │
│  │ • CPU/power/RF/WER: N/Y/T      │ │                             │  │   Mining/Energy, OEM SDK, Support AMC.      │  │
│  └────────────────────────────────┘ │                             │  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────┴─────────────────────────────┴───────────────────────────────────────────────────┘
```

---

## 📋 SLIDE 4 CHATGPT GENERATION PROMPT (WITH CPU & POWER DIAGNOSTICS)

```text
Act as a senior Feasibility Specialist and SIH Presentation Designer. Generate the concise visual text for SLIDE 4 (FEASIBILITY AND VIABILITY) of our Smart India Hackathon 2026 presentation for "iTantra", including live hardware metrics (CPU, Power, Latency).

SLIDE HEADER:
- Top-Left Circle: "Code-Ons"
- Center Title: "FEASIBILITY AND VIABILITY"
- Top-Right Badge: "SMART INDIA HACKATHON 2026"

TOP-LEFT CARD (60% WIDTH) — "Risk Assessment and Mitigation":
Format cleanly as Risk ➔ Mitigation blocks:
- Risk: Limited Memory & CPU on Budget Mobile Hardware
  ➔ Mitigation: 8-bit Model Quantization + ONNX Runtime C++ Native Execution.
- Risk: High Packet Loss & RF Interference over Wireless Links
  ➔ Mitigation: Reed-Solomon RS(255,223) Error Correction (recovers 16 lost bytes/packet) + UDP Retry Queue.
- Risk: Distortion of Proper Names Across Indian Languages
  ➔ Mitigation: Custom `PivotTranslator` Parallel Indic Unicode Script Engine (0x0C80 ➔ 0x0C00).
- Risk: Channel Collisions & Overlap in Multi-Node Mesh
  ➔ Mitigation: Time-Division Sender Queue + Unique SenderID Packet Headers.

TOP-RIGHT CARD (40% WIDTH) — "Operational Feasibility & Hardware Overhead":
- Target Hardware: Entry-level Android smartphones (Android 8.0+ / API 26+).
- CPU Utilization: shown live in the in-app diagnostics panel (500 ms /proc delta). Not Yet Tested for an idle-vs-load figure.
- Power Draw & Battery: Not Yet Tested — no current draw measured on device 3353f694. Do NOT print a mA figure.
- RAM Memory Footprint: app PSS reported live in the diagnostics panel. Not Yet Tested for a "during STT inference" figure.
- Zero Infrastructure: 100% offline deployment (no external cell towers, satellite, or cloud).

BOTTOM-LEFT CARD — "Validation & Field Measurements":
What is actually measured, and how:
- STT CER 0.03–0.34 across hi/gu/te/ta/kn/ml/bn/pa [Measured, STT_GATE_RESULTS.md, Sep 2026, laptop + device 3353f694].
- STT decode latency: conformer 0.4–0.5 s, whisper-south 1.3–4.4 s for 3.0 s audio [Measured, device 3353f694, Sep 2026].
- STT model disk footprint: 43.5 MB (whisper_tiny_si_q8_0.bin, q8_0) + 197 MB conformer [Measured, APK assets].
- VAD model disk footprint: 2.3 MB ONNX [Measured, assets/silero_vad.onnx = 2,327,524 B].
- Mesh transport latency: <350 ms end-to-end [Measured, ADB benchmark, device 3353f694] — transport only, excludes STT/TTS.
- Payload: ≤38 B frame, ≈0.5 kbps/msg [Measured, packet capture logs on UDP mesh].
- CPU load, power draw, P2P RF range (80–120 m), aggregate WER: Not Yet Tested. Do NOT print numbers for these.

BOTTOM-MIDDLE CARD — "Proven Datasets & Frameworks":
- Fine-Tuned Whisper-Tiny ML Model
- Kathbath (1,700 hrs) + Vaani (7,000 hrs) Speech Datasets
- Silero VAD v4 Engine
- Android Oboe Low-Latency NDK
- ChaCha20-Poly1305 AEAD Encryption Engine
- Wi-Fi Direct P2P Protocol

BOTTOM-RIGHT CARD (40% WIDTH) — "Economic Approach & Viability":
- Capex Reduction: replaces dedicated satellite/VHF radios with existing Android handsets. Unit prices Not Yet Tested — do NOT print $ figures.
- Opex Savings: 100x payload compression cuts transmission data volume from 32 kB/s to 0.32 kB/s.
- Critical Communications Market: $18.4 Billion in 2024 ($34.8 Billion by 2030 at 11.2% CAGR; Source: MarketsandMarkets 2024).
- Revenue Streams:
  1. B2G Government Procurement: Custom deployment for NDRF, Police, and Defense.
  2. B2B Industrial Enterprise: Licensing for mining, offshore oil rigs, and logistics.
  3. OEM SDK Integration: SDK licensing for rugged handset manufacturers.
  4. Maintenance & Support: Annual support contracts and domain-custom dictionaries.
```
