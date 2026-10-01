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
│      Sentence Tokenizer ➔ UTF-8 Text ➔ ChaCha20 + RS-FEC         │  │  • Oboe Low-Latency Audio API               │  │
│                                                                   │  │  • Silero VAD (ONNX Runtime INT8)           │  │
│      COMMUNICATION LINK:                                          │  │  • whisper-tiny-south-indic (GGML Q8_0)     │  │
│      Wi-Fi Direct P2P Group / Bluetooth UDP Mesh Network          │  │  • IndicConformer ONNX C++ Engine           │  │
│                                                                   │  │  • Indic TTS Engine & Prosody Synthesizer   │  │
│      RECEIVER NODE (TTS Mode):                                    │  │  • ML Kit & PivotTranslator (Unicode)       │  │
│      UDP Capture ➔ RS-FEC Decode ➔ AES Decrypt ➔ Text             │  │  • Wi-Fi Direct (P2P) & Bluetooth BLE       │  │
│      Reconstruction ➔ Unicode Transliteration ➔ Indic TTS        │  │  • UDP Multicast Sockets & Mesh Routing     │  │
│                                                                   │  │  • Cauchy RS K=8/M=4 FEC (12 shards)        │  │
│  [2] OPERATING MODES                                              │  │  • AES-256-GCM fallback, ChaCha20 AEAD      │  │
│      • Walkie-Talkie / PTT Mode: Instant half-duplex voice.       │  │  • Room Database & SQLite Local Storage     │  │
│      • Normal Chat Mode: Asynchronous voice/text bubbles.         │  └─────────────────────────────────────────────┘  │
│      • Emergency Alert Mode: Broadcast at 100% volume (override). │                                                   │
│                                                                   │                                                   │
│  [3] MESH PACKET FRAMING                                          │                                                   │
│      [magic:1|ttl:1|seq:2|origin:16|target:16|shard:2|len:2] |      │                                                   │
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
- Cauchy Reed-Solomon GF(2⁸) Forward Error Correction (K=8 data + M=4 parity = 12 shards)
- ChaCha20-Poly1305 AEAD with AES-256-GCM fallback (Poly1305 tag; no CRC in the TX path)
- Room Database & SQLite Local Audit Storage

LEFT SIDE CONTENT (65% WIDTH) — "System Architecture & Flow":

1. SYSTEM ARCHITECTURE PIPELINE:
   - Sender Node (STT Mode):
     Microphone Input ➔ Oboe C++ NDK ➔ Silero VAD (32 ms chunks) ➔ whisper-tiny-south-indic STT ➔ Sentence Tokenizer ➔ UTF-8 Transcript (42 B measured) ➔ ChaCha20-Poly1305 ➔ RS-FEC (K=8, M=4) Encoding
   - Communication Mesh Link:
     Peer-to-Peer Wi-Fi Direct Group Owner / Bluetooth BLE UDP Mesh Network
   - Receiver Node (TTS Mode):
     UDP Packet Capture ➔ RS-FEC Decoding ➔ ChaCha20-Poly1305 Decryption ➔ Text & Metadata Reconstruction ➔ Parallel Indic Unicode Transliteration ➔ Indic TTS Engine ➔ Intelligible Voice Output / Emergency Broadcast

2. OPERATING MODES:
   - Walkie-Talkie / PTT Mode: Half-duplex instant voice capture on press; auto-playback on receiver.
   - Normal Chat Mode: Asynchronous WhatsApp-style voice & text message bubbles.
   - Emergency Alert Mode: Non-interruptible broadcast played automatically at 100% volume, bypassing silent mode.

3. AI / ML ENGINE PIPELINE:
   - Input: 16 kHz Mono 16-bit PCM audio stream from Oboe C++ buffer.
   - VAD Filtering: Silero VAD evaluates 512-sample (32 ms) chunks, speech gate 0.25; recording auto-stops after 10 s of silence (VAD_SILENCE_TIMEOUT_MS=10000). Pause-triggered sentence formation is NOT yet implemented — STT fires on PTT release.
   - STT Execution: Quantized `whisper_tiny_si_q8_0.bin` (43.5 MB) (parambharat/whisper-tiny-south-indic), released already trained on south-Indic speech. Fine-tune on Kathbath/Vaani is P2 — not yet run.

4. PACKET FRAMING & MESH PROTOCOL:
   - Binary Packet Framing: [Wfbng hdr 40B = magic 1 | ttl 1 | seq 2 | origin 16 | target 16 | shard 2 | len 2] + [RS shard 10B] = 50 B/datagram [Measured, device 3353f694]
   - Forward Error Correction: Cauchy Reed-Solomon GF(2⁸), K=8/M=4, recovers any 4 of the 12 shards lost over noisy emergency links.
```
