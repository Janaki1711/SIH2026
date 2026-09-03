"""
test_fec.py — Verifies Block Forward Error Correction under packet loss.

Tests recovery of 8 original packets using 4 parity packets.
Any 8 packets out of the total 12 should reconstruct the
original data.
"""

import os
import sys
import random


# Add transport/fec to Python import path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "fec",
        )
    ),
)

from fec_engine import BlockFEC


def make_packet(index: int, packet_size: int) -> bytes:
    """
    Create a deterministic fixed-size test packet.

    FEC requires every block in a generation to have
    exactly the same size.
    """

    payload = (
        f"VOICE_SEG_{index:02d}_"
        f"[SECTOR_4_HELP_SEND_BOAT_NOW!]"
    ).encode("utf-8")

    # Ensure exactly packet_size bytes.
    if len(payload) > packet_size:
        return payload[:packet_size]

    return payload.ljust(
        packet_size,
        b"\x00",
    )


def display_packet(packet: bytes) -> str:
    """
    Convert a packet to a readable string for terminal output.
    """

    return packet.rstrip(
        b"\x00"
    ).decode(
        "utf-8",
        errors="replace",
    )


def run_fec_simulation():
    print("=" * 70)
    print(
        "  BLOCK FEC RESILIENCE TEST: "
        "SIMULATING 33.3% RF PACKET LOSS"
    )
    print("=" * 70)

    # Number of original packets
    K = 8

    # Number of parity packets
    M = 4

    # Every packet MUST have equal length.
    PACKET_SIZE = 64

    # Total packets transmitted
    N = K + M

    fec = BlockFEC(
        k=K,
        m=M,
    )

    # ----------------------------------------------------------
    # 1. Create original data packets
    # ----------------------------------------------------------

    original_packets = [
        make_packet(
            i,
            PACKET_SIZE,
        )
        for i in range(K)
    ]

    print(
        f"\n[1] Generated {K} Data Packets "
        f"(Size: {PACKET_SIZE} bytes each):"
    )

    for i, packet in enumerate(
        original_packets
    ):
        print(
            f"    Packet #{i:02d}: "
            f"{display_packet(packet)}"
        )

    # ----------------------------------------------------------
    # 2. Generate parity packets
    # ----------------------------------------------------------

    parity_packets = fec.encode(
        original_packets
    )

    all_packets = (
        original_packets
        + parity_packets
    )

    print(
        f"\n[2] Encoded {M} Parity Packets "
        f"(Total on air: {len(all_packets)} packets)."
    )

    # ----------------------------------------------------------
    # 3. Simulate packet loss
    #
    # With K=8 and M=4, up to 4 packets may be lost.
    # ----------------------------------------------------------

    dropped_indices = sorted(
        random.sample(
            range(N),
            M,
        )
    )

    received_packets = {
        i: all_packets[i]
        for i in range(N)
        if i not in dropped_indices
    }

    loss_percentage = (
        len(dropped_indices)
        / N
        * 100
    )

    print(
        "\n[3] INJECTING RF PACKET LOSS:"
    )

    print(
        f"    --> Packets LOST: "
        f"{dropped_indices}"
    )

    print(
        f"    --> Loss Rate: "
        f"{loss_percentage:.1f}%"
    )

    print(
        "    --> Packets RECEIVED: "
        f"{sorted(received_packets.keys())}"
    )

    # ----------------------------------------------------------
    # 4. Decode
    # ----------------------------------------------------------

    print(
        "\n[4] Running GF(2^8) "
        "Matrix Reconstruction..."
    )

    reconstructed_packets = fec.decode(
        received_packets,
        block_size=PACKET_SIZE,
    )

    # ----------------------------------------------------------
    # 5. Verify data integrity
    # ----------------------------------------------------------

    assert len(
        reconstructed_packets
    ) == K, (
        "Reconstruction count mismatch!"
    )

    for i in range(K):

        assert (
            reconstructed_packets[i]
            == original_packets[i]
        ), (
            f"Packet #{i} corruption!"
        )

    # ----------------------------------------------------------
    # Success
    # ----------------------------------------------------------

    print()
    print("=" * 70)

    print(
        "  SUCCESS: 100% DATA RECOVERED "
        "WITH ZERO RETRANSMISSION!"
    )

    print("=" * 70)

    for i, packet in enumerate(
        reconstructed_packets
    ):

        if i in dropped_indices:
            status = "RECONSTRUCTED"
        else:
            status = "RECEIVED OK"

        print(
            f"    Packet #{i:02d} "
            f"[{status:13s}]: "
            f"{display_packet(packet)}"
        )


if __name__ == "__main__":
    run_fec_simulation()
