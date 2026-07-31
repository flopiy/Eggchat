import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AES:

    @staticmethod
    def generate_key():
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt(key: bytes, data: bytes):

        nonce = os.urandom(12)

        aes = AESGCM(key)

        encrypted = aes.encrypt(
            nonce,
            data,
            None
        )

        return nonce + encrypted

    @staticmethod
    def decrypt(key: bytes, data: bytes):

        nonce = data[:12]

        ciphertext = data[12:]

        aes = AESGCM(key)

        return aes.decrypt(
            nonce,
            ciphertext,
            None
        )