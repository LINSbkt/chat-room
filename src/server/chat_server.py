"""
Main chat server implementation.
"""

import socket
import threading
import logging
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor
try:
    from .client_handler import ClientHandler
    from .message_router import MessageRouter
    from .auth_manager import AuthManager
    from .crypto_manager import ServerCryptoManager
    from ..shared.message_types import (MessageType, SystemMessage, UserListMessage,
                                      FileTransferResponse, FileChunk, FileTransferComplete)
    from ..shared.protocols import ConnectionManager
    from ..shared.file_transfer_manager import FileTransferManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from server.client_handler import ClientHandler
    from server.message_router import MessageRouter
    from server.auth_manager import AuthManager
    from server.crypto_manager import ServerCryptoManager
    from shared.message_types import (MessageType, SystemMessage, UserListMessage,
                                    FileTransferResponse, FileChunk, FileTransferComplete)
    from shared.protocols import ConnectionManager
    from shared.file_transfer_manager import FileTransferManager


class ChatServer:
    """Main chat server class."""
    
    def __init__(self, host: str = 'localhost', port: int = 8888, max_clients: int = 100):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.thread_pool = ThreadPoolExecutor(max_workers=max_clients)
        self.active_clients: Dict[str, ClientHandler] = {}
        self.message_router = MessageRouter(self)
        self.auth_manager = AuthManager()
        self.crypto_manager = ServerCryptoManager()
        self.file_transfer_manager = FileTransferManager()
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the server and begin accepting connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            
            self.running = True
            self.logger.info(f"Server started on {self.host}:{self.port}")
            self.logger.info(f"Maximum clients: {self.max_clients}")
            
            # Small delay to ensure server is fully ready
            import time
            time.sleep(0.1)
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.logger.info(f"New connection from {client_address}")
                    
                    # Create client handler and submit to thread pool
                    client_handler = ClientHandler(client_socket, client_address, self)
                    self.thread_pool.submit(client_handler.run)
                    
                except socket.error as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self):
        """Stop the server and close all connections."""
        self.running = False
        
        # Close all client connections
        for client_id, client_handler in list(self.active_clients.items()):
            client_handler.disconnect()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("Server stopped")
    
    def add_client(self, client_handler: ClientHandler):
        """Add a client to the active clients list."""
        self.active_clients[client_handler.client_id] = client_handler
        self.logger.info(f"Client {client_handler.client_id} added. Total clients: {len(self.active_clients)}")
        
        # Notify all clients about new user
        self.broadcast_system_message(f"User {client_handler.username} joined the chat")
        self.broadcast_user_list()
    
    def remove_client(self, client_id: str):
        """Remove a client from the active clients list."""
        if client_id in self.active_clients:
            client_handler = self.active_clients[client_id]
            username = client_handler.username
            
            del self.active_clients[client_id]
            self.logger.info(f"Client {client_id} removed. Total clients: {len(self.active_clients)}")
            
            # Notify all clients about user leaving
            self.broadcast_system_message(f"User {username} left the chat")
            self.broadcast_user_list()
    
    def broadcast_message(self, message, exclude_client_id: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        for client_id, client_handler in self.active_clients.items():
            if client_id != exclude_client_id:
                try:
                    client_handler.send_message(message)
                except Exception as e:
                    self.logger.error(f"Failed to send message to client {client_id}: {e}")
    
    def send_private_message(self, message, recipient_username: str):
        """Send a private message to a specific user."""
        for client_handler in self.active_clients.values():
            if client_handler.username == recipient_username:
                try:
                    client_handler.send_message(message)
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to send private message to {recipient_username}: {e}")
                    return False
        return False
    
    def broadcast_system_message(self, content: str):
        """Broadcast a system message to all clients."""
        system_message = SystemMessage(content, "info")
        self.broadcast_message(system_message)
    
    def broadcast_user_list(self):
        """Broadcast updated user list to all clients."""
        users = [client.username for client in self.active_clients.values() if client.username]
        user_list_message = UserListMessage(users)
        self.broadcast_message(user_list_message)
    
    def broadcast_file_transfer_request(self, message, exclude_user: Optional[str] = None):
        """Broadcast a file transfer request to all clients except the sender."""
        success_count = 0
        total_clients = 0
        
        for client_handler in self.active_clients.values():
            if client_handler.username and client_handler.username != exclude_user:
                total_clients += 1
                if client_handler.send_message(message):
                    success_count += 1
        
        self.logger.info(f"📤 Broadcasted file transfer request to {success_count}/{total_clients} clients")
        return success_count > 0
    
    def get_user_list(self) -> list:
        """Get list of currently connected usernames."""
        return [client.username for client in self.active_clients.values() if client.username]
    
    def is_username_taken(self, username: str) -> bool:
        """Check if a username is already taken."""
        return username in self.get_user_list()
    
    def get_client_by_username(self, username: str) -> Optional[ClientHandler]:
        """Get client handler by username."""
        for client_handler in self.active_clients.values():
            if client_handler.username == username:
                return client_handler
        return None
    
    def forward_file_transfer_response(self, message: FileTransferResponse, sender_username: str) -> bool:
        """Forward file transfer response to the original sender."""
        try:
            transfer_id = message.transfer_id
            
            # Find the original sender by looking through all clients
            for client_handler in self.active_clients.values():
                if client_handler.username and client_handler.username != sender_username:
                    # Check if this client has an active transfer with this ID
                    if hasattr(client_handler, 'file_transfer_manager') and client_handler.file_transfer_manager:
                        if transfer_id in client_handler.file_transfer_manager.active_transfers:
                            success = client_handler.send_message(message)
                            if success:
                                self.logger.info(f"📤 Forwarded file transfer response to {client_handler.username}")
                            return success
            
            self.logger.warning(f"Could not find original sender for transfer {transfer_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error forwarding file transfer response: {e}")
            return False
    
    def forward_file_chunk(self, message: FileChunk, sender_username: str) -> bool:
        """Forward file chunk to the recipient."""
        try:
            # Find the recipient by looking through active transfers
            for client_handler in self.active_clients.values():
                if client_handler.username and client_handler.username != sender_username:
                    # Check if this client has an active transfer with this ID
                    if message.transfer_id in client_handler.file_transfer_manager.active_transfers:
                        success = client_handler.send_message(message)
                        if success:
                            self.logger.debug(f"📦 Forwarded file chunk to {client_handler.username}")
                        return success
            
            self.logger.warning(f"Could not find recipient for transfer {message.transfer_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error forwarding file chunk: {e}")
            return False
    
    def forward_file_transfer_complete(self, message: FileTransferComplete, sender_username: str) -> bool:
        """Forward file transfer completion to the recipient."""
        try:
            # Find the recipient by looking through active transfers
            for client_handler in self.active_clients.values():
                if client_handler.username and client_handler.username != sender_username:
                    # Check if this client has an active transfer with this ID
                    if message.transfer_id in client_handler.file_transfer_manager.active_transfers:
                        success = client_handler.send_message(message)
                        if success:
                            self.logger.info(f"✅ Forwarded file transfer completion to {client_handler.username}")
                        return success
            
            self.logger.warning(f"Could not find recipient for transfer completion {message.transfer_id}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error forwarding file transfer completion: {e}")
            return False
