import unittest
import sys
import os
from unittest.mock import Mock, patch
from client.handlers.auth_handler import AuthHandler
from shared.message_types import MessageType, KeyExchangeMessage
# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class DummyMessage:
    def __init__(self, status):
        self.data = {'status': status}


class TestAuthHandler(unittest.TestCase):
    def setUp(self):
        # Mock ClientCore
        self.mock_core = Mock()
        self.mock_core.auth_event = Mock()
        self.mock_core.auth_event.set = Mock()
        self.mock_core.signals = Mock()
        self.mock_core.signals.connection_status_changed.emit = Mock()
        self.mock_core.signals.error_occurred.emit = Mock()
        self.mock_core.username = "alice"
        self.mock_core.crypto_manager = Mock()
        self.mock_core.crypto_manager.has_rsa_keys.return_value = True
        self.mock_core.crypto_manager.get_public_key_pem.return_value = "public_key_pem"
        self.mock_core.connection_manager = Mock()
        self.mock_core.connection_manager.send_message = Mock()

        self.handler = AuthHandler(self.mock_core)

    def test_handle_auth_response_success(self):
        message = DummyMessage(status='success')
        # Patch FileHandler only during this call
        with patch("client.handlers.file_handler.FileHandler") as mock_file_handler_class:
            mock_file_handler_instance = Mock()
            mock_file_handler_class.return_value = mock_file_handler_instance
            mock_file_handler_instance.request_file_list = Mock()

            self.handler.handle_auth_response(message)

            # Check core flags
            self.assertTrue(self.mock_core.auth_success)
            self.mock_core.auth_event.set.assert_called_once()
            self.mock_core.signals.connection_status_changed.emit.assert_called_with(
                True)
            self.mock_core.connection_manager.send_message.assert_called()  # Key exchange sent
            mock_file_handler_instance.request_file_list.assert_called_once()

    def test_handle_auth_response_failure(self):
        message = DummyMessage(status='fail')
        self.handler.handle_auth_response(message)

        self.assertFalse(self.mock_core.auth_success)
        self.mock_core.auth_event.set.assert_called_once()
        self.mock_core.signals.error_occurred.emit.assert_called_with(
            "Authentication failed")
        self.mock_core.signals.connection_status_changed.emit.assert_not_called()
        self.mock_core.connection_manager.send_message.assert_not_called()

    def test_send_key_exchange_no_rsa_keys(self):
        self.mock_core.crypto_manager.has_rsa_keys.return_value = False
        self.handler._send_key_exchange()
        self.mock_core.connection_manager.send_message.assert_not_called()


if __name__ == "__main__":
    unittest.main()
'''
$env:PYTHONPATH = "src"
python -m unittest tests.test_client.handlers.test_client_auth_handler
'''
