"""
Unit tests for CryptoManager class.
"""

import unittest
import base64
import os
import sys
from shared.crypto_manager import CryptoManager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

class TestCryptoManager(unittest.TestCase):
    """Test cases for CryptoManager."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.crypto = CryptoManager()
    
    def tearDown(self):
        """Clean up after each test method."""
        self.crypto.clear_keys()
    
    # RSA Key Generation Tests
    def test_generate_rsa_keypair(self):
        """Test RSA key pair generation."""
        private_key, public_key = self.crypto.generate_rsa_keypair()
        
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
        self.assertTrue(self.crypto.has_rsa_keys())
    
    def test_generate_rsa_keypair_custom_size(self):
        """Test RSA key pair generation with custom key size."""
        private_key, public_key = self.crypto.generate_rsa_keypair(key_size=4096)
        
        self.assertIsNotNone(private_key)
        self.assertEqual(private_key.key_size, 4096)
    
    def test_get_public_key_pem(self):
        """Test public key serialization to PEM format."""
        self.crypto.generate_rsa_keypair()
        pem = self.crypto.get_public_key_pem()
        
        self.assertIsInstance(pem, str)
        self.assertIn("BEGIN PUBLIC KEY", pem)
        self.assertIn("END PUBLIC KEY", pem)
    
    def test_get_public_key_pem_without_key(self):
        """Test that getting PEM without key raises ValueError."""
        with self.assertRaises(ValueError):
            self.crypto.get_public_key_pem()
    
    def test_load_public_key_from_pem(self):
        """Test loading public key from PEM format."""
        self.crypto.generate_rsa_keypair()
        pem = self.crypto.get_public_key_pem()
        
        loaded_key = self.crypto.load_public_key_from_pem(pem)
        self.assertIsNotNone(loaded_key)
    
    # RSA Encryption/Decryption Tests
    def test_rsa_encrypt_decrypt(self):
        """Test RSA encryption and decryption."""
        self.crypto.generate_rsa_keypair()
        original_data = b"Hello, World!"
        
        encrypted = self.crypto.encrypt_with_rsa(original_data, self.crypto.rsa_public_key)
        decrypted = self.crypto.decrypt_with_rsa(encrypted)
        
        self.assertEqual(original_data, decrypted)
        self.assertNotEqual(original_data, encrypted)
    
    def test_decrypt_rsa_without_private_key(self):
        """Test that decrypting without private key raises ValueError."""
        with self.assertRaises(ValueError):
            self.crypto.decrypt_with_rsa(b"fake_encrypted_data")
    
    # AES Key Generation Tests
    def test_generate_aes_key(self):
        """Test AES key generation."""
        key = self.crypto.generate_aes_key()
        
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)  # 256 bits
        self.assertTrue(self.crypto.has_aes_key())
        self.assertIsNotNone(self.crypto.aes_iv)
        self.assertEqual(len(self.crypto.aes_iv), 16)  # 128 bits
    
    def test_generate_aes_key_custom_size(self):
        """Test AES key generation with custom size."""
        key = self.crypto.generate_aes_key(key_size=16)  # 128 bits
        
        self.assertEqual(len(key), 16)
    
    def test_set_aes_key(self):
        """Test setting AES key manually."""
        test_key = b"0" * 32
        test_iv = b"1" * 16
        
        self.crypto.set_aes_key(test_key, test_iv)
        
        self.assertEqual(self.crypto.aes_key, test_key)
        self.assertEqual(self.crypto.aes_iv, test_iv)
    
    def test_set_aes_key_without_iv(self):
        """Test setting AES key without IV generates new IV."""
        test_key = b"0" * 32
        
        self.crypto.set_aes_key(test_key)
        
        self.assertEqual(self.crypto.aes_key, test_key)
        self.assertIsNotNone(self.crypto.aes_iv)
        self.assertEqual(len(self.crypto.aes_iv), 16)
    
    # AES Encryption/Decryption Tests
    def test_aes_encrypt_decrypt(self):
        """Test AES encryption and decryption."""
        self.crypto.generate_aes_key()
        original_text = "Hello, World! This is a test message."
        
        encrypted = self.crypto.encrypt_with_aes(original_text)
        decrypted = self.crypto.decrypt_with_aes(encrypted)
        
        self.assertEqual(original_text, decrypted)
        self.assertNotEqual(original_text, encrypted)
    
    def test_aes_encrypt_empty_string(self):
        """Test AES encryption of empty string."""
        self.crypto.generate_aes_key()
        original_text = ""
        
        encrypted = self.crypto.encrypt_with_aes(original_text)
        decrypted = self.crypto.decrypt_with_aes(encrypted)
        
        self.assertEqual(original_text, decrypted)
    
    def test_aes_encrypt_unicode(self):
        """Test AES encryption with Unicode characters."""
        self.crypto.generate_aes_key()
        original_text = "Hello 世界! 🔐 Encryption test"
        
        encrypted = self.crypto.encrypt_with_aes(original_text)
        decrypted = self.crypto.decrypt_with_aes(encrypted)
        
        self.assertEqual(original_text, decrypted)
    
    def test_aes_encrypt_long_text(self):
        """Test AES encryption with long text."""
        self.crypto.generate_aes_key()
        original_text = "A" * 1000
        
        encrypted = self.crypto.encrypt_with_aes(original_text)
        decrypted = self.crypto.decrypt_with_aes(encrypted)
        
        self.assertEqual(original_text, decrypted)
    
    def test_encrypt_aes_without_key(self):
        """Test that encrypting without AES key raises ValueError."""
        with self.assertRaises(ValueError):
            self.crypto.encrypt_with_aes("test")
    
    def test_decrypt_aes_without_key(self):
        """Test that decrypting without AES key raises ValueError."""
        with self.assertRaises(ValueError):
            self.crypto.decrypt_with_aes("fake_encrypted_data")
    
    # Hybrid Encryption Tests (RSA + AES)
    def test_encrypt_aes_key_with_rsa(self):
        """Test encrypting AES key with RSA."""
        self.crypto.generate_rsa_keypair()
        self.crypto.generate_aes_key()
        
        encrypted_key = self.crypto.encrypt_aes_key_with_rsa(self.crypto.rsa_public_key)
        
        self.assertIsInstance(encrypted_key, str)
        # Verify it's valid base64
        base64.b64decode(encrypted_key)
    
    def test_decrypt_aes_key_with_rsa(self):
        """Test decrypting AES key with RSA."""
        self.crypto.generate_rsa_keypair()
        self.crypto.generate_aes_key()
        
        original_key = self.crypto.aes_key
        original_iv = self.crypto.aes_iv
        
        encrypted_key = self.crypto.encrypt_aes_key_with_rsa(self.crypto.rsa_public_key)
        decrypted_key, decrypted_iv = self.crypto.decrypt_aes_key_with_rsa(encrypted_key)
        
        self.assertEqual(original_key, decrypted_key)
        self.assertEqual(original_iv, decrypted_iv)
    
    def test_encrypt_aes_key_without_key(self):
        """Test that encrypting AES key without key raises ValueError."""
        self.crypto.generate_rsa_keypair()
        
        with self.assertRaises(ValueError):
            self.crypto.encrypt_aes_key_with_rsa(self.crypto.rsa_public_key)
    
    # Key Management Tests
    def test_has_rsa_keys(self):
        """Test checking if RSA keys are available."""
        self.assertFalse(self.crypto.has_rsa_keys())
        
        self.crypto.generate_rsa_keypair()
        self.assertTrue(self.crypto.has_rsa_keys())
    
    def test_has_aes_key(self):
        """Test checking if AES key is available."""
        self.assertFalse(self.crypto.has_aes_key())
        
        self.crypto.generate_aes_key()
        self.assertTrue(self.crypto.has_aes_key())
    
    def test_clear_keys(self):
        """Test clearing all keys."""
        self.crypto.generate_rsa_keypair()
        self.crypto.generate_aes_key()
        
        self.assertTrue(self.crypto.has_rsa_keys())
        self.assertTrue(self.crypto.has_aes_key())
        
        self.crypto.clear_keys()
        
        self.assertFalse(self.crypto.has_rsa_keys())
        self.assertFalse(self.crypto.has_aes_key())
        self.assertIsNone(self.crypto.rsa_private_key)
        self.assertIsNone(self.crypto.rsa_public_key)
        self.assertIsNone(self.crypto.aes_key)
        self.assertIsNone(self.crypto.aes_iv)
    
    # Integration Tests
    def test_full_encryption_workflow(self):
        """Test complete encryption workflow with key exchange."""
        # Sender generates keys
        sender = CryptoManager()
        sender.generate_rsa_keypair()
        sender.generate_aes_key()
        
        # Receiver generates keys
        receiver = CryptoManager()
        receiver.generate_rsa_keypair()
        
        # Sender encrypts AES key with receiver's public key
        encrypted_aes_key = sender.encrypt_aes_key_with_rsa(receiver.rsa_public_key)
        
        # Receiver decrypts AES key
        aes_key, aes_iv = receiver.decrypt_aes_key_with_rsa(encrypted_aes_key)
        receiver.set_aes_key(aes_key, aes_iv)
        
        # Sender encrypts message
        original_message = "Secret message for secure communication!"
        encrypted_message = sender.encrypt_with_aes(original_message)
        
        # Receiver decrypts message
        decrypted_message = receiver.decrypt_with_aes(encrypted_message)
        
        self.assertEqual(original_message, decrypted_message)


if __name__ == '__main__':
    unittest.main()
'''
 $env:PYTHONPATH = "src"
>> python -m unittest tests.test_shared.test_crypto_manager  
'''