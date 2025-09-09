"""
Tests for the refactored server modular structure.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server.core.client_connection import ClientConnection
from server.handlers.server_message_handler import ServerMessageHandler
from server.handlers.server_auth_handler import ServerAuthHandler
from server.handlers.server_chat_handler import ServerChatHandler
from server.handlers.server_file_handler import ServerFileHandler
from server.client_handler import ClientHandler
from shared.message_types import MessageType, Message, ChatMessage, FileTransferRequest


class TestClientConnection(unittest.TestCase):
    """Test ClientConnection core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_socket = Mock()
        self.mock_server = Mock()
        self.client_address = ('127.0.0.1', 12345)
        
        with patch('server.core.client_connection.ConnectionManager'):
            self.connection = ClientConnection(self.mock_socket, self.client_address, self.mock_server)
    
    def test_init(self):
        """Test ClientConnection initialization."""
        self.assertEqual(self.connection.client_address, self.client_address)
        self.assertEqual(self.connection.server, self.mock_server)
        self.assertIsNone(self.connection.username)
        self.assertFalse(self.connection.is_authenticated)
        self.assertTrue(self.connection.connected)
        self.assertIsNotNone(self.connection.client_id)
    
    def test_generate_client_id(self):
        """Test client ID generation."""
        client_id = self.connection._generate_client_id()
        self.assertIsInstance(client_id, str)
        self.assertGreater(len(client_id), 0)
        
        # Should be unique
        another_id = self.connection._generate_client_id()
        self.assertNotEqual(client_id, another_id)
    
    def test_send_message_not_connected(self):
        """Test sending message when not connected."""
        self.connection.connected = False
        message = Mock()
        result = self.connection.send_message(message)
        self.assertFalse(result)
    
    def test_is_connected(self):
        """Test connection status check."""
        self.connection.connection_manager.is_connected.return_value = True
        self.assertTrue(self.connection.is_connected())
        
        self.connection.connected = False
        self.assertFalse(self.connection.is_connected())


