"""
Tests for the refactored client modular structure.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from client.core.client_core import ClientCore
from client.core.client_signals import ClientSignals
from client.handlers.auth_handler import AuthHandler
from client.handlers.chat_handler import ChatHandler
from client.handlers.file_handler import FileHandler
from client.handlers.message_handler import MessageHandler
from client.chat_client import ChatClient
from shared.message_types import MessageType, ChatMessage, AuthRequest


class TestClientSignals(unittest.TestCase):
    """Test ClientSignals class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.signals = ClientSignals()
    
    def test_signals_exist(self):
        """Test that all required signals exist."""
        required_signals = [
            'message_received',
            'user_list_updated',
            'system_message',
            'error_occurred',
            'connection_status_changed',
            'file_transfer_request',
            'file_transfer_progress',
            'file_transfer_complete'
        ]
        
        for signal_name in required_signals:
            self.assertTrue(hasattr(self.signals, signal_name), 
                          f"Signal {signal_name} not found")


class TestClientCore(unittest.TestCase):
    """Test ClientCore functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.core = ClientCore()
    
    def test_init(self):
        """Test ClientCore initialization."""
        self.assertEqual(self.core.server_host, 'localhost')
        self.assertEqual(self.core.server_port, 8888)
        self.assertFalse(self.core.connected)
        self.assertIsNone(self.core.username)
        self.assertIsNotNone(self.core.crypto_manager)
        self.assertIsNotNone(self.core.file_transfer_manager)
        self.assertIsNotNone(self.core.signals)
    
    def test_custom_server_config(self):
        """Test ClientCore with custom server configuration."""
        core = ClientCore('example.com', 9999)
        self.assertEqual(core.server_host, 'example.com')
        self.assertEqual(core.server_port, 9999)
    
    @patch('socket.socket')
    def test_send_message_not_connected(self, mock_socket):
        """Test sending message when not connected."""
        message = Mock()
        result = self.core.send_message(message)
        self.assertFalse(result)
    
    def test_request_user_list_not_connected(self):
        """Test requesting user list when not connected."""
        result = self.core.request_user_list()
        self.assertFalse(result)


class TestAuthHandler(unittest.TestCase):
    """Test AuthHandler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_core = Mock()
        self.mock_core.username = "test_user"
        self.mock_core.crypto_manager = Mock()
        self.mock_core.connection_manager = Mock()
        self.mock_core.signals = Mock()
        self.handler = AuthHandler(self.mock_core)
    
    def test_handle_auth_success(self):
        """Test handling successful authentication."""
        message = Mock()
        message.data = {'status': 'success'}
        
        self.handler.handle_auth_response(message)
        
        self.assertTrue(self.mock_core.auth_success)
        self.mock_core.auth_event.set.assert_called_once()
        self.mock_core.signals.connection_status_changed.emit.assert_called_once_with(True)
    
    def test_handle_auth_failure(self):
        """Test handling authentication failure."""
        message = Mock()
        message.data = {'status': 'failure'}
        
        self.handler.handle_auth_response(message)
        
        self.assertFalse(self.mock_core.auth_success)
        self.mock_core.auth_event.set.assert_called_once()
        self.mock_core.signals.error_occurred.emit.assert_called_once_with("Authentication failed")


class TestChatHandler(unittest.TestCase):
    """Test ChatHandler functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_core = Mock()
        self.mock_core.connected = True
        self.mock_core.username = "test_user"
        self.mock_core.crypto_manager = Mock()
        self.mock_core.signals = Mock()
        self.handler = ChatHandler(self.mock_core)
    
    def test_handle_public_message(self):
        """Test handling public message."""
        message = Mock()
        
        self.handler.handle_public_message(message)
        
        self.mock_core.signals.message_received.emit.assert_called_once_with(message)
    
    def test_handle_system_message_info(self):
        """Test handling system info message."""
        message = Mock()
        message.data = {'system_message_type': 'info', 'content': 'Test message'}
        
        self.handler.handle_system_message(message)
        
        self.mock_core.signals.system_message.emit.assert_called_once_with('Test message')
    
    def test_handle_system_message_error(self):
        """Test handling system error message."""
        message = Mock()
        message.data = {'system_message_type': 'error', 'content': 'Error message'}
        
        self.handler.handle_system_message(message)
        
        self.assertFalse(self.mock_core.connected)
        self.assertFalse(self.mock_core.auth_success)
        self.mock_core.auth_event.set.assert_called_once()
        self.mock_core.signals.error_occurred.emit.assert_called_once_with('Error message')
    
    def test_send_public_message_not_connected(self):
        """Test sending public message when not connected."""
        self.mock_core.connected = False
        
        result = self.handler.send_public_message("test message")
        
        self.assertFalse(result)


class TestMessageHandler(unittest.TestCase):
    """Test MessageHandler dispatcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_core = Mock()
        self.handler = MessageHandler(self.mock_core)
        
        # Mock the specific handlers
        self.handler.auth_handler = Mock()
        self.handler.chat_handler = Mock()
        self.handler.file_handler = Mock()
    
    def test_dispatch_auth_response(self):
        """Test dispatching AUTH_RESPONSE message."""
        message = Mock()
        message.message_type = MessageType.AUTH_RESPONSE
        
        self.handler.handle_message(message)
        
        self.handler.auth_handler.handle_auth_response.assert_called_once_with(message)
    
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


class TestChatClientFacade(unittest.TestCase):
    """Test ChatClient facade over modular components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = ChatClient()
    
    def test_init(self):
        """Test ChatClient initialization."""
        self.assertIsNotNone(self.client.core)
        self.assertIsNotNone(self.client.chat_handler)
        self.assertIsNotNone(self.client.file_handler)
        
        # Test that signals are properly exposed
        self.assertEqual(self.client.message_received, self.client.core.signals.message_received)
        self.assertEqual(self.client.error_occurred, self.client.core.signals.error_occurred)
    
    def test_properties(self):
        """Test ChatClient properties."""
        self.assertEqual(self.client.connected, self.client.core.connected)
        self.assertEqual(self.client.username, self.client.core.username)
    
    @patch.object(ClientCore, 'connect')
    def test_connect_delegation(self, mock_connect):
        """Test that connect is properly delegated."""
        mock_connect.return_value = True
        
        result = self.client.connect("test_user")
        
        mock_connect.assert_called_once_with("test_user")
        self.assertTrue(result)
    
    @patch.object(ChatHandler, 'send_public_message')
    def test_send_public_message_delegation(self, mock_send):
        """Test that send_public_message is properly delegated."""
        mock_send.return_value = True
        
        result = self.client.send_public_message("test message")
        
        mock_send.assert_called_once_with("test message")
        self.assertTrue(result)


class TestModularImports(unittest.TestCase):
    """Test that all modular imports work correctly."""
    
    def test_message_imports(self):
        """Test that message imports work from both old and new locations."""
        # Test importing from old location (compatibility)
        from shared.message_types import MessageType, ChatMessage
        self.assertTrue(True)  # If we get here, imports worked
        
        # Test importing from new location
        from shared.messages import MessageType as NewMessageType, ChatMessage as NewChatMessage
        self.assertEqual(MessageType.PUBLIC_MESSAGE, NewMessageType.PUBLIC_MESSAGE)
    
    def test_client_imports(self):
        """Test that client module imports work."""
        from client.chat_client import ChatClient
        from client.core.client_core import ClientCore
        from client.handlers.message_handler import MessageHandler
        
        # Test instantiation
        client = ChatClient()
        self.assertIsInstance(client.core, ClientCore)


if __name__ == '__main__':
    unittest.main()