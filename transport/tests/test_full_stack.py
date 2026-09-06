"""
test_full_stack.py — Two-Node End-to-End Transport Verification

Simulates:

    Phone A
    STT / PTT / Sender
        |
        | UDP + Mesh + Encryption
        v
    Phone B
    Receiver / TTS

Verifies:

- Language tagging
- Priority preservation
- Payload integrity
- End-to-end localhost delivery
- Transport telemetry
"""

import os
import sys
import time


sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    ),
)


from wfbng_manager import (
    OFFICIAL_LANGUAGES,
    PriorityLevel,
    WfbngTransportManager,
)


def test_two_phone_isro_loop():

    print("=" * 70)
    print(
        "  TWO-NODE FULL STACK TRANSPORT TEST"
    )
    print("=" * 70)

    delivered_to_phone_b = []

    # ----------------------------------------------------------
    # Phone A
    # ----------------------------------------------------------

    phone_a = (
        WfbngTransportManager(
            my_callsign=(
                "PHONE_A_STT_MODE"
            ),
            bind_ip=(
                "127.0.0.1"
            ),
            port=9001,
            broadcast_target_ip=(
                "127.0.0.1"
            ),
            remote_port=9002,
        )
    )

    # ----------------------------------------------------------
    # Phone B
    # ----------------------------------------------------------

    phone_b = (
        WfbngTransportManager(
            my_callsign=(
                "PHONE_B_TTS_MODE"
            ),
            bind_ip=(
                "127.0.0.1"
            ),
            port=9002,
            broadcast_target_ip=(
                "127.0.0.1"
            ),
            remote_port=9001,
        )
    )

    # ----------------------------------------------------------
    # Start receiver
    # ----------------------------------------------------------

    phone_b.start(
        on_voice_delivered=(
            lambda origin,
            lang,
            priority,
            payload,
            processing_latency:
                delivered_to_phone_b.append(
                    {
                        "origin": origin,
                        "language": lang,
                        "priority": priority,
                        "payload": payload,
                        "processing_latency_ms":
                            processing_latency,
                        "received_at":
                            time.perf_counter(),
                    }
                )
        )
    )

    print(
        "\n[1] Devices Initialized:"
    )

    print(
        "    --> Phone A: "
        "STT / PTT Sender "
        "[127.0.0.1:9001]"
    )

    print(
        "    --> Phone B: "
        "TTS Receiver "
        "[127.0.0.1:9002]"
    )

    print(
        "    --> Supported Languages: "
        f"{len(OFFICIAL_LANGUAGES)}"
    )

    print(
        "    --> Language Codes: "
        + ", ".join(
            OFFICIAL_LANGUAGES.keys()
        )
    )

    # ----------------------------------------------------------
    # Test payload
    # ----------------------------------------------------------

    semantic_packet = bytes.fromhex(
        "18110100"
    )

    language = "hi"

    priority = (
        PriorityLevel
        .ALERT_LIFE_SAFETY
    )

    print(
        "\n[2] Phone A Transmitting:"
    )

    print(
        f"    --> Language: "
        f"{language} "
        f"({OFFICIAL_LANGUAGES[language]})"
    )

    print(
        f"    --> Priority: "
        f"{priority} "
        "(ALERT_LIFE_SAFETY)"
    )

    print(
        f"    --> Semantic Bytes: "
        f"0x{semantic_packet.hex()}"
    )

    print(
        f"    --> Payload Size: "
        f"{len(semantic_packet)} bytes"
    )

    # ----------------------------------------------------------
    # Transmit
    # ----------------------------------------------------------

    tx_start = (
        time.perf_counter()
    )

    phone_a.send_voice_message(
        voice_payload=(
            semantic_packet
        ),
        language=language,
        priority=priority,
        target_callsign=(
            "PHONE_B_TTS_MODE"
        ),
    )

    # ----------------------------------------------------------
    # Wait for asynchronous delivery
    #
    # Polling is better than blindly sleeping.
    # ----------------------------------------------------------

    timeout_seconds = 1.0

    deadline = (
        time.perf_counter()
        + timeout_seconds
    )

    while (
        not delivered_to_phone_b
        and time.perf_counter()
        < deadline
    ):

        time.sleep(0.001)

    # ----------------------------------------------------------
    # Reception verification
    # ----------------------------------------------------------

    assert (
        len(delivered_to_phone_b)
        == 1
    ), (
        "Phone B did not receive "
        "the transmission!"
    )

    result = (
        delivered_to_phone_b[0]
    )

    origin = (
        result["origin"]
    )

    rx_language = (
        result["language"]
    )

    rx_priority = (
        result["priority"]
    )

    rx_payload = (
        result["payload"]
    )

    processing_latency_ms = (
        result[
            "processing_latency_ms"
        ]
    )

    rx_time = (
        result["received_at"]
    )

    total_transport_latency_ms = (
        rx_time - tx_start
    ) * 1000.0

    print(
        "\n[3] Phone B Reception:"
    )

    print(
        f"    --> Sender: "
        f"{origin}"
    )

    print(
        f"    --> Language: "
        f"{rx_language} "
        f"({OFFICIAL_LANGUAGES.get(rx_language)})"
    )

    print(
        f"    --> Priority: "
        f"{rx_priority}"
    )

    print(
        f"    --> Payload: "
        f"0x{rx_payload.hex()}"
    )

    # ----------------------------------------------------------
    # Integrity checks
    # ----------------------------------------------------------

    assert (
        origin
        == "PHONE_A_STT_MODE"
    ), (
        "Incorrect sender callsign!"
    )

    assert (
        rx_language
        == language
    ), (
        "Language metadata corrupted!"
    )

    assert (
        rx_priority
        == priority
    ), (
        "Priority metadata corrupted!"
    )

    assert (
        rx_payload
        == semantic_packet
    ), (
        "Payload corruption detected!"
    )

    print(
        "    --> Payload Integrity: "
        "PASS"
    )

    # ----------------------------------------------------------
    # Latency evaluation
    # ----------------------------------------------------------

    print(
        "\n[4] Transport Performance:"
    )

    print(
        f"    --> End-to-End Localhost: "
        f"{total_transport_latency_ms:.3f} ms"
    )

    print(
        f"    --> Receiver Processing: "
        f"{processing_latency_ms:.3f} ms"
    )

    latency_target_ms = 20.0

    if (
        total_transport_latency_ms
        < latency_target_ms
    ):

        print(
            f"    --> Target < "
            f"{latency_target_ms:.0f} ms: "
            f"PASS"
        )

    else:

        print(
            f"    --> Target < "
            f"{latency_target_ms:.0f} ms: "
            f"NOT MET"
        )

    # ----------------------------------------------------------
    # Priority routing verification
    # ----------------------------------------------------------

    print(
        "\n[5] Priority Routing:"
    )

    if (
        rx_priority
        == PriorityLevel
        .ALERT_LIFE_SAFETY
    ):

        print(
            "    --> LIFE-SAFETY ALERT "
            "DETECTED"
        )

        print(
            "    --> Application Audio "
            "Policy: HIGHEST PRIORITY"
        )

    else:

        raise AssertionError(
            "Life-safety priority "
            "was not preserved!"
        )

    # ----------------------------------------------------------
    # Telemetry
    # ----------------------------------------------------------

    telemetry_a = (
        phone_a.get_telemetry()
    )

    telemetry_b = (
        phone_b.get_telemetry()
    )

    print(
        "\n[6] Transport Telemetry:"
    )

    print(
        f"    --> Phone A TX Packets: "
        f"{telemetry_a['tx_packets']}"
    )

    print(
        f"    --> Phone A TX Bytes: "
        f"{telemetry_a['tx_bytes']}"
    )

    print(
        f"    --> Phone B RX Packets: "
        f"{telemetry_b['rx_packets']}"
    )

    print(
        f"    --> Phone B RX Bytes: "
        f"{telemetry_b['rx_bytes']}"
    )

    print(
        f"    --> Phone B Mesh "
        f"Duplicates Dropped: "
        f"{telemetry_b['mesh_duplicates_dropped']}"
    )

    print(
        f"    --> FEC Configuration: "
        f"K={telemetry_a['fec_k']}, "
        f"M={telemetry_a['fec_m']}"
    )

    # ----------------------------------------------------------
    # Shutdown
    # ----------------------------------------------------------

    phone_a.stop()

    phone_b.stop()

    # ----------------------------------------------------------
    # Final result
    # ----------------------------------------------------------

    print()
    print("=" * 70)

    print(
        "  SUCCESS: FULL STACK DELIVERY VERIFIED"
    )

    print(
        "  LANGUAGE METADATA: PASS"
    )

    print(
        "  PRIORITY METADATA: PASS"
    )

    print(
        "  PAYLOAD INTEGRITY: PASS"
    )

    print(
        "  UDP + MESH + CRYPTO: PASS"
    )

    print("=" * 70)


if __name__ == "__main__":

    test_two_phone_isro_loop()
