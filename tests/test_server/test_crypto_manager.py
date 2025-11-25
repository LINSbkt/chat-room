"""
Unit tests for ServerCryptoManager
"""

from unittest.mock import Mock, patch
from server.crypto_manager import ServerCryptoManager
from shared.crypto_manager import CryptoManager
import os
import sys
import unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


class TestServerCryptoManager(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test."""
        self.server_manager = ServerCryptoManager()

        # Generate RSA key pair for the server
        self.server_manager.generate_rsa_keypair()

        # Create a mock client crypto manager to simulate client keys
        self.client_manager = CryptoManager()
        self.client_manager.generate_rsa_keypair()
        self.client_public_key_pem = self.client_manager.get_public_key_pem()

    def test_add_client_public_key(self):
        """Test adding a client's public key."""
        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)

        self.assertTrue(self.server_manager.has_client_public_key("alice"))
        self.assertIn("alice", self.server_manager.get_all_clients())

    def test_add_multiple_clients(self):
        """Test adding multiple client public keys."""
        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)
        self.server_manager.add_client_public_key(
            "bob", self.client_public_key_pem)

        clients = self.server_manager.get_all_clients()
        self.assertEqual(len(clients), 2)
        self.assertIn("alice", clients)
        self.assertIn("bob", clients)

    def test_remove_client_keys(self):
        """Test removing a client's keys."""
        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)
        self.assertTrue(self.server_manager.has_client_public_key("alice"))

        self.server_manager.remove_client_keys("alice")
        self.assertFalse(self.server_manager.has_client_public_key("alice"))

    def test_generate_shared_aes_key(self):
        """Test generating a shared AES key."""
        key = self.server_manager.generate_shared_aes_key()

        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)  # 256-bit key
        self.assertIsNotNone(self.server_manager.shared_aes_iv)
        self.assertEqual(
            len(self.server_manager.shared_aes_iv), 16)  # 128-bit IV

    def test_shared_aes_key_persistence(self):
        """Test that shared AES key remains the same across multiple calls."""
        key1 = self.server_manager.generate_shared_aes_key()
        key2 = self.server_manager.generate_shared_aes_key()

        self.assertEqual(key1, key2)
        self.assertIs(key1, key2)  # Should be the exact same object

    def test_get_shared_aes_key(self):
        """Test getting the shared AES key."""
        # Key should be auto-generated if not exists
        key = self.server_manager.get_shared_aes_key()

        self.assertIsNotNone(key)
        self.assertEqual(len(key), 32)

    #
    def test_encrypt_shared_aes_key_for_client(self):
        """Test encrypting shared AES key for a specific client."""
        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)

        # sync aes_key + aes_iv (in base shared crypto manager class)
        # and shared_aes_key + shared_aes_iv (in server class)
        self.server_manager.setup_shared_aes_key()

        encrypted_key = self.server_manager.encrypt_shared_aes_key_for_client(
            "alice")

        self.assertIsNotNone(encrypted_key)
        self.assertIsInstance(encrypted_key, str)
        self.assertGreater(len(encrypted_key), 0)

    def test_encrypt_for_nonexistent_client(self):
        """Test encrypting for a client that doesn't exist."""
        with self.assertRaises(ValueError) as context:
            self.server_manager.encrypt_shared_aes_key_for_client(
                "nonexistent")

        self.assertIn("No public key found", str(context.exception))

    def test_client_can_decrypt_shared_key(self):
        """Test that client can decrypt the shared AES key encrypted for them."""
        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)

        # sync aes_key + aes_iv (in base shared crypto manager class)
        # and shared_aes_key + shared_aes_iv (in server class)
        self.server_manager.setup_shared_aes_key()

        # Server encrypts shared key for client
        encrypted_key = self.server_manager.encrypt_shared_aes_key_for_client(
            "alice")

        # Client decrypts the shared key
        decrypted_key, decrypted_iv = self.client_manager.decrypt_aes_key_with_rsa(
            encrypted_key)

        # Verify the decrypted key matches the server's shared key
        self.assertEqual(decrypted_key, self.server_manager.shared_aes_key)
        self.assertEqual(decrypted_iv, self.server_manager.shared_aes_iv)

    def test_setup_shared_aes_key(self):
        """Test setting up shared AES key in base class."""
        self.server_manager.setup_shared_aes_key()

        # Check that base class keys are set
        self.assertIsNotNone(self.server_manager.aes_key)
        self.assertIsNotNone(self.server_manager.aes_iv)
        self.assertEqual(self.server_manager.aes_key,
                         self.server_manager.shared_aes_key)
        self.assertEqual(self.server_manager.aes_iv,
                         self.server_manager.shared_aes_iv)

    def test_has_client_public_key(self):
        """Test checking if client has a public key."""
        self.assertFalse(self.server_manager.has_client_public_key("alice"))

        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)
        self.assertTrue(self.server_manager.has_client_public_key("alice"))

    def test_get_all_clients_empty(self):
        """Test getting all clients when none exist."""
        clients = self.server_manager.get_all_clients()
        self.assertEqual(len(clients), 0)
        self.assertIsInstance(clients, list)

    def test_clear_all_client_keys(self):
        """Test clearing all client keys and shared AES key."""
        # Add some clients and generate shared key
        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)
        self.server_manager.add_client_public_key(
            "bob", self.client_public_key_pem)
        self.server_manager.generate_shared_aes_key()

        # Clear everything
        self.server_manager.clear_all_client_keys()

        # Verify everything is cleared
        self.assertEqual(len(self.server_manager.get_all_clients()), 0)
        self.assertIsNone(self.server_manager.shared_aes_key)
        self.assertIsNone(self.server_manager.shared_aes_iv)
        self.assertFalse(self.server_manager.has_client_public_key("alice"))
        self.assertFalse(self.server_manager.has_client_public_key("bob"))

    def test_encryption_decryption_with_shared_key(self):
        """Test end-to-end encryption/decryption using shared AES key."""
        # Setup shared key
        self.server_manager.setup_shared_aes_key()

        # Encrypt a message
        original_message = "Hello, secure world!"
        encrypted = self.server_manager.encrypt_with_aes(original_message)

        # Decrypt the message
        decrypted = self.server_manager.decrypt_with_aes(encrypted)

        self.assertEqual(original_message, decrypted)

    def test_multiple_clients_same_shared_key(self):
        """Test that multiple clients receive the same shared key."""
        # Add two clients
        self.server_manager.add_client_public_key(
            "alice", self.client_public_key_pem)

        # sync aes_key + aes_iv (in base shared crypto manager class)
        # and shared_aes_key + shared_aes_iv (in server class)
        self.server_manager.setup_shared_aes_key()

        # Create second client
        client2 = CryptoManager()
        client2.generate_rsa_keypair()
        client2_public_key_pem = client2.get_public_key_pem()
        self.server_manager.add_client_public_key(
            "bob", client2_public_key_pem)

        # Encrypt shared key for both clients
        encrypted_for_alice = self.server_manager.encrypt_shared_aes_key_for_client(
            "alice")
        encrypted_for_bob = self.server_manager.encrypt_shared_aes_key_for_client(
            "bob")

        # Both clients decrypt their keys
        alice_key, alice_iv = self.client_manager.decrypt_aes_key_with_rsa(
            encrypted_for_alice)
        bob_key, bob_iv = client2.decrypt_aes_key_with_rsa(encrypted_for_bob)

        # Verify both received the same shared key
        self.assertEqual(alice_key, bob_key)
        self.assertEqual(alice_iv, bob_iv)
        self.assertEqual(alice_key, self.server_manager.shared_aes_key)


if __name__ == "__main__":
    unittest.main()
'''
$env:PYTHONPATH = "src"
python -m unittest tests.test_server.test_crypto_manager
'''
