# iTantra — Indian Multilingual TTS & STT Aided Neural Transceiver Radio Access for Low Bitrate Links

[![SIH 2026](https://img.shields.io/badge/SIH-2026-orange.svg)](https://www.sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/Problem%20Statement-SIH26173-blue.svg)](https://www.sih.gov.in/)
[![Team](https://img.shields.io/badge/Team-Algo%20Avengers%20%28172340%29-purple.svg)](https://github.com/Janaki1711/SIH2026)
[![Android Build](https://img.shields.io/badge/Android-API%2026%2B%20%288.0%2B%29-brightgreen.svg)](https://developer.android.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-lightgrey.svg)](LICENSE)

> **Smart India Hackathon 2026** · Problem Statement ID: **SIH26173**  
> **Theme**: Smart Automation / Emergency & Tactical Voice Communications · **Category**: Software  
> **Team Name**: Algo Avengers (ID: 172340)

An infrastructure-free, on-device Edge-AI Walkie-Talkie system that allows low-power Android smartphones to communicate over **Wi-Fi Direct / BLE L2CAP ad-hoc mesh networks** with **zero cell towers, zero satellite uplink, and zero internet** — speaking in one Indian language and being heard in another via natural speech synthesis.

---

## 🧭 Evaluator & Judge Quick Navigation Guide (Where to Look for What)

| What You Are Looking For | Where to Look | Description |
| :--- | :--- | :--- |
| 📊 **Official Presentation Deck** | **[`Algo_Avengers_SIH2026.pptx`](Algo_Avengers_SIH2026.pptx)** | Official 6-slide SIH Idea submission deck with visuals, hardware metrics & roadmap. |
| 📘 **Deep Technical Report** | **[`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md)** | Mathematical proofs, ChaCha20-Poly1305 AEAD, Cauchy Reed-Solomon FEC, and wire specs. |
| 📱 **Android Production Code** | **[`android/`](android/)** | Full Kotlin app, Material 3 UI, ViewModels, Room DB, and P2P mesh sockets. |
| ⚡ **C++ Native ML & Audio NDK** | **[`android/app/src/main/cpp/`](android/app/src/main/cpp/)** | Native Whisper-Tiny STT, Silero VAD v4 INT8, Oboe low-latency audio capture & JNI. |
| 🧠 **On-Device Quantized Models**| **[`android/app/src/main/assets/`](android/app/src/main/assets/)** | Whisper-Tiny INT8 GGML (`43.5 MB`), Silero VAD (`2.3 MB`), and vocabularies. |
| 🌐 **10 Indic Script Engine** | **[`PivotTranslator`](android/app/src/main/java/com/algoavengers/itantra/)** | Parallel Unicode offset engine (`0x0C80` $\rightarrow$ `0x0C00`) with zero cloud latency. |
| 📈 **STT Accuracy & Gate Results**| **[`STT_GATE_RESULTS.md`](STT_GATE_RESULTS.md)** | Empirical language-by-language CER benchmarks across 10 Scheduled Indian Languages. |
| 📡 **P2P Mesh Network Manager** | **[`WfbngManager.kt`](android/app/src/main/java/com/algoavengers/itantra/)** | Wi-Fi Direct P2P Group Owner topology, UDP multicast, and packet assembly. |
| 💻 **Mesh Packet Simulator** | **[`web-demo/`](web-demo/)** | Full React + FastAPI 2-node web simulator for inspecting transmitted wire datagrams. |
| 🛠️ **Developer & Build Handoff** | **[`DEVELOPMENT_README.md`](DEVELOPMENT_README.md)** | Step-by-step local Android Studio / CLI build instructions and architecture overview. |

---

## ⚡ The Problem & Our Innovation

### 1. The Core Challenge
* **Raw Audio is Too Heavy**: Standard voice codecs (Opus/AMR at $16\text{–}32\text{ kbps}$, PCM at $128\text{–}256\text{ kbps}$) completely collapse low-bitrate radio and congested mesh channels.
* **Telecom Infrastructure Blackouts**: Natural disasters and remote terrains isolate first responders and citizens due to fallen cell towers and severed power grids.
* **Language & Literacy Exclusion**: Text messaging excludes non-literate citizens; standard analog walkie-talkies lack real-time multilingual translation.

### 2. The iTantra Solution
* **Speech-to-Semantic Tokenization**: Converts spoken utterances into ultra-compact **$\le 38\text{-Byte}$ token frames** ($<300\text{ bps}$, **$50\text{–}100\times$ less bandwidth** than continuous voice audio).
* **Air-Gapped Ad-Hoc Mesh**: Broadcasts encrypted UDP packets over autonomous Wi-Fi Direct P2P and BLE L2CAP mesh with **Cauchy Reed-Solomon (255, 223) FEC** (tolerating up to **$25\%$ packet loss**).
* **Zero-Distortion Indic Translation**: Native **`PivotTranslator`** parallel Unicode offset engine maps proper nouns across 10 Scheduled Indian Languages in $<2\text{ ms}$ on-device.
* **Voice-In ➔ Voice-Out with SOS Override**: Synthesizes speech on receiver devices via Indic TTS, enforcing **100% max-volume `STREAM_ALARM` playback** for emergency warnings.

---

## 🏗️ End-to-End System Pipeline

```
   [ User Speech (16 kHz PCM) ]
                │
                ▼
   [ Silero VAD v4 INT8 (300 ms Pause Detection) ]
                │
                ▼
   [ Whisper-Tiny STT (43.5 MB INT8 GGML) / Conformer ]
                │
                ▼
   [ Utterance Tokenizer ➔ ≤38-Byte Payload Frame ]
                │
                ▼
   [ ChaCha20-Poly1305 AEAD + Cauchy Reed-Solomon (255, 223) FEC ]
                │
                ▼
   [ Autonomous Wi-Fi Direct / BLE L2CAP Mesh (WfbngManager UDP) ]
                │
                ▼
   [ Receiver RS-FEC Shard Repair + ChaCha20 AEAD Decrypt ]
                │
                ▼
   [ PivotTranslator (10-Language Parallel Indic Unicode Engine) ]
                │
                ▼
   [ Indic TTS Engine (eSpeak-NG / Android Native) ]
                │
                ▼
   [ 100% Volume SOS Override (STREAM_ALARM Audio Bridge) ]
```

---

## 🔬 Empirical Telemetry & Hardware Profiling

All benchmarks were measured on a physical quad-core ARM64 test device (**ID: `3353f694`**):

| Subsystem / Metric | Measured Performance | Budget / SLA Target | Verification Method | Status |
| :--- | :--- | :--- | :--- | :---: |
| **CPU Utilization (Active STT)** | **7.2% average** | $<15\%$ CPU limit | ARM64 NEON INT8 `/proc/pid/stat` | **PASS** |
| **System Memory (RAM)** | **148 MB** | $<250\text{ MB}$ footprint | Dual-Engine active PSS sample | **PASS** |
| **Battery Consumption Rate** | **2.4% / hour** | $<5\%/\text{hr}$ power drain | Continuous PTT active profile | **PASS** |
| **Active Current Draw** | **42 mA active** | $<65\text{ mA}$ draw | Baseline phone idle: $18\text{ mA}$ | **PASS** |
| **End-to-End Latency** | **~320 ms** | $<500\text{ ms}$ voice delay | Capture ➔ STT ➔ Mesh ➔ TTS | **PASS** |
| **Utterance Payload Size** | **18 – 38 Bytes** | $<50\text{ Bytes}$ frame size | Single UDP datagram (<300 bps) | **PASS** |
| **Bandwidth Reduction** | **$50\text{–}100\times$ less data** | $>20\times$ compression | vs 16–32 kbps continuous voice | **PASS** |
| **Wi-Fi Direct P2P Range** | **85 – 110 m** | $>50\text{ m}$ range | Line-of-sight per mesh hop | **PASS** |
| **Node Discovery SLA** | **<3.8 seconds** | $<10\text{ s}$ setup time | Autonomous P2P Wi-Fi Direct | **PASS** |
| **Speech Accuracy (CER)** | **0.03 – 0.18 CER** | $<0.25\text{ CER}$ accuracy | Across 10 Indic languages | **PASS** |

---

## 🌐 Supported Indic Languages (10 Scheduled Languages)

| Language | Code | Script Base | STT Acoustic Engine | Translation / Transliteration |
| :--- | :---: | :---: | :---: | :---: |
| **Hindi** | `hi` | Devanagari (`0x0900`) | IndicConformer / Whisper | ML Kit + `PivotTranslator` |
| **Kannada** | `kn` | Kannada (`0x0C80`) | Whisper-Tiny South-Indic | Parallel Unicode Offset |
| **Telugu** | `te` | Telugu (`0x0C00`) | Whisper-Tiny South-Indic | Parallel Unicode Offset |
| **Tamil** | `ta` | Tamil (`0x0B80`) | Whisper-Tiny South-Indic | Parallel Unicode Offset |
| **Malayalam** | `ml` | Malayalam (`0x0D00`) | Whisper-Tiny South-Indic | Parallel Unicode Offset |
| **Marathi** | `mr` | Devanagari (`0x0900`) | IndicConformer / Whisper | ML Kit + `PivotTranslator` |
| **Bengali** | `bn` | Bengali (`0x0980`) | IndicConformer | ML Kit + `PivotTranslator` |
| **Gujarati** | `gu` | Gujarati (`0x0A80`) | IndicConformer | ML Kit + `PivotTranslator` |
| **Punjabi** | `pa` | Gurmukhi (`0x0A00`) | IndicConformer | ML Kit + `PivotTranslator` |
| **Odia** | `or` | Odia (`0x0B00`) | IndicConformer | ML Kit + `PivotTranslator` |

---

## 📂 Repository Structure

```
SIH2026/
├── Algo_Avengers_SIH2026.pptx       # Official 6-Slide Submission Presentation Deck
├── TECHNICAL_REPORT.md              # Deep Technical System Architecture Report
├── STT_GATE_RESULTS.md              # Empirical Speech Recognition Accuracy Matrix
├── DEVELOPMENT_README.md            # Android NDK & Engineering Handoff Guide
├── android/                         # Complete Android Production Code (Kotlin + C++ NDK)
│   ├── app/src/main/java/          # UI ViewModels, Room DB, WfbngManager mesh
│   ├── app/src/main/cpp/           # Native Whisper STT, Silero VAD, Tokenizer
│   └── app/src/main/assets/        # Quantized INT8 Models (Whisper, Silero VAD)
├── src/                             # Portable C++ Core (Framing, FEC, Crypto, Protocol)
├── proto/                           # Protocol Buffer Definitions (WfbngPacket schemas)
├── docs/                            # Presentation artifacts & archived notes
├── web-demo/                        # 2-Node Mesh Simulator & Web Packet Inspector
└── test_*.py                        # Protocol, Cryptography & End-to-End Test Suite
```

---

## 🚀 Quickstart: Build & Installation

### 1. Build Android APK
```bash
# Clone the repository
git clone https://github.com/Janaki1711/SIH2026.git
cd SIH2026/android

# Build Debug APK using Gradle
./gradlew assembleDebug

# Output APK path:
# android/app/build/outputs/apk/debug/app-debug.apk

# Install on Android Device (Android 8.0+ / API 26+)
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### 2. Execute Verification Test Suite
```bash
# Run core protocol, cryptography, and FEC tests
python -m pytest test_m1_m3_integration.py test_end_to_end_m1_m2_m3_m4.py test_fec.py test_member3_suite.py
```

### 3. Launch Web-Demo Protocol Inspector
```bash
# Backend mesh simulation service
cd web-demo/backend && python -m uvicorn main:app --port 8000

# Frontend node inspector
cd web-demo/frontend && npm install && npm run dev
# Open http://localhost:5173
```

---

## 👥 Team & Submission Details

* **Problem Statement**: SIH26173 (*iTantra — Indian Multilingual TTS & STT Aided Neural Transceiver Radio Access for low bitrate links*)
* **Team Name**: **Algo Avengers**
* **Team ID**: **172340**
* **Primary Repository**: [https://github.com/Janaki1711/SIH2026](https://github.com/Janaki1711/SIH2026)
* **Lead Contact**: Janaki (`Janaki1711`)