class TestServerAuthHandler(unittest.TestCase):
    """Test ServerAuthHandler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = Mock()
        self.mock_connection.client_id = "test_client_123"
        self.mock_connection.server = Mock()
        self.mock_connection.server.auth_manager = Mock()
        self.handler = ServerAuthHandler(self.mock_connection)
    
    def test_handle_connect(self):
        """Test handling client connect."""
        message = Mock()
        
        with patch.object(self.handler, '_send_system_message') as mock_send:
            self.handler.handle_connect(message)
            mock_send.assert_called_once_with("Connected to chat server")
    
    def test_handle_auth_request_success(self):
        """Test successful authentication."""
        message = Mock()
        message.data = {'username': 'testuser'}
        
        # Mock successful validation and authentication
        self.mock_connection.server.auth_manager.validate_username.return_value = True
        self.mock_connection.server.auth_manager.authenticate_user.return_value = True
        self.mock_connection.send_message.return_value = True
        
        with patch('time.sleep'):  # Mock the sleep
            self.handler.handle_auth_request(message)
        
        # Check that username was set and client was authenticated
        self.assertEqual(self.mock_connection.username, 'testuser')
        self.assertTrue(self.mock_connection.is_authenticated)
        self.mock_connection.server.add_client.assert_called_once_with(self.mock_connection)
    
    def test_handle_auth_request_invalid_username(self):
        """Test authentication with invalid username."""
        message = Mock()
        message.data = {'username': ''}
        
        # Mock validation failure
        self.mock_connection.server.auth_manager.validate_username.return_value = False
        
        with patch.object(self.handler, '_send_error_message') as mock_error:
            self.handler.handle_auth_request(message)
            mock_error.assert_called_once_with("Username cannot be empty")
    
    def test_handle_disconnect(self):
        """Test handling client disconnect."""
        message = Mock()
        
        self.handler.handle_disconnect(message)
        
        self.mock_connection.disconnect.assert_called_once()


class TestServerChatHandler(unittest.TestCase):
    """Test ServerChatHandler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = Mock()
        self.mock_connection.is_authenticated = True
        self.mock_connection.username = "testuser"
        self.mock_connection.client_id = "test_client_123"
        self.mock_connection.server = Mock()
        self.handler = ServerChatHandler(self.mock_connection)
    
    def test_handle_public_message(self):
        """Test handling public message."""
        message = Mock()
        message.data = {'content': 'Hello world'}
        
        self.handler.handle_public_message(message)
        
        # Should broadcast the message
        self.mock_connection.server.broadcast_message.assert_called_once()
        args, kwargs = self.mock_connection.server.broadcast_message.call_args
        
        # Check that a ChatMessage was created and broadcasted
        chat_message = args[0]
        self.assertIsInstance(chat_message, ChatMessage)
        self.assertEqual(chat_message.content, 'Hello world')
        self.assertEqual(chat_message.sender, 'testuser')
        self.assertFalse(chat_message.is_private)
        self.assertEqual(kwargs['exclude_client_id'], 'test_client_123')
    
    def test_handle_public_message_not_authenticated(self):
        """Test handling public message when not authenticated."""
        self.mock_connection.is_authenticated = False
        message = Mock()
        message.data = {'content': 'Hello'}
        
        with patch.object(self.handler, '_send_error_message') as mock_error:
            self.handler.handle_public_message(message)
            mock_error.assert_called_once_with("Not authenticated")
    
    def test_handle_private_message(self):
        """Test handling private message."""
        message = Mock()
        message.data = {'content': 'Private hello', 'recipient': 'otheruser'}
        
        # Mock recipient client
        mock_recipient = Mock()
        self.mock_connection.server.get_client_by_username.return_value = mock_recipient
        
        self.handler.handle_private_message(message)
        
        # Should send private message to recipient
        mock_recipient.send_message.assert_called_once()
        args = mock_recipient.send_message.call_args[0]
        private_message = args[0]
        
        self.assertIsInstance(private_message, ChatMessage)
        self.assertEqual(private_message.content, 'Private hello')
        self.assertTrue(private_message.is_private)
        self.assertEqual(private_message.recipient, 'otheruser')
    
    def test_handle_user_list_request(self):
        """Test handling user list request."""
        message = Mock()
        
        # Mock authenticated clients
        mock_clients = [Mock(username='user1'), Mock(username='user2'), Mock(username='testuser')]
        self.mock_connection.server.get_authenticated_clients.return_value = mock_clients
        
        self.handler.handle_user_list_request(message)
        
        # Should send user list response
        self.mock_connection.send_message.assert_called_once()
        args = self.mock_connection.send_message.call_args[0]
        user_list_message = args[0]
        
        # Check that usernames are included
        self.assertEqual(set(user_list_message.users), {'user1', 'user2', 'testuser'})
    
    def test_handle_encrypted_message_public(self):
        """Test handling public encrypted message."""
        from shared.messages.crypto import EncryptedMessage
        
        encrypted_msg = EncryptedMessage("encrypted_content", "testuser", is_private=False)
        
        self.handler.handle_encrypted_message(encrypted_msg)
        
        # Should broadcast the encrypted message
        self.mock_connection.server.broadcast_message.assert_called_once_with(
            encrypted_msg, exclude_client_id='test_client_123')
    
    def test_handle_encrypted_message_private(self):
        """Test handling private encrypted message."""
        from shared.messages.crypto import EncryptedMessage
        
        encrypted_msg = EncryptedMessage("encrypted_content", "testuser", "recipient", is_private=True)
        
        # Mock recipient client
        mock_recipient = Mock()
        self.mock_connection.server.get_client_by_username.return_value = mock_recipient
        
        self.handler.handle_encrypted_message(encrypted_msg)
        
        # Should send to recipient
        mock_recipient.send_message.assert_called_once_with(encrypted_msg)
    
    def test_handle_encrypted_message_not_authenticated(self):
        """Test encrypted message when not authenticated."""
        from shared.messages.crypto import EncryptedMessage
        
        self.mock_connection.is_authenticated = False
        encrypted_msg = EncryptedMessage("encrypted_content", "testuser", is_private=False)
        
        with patch.object(self.handler, '_send_error_message') as mock_error:
            self.handler.handle_encrypted_message(encrypted_msg)
            mock_error.assert_called_once_with("Not authenticated")


