"""
test_udp.py — Verifies bidirectional connectionless UDP transmission.

This test runs over localhost and verifies:
- Node 1 -> Node 2 delivery
- Node 2 -> Node 1 delivery
- Payload integrity
- Transport telemetry counters

Note:
Localhost latency is NOT equivalent to real RF or over-the-air latency.
"""

import os
import sys
import time
import threading


sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "udp",
        )
    ),
)

from udp_transport import UDPTransceiver


def test_udp_transceiver():
    print("=" * 70)
    print("  UDP TRANSCEIVER TEST: BIDIRECTIONAL CONNECTIONLESS LINK")
    print("=" * 70)

    received_on_node1 = []
    received_on_node2 = []

    node1_event = threading.Event()
    node2_event = threading.Event()

    def node1_callback(data, addr):
        received_on_node1.append(
            (
                data,
                addr,
                time.perf_counter(),
            )
        )
        node1_event.set()

    def node2_callback(data, addr):
        received_on_node2.append(
            (
                data,
                addr,
                time.perf_counter(),
            )
        )
        node2_event.set()

    node1 = UDPTransceiver(
        bind_ip="127.0.0.1",
        port=8988,
    )

    node2 = UDPTransceiver(
        bind_ip="127.0.0.1",
        port=8989,
    )

    try:

        # ------------------------------------------------------
        # 1. Start both receiver nodes
        # ------------------------------------------------------

        node1.start_listening(
            node1_callback
        )

        node2.start_listening(
            node2_callback
        )

        print(
            "\n[1] UDP Transceivers Online:"
        )

        print(
            "    --> Node 1: "
            "127.0.0.1:8988"
        )

        print(
            "    --> Node 2: "
            "127.0.0.1:8989"
        )

        # Small startup delay so both receiver threads
        # are fully scheduled.
        time.sleep(0.02)

        # ------------------------------------------------------
        # 2. Node 1 -> Node 2
        # ------------------------------------------------------

        voice_packet = (
            b"AGY1"
            b"::TOLANKERE_EVACUATE_5_IMMEDIATELY::"
        )

        print(
            "\n[2] Node 1 sending voice packet "
            "to Node 2..."
        )

        start_tx_time = (
            time.perf_counter()
        )

        node1.send_packet(
            voice_packet,
            target_ip="127.0.0.1",
            port=8989,
        )

        # Wait for actual packet arrival.
        received = node2_event.wait(
            timeout=1.0
        )

        assert received, (
            "Node 2 did not receive packet "
            "within timeout!"
        )

        assert len(
            received_on_node2
        ) == 1, (
            "Unexpected Node 2 packet count!"
        )

        (
            rx_data,
            rx_addr,
            rx_time,
        ) = received_on_node2[0]

        latency_ms = (
            rx_time
            - start_tx_time
        ) * 1000.0

        assert rx_data == voice_packet, (
            "Node 2 payload corruption detected!"
        )

        print(
            f"    --> Node 2 RECEIVED "
            f"from {rx_addr}:"
        )

        print(
            f"        Payload: "
            f"{rx_data.decode(errors='replace')}"
        )

        print(
            f"        Localhost Latency: "
            f"{latency_ms:.3f} ms"
        )

        # ------------------------------------------------------
        # 3. Node 2 -> Node 1
        # ------------------------------------------------------

        ack_packet = (
            b"AGY1"
            b"::ACK_RESCUE_TEAM_EN_ROUTE::"
        )

        print(
            "\n[3] Node 2 sending "
            "reverse reply to Node 1..."
        )

        start_reply_time = (
            time.perf_counter()
        )

        node2.send_packet(
            ack_packet,
            target_ip="127.0.0.1",
            port=8988,
        )

        received = node1_event.wait(
            timeout=1.0
        )

        assert received, (
            "Node 1 did not receive "
            "reply within timeout!"
        )

        assert len(
            received_on_node1
        ) == 1, (
            "Unexpected Node 1 packet count!"
        )

        (
            ack_data,
            ack_addr,
            ack_time,
        ) = received_on_node1[0]

        ack_latency_ms = (
            ack_time
            - start_reply_time
        ) * 1000.0

        assert ack_data == ack_packet, (
            "ACK payload corruption detected!"
        )

        print(
            f"    --> Node 1 RECEIVED "
            f"reply from {ack_addr}:"
        )

        print(
            f"        Payload: "
            f"{ack_data.decode(errors='replace')}"
        )

        print(
            f"        Localhost Latency: "
            f"{ack_latency_ms:.3f} ms"
        )

        # ------------------------------------------------------
        # 4. Verify telemetry
        # ------------------------------------------------------

        node1_metrics = (
            node1.get_metrics()
        )

        node2_metrics = (
            node2.get_metrics()
        )

        print(
            "\n[4] Diagnostic Telemetry:"
        )

        print(
            "    --> Node 1: "
            f"TX={node1_metrics['tx_packets']}, "
            f"RX={node1_metrics['rx_packets']}, "
            f"TX Bytes={node1_metrics['tx_bytes']}, "
            f"RX Bytes={node1_metrics['rx_bytes']}"
        )

        print(
            "    --> Node 2: "
            f"TX={node2_metrics['tx_packets']}, "
            f"RX={node2_metrics['rx_packets']}, "
            f"TX Bytes={node2_metrics['tx_bytes']}, "
            f"RX Bytes={node2_metrics['rx_bytes']}"
        )

        # Telemetry verification.

        assert (
            node1_metrics["tx_packets"] == 1
        )

        assert (
            node1_metrics["rx_packets"] == 1
        )

        assert (
            node2_metrics["tx_packets"] == 1
        )

        assert (
            node2_metrics["rx_packets"] == 1
        )

        # ------------------------------------------------------
        # Success
        # ------------------------------------------------------

        print()
        print("=" * 70)

        print(
            "  SUCCESS: BIDIRECTIONAL UDP "
            "PACKET DELIVERY VERIFIED!"
        )

        print(
            "  PAYLOAD INTEGRITY: 100%"
        )

        print(
            "  NOTE: LATENCY ABOVE IS LOCALHOST "
            "ONLY, NOT REAL RF AIRTIME."
        )

        print("=" * 70)

    finally:

        node1.stop()
        node2.stop()


if __name__ == "__main__":
    test_udp_transceiver()
