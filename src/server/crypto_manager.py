"""
Server-side cryptographic manager for handling client encryption.
"""

import logging
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
        self.client_aes_keys: Dict[str, bytes] = {}
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
        self.client_aes_keys.pop(username, None)
        self.logger.info(f"Removed keys for client: {username}")
    
    def generate_and_encrypt_aes_key(self, username: str) -> str:
        """Generate AES key and encrypt it with client's public key."""
        if username not in self.client_public_keys:
            raise ValueError(f"No public key found for client: {username}")
        
        try:
            # Generate new AES key
            aes_key = self.generate_aes_key()
            
            # Store the AES key for this client
            self.client_aes_keys[username] = aes_key
            
            # Encrypt AES key with client's public key
            client_public_key = self.client_public_keys[username]
            encrypted_aes_key = self.encrypt_aes_key_with_rsa(client_public_key)
            
            self.logger.info(f"Generated and encrypted AES key for client: {username}")
            return encrypted_aes_key
        except Exception as e:
            self.logger.error(f"Failed to generate AES key for {username}: {e}")
            raise
    
    def get_client_aes_key(self, username: str) -> Optional[bytes]:
        """Get the AES key for a specific client."""
        return self.client_aes_keys.get(username)
    
    def encrypt_message_for_client(self, message: str, username: str) -> str:
        """Encrypt a message for a specific client."""
        if username not in self.client_aes_keys:
            raise ValueError(f"No AES key found for client: {username}")
        
        try:
            self.logger.info(f"🔐 SERVER ENCRYPTION: Starting encryption for client '{username}'")
            self.logger.info(f"🔐 SERVER ENCRYPTION: Original message: '{message}'")
            
            # Temporarily set the client's AES key
            original_aes_key = self.aes_key
            original_aes_iv = self.aes_iv
            
            self.aes_key = self.client_aes_keys[username]
            self.aes_iv = None  # Will generate new IV for each message
            
            # Encrypt the message
            encrypted_message = self.encrypt_with_aes(message)
            
            # Restore original AES key
            self.aes_key = original_aes_key
            self.aes_iv = original_aes_iv
            
            self.logger.info(f"🔐 SERVER ENCRYPTION: Message encrypted for client '{username}'")
            return encrypted_message
        except Exception as e:
            self.logger.error(f"Failed to encrypt message for {username}: {e}")
            raise
    
    def decrypt_message_from_client(self, encrypted_message: str, username: str) -> str:
        """Decrypt a message from a specific client."""
        if username not in self.client_aes_keys:
            raise ValueError(f"No AES key found for client: {username}")
        
        try:
            self.logger.info(f"🔓 SERVER DECRYPTION: Starting decryption from client '{username}'")
            self.logger.info(f"🔓 SERVER DECRYPTION: Received encrypted data: {encrypted_message}")
            
            # Temporarily set the client's AES key
            original_aes_key = self.aes_key
            original_aes_iv = self.aes_iv
            
            self.aes_key = self.client_aes_keys[username]
            self.aes_iv = None  # IV is included in the encrypted data
            
            # Decrypt the message
            decrypted_message = self.decrypt_with_aes(encrypted_message)
            
            # Restore original AES key
            self.aes_key = original_aes_key
            self.aes_iv = original_aes_iv
            
            self.logger.info(f"🔓 SERVER DECRYPTION: Message decrypted from client '{username}': '{decrypted_message}'")
            return decrypted_message
        except Exception as e:
            self.logger.error(f"Failed to decrypt message from {username}: {e}")
            raise
    
    def has_client_keys(self, username: str) -> bool:
        """Check if we have keys for a specific client."""
        return (username in self.client_public_keys and 
                username in self.client_aes_keys)
    
    def get_all_clients(self) -> list:
        """Get list of all clients with keys."""
        return list(self.client_public_keys.keys())
    
    def clear_all_client_keys(self):
        """Clear all client keys."""
        self.client_public_keys.clear()
        self.client_aes_keys.clear()
        self.logger.info("Cleared all client keys")
