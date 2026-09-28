from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet
import os
import sys


class CryptoManager:
    def __init__(self):
        self.private_key = None
        self.public_key = None

    def generate_rsa_keys(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )

        self.public_key = self.private_key.public_key()
        pem_private = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with open("server_private.pem", "wb") as f:
            f.write(pem_private)

        pem_public = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        with open("server_public.pem", "wb") as f:
            f.write(pem_public)

    def load_keys(self):
        if not os.path.exists("server_private.pem"):
            raise FileNotFoundError(
                "Chiave privata non trovata! Impossibile avviare il server in modalità 'load'."
            )

        with open("server_private.pem", "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )

        with open("server_public.pem", "rb") as f:
            self.public_key = serialization.load_pem_public_key(f.read())

    def load_public_key(self, filename="server_public.pem"):
        with open(filename, "rb") as f:
            self.public_key = serialization.load_pem_public_key(f.read())

    def encrypt_rsa(self, data_bytes):
        return self.public_key.encrypt(
            data_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def decrypt_rsa(self, encrypted_bytes):
        return self.private_key.decrypt(
            encrypted_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    @staticmethod
    def generate_fernet_key():
        return Fernet.generate_key()
