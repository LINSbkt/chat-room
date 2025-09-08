"""
Cryptographic manager for RSA and AES encryption operations.
"""

import base64
import os
import logging
from typing import Tuple, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class CryptoManager:
    """Manages RSA and AES encryption operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rsa_private_key: Optional[rsa.RSAPrivateKey] = None
        self.rsa_public_key: Optional[rsa.RSAPublicKey] = None
        self.aes_key: Optional[bytes] = None
        self.aes_iv: Optional[bytes] = None
    
    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Generate a new RSA key pair."""
        try:
            self.rsa_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
                backend=default_backend()
            )
            self.rsa_public_key = self.rsa_private_key.public_key()
            
            self.logger.info(f"Generated RSA key pair with {key_size} bits")
            return self.rsa_private_key, self.rsa_public_key
        except Exception as e:
            self.logger.error(f"Failed to generate RSA key pair: {e}")
            raise
    
    def get_public_key_pem(self) -> str:
        """Get the public key in PEM format."""
        if not self.rsa_public_key:
            raise ValueError("No public key available")
        
        try:
            pem = self.rsa_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to serialize public key: {e}")
            raise
    
    def load_public_key_from_pem(self, pem_data: str) -> rsa.RSAPublicKey:
        """Load a public key from PEM format."""
        try:
            public_key = serialization.load_pem_public_key(
                pem_data.encode('utf-8'),
                backend=default_backend()
            )
            return public_key
        except Exception as e:
            self.logger.error(f"Failed to load public key from PEM: {e}")
            raise
    
    def encrypt_with_rsa(self, data: bytes, public_key: rsa.RSAPublicKey) -> bytes:
        """Encrypt data using RSA public key."""
        try:
            encrypted = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return encrypted
        except Exception as e:
            self.logger.error(f"Failed to encrypt with RSA: {e}")
            raise
    
    def decrypt_with_rsa(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using RSA private key."""
        if not self.rsa_private_key:
            raise ValueError("No private key available")
        
        try:
            decrypted = self.rsa_private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted
        except Exception as e:
            self.logger.error(f"Failed to decrypt with RSA: {e}")
            raise
    
    def generate_aes_key(self, key_size: int = 32) -> bytes:
        """Generate a new AES key."""
        try:
            self.aes_key = os.urandom(key_size)  # 256-bit key
            self.aes_iv = os.urandom(16)  # 128-bit IV
            self.logger.info("Generated new AES key and IV")
            return self.aes_key
        except Exception as e:
            self.logger.error(f"Failed to generate AES key: {e}")
            raise
    
    def set_aes_key(self, key: bytes, iv: Optional[bytes] = None):
        """Set the AES key and IV."""
        self.aes_key = key
        if iv:
            self.aes_iv = iv
        else:
            self.aes_iv = os.urandom(16)  # Generate new IV if not provided
    
    def encrypt_with_aes(self, plaintext: str) -> str:
        """Encrypt plaintext using AES."""
        if not self.aes_key:
            raise ValueError("No AES key available")
        
        try:
            # Convert string to bytes
            plaintext_bytes = plaintext.encode('utf-8')
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.aes_key),
                modes.CBC(self.aes_iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Pad the plaintext to block size (16 bytes for AES)
            padding_length = 16 - (len(plaintext_bytes) % 16)
            padded_plaintext = plaintext_bytes + bytes([padding_length] * padding_length)
            
            # Encrypt
            ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()
            
            # Combine IV and ciphertext, then encode to base64
            encrypted_data = self.aes_iv + ciphertext
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            # Log the encryption process
            self.logger.info(f"🔐 ENCRYPTION: Original message: '{plaintext}'")
            self.logger.info(f"🔐 ENCRYPTION: Encrypted data (Base64): {encrypted_b64}")
            self.logger.info(f"🔐 ENCRYPTION: Data length: {len(plaintext)} chars -> {len(encrypted_b64)} chars")
            
            return encrypted_b64
        except Exception as e:
            self.logger.error(f"Failed to encrypt with AES: {e}")
            raise
    
    def decrypt_with_aes(self, encrypted_data: str) -> str:
        """Decrypt ciphertext using AES."""
        if not self.aes_key:
            raise ValueError("No AES key available")
        
        try:
            # Log the decryption process
            self.logger.info(f"🔓 DECRYPTION: Received encrypted data (Base64): {encrypted_data}")
            
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract IV and ciphertext
            iv = encrypted_bytes[:16]
            ciphertext = encrypted_bytes[16:]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Remove padding
            padding_length = padded_plaintext[-1]
            plaintext_bytes = padded_plaintext[:-padding_length]
            
            decrypted_text = plaintext_bytes.decode('utf-8')
            
            # Log the successful decryption
            self.logger.info(f"🔓 DECRYPTION: Successfully decrypted to: '{decrypted_text}'")
            self.logger.info(f"🔓 DECRYPTION: Data length: {len(encrypted_data)} chars -> {len(decrypted_text)} chars")
            
            return decrypted_text
        except Exception as e:
            self.logger.error(f"Failed to decrypt with AES: {e}")
            raise
    
    def encrypt_aes_key_with_rsa(self, public_key: rsa.RSAPublicKey) -> str:
        """Encrypt the AES key with RSA public key."""
        if not self.aes_key:
            raise ValueError("No AES key available")
        
        try:
            # Combine key and IV
            key_data = self.aes_key + self.aes_iv
            encrypted_key = self.encrypt_with_rsa(key_data, public_key)
            return base64.b64encode(encrypted_key).decode('utf-8')
        except Exception as e:
            self.logger.error(f"Failed to encrypt AES key with RSA: {e}")
            raise
    
    def decrypt_aes_key_with_rsa(self, encrypted_key_data: str) -> Tuple[bytes, bytes]:
        """Decrypt the AES key with RSA private key."""
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_key_data.encode('utf-8'))
            
            # Decrypt
            decrypted_data = self.decrypt_with_rsa(encrypted_bytes)
            
            # Split key and IV
            aes_key = decrypted_data[:32]  # 256-bit key
            aes_iv = decrypted_data[32:48]  # 128-bit IV
            
            return aes_key, aes_iv
        except Exception as e:
            self.logger.error(f"Failed to decrypt AES key with RSA: {e}")
            raise
    
    def has_rsa_keys(self) -> bool:
        """Check if RSA keys are available."""
        return self.rsa_private_key is not None and self.rsa_public_key is not None
    
    def has_aes_key(self) -> bool:
        """Check if AES key is available."""
        return self.aes_key is not None
    
    def clear_keys(self):
        """Clear all stored keys (for security)."""
        self.rsa_private_key = None
        self.rsa_public_key = None
        self.aes_key = None
        self.aes_iv = None
        self.logger.info("Cleared all cryptographic keys")
