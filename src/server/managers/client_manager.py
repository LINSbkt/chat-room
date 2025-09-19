"""
Client connection management.
"""

import logging
from typing import Dict, List, Optional
try:
    from ..client_handler import ClientHandler
except ImportError:
    from server.client_handler import ClientHandler


class ClientManager:
    """Manages client connections and user operations."""
    
    def __init__(self, server):
        self.server = server
        self.active_clients: Dict[str, ClientHandler] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_client(self, client_handler: ClientHandler):
        """Add a client to the active clients list."""
        self.logger.info(f"Adding client {client_handler.client_id} (username: {client_handler.username}) to active_clients")
        self.active_clients[client_handler.client_id] = client_handler
        self.logger.info(f"Client {client_handler.client_id} added successfully. Total clients: {len(self.active_clients)}")
        
        # Log all current clients
        for cid, ch in self.active_clients.items():
            self.logger.debug(f"  Active client: {cid} -> {ch.username} (authenticated: {ch.is_authenticated})")
        
        # Notify all clients about new user
        if client_handler.username:
            self.logger.info(f"Broadcasting join notification for {client_handler.username}")
            self.server.broadcast_manager.broadcast_system_message(f"User {client_handler.username} joined the chat")
            self.server.broadcast_manager.broadcast_user_list()
    
    def remove_client(self, client_handler: ClientHandler):
        """Remove a client from the active clients list."""
        if client_handler.client_id in self.active_clients:
            username = client_handler.username
            
            # Remove from AuthManager to preserve user data
            if username:
                self.server.auth_manager.disconnect_user(client_handler.client_id)
                self.logger.info(f"User '{username}' disconnected from AuthManager (data preserved)")
            
            del self.active_clients[client_handler.client_id]
            self.logger.info(f"Client {client_handler.client_id} removed. Total clients: {len(self.active_clients)}")
            
            # Notify all clients about user leaving
            if username:
                self.server.broadcast_manager.broadcast_system_message(f"User {username} left the chat")
                self.server.broadcast_manager.broadcast_user_list()
    
    def get_client_by_username(self, username: str) -> Optional[ClientHandler]:
        """Find a client by username."""
        for client_handler in self.active_clients.values():
            if client_handler.username == username and client_handler.is_authenticated:
                return client_handler
        return None
    
    def get_authenticated_clients(self) -> List[ClientHandler]:
        """Get all authenticated clients."""
        return [client for client in self.active_clients.values() 
                if client.is_authenticated and client.username]
    
    def get_user_list(self) -> List[str]:
        """Get list of authenticated usernames."""
        return [client.username for client in self.get_authenticated_clients()]
    
    def disconnect_all_clients(self):
        """Disconnect all clients."""
        for client_handler in list(self.active_clients.values()):
            client_handler.disconnect()
        self.active_clients.clear()
    
    def get_client_count(self) -> int:
        """Get total number of connected clients."""
        return len(self.active_clients)
    
    def get_authenticated_client_count(self) -> int:
        """Get number of authenticated clients."""
        return len(self.get_authenticated_clients())