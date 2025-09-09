"""
Core client functionality for connection and authentication.
"""

import socket
import threading
import logging
from typing import Optional
from .client_signals import ClientSignals

try:
    from ...shared.message_types import Message, MessageType
    from ...shared.protocols import ConnectionManager
    from ...shared.exceptions import ConnectionError
    from ...shared.file_transfer_manager import FileTransferManager
    from ..crypto_manager import ClientCryptoManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from shared.message_types import Message, MessageType
    from shared.protocols import ConnectionManager
    from shared.exceptions import ConnectionError
    from shared.file_transfer_manager import FileTransferManager
    from client.crypto_manager import ClientCryptoManager


class ClientCore:
    """Core client functionality for connection and basic operations."""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 8888):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket: Optional[socket.socket] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.connected = False
        self.username: Optional[str] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.auth_event = threading.Event()
        self.auth_success = False
        self.intentional_disconnect = False
        self.crypto_manager = ClientCryptoManager()
        self.file_transfer_manager = FileTransferManager()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize signals
        self.signals = ClientSignals()
    
    def connect(self, username: str) -> bool:
        """Connect to the server."""
        try:
            self.auth_event.clear()
            self.auth_success = False
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            
            self.connection_manager = ConnectionManager(self.client_socket)
            self.connected = True
            self.username = username
            
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            try:
                public_key_pem = self.crypto_manager.initialize_encryption()
                self.logger.info("Encryption initialized, will send key exchange after authentication")
            except Exception as e:
                self.logger.warning(f"Failed to initialize encryption: {e}")
            
            auth_message = Message(MessageType.AUTH_REQUEST, {'username': username})
            success = self.connection_manager.send_message(auth_message)
            
            self.logger.info(f"Connected to server as {username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.signals.error_occurred.emit(f"Failed to connect: {e}")
            return False
    
    def wait_for_authentication(self, timeout: float = 5.0) -> bool:
        """Wait for authentication response from server."""
        if self.auth_event.wait(timeout):
            return self.auth_success
        return False
    
    def disconnect(self, intentional: bool = True):
        """Disconnect from the server."""
        self.intentional_disconnect = intentional
        self.connected = False
        
        if self.connection_manager:
            disconnect_message = Message(MessageType.DISCONNECT, {})
            self.connection_manager.send_message(disconnect_message)
            self.connection_manager.close()
        
        if self.client_socket:
            self.client_socket.close()
        
        self.signals.connection_status_changed.emit(False)
        self.logger.info("Disconnected from server")
    
    def _receive_loop(self):
        """Main receive loop running in separate thread."""
        while self.connected and self.connection_manager and self.connection_manager.is_connected():
            try:
                message = self.connection_manager.receive_message()
                if message is None:
                    break
                
                # Import message handler when needed to avoid circular imports
                from ..handlers.message_handler import MessageHandler
                handler = MessageHandler(self)
                handler.handle_message(message)
                
            except Exception as e:
                self.logger.error(f"Error receiving message: {e}")
                break
        
        self.connected = False
        self.signals.connection_status_changed.emit(False)
        
        if not self.intentional_disconnect:
            self.signals.error_occurred.emit("Connection lost")
    
    def send_message(self, message) -> bool:
        """Send a message to the server."""
        if not self.connected or not self.connection_manager:
            return False
        
        try:
            return self.connection_manager.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
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