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
    from .crypto_manager import ClientCryptoManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import Message, MessageType, ChatMessage, SystemMessage, UserListMessage
    from shared.protocols import ConnectionManager
    from shared.exceptions import ConnectionError
    from client.crypto_manager import ClientCryptoManager


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
        self.auth_event = threading.Event()  # Event to signal authentication completion
        self.auth_success = False  # Track authentication success
        self.intentional_disconnect = False  # Track if disconnect is intentional
        self.crypto_manager = ClientCryptoManager()  # Cryptographic manager
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def connect(self, username: str) -> bool:
        """Connect to the server."""
        try:
            # Reset authentication state
            self.auth_event.clear()
            self.auth_success = False
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            
            self.connection_manager = ConnectionManager(self.client_socket)
            self.connected = True
            self.username = username
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            # Initialize encryption (but don't send key exchange yet)
            try:
                public_key_pem = self.crypto_manager.initialize_encryption()
                self.logger.info("Encryption initialized, will send key exchange after authentication")
            except Exception as e:
                self.logger.warning(f"Failed to initialize encryption: {e}")
            
            # Send authentication request
            auth_message = Message(MessageType.AUTH_REQUEST, {'username': username})
            print(f"DEBUG: Sending AUTH_REQUEST for username: {username}")
            success = self.connection_manager.send_message(auth_message)
            print(f"DEBUG: AUTH_REQUEST send result: {success}")
            
            self.logger.info(f"Connected to server as {username}")
            # Don't emit connection status yet - wait for auth response
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.error_occurred.emit(f"Failed to connect: {e}")
            return False
    
    def wait_for_authentication(self, timeout: float = 5.0) -> bool:
        """Wait for authentication response from server."""
        print(f"DEBUG: Waiting for authentication (timeout: {timeout}s)")
        
        # Wait for authentication event
        if self.auth_event.wait(timeout):
            print(f"DEBUG: Authentication completed, success: {self.auth_success}")
            return self.auth_success
        else:
            print("DEBUG: Authentication timeout")
            return False
    
    def disconnect(self, intentional: bool = True):
        """Disconnect from the server."""
        self.intentional_disconnect = intentional
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
        print("DEBUG: Receive loop started")
        while self.connected and self.connection_manager and self.connection_manager.is_connected():
            try:
                print("DEBUG: Waiting for message...")
                message = self.connection_manager.receive_message()
                if message is None:
                    print("DEBUG: Received None message, breaking loop")
                    break
                
                print(f"DEBUG: Received message: {message.message_type}")
                self._handle_message(message)
                
            except Exception as e:
                print(f"DEBUG: Exception in receive loop: {e}")
                self.logger.error(f"Error receiving message: {e}")
                break
        
        # Connection lost
        print("DEBUG: Connection lost, setting connected=False")
        self.connected = False
        self.connection_status_changed.emit(False)
        
        # Only emit error if disconnect was not intentional
        if not self.intentional_disconnect:
            self.error_occurred.emit("Connection lost")
    
    def _handle_message(self, message: Message):
        """Handle incoming messages."""
        try:
            print(f"DEBUG: Received message type: {message.message_type}")
            if message.message_type == MessageType.AUTH_RESPONSE:
                # Authentication successful
                print("DEBUG: Received AUTH_RESPONSE message")
                print(f"DEBUG: AUTH_RESPONSE data: {message.data}")
                print("DEBUG: Authentication successful, emitting connection status")
                self.auth_success = True
                self.auth_event.set()  # Signal authentication completion
                self.connection_status_changed.emit(True)
                self.logger.info("Authentication successful")
                
                # Send key exchange after successful authentication
                self._send_key_exchange()
            elif message.message_type == MessageType.PUBLIC_MESSAGE:
                self.message_received.emit(message)
            elif message.message_type == MessageType.PRIVATE_MESSAGE:
                self.message_received.emit(message)
            elif message.message_type == MessageType.SYSTEM_MESSAGE:
                # Check if it's an error message
                system_type = message.data.get('system_message_type', 'info')
                if system_type == 'error':
                    self.connected = False  # Mark as disconnected on error
                    self.auth_success = False
                    self.auth_event.set()  # Signal authentication completion (failed)
                    self.error_occurred.emit(message.data['content'])
                else:
                    self.system_message.emit(message.data['content'])
            elif message.message_type == MessageType.USER_LIST_RESPONSE:
                self.user_list_updated.emit(message.data['users'])
            elif message.message_type == MessageType.ERROR_MESSAGE:
                self.error_occurred.emit(message.data['content'])
            elif message.message_type == MessageType.AES_KEY_EXCHANGE:
                # Handle AES key exchange
                try:
                    from ..shared.message_types import AESKeyMessage
                except ImportError:
                    from shared.message_types import AESKeyMessage
                if isinstance(message, AESKeyMessage):
                    try:
                        self.crypto_manager.setup_aes_encryption(message.encrypted_aes_key)
                        self.logger.info("AES encryption setup completed")
                    except Exception as e:
                        self.logger.error(f"Failed to setup AES encryption: {e}")
            elif message.message_type == MessageType.ENCRYPTED_MESSAGE:
                # Handle encrypted message
                try:
                    from ..shared.message_types import EncryptedMessage
                except ImportError:
                    from shared.message_types import EncryptedMessage
                if isinstance(message, EncryptedMessage):
                    try:
                        self.logger.info(f"📥 CLIENT RECEIVE: Received encrypted message from {message.sender}")
                        self.logger.info(f"📥 CLIENT RECEIVE: Encrypted content: {message.encrypted_content}")
                        self.logger.info(f"📥 CLIENT RECEIVE: Message type: {'Private' if message.is_private else 'Public'}")
                        
                        decrypted_content = self.crypto_manager.decrypt_message(message.encrypted_content)
                        
                        self.logger.info(f"📥 CLIENT RECEIVE: Successfully decrypted message: '{decrypted_content}'")
                        
                        # Create a regular message with decrypted content
                        decrypted_message = ChatMessage(
                            decrypted_content,
                            message.sender,
                            message.recipient,
                            message.is_private
                        )
                        self.message_received.emit(decrypted_message)
                        self.logger.info(f"📥 CLIENT RECEIVE: Emitted decrypted message to GUI")
                    except Exception as e:
                        self.logger.error(f"Failed to decrypt message: {e}")
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def _send_key_exchange(self):
        """Send key exchange after successful authentication."""
        try:
            if self.crypto_manager.has_rsa_keys():
                public_key_pem = self.crypto_manager.get_public_key_pem()
                try:
                    from ..shared.message_types import KeyExchangeMessage
                except ImportError:
                    from shared.message_types import KeyExchangeMessage
                
                key_exchange_message = KeyExchangeMessage(public_key_pem, self.username)
                self.connection_manager.send_message(key_exchange_message)
                self.logger.info("Key exchange sent after authentication")
        except Exception as e:
            self.logger.error(f"Failed to send key exchange: {e}")
    
    def send_public_message(self, content: str) -> bool:
        """Send a public message."""
        if not self.connected or not self.username:
            return False
        
        try:
            self.logger.info(f"📤 CLIENT SEND: Preparing to send public message: '{content}'")
            
            # Check if encryption is available
            if self.crypto_manager.is_ready_for_encryption():
                self.logger.info(f"📤 CLIENT SEND: Encryption enabled, encrypting message")
                # Encrypt the message
                encrypted_content = self.crypto_manager.encrypt_message(content)
                try:
                    from ..shared.message_types import EncryptedMessage
                except ImportError:
                    from shared.message_types import EncryptedMessage
                message = EncryptedMessage(encrypted_content, self.username, is_private=False)
                self.logger.info(f"📤 CLIENT SEND: Sending encrypted public message")
            else:
                self.logger.info(f"📤 CLIENT SEND: Encryption not available, sending plaintext")
                # Send as regular message
                message = ChatMessage(content, self.username, is_private=False)
            
            success = self.connection_manager.send_message(message)
            if success:
                self.logger.info(f"📤 CLIENT SEND: Public message sent successfully")
            else:
                self.logger.error(f"📤 CLIENT SEND: Failed to send public message")
            return success
        except Exception as e:
            self.logger.error(f"Failed to send public message: {e}")
            return False
    
    def send_private_message(self, content: str, recipient: str) -> bool:
        """Send a private message."""
        if not self.connected or not self.username:
            return False
        
        try:
            self.logger.info(f"📤 CLIENT SEND: Preparing to send private message to '{recipient}': '{content}'")
            
            # Check if encryption is available
            if self.crypto_manager.is_ready_for_encryption():
                self.logger.info(f"📤 CLIENT SEND: Encryption enabled, encrypting private message")
                # Encrypt the message
                encrypted_content = self.crypto_manager.encrypt_message(content)
                try:
                    from ..shared.message_types import EncryptedMessage
                except ImportError:
                    from shared.message_types import EncryptedMessage
                message = EncryptedMessage(encrypted_content, self.username, recipient, is_private=True)
                self.logger.info(f"📤 CLIENT SEND: Sending encrypted private message to '{recipient}'")
            else:
                self.logger.info(f"📤 CLIENT SEND: Encryption not available, sending plaintext private message")
                # Send as regular message
                message = ChatMessage(content, self.username, recipient, is_private=True)
            
            success = self.connection_manager.send_message(message)
            if success:
                self.logger.info(f"📤 CLIENT SEND: Private message sent successfully to '{recipient}'")
            else:
                self.logger.error(f"📤 CLIENT SEND: Failed to send private message to '{recipient}'")
            return success
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
