# iTantra M3 — Emergency Communication Protocol (SIH 2026)

This repository contains the core implementation of the **iTantra M3 Protocol**, designed for robust, low-bandwidth, multi-lingual emergency communication.

The project is divided into two primary parts:
1. **M3 C++ Protocol Engine**: The core, highly optimized protocol implementation handling packet serialization and encoding.
2. **Web Demonstration**: A complete local simulation of two nodes (Hubbli & Tolankere) demonstrating the protocol pipeline in a graphical tactical interface.

---

## 1. Web Demonstration (Frontend & Backend)

The web demo is located in the `/web-demo` directory. It uses a **React/Vite** frontend and a **Python/FastAPI** backend to simulate a live connection between two hardware nodes over WebSocket. 

**M3 Semantic Communication (NEW):**
The web demo now features the core innovation of iTantra M3: Semantic Communication. Natural language is parsed into structured tactical semantics (ACTION, TARGET, URGENCY, etc.) and packed into ultra-compact binary payloads (typically ~4 bytes), bypassing the need to send full UTF-8 strings. The UI provides full visibility into this process with a dynamic Codebook, a Field Inspector, and compression metric comparisons.

### Features
- **Tactical Dashboard**: A React-based tactical user interface with realistic, multi-lingual PTT (Push-To-Talk) communications.
- **Semantic Message Panel (NEW)**: Expandable panel showing the exact fields extracted, their encoded binary representation, and source phrases.
- **Dynamic Codebook (NEW)**: Live mapping viewer connected directly to the backend Python enums.
- **Pipeline Visualization**: Real-time rendering of all pipeline stages: STT → Semantic Parsing → Semantic Bit-packing → Protobuf Serialization → CRC16 Validation → ChaCha20-Poly1305 Encryption.
- **Packet Inspector**: Deep-dive into the live wire-format hexadecimal output of every single packet.

### How to Run the Web Demo
You can run the backend and frontend servers manually from two separate terminals:

**1. Start the Backend (Terminal 1)**
```powershell
cd web-demo\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**2. Start the Frontend (Terminal 2)**
```powershell
cd web-demo\frontend
npm run dev
```

*(Alternatively, you can run `.\web-demo\start_demo.ps1` to launch both automatically).*

3. Access the tactical dashboard at: [http://localhost:5173/hubbli](http://localhost:5173/hubbli) and [http://localhost:5173/tolankere](http://localhost:5173/tolankere)

---

## 2. M3 C++ Protocol Engine

The `src` and `proto` directories contain the core C++ Protocol Engine. It defines the raw protocol specification (via Protocol Buffers) and manages translating text data into tightly packed binary wire formats.

### Components
- **`proto/packet_schema.proto`**: The Protobuf specification for `VoicePacket`. Defines fields for MAGIC_HEADER, sequence number, timestamps, priority, callsigns, language, and payload.
- **`src/PacketEncoder.cpp` / `PacketDecoder.cpp`**: The C++ implementation interfacing with the generated Protobuf code, performing payload compression (future arithmetic coding), validation, and serialization.
- **`CMakeLists.txt` / `build.sh` / `build_windows.ps1`**: Cross-platform build configurations to compile the core C++ binaries and run unit tests.

### Build Instructions (C++ Core)
To compile the C++ libraries and run Phase 1 tests on Windows:
```powershell
.\build_windows.ps1
```
*(Requires CMake, MSVC/MinGW, and a local Protobuf installation).*

---
**Integrity Note**: All metrics, packet loss rates, and pipeline timings shown in the demo are authentically measured or explicitly labeled as `SIMULATED`/`DEMO MODE`.
Absolutely. Here is the **complete README section in one block**. You can copy-paste it directly into `README.md` and replace the existing contents if you want.

````markdown
# iTantra — M3 Semantic Communication Engine

**Smart India Hackathon 2026 | ISRO | SIH26173**

M3 implements the semantic communication and packet-protocol layer of
iTantra.

The purpose of M3 is to convert a user's message into a structured
representation of its meaning, encode that information into a compact
packet, transmit it, and reconstruct the message at the receiver.

---

## ⚠️ DEVELOPMENT STATUS

This branch contains **Parth's M3 implementation and Web Demonstration**.

### Currently implemented

- Protobuf packet schema
- Packet encoder
- Packet decoder
- UTF-8 multilingual text handling
- Semantic message representation
- Semantic parser
- Codebook visualization
- Packet inspection
- Binary packet visualization
- Web-based sender and receiver simulation
- Compression comparison
- Pipeline visualization
- Performance/latency demonstration

### Important

The current Phase-1 C++ implementation primarily demonstrates
**packet serialization and reconstruction**.

The final semantic-compression pipeline is designed to evolve toward:

Text
↓
Tokenization
↓
Semantic Representation
↓
Compression
↓
Compact Binary Payload
↓
Packet
↓
Transmission
↓
Decoding
↓
Semantic Reconstruction

---

# 1. M3 RESPONSIBILITY

M3 is responsible for the communication representation between the
speech/AI layer and the wireless transport layer.

### M1

Speech → Text

### M2

Text → Speech

### M3

Meaning → Compact Packet

### M4

Packet → Wireless Transport

### M5

Android Runtime / Database / JNI

### M6

UI / Benchmarking / Demonstration

---

# 2. M3 PIPELINE

The complete M3 pipeline is:

```text
USER INPUT
    │
    ▼
