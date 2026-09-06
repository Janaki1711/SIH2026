"""
udp_transport.py — Connectionless UDP Transceiver

Implements asynchronous UDP packet transmission and reception.

Features:
- UDP connectionless transport
- Background receiver thread
- Socket timeout for responsive shutdown
- Broadcast support
- TX/RX telemetry counters
- Clean resource shutdown
"""

import socket
import threading

from typing import Callable, Optional, Tuple


DEFAULT_RADIO_PORT = 8988
DEFAULT_BUFFER_SIZE = 2048


class UDPTransceiver:
    """
    Connectionless UDP transmitter and receiver.

    The receiver runs in a daemon thread so packet reception does
    not block the application's main execution thread.
    """

    def __init__(
        self,
        bind_ip: str = "0.0.0.0",
        port: int = DEFAULT_RADIO_PORT,
    ):
        self.bind_ip = bind_ip
        self.port = port

        self.sock: Optional[socket.socket] = None

        self.is_running = False

        self.rx_thread: Optional[
            threading.Thread
        ] = None

        self.on_packet_received: Optional[
            Callable[
                [bytes, Tuple[str, int]],
                None,
            ]
        ] = None

        # Telemetry metrics
        self.tx_packets = 0
        self.rx_packets = 0

        self.tx_bytes = 0
        self.rx_bytes = 0

        # Protect shared counters and socket lifecycle.
        self._lock = threading.Lock()

    def _create_socket(
        self,
        bind: bool = False,
    ) -> socket.socket:
        """
        Create and configure a UDP socket.
        """

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_BROADCAST,
            1,
        )

        if bind:
            sock.bind(
                (
                    self.bind_ip,
                    self.port,
                )
            )

        return sock

    def start_listening(
        self,
        callback: Callable[
            [bytes, Tuple[str, int]],
            None,
        ],
    ) -> None:
        """
        Start the UDP receiver daemon thread.

        The callback receives:

            callback(data, address)

        where address is:

            (ip_address, port)
        """

        if self.is_running:
            raise RuntimeError(
                "UDP receiver is already running"
            )

        self.on_packet_received = callback

        self.sock = self._create_socket(
            bind=True
        )

        # Timeout allows periodic checking of is_running,
        # enabling a clean shutdown.
        self.sock.settimeout(0.2)

        self.is_running = True

        self.rx_thread = threading.Thread(
            target=self._listen_loop,
            name="udp-receiver",
            daemon=True,
        )

        self.rx_thread.start()

    def _listen_loop(self) -> None:
        """
        Background UDP receive loop.
        """

        while self.is_running:

            try:

                if self.sock is None:
                    break

                data, address = (
                    self.sock.recvfrom(
                        DEFAULT_BUFFER_SIZE
                    )
                )

                if (
                    data
                    and self.on_packet_received
                ):

                    with self._lock:

                        self.rx_packets += 1
                        self.rx_bytes += len(
                            data
                        )

                    self.on_packet_received(
                        data,
                        address,
                    )

            except socket.timeout:

                # Expected during idle periods.
                continue

            except OSError:

                # Socket was likely closed during stop().
                if self.is_running:
                    continue

                break

            except Exception:

                # Prevent one bad callback or packet
                # from permanently killing the receiver.
                if not self.is_running:
                    break

                continue

    def send_packet(
        self,
        data: bytes,
        target_ip: str = "127.0.0.1",
        port: int = DEFAULT_RADIO_PORT,
    ) -> None:
        """
        Send a connectionless UDP datagram.

        If the transceiver is not already listening,
        a socket is created automatically.
        """

        if not isinstance(
            data,
            (bytes, bytearray),
        ):
            raise TypeError(
                "UDP packet data must be bytes"
            )

        with self._lock:

            if self.sock is None:

                self.sock = self._create_socket(
                    bind=False
                )

            self.sock.sendto(
                data,
                (
                    target_ip,
                    port,
                ),
            )

            self.tx_packets += 1
            self.tx_bytes += len(data)

    def get_metrics(self) -> dict:
        """
        Return current transport telemetry.
        """

        with self._lock:

            return {
                "tx_packets": self.tx_packets,
                "rx_packets": self.rx_packets,
                "tx_bytes": self.tx_bytes,
                "rx_bytes": self.rx_bytes,
            }

    def stop(self) -> None:
        """
        Stop the receiver and close the UDP socket.
        """

        self.is_running = False

        sock = self.sock

        # Closing the socket immediately wakes recvfrom()
        # instead of waiting for the timeout.
        if sock is not None:

            try:
                sock.close()

            except OSError:
                pass

        self.sock = None

        if (
            self.rx_thread is not None
            and self.rx_thread.is_alive()
        ):

            self.rx_thread.join(
                timeout=1.0
            )

        self.rx_thread = None
        self.on_packet_received = None


if __name__ == "__main__":

    def on_packet(
        data: bytes,
        address: Tuple[str, int],
    ) -> None:

        print(
            f"RX from {address}: "
            f"{data!r}"
        )

    radio = UDPTransceiver(
        port=DEFAULT_RADIO_PORT
    )

    radio.start_listening(
        on_packet
    )

    print(
        f"UDP receiver listening "
        f"on port {DEFAULT_RADIO_PORT}"
    )

    try:

        while True:
            pass

    except KeyboardInterrupt:

        print(
            "\nStopping UDP transceiver..."
        )

    finally:

        radio.stop()
