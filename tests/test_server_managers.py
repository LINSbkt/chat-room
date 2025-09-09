"""
Tests for the server management modules.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from server.managers.client_manager import ClientManager
from server.managers.broadcast_manager import BroadcastManager
from server.managers.file_transfer_server_manager import FileTransferServerManager
from server.core.server_core import ServerCore
from server.chat_server import ChatServer
from shared.message_types import FileTransferResponse, FileChunk, FileTransferComplete


class TestClientManager(unittest.TestCase):
    """Test ClientManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_server = Mock()
        self.mock_server.broadcast_manager = Mock()
        self.manager = ClientManager(self.mock_server)
    
    def test_init(self):
        """Test ClientManager initialization."""
        self.assertEqual(self.manager.server, self.mock_server)
        self.assertEqual(self.manager.active_clients, {})
    
    def test_add_client(self):
        """Test adding a client."""
        mock_client = Mock()
        mock_client.client_id = "client123"
        mock_client.username = "testuser"
        
        self.manager.add_client(mock_client)
        
        self.assertIn("client123", self.manager.active_clients)
        self.assertEqual(self.manager.active_clients["client123"], mock_client)
        
        # Should broadcast system message and user list
        self.mock_server.broadcast_manager.broadcast_system_message.assert_called_once()
        self.mock_server.broadcast_manager.broadcast_user_list.assert_called_once()
    
    def test_remove_client(self):
        """Test removing a client."""
        mock_client = Mock()
        mock_client.client_id = "client123"
        mock_client.username = "testuser"
        
        # Add then remove
        self.manager.active_clients["client123"] = mock_client
        self.manager.remove_client(mock_client)
        
        self.assertNotIn("client123", self.manager.active_clients)
        
        # Should broadcast system message and user list
        self.mock_server.broadcast_manager.broadcast_system_message.assert_called_once()
        self.mock_server.broadcast_manager.broadcast_user_list.assert_called_once()
    
    def test_get_client_by_username(self):
        """Test getting client by username."""
        mock_client = Mock()
        mock_client.username = "testuser"
        mock_client.is_authenticated = True
        self.manager.active_clients["client123"] = mock_client
        
        result = self.manager.get_client_by_username("testuser")
        self.assertEqual(result, mock_client)
        
        # Test non-existent user
        result = self.manager.get_client_by_username("nonexistent")
        self.assertIsNone(result)
    
    def test_get_authenticated_clients(self):
        """Test getting authenticated clients."""
        # Create mock clients
        auth_client = Mock()
        auth_client.is_authenticated = True
        auth_client.username = "authuser"
        
        unauth_client = Mock()
        unauth_client.is_authenticated = False
        unauth_client.username = None
        
        self.manager.active_clients["auth"] = auth_client
        self.manager.active_clients["unauth"] = unauth_client
        
        result = self.manager.get_authenticated_clients()
        self.assertEqual(len(result), 1)
        self.assertIn(auth_client, result)
    
    def test_get_user_list(self):
        """Test getting user list."""
        auth_client = Mock()
        auth_client.is_authenticated = True
        auth_client.username = "authuser"
        
        unauth_client = Mock()
        unauth_client.is_authenticated = False
        unauth_client.username = None
        
        # Mock get_authenticated_clients to return the auth client
        self.manager.get_authenticated_clients = Mock(return_value=[auth_client])
        
        result = self.manager.get_user_list()
        self.assertEqual(result, ["authuser"])