SEMANTIC PARSER
    │
    ▼
SEMANTIC MESSAGE
    │
    ├── ACTION
    ├── ENTITY
    ├── QUANTITY
    ├── TARGET
    ├── URGENCY
    ├── CONDITION
    └── EMOTION
    │
    ▼
TOKENIZATION / ENCODING
    │
    ▼
PACKET CREATION
    │
    ├── Header
    ├── Sequence Number
    ├── Timestamp
    ├── Priority
    ├── Language
    ├── Payload
    └── Integrity Information
    │
    ▼
BINARY DATA
    │
    ▼
TRANSMISSION
    │
    ▼
RECEIVER
    │
    ▼
PACKET DECODING
    │
    ▼
SEMANTIC RECONSTRUCTION
    │
    ▼
TARGET LANGUAGE
    │
    ▼
FINAL MESSAGE
````

---

# 3. PROJECT STRUCTURE

```text
itantra-m3/
│
├── proto/
│   └── packet_schema.proto
│
├── src/
│   ├── PacketEncoder.cpp
│   ├── PacketEncoder.hpp
│   ├── PacketDecoder.cpp
│   ├── PacketDecoder.hpp
│   └── main.cpp
│
├── generated/
│   └── Generated Protocol Buffer files
│
├── build/
│   └── Native build files
│
├── web-demo/
│   ├── backend/
│   ├── frontend/
│   └── start_demo.ps1
│
├── demo.py
│
├── CMakeLists.txt
├── build.sh
├── build_msys2_native.sh
├── build_windows.ps1
│
└── README.md
```

---

# 4. TECHNOLOGIES

## Native Protocol Engine

* C++
* C++20
* CMake
* Protocol Buffers
* Protobuf generated C++ code
* UTF-8
* `uint8_t` byte buffers

## Web Demonstration

### Backend

* Python
* REST API
* WebSocket communication

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS

---

# 5. REQUIREMENTS

## Native C++ Engine

Install:

* GCC / G++
* CMake
* Protocol Buffers / `protoc`

## Web Demo

Install:

* Python 3
* Node.js
* npm

---

# 6. RUNNING THE WEB DEMO

From the project root:

```powershell
cd web-demo
```

Start the demonstration using:

```powershell
.\start_demo.ps1
```

If the project requires the frontend to be started separately:

```powershell
cd frontend
npm install
npm run dev
```

Open the localhost URL shown by the terminal.

---

# 7. WEB DEMO FEATURES

The Web Demo is designed to make the internal communication process
visible instead of hiding it behind a simple chat interface.

## Sender

The sender can:

* Enter a message
* Select source language
* Select target language
* Select destination
* Select urgency
* Generate semantic representation
* Encode the message
* Inspect the generated packet

---

# 8. SEMANTIC MESSAGE INSPECTOR

The Semantic Inspector displays the meaning extracted from the
message.

Example:

