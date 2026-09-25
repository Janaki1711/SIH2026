# SLIDE 3 — TECHNICAL APPROACH (EXCLUSIVE FOCUS DECK)

---

## 🎨 SLIDE 3 VISUAL ARCHITECTURE & CARD LAYOUT

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  (Code-Ons)                                    TECHNICAL APPROACH                                    [SIH 2026 LOGO] │
├───────────────────────────────────────────────────────────────────┬───────────────────────────────────────────────────┤
│  LEFT SECTION (65% Width): SYSTEM ARCHITECTURE & PROCESS FLOW     │  RIGHT CARD (35% Width): TECH STACK USED          │
│                                                                   │  ┌─────────────────────────────────────────────┐  │
│  [1] SYSTEM ARCHITECTURE DIAGRAM                                  │  │  Tech Stack Used:                           │  │
│      SENDER NODE (STT Mode):                                      │  │  • Android / Kotlin (Jetpack Coroutines)    │  │
│      Mic ➔ Oboe C++ NDK ➔ Silero VAD ➔ Whisper STT ➔               │  │  • C++20 / Android NDK / JNI Bridge         │  │
│      Sentence Tokenizer ➔ 64B Binary Pack ➔ AES-128 / RS-FEC     │  │  • Oboe Low-Latency Audio API               │  │
│                                                                   │  │  • Silero VAD (ONNX Runtime INT8)           │  │
│      COMMUNICATION LINK:                                          │  │  • whisper-tiny-south-indic (GGML Q8_0)     │  │
│      Wi-Fi Direct P2P Group / Bluetooth UDP Mesh Network          │  │  • IndicConformer ONNX C++ Engine           │  │
│                                                                   │  │  • Indic TTS Engine & Prosody Synthesizer   │  │
│      RECEIVER NODE (TTS Mode):                                    │  │  • ML Kit & PivotTranslator (Unicode)       │  │
│      UDP Capture ➔ RS-FEC Decode ➔ AES Decrypt ➔ Text             │  │  • Wi-Fi Direct (P2P) & Bluetooth BLE       │  │
│      Reconstruction ➔ Unicode Transliteration ➔ Indic TTS        │  │  • UDP Multicast Sockets & Mesh Routing     │  │
│                                                                   │  │  • Reed-Solomon FEC (255,223) & CRC32       │  │
│  [2] OPERATING MODES                                              │  │  • AES-128 Symmetric Data Encryption        │  │
│      • Walkie-Talkie / PTT Mode: Instant half-duplex voice.       │  │  • Room Database & SQLite Local Storage     │  │
│      • Normal Chat Mode: Asynchronous voice/text bubbles.         │  └─────────────────────────────────────────────┘  │
│      • Emergency Alert Mode: Broadcast at 100% volume (override). │                                                   │
│                                                                   │                                                   │
│  [3] MESH PACKET FRAMING                                          │                                                   │
│      [Header: 4B] | [SenderID: 8B] | [Lang: 2B] | [Payload: 64B] |  │                                                   │
│      [RS-FEC/CRC: 16B]                                            │                                                   │
└───────────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────┘
```

---

## 📋 SLIDE 3 CHATGPT GENERATION PROMPT (SLIDE 3 ONLY)

```text
Act as a senior System Architect and SIH Presentation Specialist. Generate the exact layout and text content for SLIDE 3 (TECHNICAL APPROACH) of our Smart India Hackathon 2026 presentation for "iTantra", strictly matching the layout of the reference SIH winners' slide.

SLIDE HEADER:
- Top-Left Circle: "Code-Ons"
- Center Title: "TECHNICAL APPROACH"
- Top-Right Badge: "SMART INDIA HACKATHON 2026"

RIGHT SIDE CARD (35% WIDTH) — "Tech Stack Used":
Create a prominent card box containing the complete technology stack:
- Android / Kotlin (Jetpack Coroutines, Material 3 UI)
- C++20 / Android NDK / JNI Native Bridge
- Oboe Low-Latency Audio API (16 kHz, 16-bit PCM)
- Silero VAD (ONNX Runtime INT8 C++ API)
- whisper-tiny-south-indic (GGML Q8_0, 43.5 MB)
- IndicConformer ONNX Engine
- Indic TTS Engine & Prosody Synthesizer
- ML Kit Offline Translation & PivotTranslator Engine
- Wi-Fi Direct (P2P) & Bluetooth BLE Transceivers
- UDP Multicast Sockets & Time-Division Mesh Routing
- Reed-Solomon Forward Error Correction (RS-FEC 255,223)
- AES-128 Symmetric Data Encryption & CRC32 Checksums
- Room Database & SQLite Local Audit Storage

LEFT SIDE CONTENT (65% WIDTH) — "System Architecture & Flow":

1. SYSTEM ARCHITECTURE PIPELINE:
   - Sender Node (STT Mode):
     Microphone Input ➔ Oboe C++ NDK ➔ Silero VAD (300ms pause detect) ➔ whisper-tiny-south-indic STT ➔ Sentence Tokenizer ➔ Compact Binary Compression (64B–128B) ➔ AES-128 Encryption ➔ RS-FEC Encoding
   - Communication Mesh Link:
     Peer-to-Peer Wi-Fi Direct Group Owner / Bluetooth BLE UDP Mesh Network
   - Receiver Node (TTS Mode):
     UDP Packet Capture ➔ RS-FEC Decoding ➔ AES-128 Decryption ➔ Text & Metadata Reconstruction ➔ Parallel Indic Unicode Transliteration ➔ Indic TTS Engine ➔ Intelligible Voice Output / Emergency Broadcast

2. OPERATING MODES:
   - Walkie-Talkie / PTT Mode: Half-duplex instant voice capture on press; auto-playback on receiver.
   - Normal Chat Mode: Asynchronous WhatsApp-style voice & text message bubbles.
   - Emergency Alert Mode: Non-interruptible broadcast played automatically at 100% volume, bypassing silent mode.

3. AI / ML ENGINE PIPELINE:
   - Input: 16 kHz Mono 16-bit PCM audio stream from Oboe C++ buffer.
   - VAD Filtering: Silero VAD evaluates 30ms windows; triggers STT after 300ms continuous silence.
   - STT Execution: Quantized `whisper_tiny_si_q8_0.bin` (43.5 MB) fine-tuned on 1,700 hrs Kathbath + 7,000 hrs Vaani datasets.

4. PACKET FRAMING & MESH PROTOCOL:
   - Binary Packet Framing: [Header: 4B] | [SenderID: 8B] | [LangCode: 2B] | [MsgSeq: 4B] | [Payload: 64-128B] | [RS-FEC/CRC: 16B]
   - Forward Error Correction: Reed-Solomon (255,223) code recovers up to 16 lost bytes per packet over noisy emergency links.
```
