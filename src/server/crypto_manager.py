"""
Server-side cryptographic manager for handling client encryption.
"""

import logging
import os
from typing import Dict, Optional
from cryptography.hazmat.primitives.asymmetric import rsa
try:
    from ..shared.crypto_manager import CryptoManager
    from ..shared.message_types import KeyExchangeMessage, AESKeyMessage
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared.crypto_manager import CryptoManager
    from shared.message_types import KeyExchangeMessage, AESKeyMessage


class ServerCryptoManager(CryptoManager):
    """Server-side crypto manager for handling multiple client keys."""

    def __init__(self):
        super().__init__()
        self.client_public_keys: Dict[str, rsa.RSAPublicKey] = {}
        self.shared_aes_key: Optional[bytes] = None
        self.shared_aes_iv: Optional[bytes] = None
        self.logger = logging.getLogger(__name__)

    def add_client_public_key(self, username: str, public_key_pem: str):
        """Add a client's public key."""
        try:
            public_key = self.load_public_key_from_pem(public_key_pem)
            self.client_public_keys[username] = public_key
            self.logger.info(f"Added public key for client: {username}")
        except Exception as e:
            self.logger.error(f"Failed to add public key for {username}: {e}")
            raise

    def remove_client_keys(self, username: str):
        """Remove a client's keys."""
        self.client_public_keys.pop(username, None)
        self.logger.info(f"Removed keys for client: {username}")

    def generate_shared_aes_key(self) -> bytes:
        """Generate a shared AES key for all clients."""
        try:
            # Generate new shared AES key if not already exists
            if not self.shared_aes_key:
                self.shared_aes_key = os.urandom(32)  # 256-bit key
                self.shared_aes_iv = os.urandom(16)   # 128-bit IV
                self.logger.info(
                    "Generated new shared AES key for all clients")

            return self.shared_aes_key
        except Exception as e:
            self.logger.error(f"Failed to generate shared AES key: {e}")
            raise

    def encrypt_shared_aes_key_for_client(self, username: str) -> str:
        """Encrypt the shared AES key with client's public key."""
        if username not in self.client_public_keys:
            raise ValueError(f"No public key found for client: {username}")

        try:
            # Ensure shared key exists
            if not self.shared_aes_key:
                self.generate_shared_aes_key()

            # Encrypt shared AES key with client's public key
            client_public_key = self.client_public_keys[username]
            # The base class encrypt_aes_key_with_rsa uses self.aes_key and self.aes_iv
            # which are set by generate_shared_aes_key
            encrypted_aes_key = self.encrypt_aes_key_with_rsa(
                client_public_key)

            self.logger.info(
                f"Encrypted shared AES key for client: {username}")
            return encrypted_aes_key
        except Exception as e:
            self.logger.error(
                f"Failed to encrypt shared AES key for {username}: {e}")
            raise

    def get_shared_aes_key(self) -> bytes:
        """Get the shared AES key."""
        if not self.shared_aes_key:
            self.generate_shared_aes_key()
        return self.shared_aes_key

    def setup_shared_aes_key(self):
        """Setup the shared AES key in the base class."""
        try:
            # Generate shared key if not exists
            if not self.shared_aes_key:
                self.generate_shared_aes_key()

            # Set the shared key in the base class
            self.aes_key = self.shared_aes_key
            self.aes_iv = self.shared_aes_iv

            self.logger.info("Server shared AES key setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup shared AES key: {e}")
            raise

    def has_client_public_key(self, username: str) -> bool:
        """Check if client has a public key."""
        return username in self.client_public_keys

    def get_all_clients(self) -> list:
        """Get list of all client usernames."""
        return list(self.client_public_keys.keys())

    def clear_all_client_keys(self):
        """Clear all client keys."""
        self.client_public_keys.clear()
        self.shared_aes_key = None
        self.shared_aes_iv = None
        self.logger.info("Cleared all client keys and reset shared AES key")
