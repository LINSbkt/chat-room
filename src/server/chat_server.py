"""
Main chat server implementation - refactored to use modular structure.
"""

import logging
from typing import Optional
try:
    from .client_handler import ClientHandler
    from .message_router import MessageRouter
    from .auth_manager import AuthManager
    from .crypto_manager import ServerCryptoManager
    from .core.server_core import ServerCore
    from .managers.client_manager import ClientManager
    from .managers.broadcast_manager import BroadcastManager
    from .managers.file_transfer_server_manager import FileTransferServerManager
    from ..shared.file_transfer_manager import FileTransferManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from server.client_handler import ClientHandler
    from server.message_router import MessageRouter
    from server.auth_manager import AuthManager
    from server.crypto_manager import ServerCryptoManager
    from server.core.server_core import ServerCore
    from server.managers.client_manager import ClientManager
    from server.managers.broadcast_manager import BroadcastManager
    from server.managers.file_transfer_server_manager import FileTransferServerManager
    from shared.file_transfer_manager import FileTransferManager


class ChatServer:
    """Main chat server class - now uses modular components."""
    
    def __init__(self, host: str = 'localhost', port: int = 8888, max_clients: int = 100):
        # Core server functionality
        self.server_core = ServerCore(host, port, max_clients)
        
        # Managers
        self.client_manager = ClientManager(self)
        self.broadcast_manager = BroadcastManager(self)
        self.file_transfer_server_manager = FileTransferServerManager(self)
        
        # Other components
        self.message_router = MessageRouter(self)
        self.auth_manager = AuthManager()
        self.crypto_manager = ServerCryptoManager()
        self.file_transfer_manager = FileTransferManager()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the server and begin accepting connections."""
        # Use server core to handle networking, provide our connection handler
        self.server_core.start_listening(self._handle_new_connection)
    
    def stop(self):
        """Stop the server and close all connections."""
        # Disconnect all clients
        self.client_manager.disconnect_all_clients()
        
        # Stop server core
        self.server_core.stop()
        
        self.logger.info("Server stopped")
    
    def _handle_new_connection(self, client_socket, client_address):
        """Handle a new client connection."""
        client_handler = ClientHandler(client_socket, client_address, self)
        client_handler.run()
    
    # Delegation methods for backward compatibility
    def add_client(self, client_handler: ClientHandler):
        """Add a client to the active clients list."""
        self.client_manager.add_client(client_handler)
    
    def remove_client(self, client_handler: ClientHandler):
        """Remove a client from the active clients list."""
        self.client_manager.remove_client(client_handler)
    
    def get_client_by_username(self, username: str) -> Optional[ClientHandler]:
        """Get client handler by username."""
        return self.client_manager.get_client_by_username(username)
    
    def get_authenticated_clients(self):
        """Get all authenticated clients."""
        return self.client_manager.get_authenticated_clients()
    
    def get_user_list(self) -> list:
        """Get list of currently connected usernames."""
        return self.client_manager.get_user_list()
    
    def is_username_taken(self, username: str) -> bool:
        """Check if a username is already taken."""
        return username in self.get_user_list()
    
    # Broadcasting methods - delegate to broadcast manager
    def broadcast_message(self, message, exclude_client_id: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        self.broadcast_manager.broadcast_message(message, exclude_client_id)
    
    def send_private_message(self, message, recipient_username: str):
        """Send a private message to a specific user."""
        return self.broadcast_manager.send_private_message(message, recipient_username)
    
    def broadcast_system_message(self, content: str):
        """Broadcast a system message to all clients."""
        self.broadcast_manager.broadcast_system_message(content)
    
    def broadcast_user_list(self):
        """Broadcast updated user list to all clients."""
        self.broadcast_manager.broadcast_user_list()
    
    def broadcast_file_transfer_request(self, message, exclude_user: Optional[str] = None):
        """Broadcast a file transfer request to all clients except the sender."""
        return self.broadcast_manager.broadcast_file_transfer_request(message, exclude_user)
    
    # File transfer methods - delegate to file transfer manager
    def forward_file_transfer_response(self, message, sender_username: str) -> bool:
        """Forward file transfer response to the original sender."""
        return self.file_transfer_server_manager.forward_file_transfer_response(message, sender_username)
    
    def forward_file_chunk(self, message, sender_username: str) -> bool:
        """Forward file chunk to the recipient."""
        return self.file_transfer_server_manager.forward_file_chunk(message, sender_username)
    
    def forward_file_transfer_complete(self, message, sender_username: str) -> bool:
        """Forward file transfer completion to the recipient."""
        return self.file_transfer_server_manager.forward_file_transfer_complete(message, sender_username)
    
    # Properties for backward compatibility
    @property
    def active_clients(self):
        """Get active clients dictionary."""
        return self.client_manager.active_clients
    
    @property
    def active_file_transfers(self):
        """Get active file transfers dictionary."""
        return self.file_transfer_server_manager.active_file_transfers
    
    @property
    def running(self):
        """Check if server is running."""
        return self.server_core.is_running()