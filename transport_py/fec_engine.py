# ==============================================================================
# iTantra WFB-ng Transport - Reed-Solomon GF(2^8) Erasure Coding Engine
# Standard: Cauchy Matrix over GF(2^8) with Primitive Polynomial 0x11D (285)
# Configuration: K=8 Data Shards, M=4 Parity Shards (N=12 Total)
# ==============================================================================

from typing import List, Dict

class GF256:
    """Galois Field GF(2^8) with Primitive Polynomial x^8 + x^4 + x^3 + x^2 + 1 (0x11D = 285)."""
    POLYNOMIAL = 0x11D

    def __init__(self):
        self.exp = [0] * 512
        self.log = [0] * 256
        x = 1
        for i in range(255):
            self.exp[i] = x
            self.exp[i + 255] = x
            self.log[x] = i
            x <<= 1
            if x & 0x100:
                x ^= self.POLYNOMIAL
        self.log[0] = 0

    def add(self, a: int, b: int) -> int:
        return a ^ b

    def sub(self, a: int, b: int) -> int:
        return a ^ b

    def mul(self, a: int, b: int) -> int:
        if a == 0 or b == 0:
            return 0
        return self.exp[self.log[a] + self.log[b]]

    def div(self, a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError("Division by zero in GF(2^8)")
        if a == 0:
            return 0
        return self.exp[self.log[a] + 255 - self.log[b]]

    def inv(self, a: int) -> int:
        if a == 0:
            raise ZeroDivisionError("Zero has no multiplicative inverse in GF(2^8)")
        return self.exp[255 - self.log[a]]

_gf = GF256()

class ReedSolomonFECEngine:
    """
    Systematic Cauchy Reed-Solomon Erasure Coding.
    
    Specification:
    - K (Data Shards) = 8
    - M (Parity Shards) = 4
    - Total Shards (N) = 12
    - Fault Tolerance: Any 4 arbitrary shard losses can be 100% reconstructed.
    - Cauchy Generator Matrix: C[i][j] = 1 / ((i + K) ^ j) for i in 0..M-1, j in 0..K-1
    """

    def __init__(self, k: int = 8, m: int = 4):
        self.k = k
        self.m = m
        self.n = k + m

        # Precompute Cauchy parity generator matrix (M rows x K cols)
        self.matrix: List[List[int]] = []
        for i in range(m):
            row = []
            x_i = i + k
            for j in range(k):
                y_j = j
                denom = x_i ^ y_j
                row.append(_gf.inv(denom))
            self.matrix.append(row)

    def encode(self, payload: bytes) -> List[bytes]:
        """
        Encodes a payload into (K + M) shards.
        Returns:
            List of N shards where:
            - index 0..K-1: Systematic Data Shards
            - index K..K+M-1: Parity Shards
        """
        shard_size = (len(payload) + self.k - 1) // self.k
        padded_len = shard_size * self.k
        padded_payload = payload.ljust(padded_len, b'\x00')

        # 1. Systematic Data Shards (0..K-1)
        data_shards = [padded_payload[i * shard_size : (i + 1) * shard_size] for i in range(self.k)]
        
        # 2. Cauchy Parity Shards (K..K+M-1)
        parity_shards = []
        for i in range(self.m):
            parity = bytearray(shard_size)
            for j in range(self.k):
                coeff = self.matrix[i][j]
                d_shard = data_shards[j]
                for b in range(shard_size):
                    parity[b] ^= _gf.mul(coeff, d_shard[b])
            parity_shards.append(bytes(parity))

        return data_shards + parity_shards

    def decode(self, received_shards: Dict[int, bytes], original_payload_len: int) -> bytes:
        """
        Reconstructs original payload from any K received shards.
        Args:
            received_shards: Map of { shard_index (0..N-1) : shard_bytes }
            original_payload_len: Original payload length before padding.
        Returns:
            Original payload bytes.
        """
        if len(received_shards) < self.k:
            raise ValueError(f"Insufficient shards for RS reconstruction: need {self.k}, got {len(received_shards)}")

        # Fast path: All K data shards are present (no parity computation needed)
        if all(i in received_shards for i in range(self.k)):
            recovered = b"".join(received_shards[i] for i in range(self.k))
            return recovered[:original_payload_len]

        # Select first K available shards
        selected_indices = sorted(list(received_shards.keys()))[:self.k]
        shard_size = len(received_shards[selected_indices[0]])

        # Build K x K submatrix
        submatrix: List[List[int]] = []
        for idx in selected_indices:
            if idx < self.k:
                # Identity row for data shard
                row = [0] * self.k
                row[idx] = 1
            else:
                # Cauchy parity row
                row = list(self.matrix[idx - self.k])
            submatrix.append(row)

        # Invert K x K submatrix over GF(2^8)
        inv_matrix = self._invert_matrix(submatrix)

        # Reconstruct all K data shards
        recovered_data_shards = []
        for i in range(self.k):
            reconstructed = bytearray(shard_size)
            for j in range(self.k):
                coeff = inv_matrix[i][j]
                r_shard = received_shards[selected_indices[j]]
                for b in range(shard_size):
                    reconstructed[b] ^= _gf.mul(coeff, r_shard[b])
            recovered_data_shards.append(bytes(reconstructed))

        recovered = b"".join(recovered_data_shards)
        return recovered[:original_payload_len]

    def _invert_matrix(self, mat: List[List[int]]) -> List[List[int]]:
        dim = len(mat)
        A = [list(row) for row in mat]
        I = [[1 if i == j else 0 for j in range(dim)] for i in range(dim)]

        for col in range(dim):
            # Pivot selection
            pivot_row = -1
            for row in range(col, dim):
                if A[row][col] != 0:
                    pivot_row = row
                    break
            if pivot_row == -1:
                raise ValueError("Singular matrix encountered during RS erasure decoding")

            # Swap rows
            A[col], A[pivot_row] = A[pivot_row], A[col]
            I[col], I[pivot_row] = I[pivot_row], I[col]

            # Scale pivot row
            pivot_inv = _gf.inv(A[col][col])
            for j in range(dim):
                A[col][j] = _gf.mul(A[col][j], pivot_inv)
                I[col][j] = _gf.mul(I[col][j], pivot_inv)

            # Eliminate other rows
            for row in range(dim):
                if row != col and A[row][col] != 0:
                    factor = A[row][col]
                    for j in range(dim):
                        A[row][j] ^= _gf.mul(factor, A[col][j])
                        I[row][j] ^= _gf.mul(factor, I[col][j])

        return I
