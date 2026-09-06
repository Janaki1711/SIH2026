from crypto_engine import TacticalCrypto


def test_crypto():

    crypto = TacticalCrypto()

    plaintext = b"RESCUE_TEAM_SEND_BOAT"

    encrypted = crypto.encrypt(
        plaintext,
        sequence_num=1,
    )

    decrypted = crypto.decrypt(
        encrypted
    )

    assert decrypted == plaintext

    # Tamper with ciphertext.
    tampered = bytearray(encrypted)
    tampered[-1] ^= 0x01

    assert (
        crypto.decrypt(
            bytes(tampered)
        )
        is None
    )

    print(
        "SUCCESS: encryption, decryption "
        "and tamper detection verified"
    )


if __name__ == "__main__":
    test_crypto()