```text
┌─────────────────────────────┐
│      SEMANTIC MESSAGE      │
├─────────────────────────────┤
│ ACTION       SEND_TEAM      │
│ ENTITY       RESCUE         │
│ QUANTITY     2              │
│ TARGET       HUBBLI         │
│ URGENCY      CRITICAL       │
│ CONDITION    TRAPPED        │
│ EMOTION      DISTRESS       │
└─────────────────────────────┘
```

Each field can be inspected to understand how the original sentence
is converted into structured information.

---

# 9. CODEBOOK

The codebook defines how semantic values are represented internally.

For example:

```text
ACTION

SEND_TEAM
RESCUE
EVACUATE
REPORT
...

URGENCY

ROUTINE
TACTICAL
CRITICAL

EMOTION

CALM
DISTRESS
FEAR
PANIC
...
```

The Web Demo exposes the codebook so that the conversion from
human-readable meaning to machine-readable representation can be
observed.

---

# 10. PACKET INSPECTOR

The Packet Inspector displays the communication packet at different
stages.

It can show:

* Original message
* Semantic representation
* Encoded fields
* Packet fields
* Payload
* Binary representation
* Packet size
* Compression information
* Integrity information

This allows the complete transformation to be visually inspected.

---

# 11. COMPRESSION COMPARISON

The Web Demo compares:

```text
Original Message
       ↓
Semantic Representation
       ↓
Encoded Packet
       ↓
Final Binary Payload
```

The objective of the final iTantra system is to transmit the
**meaning of the message instead of transmitting unnecessary raw
audio data**.

---

# 12. RECEIVER

The receiver demonstrates:

```text
RECEIVED BINARY DATA
        ↓
PACKET DECODER
        ↓
PACKET FIELDS
        ↓
SEMANTIC MESSAGE
        ↓
TARGET LANGUAGE
        ↓
FINAL OUTPUT
```

The receiver displays the decoded message and the intermediate
processing steps.

---

# 13. TECHNICAL VIEW

The Technical View exposes the internal processing pipeline.

```text
INPUT
 ↓
SEMANTIC PARSING
 ↓
TOKENIZATION
 ↓
SEMANTIC ENCODING
 ↓
COMPRESSION
 ↓
PACKETIZATION
 ↓
TRANSMISSION
 ↓
DECODING
 ↓
RECONSTRUCTION
 ↓
OUTPUT
```

This view is intended for technical demonstration and understanding
of the communication process.

---

# 14. FALLBACK MODE

If the semantic parser cannot confidently identify the required
meaning, the system uses a fallback representation.

Fallback ensures that the message can still be represented even when
semantic parsing is unsuccessful.

Current difficult cases include:

* Location names
* Proper nouns
* Emotions
* Context-dependent words
* Multilingual expressions
* Unusual sentence structures

Reducing fallback usage is an active development area.

---

# 15. PHASE 1 — PACKET SERIALIZATION

Phase 1 establishes the packet communication architecture.

The basic flow is:

```text
TEXT
 ↓
VoicePacket
 ↓
Protobuf Serialization
 ↓
BINARY BYTES
 ↓
Protobuf Deserialization
 ↓
VoicePacket
 ↓
TEXT
```

The Phase-1 payload may contain raw UTF-8 text.

Therefore:

> **Protobuf serialization should not be confused with the final
> semantic compression algorithm.**

The architecture is designed so that the payload can later be replaced
with a compressed semantic representation without redesigning the
entire packet system.

---

# 16. FUTURE SEMANTIC COMPRESSION

The intended final architecture is:

```text
Speech
 ↓
STT
 ↓
Text
 ↓
Semantic Parser
 ↓
Semantic Representation
 ↓
Tokenizer
 ↓
Compact Encoding
 ↓
Compression
 ↓
Binary Packet
 ↓
Wireless Link
 ↓
Decoder
 ↓
Semantic Reconstruction
 ↓
Translation
 ↓
TTS
 ↓
Speech
```

This allows the system to communicate the **meaning** of a sentence
using substantially less data than transmitting raw speech.

---

# 17. C++ PHASE-1 DEMO

From the project root:

```powershell
python demo.py
```

The Phase-1 demonstration tests:

1. English
2. Hindi
3. Marathi
4. Empty input
5. Long input

The demonstration verifies the packet round trip:

```text
Input Text
    ↓
Packet Encoder
    ↓
Serialized Bytes
    ↓
Packet Decoder
    ↓
Recovered Text
```

