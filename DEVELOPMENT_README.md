# iTantra — Development Handoff README

**SIH 2026 | ISRO | Problem SIH26173**
**Branch: `integration`**
**Last APK: 79MB debug build — `android/app/build/outputs/apk/debug/app-debug.apk`**

---

## 1. What This Is

Offline multilingual emergency walkie-talkie for disaster zones. No internet required in the field. Phones on the same Wi-Fi/hotspot mesh hear each other in their own selected language.

**Rescue scenario:**
- Rescuer (English) speaks → every victim phone hears in Hindi / Kannada / Marathi / Telugu / etc.
- Victim (Hindi) speaks → rescuer hears in English, another victim hears in Telugu
- Works with 3+ phones simultaneously. Inbound messages queue so voices don't overlap.

---

## 2. Repository Layout

```
SIH2026/
├── android/                         ← Android app (Kotlin)
│   └── app/src/main/java/org/isro/itantra/
│       ├── LoginActivity.kt         ← Phone + OTP login
│       ├── OtpActivity.kt           ← OTP verify, generates NODE_ID
│       ├── ProfileSetupActivity.kt  ← Name + language, shows NODE_ID
│       ├── MainActivity.kt          ← All app logic (~2400 lines)
│       ├── audio/                   ← STT bridge, spell corrector
│       ├── database/                ← Room DB — message audit log
│       ├── input/                   ← PTT volume button provider
│       ├── location/
│       │   └── OfflineGpsFix.kt     ← GPS-only location + Haversine + compass
│       ├── runtime/
│       │   ├── PTTStateMachine.kt   ← State: IDLE/PTT_CAPTURING/TRANSMITTING/RECEIVING/QUEUE_WAITING
│       │   ├── PTTEvent.kt          ← Events including QUEUE_DRAIN
│       │   ├── PTTState.kt
│       │   └── MessageScheduler.kt  ← FIFO inbound queue, SOS preempt, PTT block
│       ├── semantic/
│       │   └── SemanticBridge.kt    ← JNI to libitantra_core.so (M3 compression)
│       ├── service/
│       │   └── RadioDaemonService.kt← Foreground notification stub (not wired yet)
│       ├── transport/
│       │   ├── udp/UdpTransceiver.kt← UDP send/receive, beacon, peer discovery
│       │   ├── wfbng/WfbngManager.kt← Encryption + FEC + mesh routing
│       │   ├── ChaCha20Poly1305Engine.kt
│       │   └── ReedSolomonFECEngine.kt
│       ├── tts/
│       │   └── IndicTTSManager.kt   ← Android TTS wrapper, prosody, locale fallback
│       └── ui/
│           └── LiveTelemetryOverlay.kt
│
├── android/app/src/main/assets/
│   ├── encoder.onnx                 ← AI4Bharat IndicConformer STT encoder
│   ├── ctc_decoder.onnx             ← CTC decoder
│   ├── silero_vad.onnx              ← Voice Activity Detection
│   └── tokens.txt / vocab.json      ← Vocabulary
│
├── web-demo/
│   ├── backend/                     ← FastAPI + Python M3 pipeline
│   └── frontend/                    ← React/Vite tactical dashboard
│
└── proto/                           ← Protobuf packet schema
```

---

## 3. What Works (Tested on Device)

| Feature | Status | Notes |
|---------|--------|-------|
| Login → OTP → Profile → Main | ✅ Working | OTP `123456` works offline |
| Node ID generation | ✅ Working | 4-char alphanumeric, persists |
| Auto mesh join | ✅ Working | UDP broadcast, no peer picker |
| EN → HI speech-to-speech | ✅ Confirmed | Tested on 2 phones |
| EN → other Indic TTS | ✅ Audio plays | English TTS fallback until models download |
| Text send/receive | ✅ Working | All language pairs |
| MLKit translation pivot | ✅ Working | X→EN→Y for all Indic pairs |
| WhatsApp-style chat bubbles | ✅ Working | Per-peer color, sender name |
| Tap-to-speak PTT | ✅ Working | Toggle, live recording timer |
| FIFO message scheduler | ✅ Working | PTT blocked while playing |
| Mesh roster display | ✅ Working | Shows name · lang · GPS |
| GPS location capture | ✅ Code complete | Needs outdoor satellite fix |
| GPS in beacons | ✅ Working | `ITANTRA_BCN:node:lang:gps:ts` |
| iTantra logo icon | ✅ Working | All mipmap densities |
| ChaCha20 encryption | ✅ Working | 32-byte shared key |
| Reed-Solomon FEC 8+4 | ✅ Working | Packet recovery |

---

## 4. Known Issues / Not Yet Done

