#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# demo.py — iTantra M3 Phase 1 Python Demonstration
#
# This runs the SAME pipeline as the C++ engine:
#   TEXT → VoicePacket → Protobuf bytes → VoicePacket → TEXT
#
# Uses the same packet_schema.proto (generated to build/packet_schema_pb2.py).
# This is NOT the production engine — it is a working demonstration that
# proves the protocol design is correct before the C++ build environment
# is finalized.
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
import time
import struct

# Add the build directory to path so we can import the generated pb2 file
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))

try:
    import packet_schema_pb2 as schema
except ImportError as e:
    print(f"ERROR: Could not import generated protobuf module: {e}")
    print("Run: protoc --proto_path=proto --python_out=build proto/packet_schema.proto")
    sys.exit(1)


# ── Encoder (mirrors PacketEncoder.cpp) ───────────────────────────────────────

MAGIC_HEADER = 0x41475931  # "AGY1"

def encode(text: str, language: str, callsign: str, sequence: int, priority: int) -> bytes:
    """
    Encode a message into Protobuf wire bytes.
    Mirrors PacketEncoder::encode() in C++.
    """
    if not text:
        raise ValueError("PacketEncoder::encode — text payload must not be empty")
    if priority not in (0, 1, 2):
        raise ValueError("priority must be 0 (ROUTINE), 1 (TACTICAL), or 2 (LIFE_SAFETY_ALERT)")

    packet = schema.VoicePacket()
    packet.magic_header    = MAGIC_HEADER
    packet.sequence_number = sequence
    packet.timestamp_ms    = int(time.time() * 1000)
    packet.priority        = priority
    packet.source_callsign = callsign
    packet.source_language = language

    # PHASE 1: compressed_payload = raw UTF-8 bytes (no actual compression)
    # Phase 2: this becomes arithmetic_encode(sentencepiece_tokenize(text))
    packet.compressed_payload = text.encode('utf-8')

    return packet.SerializeToString()


# ── Decoder (mirrors PacketDecoder.cpp) ───────────────────────────────────────

def decode(data: bytes) -> schema.VoicePacket:
    """
    Decode Protobuf wire bytes back into a VoicePacket.
    Mirrors PacketDecoder::decode() in C++.
    """
    if not data:
        raise ValueError("PacketDecoder::decode — received empty byte buffer")

    packet = schema.VoicePacket()
    if not packet.ParseFromString(data):
        raise RuntimeError("PacketDecoder::decode — Protobuf deserialization failed")
    return packet


# ── Utilities ─────────────────────────────────────────────────────────────────

PRIORITY_NAMES = {
    0: "ROUTINE (0)",
    1: "TACTICAL (1)",
    2: "LIFE_SAFETY_ALERT (2)",
}

def hex_dump(data: bytes) -> str:
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        lines.append('  ' + hex_part)
    return '\n'.join(lines)

def divider(ch='─', width=58):
    print(ch * width)


# ── Single Test Runner ────────────────────────────────────────────────────────

