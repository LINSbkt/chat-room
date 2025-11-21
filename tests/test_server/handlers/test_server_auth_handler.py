"""
Unit tests for ServerAuthHandler class.
"""
from shared.message_types import Message, MessageType, SystemMessage, ChatMessage
from server.handlers.server_auth_handler import ServerAuthHandler
import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import sys
import os

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))


class TestServerAuthHandler(unittest.TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_connection.client_id = "client123"
        self.mock_connection.server.auth_manager.validate_username.return_value = True
        self.mock_connection.server.auth_manager.authenticate_user.return_value = True
        self.mock_connection.send_message.return_value = True
        self.mock_connection.server.add_client = MagicMock()
        self.handler = ServerAuthHandler(self.mock_connection)

    def test_handle_connect(self):
        message = Message(MessageType.CONNECT, {})
        self.handler._send_system_message = MagicMock()
        self.handler.handle_connect(message)
        self.handler._send_system_message.assert_called_with(
            "Connected to chat server")

    def test_handle_auth_request_success(self):
        message = Message(MessageType.AUTH_REQUEST, {'username': 'testuser'})
        self.handler._send_system_message = MagicMock()
        self.handler.handle_auth_request(message)
        self.mock_connection.send_message.assert_called()
        self.assertTrue(self.mock_connection.is_authenticated)
        self.assertEqual(self.mock_connection.username, 'testuser')
    # Test username validation

    def test_handle_auth_request_empty_username(self):
        self.mock_connection.server.auth_manager.validate_username.return_value = False
        message = Message(MessageType.AUTH_REQUEST, {'username': ''})
        self.handler._send_error_message = MagicMock()
        self.handler.handle_auth_request(message)
        self.handler._send_error_message.assert_called_with(
            "Username cannot be empty")

    def test_handle_auth_request_invalid_username_too_long(self):
        self.mock_connection.server.auth_manager.validate_username.return_value = False
        long_username = 'a' * 21  # 21 characters
        message = Message(MessageType.AUTH_REQUEST, {
                          'username': long_username})
        self.handler._send_error_message = MagicMock()

        self.handler.handle_auth_request(message)
        self.handler._send_error_message.assert_called_with(
            "Username too long (max 20 characters)")

        self.handler._send_error_message.assert_called_with(
            "Username too long (max 20 characters)")

    def test_handle_auth_request_invalid_username_bad_chars(self):
        self.mock_connection.server.auth_manager.validate_username.return_value = False
        bad_username = 'bad@name!'
        message = Message(MessageType.AUTH_REQUEST, {'username': bad_username})
        self.handler._send_error_message = MagicMock()

        self.handler.handle_auth_request(message)
        self.handler._send_error_message.assert_called_with(
            "Username contains invalid characters")

    def test_handle_auth_request_username_taken(self):
        self.mock_connection.server.auth_manager.validate_username.return_value = False
        message = Message(MessageType.AUTH_REQUEST, {'username': 'validname'})
        self.handler._send_error_message = MagicMock()

        self.handler.handle_auth_request(message)
        self.handler._send_error_message.assert_called_with(
            "Username already taken")

    def test_handle_disconnect(self):
        message = Message(MessageType.DISCONNECT, {})
        self.handler.handle_disconnect(message)
        self.mock_connection.disconnect.assert_called()

    def test_send_system_message(self):
        with patch('shared.message_types.SystemMessage') as MockSystemMessage:
            mock_msg = MockSystemMessage.return_value
            self.handler._send_system_message("Hello system")
            self.mock_connection.send_message.assert_called_with(mock_msg)

    def test_send_error_message(self):
        with patch('shared.message_types.SystemMessage') as MockSystemMessage:
            mock_error_msg = MockSystemMessage.return_value
            self.handler._send_error_message("Error occurred")
            self.mock_connection.send_message.assert_called_with(
                mock_error_msg)

    def test_create_error_system_message(self):
        with patch('shared.message_types.SystemMessage') as MockSystemMessage:
            error_msg = self.handler._create_error_system_message(
                "Something went wrong")
            MockSystemMessage.assert_called_with(
                "Something went wrong", "error")

'''
    def test_send_message_history(self):
        self.mock_connection.server.get_messages.return_value = [
            {'content': 'Hello', 'sender': 'Alice', 'timestamp': '10:00'}
        ]
        self.mock_connection.server.get_private_contexts_for_user.return_value = []
        self.mock_connection.server.get_file_transfers.return_value = []

        self.handler._send_message_history('testuser')
        self.assertTrue(self.mock_connection.send_message.called)
        args, _ = self.mock_connection.send_message.call_args
        sent_msg = args[0]
        self.assertEqual(sent_msg.content, 'Hello')
        self.assertEqual(sent_msg.sender, 'Alice')
        self.assertFalse(sent_msg.is_private)
'''

if __name__ == '__main__':
    unittest.main()
'''
$env:PYTHONPATH = "src"
python -m unittest tests.test_server.handlers.test_server_auth_handler
'''
