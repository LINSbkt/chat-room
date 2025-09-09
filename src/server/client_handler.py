"""
Client handler for managing individual client connections.
"""

import logging
import threading
from typing import Optional
try:
    from ..shared.message_types import (Message, MessageType, SystemMessage, ChatMessage,
                                      FileTransferRequest, FileTransferResponse, 
                                      FileChunk, FileTransferComplete)
    from ..shared.protocols import ConnectionManager
    from ..shared.exceptions import AuthenticationError, ConnectionError
    from ..shared.file_transfer_manager import FileTransferManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared.message_types import (Message, MessageType, SystemMessage, ChatMessage,
                                    FileTransferRequest, FileTransferResponse, 
                                    FileChunk, FileTransferComplete)
    from shared.protocols import ConnectionManager
    from shared.exceptions import AuthenticationError, ConnectionError
    from shared.file_transfer_manager import FileTransferManager


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
        self.file_transfer_manager = FileTransferManager()
        
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
            # Route all messages through the message router first
            if self.server.message_router.route_message(message, self):
                return  # Message was handled by router
            # Fallback to direct handling for messages not handled by router
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
            elif message.message_type == MessageType.FILE_TRANSFER_REQUEST:
                self.handle_file_transfer_request(message)
            elif message.message_type == MessageType.FILE_TRANSFER_RESPONSE:
                self.handle_file_transfer_response(message)
            elif message.message_type == MessageType.FILE_CHUNK:
                self.handle_file_chunk(message)
            elif message.message_type == MessageType.FILE_TRANSFER_COMPLETE:
                self.handle_file_transfer_complete(message)
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
            print(f"DEBUG: Handling AUTH_REQUEST from client {self.client_id}")
            username = message.data.get('username', '').strip()
            print(f"DEBUG: Username received: '{username}'")
            
            # Use AuthManager for validation and authentication
            if not self.server.auth_manager.validate_username(username):
                print(f"DEBUG: Username validation failed for '{username}'")
                if not username:
                    self.send_error_message("Username cannot be empty")
                elif len(username) > 20:
                    self.send_error_message("Username too long (max 20 characters)")
                elif not username.replace(' ', '').replace('_', '').replace('-', '').isalnum():
                    self.send_error_message("Username contains invalid characters")
                else:
                    self.send_error_message("Username already taken")
                return
            
            print(f"DEBUG: Username validation passed for '{username}'")
            
            # Authenticate user through AuthManager
            if not self.server.auth_manager.authenticate_user(username, self.client_id):
                print(f"DEBUG: AuthManager authentication failed for '{username}'")
                self.send_error_message("Authentication failed")
                return
            
            print(f"DEBUG: AuthManager authentication successful for '{username}'")
            
            # Set username and authenticate
            self.username = username
            self.is_authenticated = True
            
            # Add client to server
            self.server.add_client(self)
            print(f"DEBUG: Client {self.client_id} added to server")
            
            # Send authentication response FIRST
            auth_response = Message(MessageType.AUTH_RESPONSE, {'username': username, 'status': 'success'})
            print(f"DEBUG: Sending AUTH_RESPONSE for user {username}")
            success = self.send_message(auth_response)
            print(f"DEBUG: AUTH_RESPONSE send result: {success}")
            
            if not success:
                print(f"DEBUG: Failed to send AUTH_RESPONSE!")
                self.send_error_message("Failed to send authentication response")
                return
            
            # Wait a moment to ensure AUTH_RESPONSE is sent before other messages
            import time
            time.sleep(0.1)
            
            self.send_system_message(f"Welcome {username}!")
            self.logger.info(f"Client {self.client_id} authenticated as {username}")
            print(f"DEBUG: Authentication process completed for {username}")
            
        except Exception as e:
            print(f"DEBUG: Exception in handle_auth_request: {e}")
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
            print(f"DEBUG: Handling private message from {self.username}")
            print(f"DEBUG: Message data: {message.data}")
            print(f"DEBUG: Message recipient attribute: {message.recipient}")
            
            content = message.data.get('content', '').strip()
            recipient = message.data.get('recipient', '').strip()
            
            # Fallback to message.recipient if not in data
            if not recipient and hasattr(message, 'recipient'):
                recipient = message.recipient
            
            print(f"DEBUG: Extracted content: '{content}', recipient: '{recipient}'")
            
            if not content or not recipient:
                print(f"DEBUG: Invalid format - content: '{content}', recipient: '{recipient}'")
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
            print(f"DEBUG: Exception in handle_private_message: {e}")
    
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
    
    def handle_file_transfer_request(self, message: FileTransferRequest):
        """Handle file transfer request."""
        if not self.is_authenticated:
            self.send_error_message("Not authenticated")
            return
        
        try:
            self.logger.info(f"📤 File transfer request from {self.username}: {message.filename} ({message.file_size} bytes) to {message.recipient}")
            
            # Handle global file transfers
            if message.recipient == "GLOBAL":
                # Broadcast to all connected users except sender
                success = self.server.broadcast_file_transfer_request(message, exclude_user=self.username)
                if success:
                    self.logger.info(f"📤 Broadcasted file transfer request to all users")
                else:
                    # Check if there are any other users to send to
                    other_users = [client.username for client in self.server.active_clients.values() 
                                 if client.username and client.username != self.username]
                    if not other_users:
                        self.logger.info(f"📤 No other users online to receive file transfer")
                        # Don't send error message if no other users are online
                    else:
                        self.send_error_message("Failed to broadcast file transfer request")
            else:
                # Handle private file transfers
                recipient_handler = self.server.get_client_by_username(message.recipient)
                if not recipient_handler:
                    self.send_error_message(f"User {message.recipient} not found")
                    return
                
                # Forward the request to the recipient
                success = recipient_handler.send_message(message)
                if success:
                    # Track the file transfer
                    transfer_id = message.transfer_id
                    if transfer_id:
                        self.server.active_file_transfers[transfer_id] = {
                            'sender': self.username,
                            'recipient': message.recipient
                        }
                        self.logger.info(f"📤 Forwarded file transfer request to {message.recipient}, tracking transfer {transfer_id}")
                    else:
                        self.logger.info(f"📤 Forwarded file transfer request to {message.recipient}")
                else:
                    self.send_error_message("Failed to send file transfer request")
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer request: {e}")
            self.send_error_message("Error processing file transfer request")
    
    def handle_file_transfer_response(self, message: FileTransferResponse):
        """Handle file transfer response (accept/decline)."""
        if not self.is_authenticated:
            self.send_error_message("Not authenticated")
            return
        
        try:
            self.logger.info(f"📥 File transfer response from {self.username}: {'accepted' if message.accepted else 'declined'}")
            
            # Find the original sender and forward the response
            # We need to track this through the server's file transfer system
            success = self.server.forward_file_transfer_response(message, self.username)
            if not success:
                # Don't send error message that causes disconnection
                # Just log the warning - the transfer might have already completed or been cancelled
                self.logger.warning(f"Could not forward file transfer response for transfer {message.transfer_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer response: {e}")
            self.send_error_message("Error processing file transfer response")
    
    def handle_file_chunk(self, message: FileChunk):
        """Handle file chunk."""
        if not self.is_authenticated:
            self.send_error_message("Not authenticated")
            return
        
        try:
            self.logger.debug(f"📦 Received file chunk {message.chunk_index + 1}/{message.total_chunks} for transfer {message.transfer_id}")
            
            # Forward the chunk to the recipient
            success = self.server.forward_file_chunk(message, self.username)
            if not success:
                self.send_error_message("Failed to forward file chunk")
                
        except Exception as e:
            self.logger.error(f"Error handling file chunk: {e}")
            self.send_error_message("Error processing file chunk")
    
    def handle_file_transfer_complete(self, message: FileTransferComplete):
        """Handle file transfer completion."""
        if not self.is_authenticated:
            self.send_error_message("Not authenticated")
            return
        
        try:
            status = "completed successfully" if message.success else "failed"
            self.logger.info(f"✅ File transfer {message.transfer_id} {status}")
            
            # Forward the completion message
            success = self.server.forward_file_transfer_complete(message, self.username)
            if not success:
                self.send_error_message("Failed to process file transfer completion")
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer completion: {e}")
            self.send_error_message("Error processing file transfer completion")
    
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
                # Remove from AuthManager
                self.server.auth_manager.disconnect_user(self.client_id)
                self.server.remove_client(self.client_id)
            
            self.connection_manager.close()
            self.logger.info(f"Client {self.client_id} disconnected")
