"""
Main chat client implementation.
"""

import socket
import threading
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
try:
    from ..shared.message_types import Message, MessageType, ChatMessage, SystemMessage, UserListMessage
    from ..shared.protocols import ConnectionManager
    from ..shared.exceptions import ConnectionError
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import Message, MessageType, ChatMessage, SystemMessage, UserListMessage
    from shared.protocols import ConnectionManager
    from shared.exceptions import ConnectionError


class ChatClient(QObject):
    """Main chat client class."""
    
    # Signals for GUI updates
    message_received = pyqtSignal(object)  # Message object
    user_list_updated = pyqtSignal(list)   # List of usernames
    system_message = pyqtSignal(str)       # System message content
    error_occurred = pyqtSignal(str)       # Error message
    connection_status_changed = pyqtSignal(bool)  # Connected status
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 8888):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket: Optional[socket.socket] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.connected = False
        self.username: Optional[str] = None
        self.receive_thread: Optional[threading.Thread] = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect(self, username: str) -> bool:
        """Connect to the server."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            
            self.connection_manager = ConnectionManager(self.client_socket)
            self.connected = True
            self.username = username
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # Send authentication request
            auth_message = Message(MessageType.AUTH_REQUEST, {'username': username})
            self.connection_manager.send_message(auth_message)
            
            self.logger.info(f"Connected to server as {username}")
            # Don't emit connection status yet - wait for auth response
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.error_occurred.emit(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the server."""
        self.connected = False
        
        if self.connection_manager:
            # Send disconnect message
            disconnect_message = Message(MessageType.DISCONNECT, {})
            self.connection_manager.send_message(disconnect_message)
            self.connection_manager.close()
        
        if self.client_socket:
            self.client_socket.close()
        
        self.connection_status_changed.emit(False)
        self.logger.info("Disconnected from server")
    
    def _receive_loop(self):
        """Main receive loop running in separate thread."""
        while self.connected and self.connection_manager and self.connection_manager.is_connected():
            try:
                message = self.connection_manager.receive_message()
                if message is None:
                    break
                
                self._handle_message(message)
                
            except Exception as e:
                self.logger.error(f"Error receiving message: {e}")
                break
        
        # Connection lost
        self.connected = False
        self.connection_status_changed.emit(False)
        self.error_occurred.emit("Connection lost")
    
    def _handle_message(self, message: Message):
        """Handle incoming messages."""
        try:
            print(f"DEBUG: Received message type: {message.message_type}")
            if message.message_type == MessageType.AUTH_RESPONSE:
                # Authentication successful
                print("DEBUG: Authentication successful, emitting connection status")
                self.connection_status_changed.emit(True)
                self.logger.info("Authentication successful")
            elif message.message_type == MessageType.PUBLIC_MESSAGE:
                self.message_received.emit(message)
            elif message.message_type == MessageType.PRIVATE_MESSAGE:
                self.message_received.emit(message)
            elif message.message_type == MessageType.SYSTEM_MESSAGE:
                self.system_message.emit(message.data['content'])
            elif message.message_type == MessageType.USER_LIST_RESPONSE:
                self.user_list_updated.emit(message.data['users'])
            elif message.message_type == MessageType.ERROR_MESSAGE:
                self.error_occurred.emit(message.data['content'])
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def send_public_message(self, content: str) -> bool:
        """Send a public message."""
        if not self.connected or not self.username:
            return False
        
        try:
            message = ChatMessage(content, self.username, is_private=False)
            return self.connection_manager.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to send public message: {e}")
            return False
    
    def send_private_message(self, content: str, recipient: str) -> bool:
        """Send a private message."""
        if not self.connected or not self.username:
            return False
        
        try:
            message = ChatMessage(content, self.username, recipient, is_private=True)
            return self.connection_manager.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to send private message: {e}")
            return False
    
    def request_user_list(self) -> bool:
        """Request updated user list."""
        if not self.connected:
            return False
        
        try:
            message = Message(MessageType.USER_LIST_REQUEST, {})
            return self.connection_manager.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to request user list: {e}")
            return False