---

# 18. NATIVE BUILD

From the project root:

```powershell
mkdir build
cd build
```

Configure:

```powershell
cmake ..
```

Build:

```powershell
cmake --build . --config Release
```

---

# 19. QUICK TEST

After starting the Web Demo:

1. Open the Sender interface.
2. Enter a message.
3. Select the source language.
4. Select the target language.
5. Select the destination.
6. Select urgency.
7. Send the message.
8. Open the Semantic Inspector.
9. Observe the semantic fields.
10. Inspect the encoded packet.
11. Check packet size.
12. Check latency.
13. Open the Receiver.
14. Observe packet decoding.
15. Verify the reconstructed message.

Example input:

```text
Send two rescue teams to Hubbli immediately.
People are trapped and in distress.
```

Expected semantic representation:

```text
ACTION       → SEND_TEAM
ENTITY       → RESCUE
QUANTITY     → 2
TARGET       → HUBBLI
URGENCY      → CRITICAL
CONDITION    → TRAPPED
EMOTION      → DISTRESS
```

---

# 20. PERFORMANCE DEMONSTRATION

The Web Demo can be used to demonstrate:

* Processing latency
* Encoding time
* Decoding time
* Packet size
* Original data size
* Compression ratio
* Semantic parsing success rate
* Fallback rate

These metrics are displayed for demonstration and development
purposes.

---

# 21. WHY M3 MATTERS

Traditional voice communication sends large amounts of audio data.

iTantra instead aims to transform:

```text
VOICE
 ↓
MEANING
 ↓
COMPACT REPRESENTATION
 ↓
SMALL PACKET
```

The wireless layer can then transport the compact representation
instead of continuously transporting raw audio.

At the receiver:

```text
SMALL PACKET
 ↓
MEANING
 ↓
LANGUAGE TRANSLATION
 ↓
SPEECH
```

This is the core idea behind semantic communication.

---

# 22. INTEGRATION WITH THE OTHER TEAM MEMBERS

```text
                 iTantra
                    │
          ┌─────────┴─────────┐
          │                   │
       SENDER              RECEIVER
          │                   │
          ▼                   ▲
        M1 STT              M2 TTS
          │                   │
          ▼                   │
         TEXT                 │
          │                   │
          └──────► M3 ◄───────┘
                 │
                 ▼
          Semantic Packet
                 │
                 ▼
                M4
          Wireless Transport
                 │
                 ▼
             Receiver
                 │
                 ▼
                M3
                 │
                 ▼
                M2
                 │
                 ▼
               SPEECH
```

---

# 23. DEVELOPMENT ROADMAP

### Completed

* [x] Protobuf schema
* [x] Packet encoder
* [x] Packet decoder
* [x] Multilingual UTF-8 support
* [x] C++ round-trip testing
* [x] Web demonstration
* [x] Sender interface
* [x] Receiver interface
* [x] Semantic Inspector
* [x] Codebook visualization
* [x] Packet Inspector
* [x] Pipeline visualization
* [x] Performance visualization

### Next

* [ ] Improve semantic parsing
* [ ] Reduce fallback rate
* [ ] Improve proper-noun/location recognition
* [ ] Improve multilingual semantic recognition
* [ ] Finalize compact tokenization
* [ ] Integrate semantic compression
* [ ] Integrate M3 with M4 wireless transport
* [ ] Integrate with Android/JNI layer

---

# 24. TEAM BRANCH

This implementation is maintained in:

```text
Branch: parth
```

To obtain the latest version:

```powershell
git fetch origin
git switch parth
git pull origin parth
```

---

# 25. IMPORTANT DEVELOPMENT NOTE

The Web Demo is primarily a visualization and development
environment.

It exposes internal processing stages so developers and judges can
observe what happens to the message at every step.

The final deployment target is an offline Android application where
the same communication principles operate locally without cloud-based
STT, TTS, or translation APIs.

---

# END

iTantra M3

VOICE → MEANING → COMPACT PACKET → MEANING → VOICE

```

**One caution:** in the `Running the Web Demo` section, keep only the commands that actually work on your machine. In particular, if `.\start_demo.ps1` already starts both backend and frontend, you don't need the separate `npm` commands.
```