class TestServerFileHandler(unittest.TestCase):
    """Test ServerFileHandler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = Mock()
        self.mock_connection.is_authenticated = True
        self.mock_connection.username = "sender"
        self.mock_connection.server = Mock()
        self.mock_connection.server.active_file_transfers = {}
        self.handler = ServerFileHandler(self.mock_connection)
    
    def test_handle_file_transfer_request_private(self):
        """Test handling private file transfer request."""
        message = FileTransferRequest("test.txt", 1024, "hash123", "sender", "recipient")
        message.set_transfer_id("transfer_123")
        
        # Mock recipient client
        mock_recipient = Mock()
        mock_recipient.send_message.return_value = True
        self.mock_connection.server.get_client_by_username.return_value = mock_recipient
        
        self.handler.handle_file_transfer_request(message)
        
        # Should forward to recipient
        mock_recipient.send_message.assert_called_once_with(message)
        
        # Should track the transfer
        self.assertIn("transfer_123", self.mock_connection.server.active_file_transfers)
        transfer_info = self.mock_connection.server.active_file_transfers["transfer_123"]
        self.assertEqual(transfer_info['sender'], 'sender')
        self.assertEqual(transfer_info['recipient'], 'recipient')
    
    def test_handle_file_transfer_request_global(self):
        """Test handling global file transfer request."""
        message = FileTransferRequest("test.txt", 1024, "hash123", "sender", "GLOBAL")
        
        # Mock broadcast method
        self.mock_connection.server.broadcast_file_transfer_request.return_value = True
        
        self.handler.handle_file_transfer_request(message)
        
        # Should broadcast to all users except sender
        self.mock_connection.server.broadcast_file_transfer_request.assert_called_once_with(
            message, exclude_user='sender')
    
    def test_handle_file_transfer_request_not_authenticated(self):
        """Test file transfer request when not authenticated."""
        self.mock_connection.is_authenticated = False
        message = Mock()
        
        with patch.object(self.handler, '_send_error_message') as mock_error:
            self.handler.handle_file_transfer_request(message)
            mock_error.assert_called_once_with("Not authenticated")


class TestServerMessageHandler(unittest.TestCase):
    """Test ServerMessageHandler dispatcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = Mock()
        self.mock_connection.server = Mock()
        self.mock_connection.server.message_router = Mock()
        
        # Mock message router to return False (not handled by router)
        self.mock_connection.server.message_router.route_message.return_value = False
        
        self.handler = ServerMessageHandler(self.mock_connection)
        
        # Mock the specific handlers
        self.handler.auth_handler = Mock()
        self.handler.chat_handler = Mock()
        self.handler.file_handler = Mock()
    
    def test_dispatch_auth_request(self):
        """Test dispatching AUTH_REQUEST message."""
        message = Mock()
        message.message_type = MessageType.AUTH_REQUEST
        
        self.handler.handle_message(message)
        
        self.handler.auth_handler.handle_auth_request.assert_called_once_with(message)
    
    def test_dispatch_public_message(self):
        """Test dispatching PUBLIC_MESSAGE."""
        message = Mock()
        message.message_type = MessageType.PUBLIC_MESSAGE
        
        self.handler.handle_message(message)
        
        self.handler.chat_handler.handle_public_message.assert_called_once_with(message)
    
    def test_dispatch_file_transfer_request(self):
        """Test dispatching FILE_TRANSFER_REQUEST."""
        message = Mock()
        message.message_type = MessageType.FILE_TRANSFER_REQUEST
        
        self.handler.handle_message(message)
        
        self.handler.file_handler.handle_file_transfer_request.assert_called_once_with(message)
    
    def test_dispatch_encrypted_message(self):
        """Test dispatching ENCRYPTED_MESSAGE."""
        message = Mock()
        message.message_type = MessageType.ENCRYPTED_MESSAGE
        
        self.handler.handle_message(message)
        
        self.handler.chat_handler.handle_encrypted_message.assert_called_once_with(message)
    
    def test_message_router_handles_message(self):
        """Test when message router handles the message."""
        message = Mock()
        message.message_type = MessageType.PUBLIC_MESSAGE
        
        # Mock router handling the message
        self.mock_connection.server.message_router.route_message.return_value = True
        
        self.handler.handle_message(message)
        
        # Should not call any handlers since router handled it
        self.handler.chat_handler.handle_public_message.assert_not_called()


class TestClientHandlerFacade(unittest.TestCase):
    """Test ClientHandler facade over modular components."""
    
    @patch('server.core.client_connection.ConnectionManager')
    def test_init(self, mock_connection_manager):
        """Test ClientHandler initialization."""
        mock_socket = Mock()
        client_address = ('127.0.0.1', 12345)
        mock_server = Mock()
        
        handler = ClientHandler(mock_socket, client_address, mock_server)
        
        # Should inherit from ClientConnection
        self.assertIsInstance(handler, ClientConnection)
        self.assertEqual(handler.client_address, client_address)
        self.assertEqual(handler.server, mock_server)
    
    @patch('server.core.client_connection.ConnectionManager')
    def test_backward_compatibility_methods(self, mock_connection_manager):
        """Test backward compatibility methods."""
        mock_socket = Mock()
        client_address = ('127.0.0.1', 12345)
        mock_server = Mock()
        
        handler = ClientHandler(mock_socket, client_address, mock_server)
        handler.connection_manager = Mock()
        handler.connection_manager.send_message.return_value = True
        
        # Test legacy methods
        with patch.object(handler, 'send_message') as mock_send:
            handler.send_error_message("Test error")
            handler.send_system_message("Test system")
            
            # Should have been called twice
            self.assertEqual(mock_send.call_count, 2)


if __name__ == '__main__':
    unittest.main()