def run_test(test_num, label, text, language, callsign, sequence, priority):
    print()
    divider('═')
    print(f"  TEST {test_num} — {label}")
    divider('═')

    # ── SENDER ────────────────────────────────────────────────────────────────
    print()
    print("  ┌─────────────────────────────────────────────────┐")
    print("  │                    SENDER                       │")
    print("  └─────────────────────────────────────────────────┘")
    print()
    display_text = "(empty)" if not text else text
    print(f"  Input Text    : {display_text}")
    print(f"  Language      : {language}")
    print(f"  Callsign      : {callsign}")
    print(f"  Priority      : {priority}")
    print(f"  Sequence      : {sequence}")
    print(f"  UTF-8 Bytes   : {len(text.encode('utf-8'))} bytes")
    print()
    print("  ✓ [1/4] Input received")

    try:
        print("  ✓ [2/4] VoicePacket created")
        print("  ✓ [3/4] UTF-8 payload set in compressed_payload field")

        wire_bytes = encode(text, language, callsign, sequence, priority)

        print(f"  ✓ [4/4] Protobuf serialized → {len(wire_bytes)} bytes")

    except (ValueError, RuntimeError) as e:
        print(f"  ✗ [2/4] Encoder rejected input:")
        print(f"          {e}")
        print()
        print("  ── Result: REJECTED (expected for empty input) ──")
        return False

    # Size analysis
    utf8_len = len(text.encode('utf-8'))
    overhead = len(wire_bytes) - utf8_len
    print()
    print("  ┌─ Payload Analysis ────────────────────────────────┐")
    print(f"  │  Input UTF-8 bytes   : {utf8_len:6d} bytes              │")
    print(f"  │  Protobuf packet     : {len(wire_bytes):6d} bytes              │")
    print(f"  │  Protocol overhead   : {overhead:6d} bytes              │")
    print("  │                                                   │")
    print("  │  NOTE: Protobuf is SERIALIZATION, not compression │")
    print("  │  Phase 2 will add arithmetic coding to reduce     │")
    print("  │  compressed_payload before serialization.         │")
    print("  └───────────────────────────────────────────────────┘")

    # Hex dump
    print()
    print("  Raw wire bytes:")
    print(hex_dump(wire_bytes))

    # ── SIMULATED M4 TRANSPORT ────────────────────────────────────────────────
    print()
    print("  ╔═══════════════════════════════════════════════════╗")
    print("  ║          ~~~ SIMULATED M4 TRANSPORT ~~~           ║")
    print("  ║                                                   ║")
    print(f"  ║  → Packet transmitted ({len(wire_bytes):3d} bytes)              ║")
    print(f"  ║  → Packet received    ({len(wire_bytes):3d} bytes)              ║")
    print("  ║  → Zero byte corruption (ideal channel)           ║")
    print("  ╚═══════════════════════════════════════════════════╝")

    # ── RECEIVER ─────────────────────────────────────────────────────────────
    print()
    print("  ┌─────────────────────────────────────────────────┐")
    print("  │                   RECEIVER                       │")
    print("  └─────────────────────────────────────────────────┘")
    print()

    try:
        print("  ✓ [1/4] Bytes received from transport")
        received = decode(wire_bytes)
        print("  ✓ [2/4] Protobuf parsed successfully")
        print("  ✓ [3/4] Packet fields recovered")
        print("  ✓ [4/4] Text reconstructed")
    except Exception as e:
        print(f"  ✗ Decode failed: {e}")
        return False

    recovered_text = received.compressed_payload.decode('utf-8')

    print()
    print("  ┌─ Decoded VoicePacket ──────────────────────────────┐")
    print(f"  │  magic_header    : 0x{received.magic_header:08X}              │")
    print(f"  │  sequence_number : {received.sequence_number:6d}                     │")
    print(f"  │  source_language : {received.source_language:>6s}                     │")
    print(f"  │  source_callsign : {received.source_callsign:<15s}          │")
    print(f"  │  priority        : {PRIORITY_NAMES[received.priority]:<27s}  │")
    print(f"  │  payload size    : {len(received.compressed_payload):6d} bytes              │")
    print("  └───────────────────────────────────────────────────┘")
    print()
    print(f"  Recovered Text: {recovered_text}")

    passed = (recovered_text == text)
    if passed:
        print()
        print("  ✓✓ ROUNDTRIP VERIFIED — recovered text matches input exactly")
    else:
        print()
        print("  ✗✗ ROUNDTRIP FAILED — text mismatch!")

    return passed


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║              iTANTRA M3 — PHASE 1                       ║")
    print("║         Protobuf Communication Simulator                 ║")
    print("║                                                          ║")
    print("║  Pipeline:  TEXT → BYTES → TEXT                         ║")
    print("║  Transport: SIMULATED (no networking)                    ║")
    print("║  Member:    M3 — Serialization Lead                     ║")
    print("╚══════════════════════════════════════════════════════════╝")

    results = {}

    # Test 1 — English
    results['t1'] = run_test(
        1, "English message",
        "Send help to sector 4",
        "en", "CMD_ALPHA", 1, 1
    )

    # Test 2 — Hindi (primary SIH demonstration)
    results['t2'] = run_test(
        2, "Hindi — primary SIH demonstration",
        "सेक्टर 4 में तुरंत मदद भेजो",
        "hi", "RESCUE_01", 2, 2
    )

    # Test 3 — Marathi
    results['t3'] = run_test(
        3, "Marathi",
        "सेक्टर ४ मध्ये मदत पाठवा",
        "mr", "FIELD_02", 3, 2
    )

    # Test 4 — Empty (expected rejection)
    print()
    divider('═')
    print("  TEST 4 — Empty input (expected rejection)")
    divider('═')
    print()
    print("  Attempting to encode an empty string...")
    t4_rejected = False
    try:
        encode("", "en", "CMD_ALPHA", 4, 0)
        print("  ✗ ERROR: Empty input was NOT rejected — this is a bug.")
    except ValueError as e:
        print(f"  ✓ Empty input correctly rejected:")
        print(f"    {e}")
        t4_rejected = True
    results['t4'] = t4_rejected

    # Test 5 — Long message
    phrase = "सेक्टर 4 में मदद भेजो। "
    long_text = phrase * (500 // len(phrase.encode('utf-8')) + 1)
    long_text = long_text[:500 + len(phrase)]  # ~500+ bytes
    results['t5'] = run_test(
        5, "Long message — payload size analysis",
        long_text,
        "hi", "FIELD_03", 5, 0
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    passed = sum(1 for v in results.values() if v)
    total  = len(results)

    result_str = f"{passed}/{total} tests passed"
    pad = 58 - 11 - len(result_str) - 3
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                    PHASE 1 SUMMARY                      ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Test 1 — English          : " + ("✓ PASS" if results['t1'] else "✗ FAIL") + "                    ║")
    print("║  Test 2 — Hindi            : " + ("✓ PASS" if results['t2'] else "✗ FAIL") + "                    ║")
    print("║  Test 3 — Marathi          : " + ("✓ PASS" if results['t3'] else "✗ FAIL") + "                    ║")
    print("║  Test 4 — Empty (rejected) : " + ("✓ PASS" if results['t4'] else "✗ FAIL") + "                    ║")
    print("║  Test 5 — Long message     : " + ("✓ PASS" if results['t5'] else "✗ FAIL") + "                    ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Result: " + result_str + " " * max(pad, 0) + "║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  PHASE 1 OBJECTIVE:                                      ║")
    print("║  TEXT → BYTES → TEXT   ✓ DEMONSTRATED                   ║")
    print("║                                                          ║")
    print("║  NEXT: Phase 2 — SentencePiece tokenization +           ║")
    print("║        arithmetic coding in compressed_payload           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