| Item | Status | Where to Fix |
|------|--------|-------------|
| Non-English STT (hi-IN, te-IN) | ⚠️ Needs device offline pack | Settings → Languages → Download |
| MLKit models first download | ⚠️ Needs WiFi once | Auto-downloads at startup |
| GPS indoors | ⚠️ Hardware limit | Works outdoors near window |
| SemanticBridge not wired in TX | ❌ TODO | `transmitMessage()` sends UTF-8 |
| RadioDaemonService is stub | ❌ TODO | App dies when backgrounded |
| Lab tests are `pass` stubs | ❌ TODO | `web-demo/backend/main.py:349` |
| React frontend `#root` missing | ❌ TODO | `web-demo/frontend/index.html` |

---

## 5. How to Build

```bash
# Prerequisites
export JAVA_HOME=/home/janaki/.jdks/temurin-17/bin/..
export ANDROID_HOME=/home/janaki/Android/Sdk
export ANDROID_SDK_ROOT=/home/janaki/Android/Sdk

cd /home/janaki/SIH2026/android
./gradlew assembleDebug

# APK output
android/app/build/outputs/apk/debug/app-debug.apk

# Install on connected phone
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

---

## 6. Architecture: Speech-to-Speech Pipeline

```
SENDER PHONE                          RECEIVER PHONE
─────────────                         ──────────────
Tap PTT button
  → Android STT (sender's lang)       
  → correctedText in senderLang       
  → transmitMessage(text, langCode)   
  → WfbngManager.sendVoiceMessage(    
      payload=UTF-8 bytes,            →  onVoicePayloadDelivered()
      lang=senderLangCode,               sourceLang = packet.lang
      target="ALL"  ← broadcast)        targetLang = receiver's spinner
                                         translateWithMlKit(
                                           text, sourceLang, targetLang
                                         ) → pivot: src→EN→target
                                         MessageScheduler.enqueue(item)
                                         → playTTS(translated, targetLang)
```

**MLKit pivot for Indic↔Indic:**
- `hi→mr` = `hi→EN→mr` (two downloaded models)
- `kn→te` = `kn→EN→te`
- All 10×10 combinations covered via English pivot
- Models: ~20MB each, download once on WiFi, then fully offline forever

---

## 7. Node Identity System

```
At OTP verify (OtpActivity.kt):
  seed = userId + phone.takeLast(4) + random(1000..9999)
  nodeId = generateNodeId(seed)  →  e.g. "R7K2"
  Persisted as PREF_NODE_ID

myCallsign in MainActivity:
  = "DisplayName_NodeID"  e.g. "Janaki_R7K2"
  
In chat bubbles:
  displayNameFromCallsign("Janaki_R7K2") → "Janaki"
  
In beacons:
  ITANTRA_BCN:Janaki_R7K2:hi:12.97,77.59,8m:1726123456789
```

---

## 8. Beacon Format

```
ITANTRA_BCN:{callsign}:{lang}:{lat,lon,acc}:{timestamp_ms}

Example:
  ITANTRA_BCN:Janaki_R7K2:hi:12.9716,77.5946,8m:1726123456789
  ITANTRA_BCN:Parth_A91C:en:GPS_UNAVAIL:1726123456789

Interval: every 15 seconds
Receiver parses → meshRoster[callsign] = "lang|gps|ip"
```

---

## 9. PTT State Machine

```
IDLE_LISTENING
    ↓ PTT_DOWN              ↓ PACKET_RECEIVED     ↓ SOS_TRIGGERED
PTT_CAPTURING           RECEIVING              ALARM_ACTIVE
    ↓ PTT_UP                ↓ PACKET_RECEIVED      ↓ ALARM_FINISHED
TRANSMITTING            QUEUE_WAITING          IDLE_LISTENING
    ↓ TRANSMISSION_COMPLETE  ↓ QUEUE_DRAIN
IDLE_LISTENING          IDLE_LISTENING
```

**MessageScheduler behaviour:**
- `enqueue(item)` → `stateMachine.handleEvent(PACKET_RECEIVED)`
- `isChannelBusy = isPlaying` (only while TTS speaks, not while queue has items)
- SOS items inserted at front of queue
- `onPlaybackDone()` called by `IndicTTSManager.onTtsDone` callback
- 8-second fallback auto-advance if TTS never fires `onDone`

---

## 10. GPS Implementation

**File:** `android/app/src/main/java/org/isro/itantra/location/OfflineGpsFix.kt`

```kotlin
// Part 1 — Location capture
LocationManager.GPS_PROVIDER  // strict satellite only, no network
MIN_INTERVAL_MS = 20_000      // request every 20s
getLastKnownLocation()        // returns cached fix immediately

// Part 2 — Haversine
calculateDistanceAndBearing(myLat, myLon, targetLat, targetLon)
→ Pair(distanceMeters, bearing0to360)

// Part 3 — Tactical compass
TacticalCompass uses Sensor.TYPE_ROTATION_VECTOR
→ phone azimuth from SensorManager.getOrientation()
→ arrowRotation = (targetBearing - phoneAzimuth + 360) % 360
→ set compassArrowView.rotation = arrowRotation
```

**Permission flow:**
- `ACCESS_FINE_LOCATION` in `AndroidManifest.xml` ✅
- Runtime request in `onCreate()` with code `101`
- `onRequestPermissionsResult()` starts GPS on grant ✅

---

## 11. Transport Layer

**`WfbngManager`** coordinates:
1. `ChaCha20Poly1305Engine` — encrypt/decrypt with 32-byte shared key `{0x42 * 32}`
2. `ReedSolomonFECEngine` — 8 data + 4 parity shards
3. `UdpTransceiver` — UDP port 8988, broadcasts to `255.255.255.255`

**`UdpTransceiver` handshake:**
```
Phone A → ITANTRA_HELLO:callsign:seq:ts   (broadcast)
Phone B → ITANTRA_ACK:callsign:seq:ts     (unicast reply)
Phone A → ITANTRA_CONFIRM:callsign:seq    → onLinkConfirmed fires
```

**Peer discovery:** `discoveredPeers: ConcurrentHashMap<String, InetAddress>`

**Voice packet wire format:**
```
[2 bytes lang code][1 byte priority][N bytes payload]
→ encrypted → FEC sharded → UDP packets
```

---

## 12. Dependencies (build.gradle)

```groovy
// Core
androidx.appcompat:appcompat:1.6.1
androidx.core:core-ktx:1.12.0
com.google.android.material:material:1.11.0

// Database
androidx.room:room-runtime (+ ktx)

// Audio / STT
com.microsoft.onnxruntime:onnxruntime-android:1.18.0
com.google.oboe:oboe:1.8.0

// Translation
com.google.mlkit:translate:17.0.3
com.google.mlkit:language-id:17.0.6

// ONNX models in assets/
// encoder.onnx, ctc_decoder.onnx, silero_vad.onnx
```

---

## 13. Web Demo (Python/FastAPI + React)

**Start:**
```bash
cd web-demo/backend
pip install -r requirements.txt   # NOTE: add 'cryptography' manually
python -m uvicorn main:app --host 0.0.0.0 --port 8000

cd web-demo/frontend
npm install && npm run dev
# → http://localhost:5173
```

**Known issues in web demo:**
- `cryptography` missing from `requirements.txt` — add it manually
- `frontend/index.html` is vanilla chat SPA (no `#root`) — React routes won't mount
- WebSocket client uses `/ws/chat/{token}`, server serves `/api/chat/{token}`
- Lab tests (`test_latency`, `test_packets`) are `pass` stubs

---

## 14. What to Work on Next

### High priority
1. **Wire SemanticBridge in `transmitMessage()`** — currently sends UTF-8. Should call `SemanticBridge.compressTranscript()` when `isLibraryLoaded`. The JNI is ready; just needs the call site.
2. **Fix React frontend** — add `<div id="root"></div>` to `index.html` so `/hubbli` and `/tolankere` routes mount.
3. **WebSocket path alignment** — change client from `/ws/chat/{token}` to `/api/chat/{token}`.
4. **`RadioDaemonService`** — move `WfbngManager` into the service so the app receives packets in background (screen off).

### Medium priority
5. **Indic STT offline packs** — guide users to install hi-IN, te-IN, kn-IN packs from Settings → General Management → Language → Text-to-speech.
6. **MLKit model pre-download UI** — show progress bar at first launch.
7. **GPS compass UI** — `TacticalCompass` is coded but not wired to any ImageView yet.

### Low priority
8. Fix `requirements.txt` — add `cryptography==41.0.7`.
9. Fix `start_demo.ps1` hardcoded paths.
10. Clean up README.md paste artifact (line 64).

---

## 15. Branch Structure

| Branch | Owner | Content |
|--------|-------|---------|
| `integration` | Janaki | Android app + web demo |
| `parth` / `parth-tinyml` | Parth | M3 C++ engine + TinyML |
| `main` | — | Stable merged code |

**Current HEAD:** `integration` @ `0ef9b3a`

---

## 16. Quick Checklist for Next Dev Session

- [ ] Confirm EN→HI works on fresh install (OTP demo: `123456`)
- [ ] Download MLKit models on WiFi → test kn→te, mr→en
- [ ] Go outside → confirm GPS fix in roster within 60s
- [ ] Wire `SemanticBridge.compressTranscript()` in `transmitMessage()`
- [ ] Fix `frontend/index.html` `#root` div
- [ ] Merge `parth-tinyml` TFLite weights into `integration`
