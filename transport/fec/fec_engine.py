"""
fec_engine.py — WFB-ng Inspired Block Forward Error Correction (FEC)
Implements Galois Field GF(2^8) matrix-based erasure coding.

Zero external dependencies.
Pure Python implementation.
"""

# GF(2^8) with primitive polynomial:
# x^8 + x^4 + x^3 + x^2 + 1
GF_SIZE = 256
GF_POLY = 0x11D

# Lookup tables for fast GF multiplication
EXP_TABLE = [0] * (GF_SIZE * 2)
LOG_TABLE = [0] * GF_SIZE


def _init_gf_tables():
    """Initialize logarithm and exponent tables for GF(2^8)."""

    x = 1

    for i in range(GF_SIZE - 1):
        EXP_TABLE[i] = x
        EXP_TABLE[i + (GF_SIZE - 1)] = x
        LOG_TABLE[x] = i

        x <<= 1

        if x & 0x100:
            x ^= GF_POLY

    LOG_TABLE[0] = 0


_init_gf_tables()


def gf_mul(a: int, b: int) -> int:
    """
    Multiply two values in GF(2^8).
    """

    if a == 0 or b == 0:
        return 0

    return EXP_TABLE[
        LOG_TABLE[a] + LOG_TABLE[b]
    ]


def gf_div(a: int, b: int) -> int:
    """
    Divide a by b in GF(2^8).
    """

    if b == 0:
        raise ZeroDivisionError(
            "GF(2^8) division by zero"
        )

    if a == 0:
        return 0

    return EXP_TABLE[
        (
            LOG_TABLE[a]
            - LOG_TABLE[b]
            + (GF_SIZE - 1)
        )
        % (GF_SIZE - 1)
    ]


def gf_inv(a: int) -> int:
    """
    Return multiplicative inverse of a in GF(2^8).
    """

    if a == 0:
        raise ZeroDivisionError(
            "GF(2^8) inverse of zero"
        )

    return EXP_TABLE[
        (GF_SIZE - 1) - LOG_TABLE[a]
    ]


