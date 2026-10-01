# iTantra — Indian Multilingual TTS & STT Aided Neural Transceiver Radio Access for Low Bitrate Links

**Smart India Hackathon 2026** · Problem Statement **SIH26173** · Sponsoring Agency **ISRO**
Team **Algo Avengers** (172340) · PS Category: Software · Theme: Smart Automation / Disaster Management & Emergency Communication

An offline-first Android walkie-talkie that lets two low-end phones talk across a Wi-Fi / Bluetooth mesh with **no towers, no internet, and no cloud** — speaking in one Indian language and being heard in another.

---

## 1. The problem

Voice is data-intensive and hard to move over low data-rate links. In a disaster or a remote area the network is either absent or congested, and the people who most need alerts are often the ones least served by text — non-literate users, and anyone reading in a language that isn't theirs.

iTantra answers three constraints at once:

| Constraint | Consequence for the design |
|---|---|
| No network available | Everything runs on-device; nothing depends on a server |
| Low-rate / congested link | Voice is transcribed, compressed and re-synthesised instead of streaming PCM |
| Ten languages, mixed literacy | Speech in → speech out, with receiver-side translation |

---

## 2. What it does

- **Push-to-talk over mesh** — one tap to record, one tap to send, to every peer on the link.
- **Offline speech-to-text** for Indian languages, on-device, CPU-only.
- **Receiver-side translation** — the wire carries the raw transcript; each phone renders it into its own chosen language.
- **Offline text-to-speech** so the message is *heard*, not just read — the inclusivity requirement for non-literate users.
- **Max-volume, non-interruptible voice alerts** for emergency traffic.
- **Wi-Fi / Bluetooth mesh transport** — no router or internet needed; phones form the network themselves.
- **Typed messages** alongside voice, for when speaking isn't appropriate.
- **First-run onboarding guide** (6 steps) plus a `?` button to replay it.

---

## 3. How it works

```
   mic ──► VAD ──► STT ──► transcript (UTF-8)
                              │
                              ├─► transmit ──► ChaCha20-Poly1305
                              │                   └─► Reed-Solomon FEC (K=8, M=4)
                              │                        └─► Wi-Fi / BT mesh datagrams
                              │
   speaker ◄── TTS ◄── translate (ML Kit cascade, offline) ◄── receive
```

**Speech-to-text** uses two engines behind one gate, chosen per language by measured character error rate:

| Languages | Engine |
|---|---|
| te, ta, kn, ml | `parambharat/whisper-tiny-south-indic` (ggml q8_0) |
| hi, bn, pa, gu, or, mr | AI4Bharat Conformer |
| en | ML Kit |

**Translation** runs through an ML Kit cascade with an English pivot and an offline gloss fallback. When no genuine translation is produced the receiver shows the honest `[lang] original` label — **the app never fabricates a translation.**

**Transport** encrypts each message, then adds forward error correction so a lossy link can drop shards without losing the message.

---

## 4. Verified results

All figures below were measured on a real device or in CI unless stated otherwise.

| Metric | Value | Status |
|---|---|---|
| APK size | 270 MB (283,138,116 B) | **Measured** |
| STT model (whisper ggml q8_0) | 43,537,433 B | **Measured** |
| VAD model (Silero) | 2,327,524 B | **Measured** |
| Backend test suite | 467 passed, 10 skipped | **Measured** |
| Root test suites | 15 passed, 16 subtests | **Measured** |
| STT CER, on-device samples | 0.03 – 0.34 (hi 0.03 … ml 0.34) | **Measured** |
| Decode latency, 3.0 s audio | conformer 0.4 – 0.5 s; whisper 1.3 – 4.4 s | **Measured** |
| Mesh transport latency | < 350 ms (transport only) | **Measured** |
| Wire cost per message | 42 B transcript → 50 B/datagram × 12 FEC shards = **6,600 B** across 11 destinations, vs 48,000 B PCM | **Measured** |
| FEC | Cauchy Reed-Solomon over GF(2⁸), K=8 / M=4 | **Measured** (implemented) |
| Cipher | AES-256-GCM (Poly1305 tag; no CRC in the TX path) | **Measured** (implemented) |
| Engine frame cap | `MAX_FRAME_SIZE = 38` B — semantic engine only, **not on the wire** | **Measured** |

### Not yet tested

These are honestly still open and are **not** claimed anywhere:

- Character error rate against **human-recorded** voice (current refs are synthetic)
- Idle CPU draw, battery/power draw under load
- TTS perceived quality (MOS)
- RF range and packet loss across real terrain
- Market/impact citations

---

## 5. Build & run

```bash
cd android
export JAVA_HOME=/path/to/jdk-17
export ANDROID_HOME=/path/to/Android/Sdk
./gradlew assembleDebug
# APK → android/app/build/outputs/apk/debug/app-debug.apk
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```

Requires JDK 17 and the Android SDK. The app needs no account server: log in once, then it runs offline.

**Tests**

```bash
# protocol / integration suites (repo root)
python -m pytest test_m1_m3_integration.py test_end_to_end_m1_m2_m3_m4.py \
                 test_member3_suite.py test_fec.py

# backend suite
python -m pytest web-demo/backend
```

**Web demo** (simulated two-node mesh, for inspecting the wire format without hardware):

```bash
cd web-demo/backend  && python -m uvicorn main:app --port 8000
cd web-demo/frontend && npm run dev
# → http://localhost:5173/hubbli
```

---

## 6. Repository layout

| Path | Contents |
|---|---|
| `android/` | The Android application — UI, PTT, mesh transport, native STT/TTS |
| `android/app/src/main/cpp/` | Native engines: whisper, conformer, Silero VAD, TTS, semantic layer |
| `src/` | Portable C++ protocol core (packet framing, FEC, semantics) shared with tests |
| `web-demo/` | React + FastAPI two-node simulator with packet inspector |
| `ppt.md`, `build_ppt.py`, `iTantra_SIH2026.pptx` | Submission deck: content source, stdlib-only generator, built deck |
| `STT_GATE_RESULTS.md` | Language-by-language STT gate and on-device CER tables |
| `DEVELOPMENT_README.md` | Deep technical handoff: architecture, PTT state machine, transport, branches |

---

## 7. Branches

| Branch | Role |
|---|---|
| `main` | Landing branch for the repository |
| `integration` | Current, complete build — all work merged here |
| `itantra2.0` | UI and onboarding work |
| `parth` | Protocol / semantic layer |

---

## 8. Status

Working on-device: mesh transport, push-to-talk, offline STT, receiver-side translation, TTS playback, emergency alerts, onboarding.

Open: human-voice CER, power and RF measurements, TTS MOS, and fine-tuning of the south-indian STT encoder against a human-recorded eval set.

See `DEVELOPMENT_README.md` for the full technical breakdown and `STT_GATE_RESULTS.md` for the speech recognition evidence.
