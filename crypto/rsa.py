from cryptography.hazmat.primitives import hashes

from cryptography.hazmat.primitives.asymmetric import (
    rsa,
    padding
)

from cryptography.hazmat.primitives import serialization


class RSA:

    @staticmethod
    def generate_keys():

        private = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        public = private.public_key()

        return private, public

    @staticmethod
    def encrypt(public_key, data: bytes):

        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(
                    algorithm=hashes.SHA256()
                ),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def decrypt(private_key, data: bytes):

        return private_key.decrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(
                    algorithm=hashes.SHA256()
                ),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    @staticmethod
    def save_private(private_key, path):

        with open(path, "wb") as f:

            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )

    @staticmethod
    def save_public(public_key, path):

        with open(path, "wb") as f:

            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
            )

    @staticmethod
    def load_private(path):

        with open(path, "rb") as f:

            return serialization.load_pem_private_key(
                f.read(),
                password=None
            )

    @staticmethod
    def load_public(path):

        with open(path, "rb") as f:

            return serialization.load_pem_public_key(
                f.read()
            )