class BlockFEC:
    """
    Block Forward Error Correction encoder and decoder.

    K = Number of original data packets
    M = Number of parity packets
    N = Total packets = K + M

    Any K packets out of N can reconstruct
    the original K packets.
    """

    def __init__(
        self,
        k: int = 8,
        m: int = 4
    ):
        """
        Initialize FEC encoder/decoder.
        """

        if k <= 0:
            raise ValueError(
                "K must be greater than zero"
            )

        if m <= 0:
            raise ValueError(
                "M must be greater than zero"
            )

        if k + m > 255:
            raise ValueError(
                "K + M must be <= 255 for GF(2^8)"
            )

        self.k = k
        self.m = m
        self.n = k + m

        # M x K Cauchy parity matrix
        self.matrix = self._build_cauchy_matrix(
            self.k,
            self.m
        )

    def _build_cauchy_matrix(
        self,
        k: int,
        m: int
    ) -> list[list[int]]:
        """
        Construct an M x K Cauchy matrix.

        Every valid square submatrix is invertible,
        allowing recovery from any K received packets.
        """

        matrix = []

        for i in range(m):

            row = []

            for j in range(k):

                # Two disjoint sets of field elements.
                #
                # X = 0 ... m-1
                # Y = m ... m+k-1
                #
                # Cauchy coefficient:
                #
                # 1 / (X_i XOR Y_j)

                x_i = i
                y_j = m + j

                value = gf_inv(
                    x_i ^ y_j
                )

                row.append(value)

            matrix.append(row)

        return matrix

    def encode(
        self,
        data_packets: list[bytes]
    ) -> list[bytes]:
        """
        Generate M parity packets from K data packets.

        All data packets must have identical length.
        """

        if len(data_packets) != self.k:
            raise ValueError(
                f"Expected {self.k} data packets, "
                f"got {len(data_packets)}"
            )

        if not data_packets:
            raise ValueError(
                "No data packets supplied"
            )

        block_size = len(
            data_packets[0]
        )

        for packet in data_packets:

            if len(packet) != block_size:
                raise ValueError(
                    "All data packets must have "
                    "equal length"
                )

        parity_packets = []

        for row in self.matrix:

            parity = bytearray(
                block_size
            )

            for byte_index in range(
                block_size
            ):

                accumulator = 0

                for column_index in range(
                    self.k
                ):

                    coefficient = row[
                        column_index
                    ]

                    data_byte = (
                        data_packets[
                            column_index
                        ][
                            byte_index
                        ]
                    )

                    accumulator ^= gf_mul(
                        coefficient,
                        data_byte
                    )

                parity[
                    byte_index
                ] = accumulator

            parity_packets.append(
                bytes(parity)
            )

        return parity_packets

    def decode(
        self,
        received_packets: dict[int, bytes],
        block_size: int
    ) -> list[bytes]:
        """
        Recover the original K data packets.

        received_packets maps:

            packet_index -> packet_bytes

        Packet indices:

            0 ... K-1       Original data packets
            K ... K+M-1     Parity packets

        At least K packets must be available.
        """

        if len(received_packets) < self.k:
            raise ValueError(
                f"Cannot decode: received "
                f"{len(received_packets)} packets, "
                f"need at least {self.k}"
            )

        # Validate packet indices

        for index in received_packets:

            if index < 0 or index >= self.n:
                raise ValueError(
                    f"Invalid packet index: {index}"
                )

        # Validate packet sizes

        for packet in received_packets.values():

            if len(packet) != block_size:
                raise ValueError(
                    "Received packet size does not "
                    "match block_size"
                )

        # Fast path:
        # all original data packets are available.

        if all(
            index in received_packets
            for index in range(self.k)
        ):

            return [
                received_packets[index]
                for index in range(self.k)
            ]

        # Select any K available packets.

        indices = sorted(
            received_packets.keys()
        )[:self.k]

        # Build decoding matrix.

        sub_matrix = []

        for packet_index in indices:

            if packet_index < self.k:

                # Original data packet.
                #
                # Its encoding row is an identity row.

                row = [
                    (
                        1
                        if column == packet_index
                        else 0
                    )
                    for column in range(
                        self.k
                    )
                ]

            else:

                # Parity packet.
                #
                # Its encoding row comes from
                # the Cauchy matrix.

                parity_index = (
                    packet_index - self.k
                )

                row = list(
                    self.matrix[
                        parity_index
                    ]
                )

            sub_matrix.append(
                row
            )

        # Invert the selected encoding matrix.

        inverse_matrix = (
            self._invert_matrix(
                sub_matrix
            )
        )

        # Multiply inverse matrix by
        # received packet vectors.

        reconstructed = []

        for row in inverse_matrix:

            data = bytearray(
                block_size
            )

            for byte_index in range(
                block_size
            ):

                accumulator = 0

                for column_index in range(
                    self.k
                ):

                    coefficient = row[
                        column_index
                    ]

                    packet_index = indices[
                        column_index
                    ]

                    packet_byte = (
                        received_packets[
                            packet_index
                        ][
                            byte_index
                        ]
                    )

                    accumulator ^= gf_mul(
                        coefficient,
                        packet_byte
                    )

                data[
                    byte_index
                ] = accumulator

            reconstructed.append(
                bytes(data)
            )

        return reconstructed

    def _invert_matrix(
        self,
        matrix: list[list[int]]
    ) -> list[list[int]]:
        """
        Invert a square matrix over GF(2^8)
        using Gaussian elimination.
        """

        n = len(matrix)

        if n == 0:
            raise ValueError(
                "Cannot invert empty matrix"
            )

        for row in matrix:

            if len(row) != n:
                raise ValueError(
                    "Matrix must be square"
                )

        # Create augmented matrix:
        #
        # [ A | I ]

        augmented = []

        for i in range(n):

            identity_row = [
                1 if i == j else 0
                for j in range(n)
            ]

            augmented.append(
                matrix[i][:]
                + identity_row
            )

        # Gaussian elimination.

        for column in range(n):

            # Find pivot row.

            pivot_row = None

            for row_index in range(
                column,
                n
            ):

                if (
                    augmented[
                        row_index
                    ][
                        column
                    ]
                    != 0
                ):

                    pivot_row = row_index
                    break

            if pivot_row is None:
                raise ValueError(
                    "Matrix is singular and "
                    "non-invertible"
                )

            # Move pivot into position.

            if pivot_row != column:

                (
                    augmented[column],
                    augmented[pivot_row]
                ) = (
                    augmented[pivot_row],
                    augmented[column]
                )

            # Normalize pivot row.

            pivot_value = (
                augmented[column][column]
            )

            inverse_pivot = gf_inv(
                pivot_value
            )

            for c in range(2 * n):

                augmented[
                    column
                ][
                    c
                ] = gf_mul(
                    augmented[
                        column
                    ][
                        c
                    ],
                    inverse_pivot
                )

            # Eliminate this column
            # from every other row.

            for row_index in range(n):

                if row_index == column:
                    continue

                factor = (
                    augmented[
                        row_index
                    ][
                        column
                    ]
                )

                if factor == 0:
                    continue

                for c in range(2 * n):

                    augmented[
                        row_index
                    ][
                        c
                    ] ^= gf_mul(
                        factor,
                        augmented[
                            column
                        ][
                            c
                        ]
                    )

        # Extract right half:
        #
        # [ I | A^-1 ]

        return [
            row[n:]
            for row in augmented
        ]
