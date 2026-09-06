"""
wfbng_manager.py — Resilient Tactical Transport Manager

Transport stack:

    Application Voice Payload
            |
            v
    Language + Priority Envelope
            |
            v
    Tactical Encryption
            |
            v
    Mesh Routing Envelope
            |
            v
    UDP Transport
            |
            v
         Network

Configured components:
- Tactical crypto
- Connectionless UDP
- Multi-hop mesh routing
- Block FEC configuration

Important:
The BlockFEC instance is configured here, but true FEC transmission
requires grouping multiple application packets into an FEC block and
adding a block-framing protocol. That is intentionally kept separate
rather than pretending that a single packet is FEC protected.
"""

import os
import sys
import time

from pathlib import Path
from typing import Callable, Dict, Optional, Tuple


# --------------------------------------------------------------
# Module path setup
# --------------------------------------------------------------

BASE_DIR = Path(
    __file__
).resolve().parent

sys.path.insert(
    0,
    str(BASE_DIR / "fec"),
)

sys.path.insert(
    0,
    str(BASE_DIR / "crypto"),
)

sys.path.insert(
    0,
    str(BASE_DIR / "udp"),
)

sys.path.insert(
    0,
    str(BASE_DIR / "mesh"),
)


from fec_engine import BlockFEC
from crypto_engine import TacticalCrypto
from udp_transport import (
    DEFAULT_RADIO_PORT,
    UDPTransceiver,
)
from mesh_router import MeshRouter


# --------------------------------------------------------------
# Supported application language identifiers
# --------------------------------------------------------------

OFFICIAL_LANGUAGES = {
    "hi": "Hindi",
    "gu": "Gujarati",
    "mr": "Marathi",
    "kn": "Kannada",
    "ml": "Malayalam",
    "ta": "Tamil",
    "te": "Telugu",
    "or": "Odia",
    "bn": "Bengali",
    "en": "English",
}


class PriorityLevel:
    """
    Application-level message priority.
    """

    ROUTINE = 0

    TACTICAL = 1

    ALERT_LIFE_SAFETY = 2


