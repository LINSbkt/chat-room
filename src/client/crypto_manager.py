"""
Client-side cryptographic manager for secure communication.
"""

import logging
from typing import Optional
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


class ClientCryptoManager(CryptoManager):
    """Client-side crypto manager for secure communication with server."""
    
    def __init__(self):
        super().__init__()
        self.server_public_key: Optional[rsa.RSAPublicKey] = None
        self.is_encryption_enabled = False
        self.logger = logging.getLogger(__name__)
    
    def initialize_encryption(self) -> str:
        """Initialize encryption by generating RSA key pair and returning public key."""
        try:
            # Generate RSA key pair
            self.generate_rsa_keypair()
            
            # Get public key in PEM format
            public_key_pem = self.get_public_key_pem()
            
            self.logger.info("Initialized encryption with RSA key pair")
            return public_key_pem
        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def set_server_public_key(self, public_key_pem: str):
        """Set the server's public key."""
        try:
            self.server_public_key = self.load_public_key_from_pem(public_key_pem)
            self.logger.info("Set server public key")
        except Exception as e:
            self.logger.error(f"Failed to set server public key: {e}")
            raise
    
    def setup_aes_encryption(self, encrypted_aes_key: str):
        """Setup AES encryption using the encrypted key from server."""
        try:
            # Decrypt the AES key using our private key
            aes_key, aes_iv = self.decrypt_aes_key_with_rsa(encrypted_aes_key)
            
            # Set the AES key
            self.set_aes_key(aes_key, aes_iv)
            
            # Enable encryption
            self.is_encryption_enabled = True
            
            self.logger.info("AES encryption setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup AES encryption: {e}")
            raise
    
    def encrypt_message(self, message: str) -> str:
        """Encrypt a message for sending."""
        if not self.is_encryption_enabled:
            self.logger.warning("Encryption not enabled, sending plaintext")
            return message
        
        try:
            self.logger.info(f"🔐 CLIENT ENCRYPTION: Starting encryption for message: '{message}'")
            encrypted = self.encrypt_with_aes(message)
            self.logger.info(f"🔐 CLIENT ENCRYPTION: Message encrypted successfully")
            return encrypted
        except Exception as e:
            self.logger.error(f"Failed to encrypt message: {e}")
            raise
    
    def decrypt_message(self, encrypted_message: str) -> str:
        """Decrypt a received message."""
        if not self.is_encryption_enabled:
            self.logger.warning("Encryption not enabled, treating as plaintext")
            return encrypted_message
        
        try:
            self.logger.info(f"🔓 CLIENT DECRYPTION: Starting decryption for encrypted message")
            decrypted = self.decrypt_with_aes(encrypted_message)
            self.logger.info(f"🔓 CLIENT DECRYPTION: Message decrypted successfully")
            return decrypted
        except Exception as e:
            self.logger.error(f"Failed to decrypt message: {e}")
            raise
    
    def create_key_exchange_message(self, username: str) -> KeyExchangeMessage:
        """Create a key exchange message with our public key."""
        if not self.has_rsa_keys():
            raise ValueError("RSA keys not initialized")
        
        public_key_pem = self.get_public_key_pem()
        return KeyExchangeMessage(public_key_pem, username)
    
    def create_aes_key_request(self, username: str) -> dict:
        """Create a request for AES key from server."""
        return {
            'message_type': 'AES_KEY_REQUEST',
            'sender': username,
            'data': {}
        }
    
    def is_ready_for_encryption(self) -> bool:
        """Check if encryption is ready to use."""
        return (self.has_rsa_keys() and 
                self.has_aes_key() and 
                self.is_encryption_enabled)
    
    def disable_encryption(self):
        """Disable encryption (fallback to plaintext)."""
        self.is_encryption_enabled = False
        self.logger.info("Encryption disabled")
    
    def enable_encryption(self):
        """Enable encryption if keys are available."""
        if self.has_rsa_keys() and self.has_aes_key():
            self.is_encryption_enabled = True
            self.logger.info("Encryption enabled")
        else:
            self.logger.warning("Cannot enable encryption: missing keys")
    
    def get_encryption_status(self) -> dict:
        """Get current encryption status."""
        return {
            'rsa_keys_available': self.has_rsa_keys(),
            'aes_key_available': self.has_aes_key(),
            'encryption_enabled': self.is_encryption_enabled,
            'server_public_key_available': self.server_public_key is not None
        }
