import unittest
import os
import sys
import logging
from client.crypto_manager import ClientCryptoManager
from server.crypto_manager import ServerCryptoManager
from shared.crypto_manager import CryptoManager

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class TestClientCryptoManager(unittest.TestCase):
    """Unit tests for ClientCryptoManager."""

    def setUp(self):
        """Initialize a fresh ClientCryptoManager before each test."""
        self.client = ClientCryptoManager()
        # Optional: quiet logging for tests
        self.client.logger.setLevel(logging.CRITICAL)

        # Use a shared CryptoManager instance to simulate server keys
        self.mock_server = CryptoManager()
        self.mock_server.generate_rsa_keypair()
        self.server_public_pem = self.mock_server.get_public_key_pem()

    def test_initialize_encryption_generates_keys(self):
        """RSA keys are generated and public key PEM is returned."""
        public_pem = self.client.initialize_encryption()
        self.assertIsNotNone(public_pem)
        self.assertTrue(public_pem.startswith("-----BEGIN PUBLIC KEY-----"))
        self.assertTrue(self.client.has_rsa_keys())

    def test_set_server_public_key(self):
        """Client can set server public key."""
        self.client.set_server_public_key(self.server_public_pem)
        self.assertIsNotNone(self.client.server_public_key)

    def test_setup_aes_encryption(self):
        """Client can setup AES key from an encrypted AES key."""
        self.client.initialize_encryption()
        # Server encrypts AES key with client's public key
        server_aes_key = os.urandom(32)
        server_aes_iv = os.urandom(16)
        self.client.set_aes_key(server_aes_key, server_aes_iv)

        # Load public key object from PEM
        client_public_key_obj = self.client.load_public_key_from_pem(
            self.client.get_public_key_pem()
        )
        # Encrypt AES key with client's public key
        encrypted_aes = self.client.encrypt_aes_key_with_rsa(
            client_public_key_obj
        )
        # Client sets AES from encrypted key
        self.client.setup_aes_encryption(encrypted_aes)
        self.assertTrue(self.client.has_aes_key())
        self.assertTrue(self.client.is_encryption_enabled)

    def test_encrypt_decrypt_message(self):
        """Encrypted message can be decrypted correctly."""
        self.client.initialize_encryption()
        # Setup AES manually
        aes_key = os.urandom(32)
        aes_iv = os.urandom(16)
        self.client.set_aes_key(aes_key, aes_iv)
        self.client.enable_encryption()

        message = "Hello secure world"
        encrypted = self.client.encrypt_message(message)
        decrypted = self.client.decrypt_message(encrypted)

        self.assertNotEqual(message, encrypted)
        self.assertEqual(message, decrypted)

    def test_create_key_exchange_message(self):
        """Key exchange message includes public key."""
        self.client.initialize_encryption()
        username = "alice"
        msg = self.client.create_key_exchange_message(username)
        self.assertEqual(msg.sender, username)
        self.assertTrue(msg.public_key.startswith(
            "-----BEGIN PUBLIC KEY-----"))

    def test_create_aes_key_request(self):
        """AES key request dictionary is correct."""
        username = "alice"
        req = self.client.create_aes_key_request(username)
        self.assertEqual(req['message_type'], "AES_KEY_REQUEST")
        self.assertEqual(req['sender'], username)

    def test_is_ready_for_encryption_flag(self):
        """is_ready_for_encryption returns correct status."""
        self.client.initialize_encryption()
        self.assertFalse(self.client.is_ready_for_encryption())

        # Setup AES manually
        self.client.set_aes_key(os.urandom(32), os.urandom(16))
        self.client.enable_encryption()
        self.assertTrue(self.client.is_ready_for_encryption())

    def test_enable_disable_encryption(self):
        """Enable/disable encryption toggles correctly."""
        self.client.initialize_encryption()
        self.client.set_aes_key(os.urandom(32), os.urandom(16))

        self.client.disable_encryption()
        self.assertFalse(self.client.is_encryption_enabled)

        self.client.enable_encryption()
        self.assertTrue(self.client.is_encryption_enabled)

    def test_get_encryption_status(self):
        """Encryption status dictionary reports correctly."""
        status = self.client.get_encryption_status()
        self.assertFalse(status['rsa_keys_available'])
        self.assertFalse(status['aes_key_available'])
        self.assertFalse(status['encryption_enabled'])
        self.assertFalse(status['server_public_key_available'])

        # Setup keys
        self.client.initialize_encryption()
        self.client.set_server_public_key(self.server_public_pem)
        self.client.set_aes_key(os.urandom(32), os.urandom(16))
        self.client.enable_encryption()

        status = self.client.get_encryption_status()
        self.assertTrue(all(status.values()))


class TestClientServerCryptoFlow(unittest.TestCase):
    """Integration-style test for client-server crypto interaction."""

    def setUp(self):
        # Server and client instances
        self.server = ServerCryptoManager()
        self.client = ClientCryptoManager()

        # Setup server keys
        self.server.generate_rsa_keypair()
        self.client.initialize_encryption()

        # Add client public key to server
        client_pub_pem = self.client.get_public_key_pem()
        self.server.add_client_public_key("alice", client_pub_pem)

    def test_aes_key_exchange_and_message_encryption(self):
        # Server generates shared AES key
        self.server.generate_shared_aes_key()

        # Synchronize AES key setup
        self.server.setup_shared_aes_key()

        # Server encrypts AES key for client
        encrypted_aes_key = self.server.encrypt_shared_aes_key_for_client(
            "alice")

        # Client sets server public key (optional for verification)
        self.client.set_server_public_key(self.server.get_public_key_pem())

        # Client sets up AES encryption with server-provided key
        self.client.setup_aes_encryption(encrypted_aes_key)

        # Verify encryption is enabled
        self.assertTrue(self.client.is_encryption_enabled)
        self.assertTrue(self.client.has_aes_key())
        self.assertTrue(self.client.has_rsa_keys())

        # Encrypt and decrypt a message
        original_message = "Hello secure world!"
        encrypted_message = self.client.encrypt_message(original_message)
        decrypted_message = self.client.decrypt_message(encrypted_message)

        self.assertNotEqual(original_message, encrypted_message)
        self.assertEqual(original_message, decrypted_message)


if __name__ == "__main__":
    unittest.main()

'''
$env:PYTHONPATH = "src"
python -m unittest tests.test_client.test_client_crypto_manager
'''