class TestBroadcastManager(unittest.TestCase):
    """Test BroadcastManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_server = Mock()
        self.mock_server.client_manager = Mock()
        self.manager = BroadcastManager(self.mock_server)
    
    def test_broadcast_message(self):
        """Test broadcasting message to all clients."""
        # Create mock clients
        client1 = Mock()
        client2 = Mock()
        exclude_client = Mock()
        
        self.mock_server.client_manager.active_clients = {
            "client1": client1,
            "client2": client2,
            "exclude": exclude_client
        }
        
        message = Mock()
        
        # Broadcast excluding one client
        self.manager.broadcast_message(message, exclude_client_id="exclude")
        
        # Should send to client1 and client2, but not exclude_client
        client1.send_message.assert_called_once_with(message)
        client2.send_message.assert_called_once_with(message)
        exclude_client.send_message.assert_not_called()
    
    def test_send_private_message(self):
        """Test sending private message."""
        mock_client = Mock()
        mock_client.send_message.return_value = True
        
        self.mock_server.client_manager.get_client_by_username.return_value = mock_client
        
        message = Mock()
        result = self.manager.send_private_message(message, "testuser")
        
        self.assertTrue(result)
        mock_client.send_message.assert_called_once_with(message)
    
    def test_send_private_message_user_not_found(self):
        """Test sending private message to non-existent user."""
        self.mock_server.client_manager.get_client_by_username.return_value = None
        
        message = Mock()
        result = self.manager.send_private_message(message, "nonexistent")
        
        self.assertFalse(result)
    
    def test_broadcast_system_message(self):
        """Test broadcasting system message."""
        with patch.object(self.manager, 'broadcast_message') as mock_broadcast:
            self.manager.broadcast_system_message("Test message")
            
            # Should create SystemMessage and broadcast it
            mock_broadcast.assert_called_once()
            args = mock_broadcast.call_args[0]
            system_message = args[0]
            
            # Check it's a SystemMessage with correct content
            self.assertEqual(system_message.content, "Test message")
    
    def test_broadcast_file_transfer_request(self):
        """Test broadcasting file transfer request."""
        # Create mock clients
        sender_client = Mock()
        sender_client.username = "sender"
        sender_client.send_message.return_value = True
        
        recipient_client = Mock()
        recipient_client.username = "recipient"
        recipient_client.send_message.return_value = True
        
        self.mock_server.client_manager.active_clients = {
            "sender": sender_client,
            "recipient": recipient_client
        }
        
        message = Mock()
        result = self.manager.broadcast_file_transfer_request(message, exclude_user="sender")
        
        # Should return True (success) and send only to recipient
        self.assertTrue(result)
        sender_client.send_message.assert_not_called()
        recipient_client.send_message.assert_called_once_with(message)


class TestFileTransferServerManager(unittest.TestCase):
    """Test FileTransferServerManager functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_server = Mock()
        self.mock_server.client_manager = Mock()
        self.manager = FileTransferServerManager(self.mock_server)
    
    def test_track_transfer(self):
        """Test tracking a file transfer."""
        self.manager.track_transfer("transfer123", "sender", "recipient")
        
        self.assertIn("transfer123", self.manager.active_file_transfers)
        transfer_info = self.manager.active_file_transfers["transfer123"]
        self.assertEqual(transfer_info['sender'], "sender")
        self.assertEqual(transfer_info['recipient'], "recipient")
    
    def test_cleanup_transfer(self):
        """Test cleaning up a transfer."""
        self.manager.active_file_transfers["transfer123"] = {"sender": "test", "recipient": "test"}
        
        self.manager.cleanup_transfer("transfer123")
        
        self.assertNotIn("transfer123", self.manager.active_file_transfers)
    
    def test_forward_file_transfer_response(self):
        """Test forwarding file transfer response."""
        # Set up tracked transfer
        self.manager.active_file_transfers["transfer123"] = {
            "sender": "original_sender",
            "recipient": "recipient"
        }
        
        # Mock original sender client
        mock_sender = Mock()
        mock_sender.send_message.return_value = True
        self.mock_server.client_manager.get_client_by_username.return_value = mock_sender
        
        # Create response message
        response = FileTransferResponse("transfer123", True, "Accepted")
        
        result = self.manager.forward_file_transfer_response(response, "recipient")
        
        self.assertTrue(result)
        mock_sender.send_message.assert_called_once_with(response)
    
    def test_forward_file_transfer_response_sender_not_found(self):
        """Test forwarding response when original sender not found."""
        # Set up tracked transfer
        self.manager.active_file_transfers["transfer123"] = {
            "sender": "original_sender",
            "recipient": "recipient"
        }
        
        # Mock - sender not found
        self.mock_server.client_manager.get_client_by_username.return_value = None
        
        response = FileTransferResponse("transfer123", True, "Accepted")
        result = self.manager.forward_file_transfer_response(response, "recipient")
        
        self.assertFalse(result)
        # Transfer should be cleaned up
        self.assertNotIn("transfer123", self.manager.active_file_transfers)