class WfbngTransportManager:
    """
    High-level tactical transport manager.

    Responsibilities:

    - Validate language metadata.
    - Add message priority.
    - Encrypt application payload.
    - Route using mesh routing.
    - Transmit over UDP.
    - Decrypt locally delivered messages.
    - Expose transport telemetry.
    """

    def __init__(
        self,
        my_callsign: str,
        bind_ip: str = "0.0.0.0",
        port: int = DEFAULT_RADIO_PORT,
        broadcast_target_ip: str = "127.0.0.1",
        remote_port: int = DEFAULT_RADIO_PORT,
    ):

        if not my_callsign:

            raise ValueError(
                "my_callsign cannot be empty"
            )

        self.my_callsign = my_callsign

        self.port = port

        self.broadcast_target_ip = (
            broadcast_target_ip
        )

        self.remote_port = (
            remote_port
        )

        # --------------------------------------------------
        # Layer 1: Tactical cryptography
        # --------------------------------------------------

        self.crypto = TacticalCrypto()

        # --------------------------------------------------
        # Layer 2: UDP transport
        # --------------------------------------------------

        self.udp = UDPTransceiver(
            bind_ip=bind_ip,
            port=port,
        )

        # --------------------------------------------------
        # Layer 3: Mesh router
        # --------------------------------------------------

        self.mesh = MeshRouter(
            my_callsign=my_callsign,
            broadcast_fn=(
                self._raw_udp_broadcast
            ),
        )

        # --------------------------------------------------
        # Layer 4: FEC configuration
        # --------------------------------------------------

        self.fec = BlockFEC(
            k=8,
            m=4,
        )

        # --------------------------------------------------
        # Sequence number
        #
        # Mesh header uses uint16.
        # --------------------------------------------------

        self.sequence_counter = 0

        # --------------------------------------------------
        # Application callback
        #
        # Callback arguments:
        #
        # origin
        # language
        # priority
        # voice_payload
        # local_processing_latency_ms
        # --------------------------------------------------

        self.on_voice_payload_delivered: Optional[
            Callable[
                [
                    str,
                    str,
                    int,
                    bytes,
                    float,
                ],
                None,
            ]
        ] = None

        self.is_running = False

    # ----------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------

    def start(
        self,
        on_voice_delivered: Callable[
            [
                str,
                str,
                int,
                bytes,
                float,
            ],
            None,
        ],
    ) -> None:
        """
        Start the transport receiver.
        """

        if self.is_running:

            return

        self.on_voice_payload_delivered = (
            on_voice_delivered
        )

        self.udp.start_listening(
            self._on_raw_udp_received
        )

        self.is_running = True

    def stop(
        self,
    ) -> None:
        """
        Stop the transport stack.
        """

        if not self.is_running:

            return

        self.is_running = False

        self.udp.stop()

    # ----------------------------------------------------------
    # Sequence generation
    # ----------------------------------------------------------

    def _next_sequence(
        self,
    ) -> int:
        """
        Generate a uint16 sequence number.
        """

        self.sequence_counter = (
            self.sequence_counter + 1
        ) & 0xFFFF

        return self.sequence_counter

    # ----------------------------------------------------------
    # Application send API
    # ----------------------------------------------------------

    def send_voice_message(
        self,
        voice_payload: bytes,
        language: str = "hi",
        priority: int = (
            PriorityLevel.ROUTINE
        ),
        target_callsign: str = "ALL",
    ) -> None:
        """
        Send a voice/application payload.

        Pipeline:

            application payload
                ->
            language/priority envelope
                ->
            encryption
                ->
            mesh routing
                ->
            UDP
        """

        if (
            language
            not in OFFICIAL_LANGUAGES
        ):

            supported = (
                ", ".join(
                    OFFICIAL_LANGUAGES.keys()
                )
            )

            raise ValueError(
                f"Unsupported language "
                f"'{language}'. "
                f"Supported: {supported}"
            )

        if (
            priority
            not in (
                PriorityLevel.ROUTINE,
                PriorityLevel.TACTICAL,
                PriorityLevel.ALERT_LIFE_SAFETY,
            )
        ):

            raise ValueError(
                "Invalid priority level"
            )

        if not isinstance(
            voice_payload,
            (
                bytes,
                bytearray,
            ),
        ):

            raise TypeError(
                "voice_payload must be bytes"
            )

        sequence = (
            self._next_sequence()
        )

        # --------------------------------------------------
        # Application envelope
        #
        # Byte layout:
        #
        # [ language: 2 bytes ]
        # [ priority: 1 byte ]
        # [ application payload ]
        # --------------------------------------------------

        language_bytes = (
            language
            .encode("utf-8")[:2]
            .ljust(
                2,
                b"\x00",
            )
        )

        tagged_payload = (
            language_bytes
            + bytes([priority])
            + bytes(voice_payload)
        )

        # --------------------------------------------------
        # Encrypt
        # --------------------------------------------------

        encrypted_payload = (
            self.crypto.encrypt(
                tagged_payload,
                sequence_num=sequence,
            )
        )

        # --------------------------------------------------
        # Route through mesh
        # --------------------------------------------------

        self.mesh.send_new_packet(
            target_callsign=(
                target_callsign
            ),
            seq=sequence,
            payload=encrypted_payload,
        )

    # ----------------------------------------------------------
    # Mesh -> UDP
    # ----------------------------------------------------------

    def _raw_udp_broadcast(
        self,
        wire_packet: bytes,
    ) -> None:
        """
        Send raw mesh frame to UDP transport.
        """

        self.udp.send_packet(
            wire_packet,
            target_ip=(
                self.broadcast_target_ip
            ),
            port=self.remote_port,
        )

    # ----------------------------------------------------------
    # UDP receive
    # ----------------------------------------------------------

    def _on_raw_udp_received(
        self,
        data: bytes,
        addr: Tuple[
            str,
            int,
        ],
    ) -> None:
        """
        Receive a raw UDP frame.

        Note:

        This timestamp begins when the UDP
        receiver callback executes. Therefore,
        it cannot measure true RF/airtime latency.
        """

        processing_start = (
            time.perf_counter()
        )

        def on_local_delivery(
            origin: str,
            encrypted_payload: bytes,
        ) -> None:

            self._on_mesh_local_deliver(
                origin=origin,
                encrypted_payload=(
                    encrypted_payload
                ),
                processing_start=(
                    processing_start
                ),
            )

        self.mesh.route_incoming(
            raw_bytes=data,
            on_local_deliver=(
                on_local_delivery
            ),
        )

    # ----------------------------------------------------------
    # Local mesh delivery
    # ----------------------------------------------------------

    def _on_mesh_local_deliver(
        self,
        origin: str,
        encrypted_payload: bytes,
        processing_start: float,
    ) -> None:
        """
        Decrypt and deliver a locally addressed
        application packet.
        """

        try:

            plaintext = (
                self.crypto.decrypt(
                    encrypted_payload
                )
            )

        except Exception:

            # Never allow malformed network data
            # to kill the receive thread.

            return

        if plaintext is None:

            return

        if len(plaintext) < 3:

            return

        language = (
            plaintext[:2]
            .rstrip(
                b"\x00"
            )
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        priority = (
            plaintext[2]
        )

        voice_payload = (
            plaintext[3:]
        )

        processing_latency_ms = (
            time.perf_counter()
            - processing_start
        ) * 1000.0

        callback = (
            self.on_voice_payload_delivered
        )

        if callback is not None:

            callback(
                origin,
                language,
                priority,
                voice_payload,
                processing_latency_ms,
            )

    # ----------------------------------------------------------
    # Telemetry
    # ----------------------------------------------------------

    def get_telemetry(
        self,
    ) -> Dict:
        """
        Return transport telemetry.
        """

        udp_metrics = (
            self.udp.get_metrics()
        )

        mesh_metrics = (
            self.mesh.get_metrics()
        )

        return {
            "callsign":
                self.my_callsign,

            "is_running":
                self.is_running,

            "tx_packets":
                udp_metrics[
                    "tx_packets"
                ],

            "rx_packets":
                udp_metrics[
                    "rx_packets"
                ],

            "tx_bytes":
                udp_metrics[
                    "tx_bytes"
                ],

            "rx_bytes":
                udp_metrics[
                    "rx_bytes"
                ],

            "mesh_relayed":
                mesh_metrics[
                    "relayed_count"
                ],

            "mesh_duplicates_dropped":
                mesh_metrics[
                    "dropped_duplicates"
                ],

            "mesh_local_deliveries":
                mesh_metrics[
                    "locally_delivered"
                ],

            "mesh_invalid_packets":
                mesh_metrics[
                    "invalid_packets"
                ],

            "known_neighbors":
                mesh_metrics[
                    "known_neighbors"
                ],

            "fec_k":
                self.fec.k,

            "fec_m":
                self.fec.m,
        }
