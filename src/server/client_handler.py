"""
Client handler for managing individual client connections.
"""

import logging
import threading
from typing import Optional
try:
    from ..shared.message_types import Message, MessageType, SystemMessage, ChatMessage
    from ..shared.protocols import ConnectionManager
    from ..shared.exceptions import AuthenticationError, ConnectionError
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared.message_types import Message, MessageType, SystemMessage, ChatMessage
    from shared.protocols import ConnectionManager
    from shared.exceptions import AuthenticationError, ConnectionError


class ClientHandler:
    """Handles individual client connections."""
    
    def __init__(self, client_socket, client_address, server):
        self.client_socket = client_socket
        self.client_address = client_address
        self.server = server
        self.client_id = self._generate_client_id()
        self.username: Optional[str] = None
        self.is_authenticated = False
        self.connected = True
        self.connection_manager = ConnectionManager(client_socket)
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.client_id}")
    
    def _generate_client_id(self) -> str:
        """Generate a unique client ID."""
        import uuid
        return str(uuid.uuid4())
    
    def run(self):
        """Main client handling loop."""
        try:
            self.logger.info(f"Client handler started for {self.client_address}")
            
            while self.connected and self.connection_manager.is_connected():
                try:
                    message = self.connection_manager.receive_message()
                    if message is None:
                        break
                    
                    self.handle_message(message)
                    
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
        finally:
            self.disconnect()
    
    def handle_message(self, message: Message):
        """Process incoming messages."""
        try:
            self.logger.debug(f"Received message: {message.message_type}")
            
            if message.message_type == MessageType.CONNECT:
                self.handle_connect(message)
            elif message.message_type == MessageType.AUTH_REQUEST:
                self.handle_auth_request(message)
            elif message.message_type == MessageType.PUBLIC_MESSAGE:
                self.handle_public_message(message)
            elif message.message_type == MessageType.PRIVATE_MESSAGE:
                self.handle_private_message(message)
            elif message.message_type == MessageType.USER_LIST_REQUEST:
                self.handle_user_list_request(message)
            elif message.message_type == MessageType.DISCONNECT:
                self.handle_disconnect(message)
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self.send_error_message(f"Error processing message: {e}")
    
    def handle_connect(self, message: Message):
        """Handle client connection."""
        self.logger.info(f"Client {self.client_id} connected")
        self.send_system_message("Connected to chat server")
    
    def handle_auth_request(self, message: Message):
        """Handle authentication request."""
        try:
            username = message.data.get('username', '').strip()
            
            if not username:
                self.send_error_message("Username cannot be empty")
                return
            
            if self.server.is_username_taken(username):
                self.send_error_message("Username already taken")
                return
            
            # Set username and authenticate
            self.username = username
            self.is_authenticated = True
            
            # Add client to server
            self.server.add_client(self)
            
            # Send authentication response
            auth_response = Message(MessageType.AUTH_RESPONSE, {'username': username, 'status': 'success'})
            print(f"DEBUG: Sending AUTH_RESPONSE for user {username}")
            self.send_message(auth_response)
            
            self.send_system_message(f"Welcome {username}!")
            self.logger.info(f"Client {self.client_id} authenticated as {username}")
            
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            self.send_error_message("Authentication failed")
    
    def handle_public_message(self, message: Message):
        """Handle public message."""
        if not self.is_authenticated:
            self.send_error_message("Not authenticated")
            return
        
        try:
            content = message.data.get('content', '').strip()
            if not content:
                return
            
            # Create new message with proper formatting
            chat_message = ChatMessage(content, self.username, is_private=False)
            
            # Broadcast to all clients except sender
            self.server.broadcast_message(chat_message, exclude_client_id=self.client_id)
            
            self.logger.info(f"Broadcasted public message from {self.username}")
            
        except Exception as e:
            self.logger.error(f"Error handling public message: {e}")
    
    def handle_private_message(self, message: Message):
        """Handle private message."""
        if not self.is_authenticated:
            self.send_error_message("Not authenticated")
            return
        
        try:
            content = message.data.get('content', '').strip()
            recipient = message.data.get('recipient', '').strip()
            
            if not content or not recipient:
                self.send_error_message("Invalid private message format")
                return
            
            # Create private message
            private_message = ChatMessage(content, self.username, recipient, is_private=True)
            
            # Send to recipient
            success = self.server.send_private_message(private_message, recipient)
            
            if success:
                self.logger.info(f"Sent private message from {self.username} to {recipient}")
            else:
                self.send_error_message(f"User {recipient} not found")
            
        except Exception as e:
            self.logger.error(f"Error handling private message: {e}")
    
    def handle_user_list_request(self, message: Message):
        """Handle user list request."""
        if not self.is_authenticated:
            self.send_error_message("Not authenticated")
            return
        
        try:
            try:
                from ..shared.message_types import UserListMessage
            except ImportError:
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
                from shared.message_types import UserListMessage
            
            users = self.server.get_user_list()
            user_list_message = UserListMessage(users)
            self.send_message(user_list_message)
            
        except Exception as e:
            self.logger.error(f"Error handling user list request: {e}")
    
    def handle_disconnect(self, message: Message):
        """Handle client disconnect."""
        self.logger.info(f"Client {self.client_id} requested disconnect")
        self.disconnect()
    
    def send_message(self, message: Message) -> bool:
        """Send a message to the client."""
        try:
            return self.connection_manager.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    def send_system_message(self, content: str):
        """Send a system message to the client."""
        system_message = SystemMessage(content, "info")
        self.send_message(system_message)
    
    def send_error_message(self, content: str):
        """Send an error message to the client."""
        error_message = SystemMessage(content, "error")
        self.send_message(error_message)
    
    def disconnect(self):
        """Handle client disconnection."""
        if self.connected:
            self.connected = False
            
            if self.is_authenticated and self.username:
                self.server.remove_client(self.client_id)
            
            self.connection_manager.close()
            self.logger.info(f"Client {self.client_id} disconnected")