class TestServerCore(unittest.TestCase):
    """Test ServerCore functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.core = ServerCore("localhost", 9999, 50)
    
    def test_init(self):
        """Test ServerCore initialization."""
        self.assertEqual(self.core.host, "localhost")
        self.assertEqual(self.core.port, 9999)
        self.assertEqual(self.core.max_clients, 50)
        self.assertFalse(self.core.running)
        self.assertIsNone(self.core.server_socket)
    
    def test_is_running(self):
        """Test running status check."""
        self.assertFalse(self.core.is_running())
        
        self.core.running = True
        self.assertTrue(self.core.is_running())
    
    def test_stop(self):
        """Test stopping the server core."""
        self.core.running = True
        mock_socket = Mock()
        self.core.server_socket = mock_socket
        
        with patch.object(self.core.thread_pool, 'shutdown') as mock_shutdown:
            self.core.stop()
            
            self.assertFalse(self.core.running)
            mock_socket.close.assert_called_once()
            mock_shutdown.assert_called_once_with(wait=True)


class TestChatServerFacade(unittest.TestCase):
    """Test ChatServer facade over modular components."""
    
    def test_init(self):
        """Test ChatServer initialization."""
        server = ChatServer("localhost", 8888, 100)
        
        # Should have all managers
        self.assertIsNotNone(server.client_manager)
        self.assertIsNotNone(server.broadcast_manager)
        self.assertIsNotNone(server.file_transfer_server_manager)
        self.assertIsNotNone(server.server_core)
        
        # Should have other components
        self.assertIsNotNone(server.message_router)
        self.assertIsNotNone(server.auth_manager)
        self.assertIsNotNone(server.crypto_manager)
    
    def test_delegation_methods(self):
        """Test that methods properly delegate to managers."""
        server = ChatServer()
        
        # Mock managers
        server.client_manager = Mock()
        server.broadcast_manager = Mock()
        server.file_transfer_server_manager = Mock()
        
        mock_client = Mock()
        
        # Test client management delegation
        server.add_client(mock_client)
        server.client_manager.add_client.assert_called_once_with(mock_client)
        
        server.remove_client(mock_client)
        server.client_manager.remove_client.assert_called_once_with(mock_client)
        
        server.get_client_by_username("test")
        server.client_manager.get_client_by_username.assert_called_once_with("test")
        
        # Test broadcast delegation
        message = Mock()
        server.broadcast_message(message, "exclude123")
        server.broadcast_manager.broadcast_message.assert_called_once_with(message, "exclude123")
        
        server.broadcast_system_message("test message")
        server.broadcast_manager.broadcast_system_message.assert_called_once_with("test message")
        
        # Test file transfer delegation
        response = Mock()
        server.forward_file_transfer_response(response, "sender")
        server.file_transfer_server_manager.forward_file_transfer_response.assert_called_once_with(response, "sender")
    
    def test_properties(self):
        """Test backward compatibility properties."""
        server = ChatServer()
        
        # Mock managers
        server.client_manager = Mock()
        server.client_manager.active_clients = {"test": "client"}
        server.file_transfer_server_manager = Mock()
        server.file_transfer_server_manager.active_file_transfers = {"test": "transfer"}
        server.server_core = Mock()
        server.server_core.is_running.return_value = True
        
        # Test properties
        self.assertEqual(server.active_clients, {"test": "client"})
        self.assertEqual(server.active_file_transfers, {"test": "transfer"})
        self.assertTrue(server.running)


if __name__ == '__main__':
    unittest.main()