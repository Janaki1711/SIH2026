"""
mesh_router.py — Multi-Hop Mesh Router

Features:
- Up to 7-hop forwarding
- TTL-based loop limitation
- Stable message deduplication
- LRU deduplication cache
- Broadcast and unicast delivery
- Neighbor tracking
- Basic store-and-forward rendezvous buffering

Packet format:

    +-------+------+----------+------------------+------------------+
    | Magic | TTL  | Sequence | Origin Callsign  | Target Callsign  |
    | 1 byte|1 byte| 2 bytes  | 16 bytes         | 16 bytes         |
    +-------+------+----------+------------------+------------------+

    Followed by payload.
"""

import hashlib
import struct
import time

from collections import OrderedDict
from typing import Callable, Dict, List, Optional, Tuple


MAX_HOPS = 7
DEDUP_CACHE_SIZE = 128

HEADER_FORMAT = "!BBH16s16s"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class MeshPacketHeader:
    """
    Mesh routing envelope.

    Header fields:

        Magic:
            Identifies a mesh packet.

        TTL:
            Number of forwarding hops remaining.

        Sequence:
            Sender-provided 16-bit message sequence number.

        Origin:
            Original source callsign.

        Target:
            Destination callsign, ALL, or *.

    TTL is intentionally NOT part of the stable deduplication
    identity because it changes at every hop.
    """

    MAGIC = 0x4D

    @staticmethod
    def pack(
        origin: str,
        target: str,
        seq: int,
        ttl: int,
        payload: bytes,
    ) -> bytes:
        """
        Serialize a mesh packet.
        """

        if not 0 <= seq <= 0xFFFF:
            raise ValueError(
                "Sequence must fit in 16 bits"
            )

        if not 0 <= ttl <= 0xFF:
            raise ValueError(
                "TTL must fit in 8 bits"
            )

        origin_bytes = (
            origin.encode("utf-8")[:16]
            .ljust(16, b"\x00")
        )

        target_bytes = (
            target.encode("utf-8")[:16]
            .ljust(16, b"\x00")
        )

        header = struct.pack(
            HEADER_FORMAT,
            MeshPacketHeader.MAGIC,
            ttl,
            seq,
            origin_bytes,
            target_bytes,
        )

        return header + payload

    @staticmethod
    def unpack(
        data: bytes,
    ) -> Optional[
        Tuple[int, int, str, str, bytes]
    ]:
        """
        Deserialize a mesh packet.

        Returns:

            ttl,
            sequence,
            origin,
            target,
            payload

        or None if invalid.
        """

        if len(data) < HEADER_SIZE:
            return None

        try:

            (
                magic,
                ttl,
                seq,
                origin_bytes,
                target_bytes,
            ) = struct.unpack(
                HEADER_FORMAT,
                data[:HEADER_SIZE],
            )

        except struct.error:
            return None

        if magic != MeshPacketHeader.MAGIC:
            return None

        origin = (
            origin_bytes
            .rstrip(b"\x00")
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        target = (
            target_bytes
            .rstrip(b"\x00")
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        payload = data[
            HEADER_SIZE:
        ]

        return (
            ttl,
            seq,
            origin,
            target,
            payload,
        )


class MeshRouter:
    """
    Multi-hop mesh routing engine.

    Each router can:

    1. Receive a mesh packet.
    2. Detect duplicate messages.
    3. Deliver packets addressed locally.
    4. Forward packets while TTL remains.
    5. Track neighboring origins.
    6. Buffer packets for rendezvous delivery.
    """

    def __init__(
        self,
        my_callsign: str,
        broadcast_fn: Callable[
            [bytes],
            None,
        ],
    ):
        if not my_callsign:
            raise ValueError(
                "Callsign cannot be empty"
            )

        self.my_callsign = my_callsign

        self.broadcast_fn = (
            broadcast_fn
        )

        # Stable message identity cache.
        #
        # OrderedDict provides LRU behavior.
        self.seen_hashes: OrderedDict[
            str,
            float,
        ] = OrderedDict()

        # Offline/store-and-forward buffer.
        #
        # target_callsign -> packets
        self.rendezvous_buffer: Dict[
            str,
            List[bytes],
        ] = {}

        # Origin/neighbor activity tracking.
        #
        # callsign -> last seen epoch
        self.known_neighbors: Dict[
            str,
            float,
        ] = {}

        # Telemetry.
        self.relayed_count = 0
        self.dropped_duplicates = 0
        self.locally_delivered = 0
        self.invalid_packets = 0

    def _get_message_hash(
        self,
        origin: str,
        target: str,
        seq: int,
        payload: bytes,
    ) -> str:
        """
        Create a stable message identity.

        TTL is deliberately excluded because it changes
        during forwarding.
        """

        identity = (
            origin.encode("utf-8")
            + b"\x00"
            + target.encode("utf-8")
            + b"\x00"
            + struct.pack(
                "!H",
                seq,
            )
            + payload
        )

        return hashlib.sha256(
            identity
        ).hexdigest()[:32]

    def _mark_seen(
        self,
        message_hash: str,
    ) -> None:
        """
        Insert or refresh an entry in the LRU cache.
        """

        if message_hash in self.seen_hashes:

            self.seen_hashes.move_to_end(
                message_hash
            )

            self.seen_hashes[
                message_hash
            ] = time.time()

            return

        self.seen_hashes[
            message_hash
        ] = time.time()

        if (
            len(self.seen_hashes)
            > DEDUP_CACHE_SIZE
        ):

            self.seen_hashes.popitem(
                last=False
            )

    def _is_seen(
        self,
        message_hash: str,
    ) -> bool:
        """
        Check whether a message was already processed.
        """

        if (
            message_hash
            not in self.seen_hashes
        ):

            return False

        self.seen_hashes.move_to_end(
            message_hash
        )

        return True

    def route_incoming(
        self,
        raw_bytes: bytes,
        on_local_deliver: Callable[
            [str, bytes],
            None,
        ],
    ) -> None:
        """
        Process an incoming mesh packet.

        Possible outcomes:

        1. Drop invalid packet.
        2. Drop duplicate.
        3. Deliver locally.
        4. Relay to neighboring nodes.
        """

        unpacked = (
            MeshPacketHeader.unpack(
                raw_bytes
            )
        )

        if unpacked is None:

            self.invalid_packets += 1

            return

        (
            ttl,
            seq,
            origin,
            target,
            payload,
        ) = unpacked

        # Create stable identity.
        #
        # This remains identical across hops.
        message_hash = (
            self._get_message_hash(
                origin,
                target,
                seq,
                payload,
            )
        )

        # --------------------------------------------------
        # 1. Deduplication
        # --------------------------------------------------

        if self._is_seen(
            message_hash
        ):

            self.dropped_duplicates += 1

            return

        self._mark_seen(
            message_hash
        )

        # --------------------------------------------------
        # 2. Neighbor activity
        # --------------------------------------------------

        self.known_neighbors[
            origin
        ] = time.time()

        # --------------------------------------------------
        # 3. Local delivery
        # --------------------------------------------------

        is_broadcast = target in (
            "ALL",
            "*",
        )

        is_for_me = (
            target
            == self.my_callsign
        )

        if (
            is_for_me
            or is_broadcast
        ):

            self.locally_delivered += 1

            on_local_deliver(
                origin,
                payload,
            )

        # --------------------------------------------------
        # 4. Stop private packet after delivery
        # --------------------------------------------------

        if is_for_me:

            return

        # --------------------------------------------------
        # 5. Forward while TTL remains
        # --------------------------------------------------

        if ttl <= 1:

            return

        new_ttl = ttl - 1

        relayed_packet = (
            MeshPacketHeader.pack(
                origin,
                target,
                seq,
                new_ttl,
                payload,
            )
        )

        self.relayed_count += 1

        self.broadcast_fn(
            relayed_packet
        )

    def send_new_packet(
        self,
        target_callsign: str,
        seq: int,
        payload: bytes,
    ) -> None:
        """
        Originate and broadcast a new mesh packet.
        """

        packet = (
            MeshPacketHeader.pack(
                self.my_callsign,
                target_callsign,
                seq,
                MAX_HOPS,
                payload,
            )
        )

        message_hash = (
            self._get_message_hash(
                self.my_callsign,
                target_callsign,
                seq,
                payload,
            )
        )

        # Mark locally originated packets as seen
        # to prevent receiving our own broadcast
        # from causing a forwarding loop.

        self._mark_seen(
            message_hash
        )

        self.broadcast_fn(
            packet
        )

    def buffer_for_peer(
        self,
        peer_callsign: str,
        packet: bytes,
    ) -> None:
        """
        Store a packet for later rendezvous delivery.
        """

        if (
            peer_callsign
            not in self.rendezvous_buffer
        ):

            self.rendezvous_buffer[
                peer_callsign
            ] = []

        self.rendezvous_buffer[
            peer_callsign
        ].append(
            packet
        )

    def retrieve_buffered_packets(
        self,
        peer_callsign: str,
    ) -> List[bytes]:
        """
        Retrieve and remove packets buffered for a peer.
        """

        return (
            self.rendezvous_buffer.pop(
                peer_callsign,
                [],
            )
        )

    def get_metrics(self) -> Dict[
        str,
        int,
    ]:
        """
        Return router telemetry.
        """

        return {
            "relayed_count":
                self.relayed_count,

            "dropped_duplicates":
                self.dropped_duplicates,

            "locally_delivered":
                self.locally_delivered,

            "invalid_packets":
                self.invalid_packets,

            "known_neighbors":
                len(
                    self.known_neighbors
                ),

            "dedup_cache_size":
                len(
                    self.seen_hashes
                ),
        }
