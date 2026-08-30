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
