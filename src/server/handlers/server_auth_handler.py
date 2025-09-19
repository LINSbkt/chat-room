"""
Server authentication handler.
"""

import logging
import time
try:
    from ...shared.message_types import Message, MessageType
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import Message, MessageType


class ServerAuthHandler:
    """Handles server-side authentication logic."""
    
    def __init__(self, client_connection):
        self.client_connection = client_connection
        self.logger = logging.getLogger(__name__)
    
    def handle_connect(self, message: Message):
        """Handle client connection."""
        self.logger.info(f"Client {self.client_connection.client_id} connected")
        self._send_system_message("Connected to chat server")
    
    def handle_auth_request(self, message: Message):
        """Handle authentication request."""
        try:
            self.logger.info(f"Handling AUTH_REQUEST from client {self.client_connection.client_id}")
            username = message.data.get('username', '').strip()
            self.logger.info(f"Username received: '{username}'")
            
            # Use AuthManager for validation and authentication
            if not self.client_connection.server.auth_manager.validate_username(username):
                self.logger.info(f"Username validation failed for '{username}'")
                if not username:
                    self._send_error_message("Username cannot be empty")
                elif len(username) > 20:
                    self._send_error_message("Username too long (max 20 characters)")
                elif not username.replace(' ', '').replace('_', '').replace('-', '').isalnum():
                    self._send_error_message("Username contains invalid characters")
                else:
                    self._send_error_message("Username already taken")
                return
            
            self.logger.info(f"Username validation passed for '{username}'")
            
            # Authenticate user through AuthManager
            if not self.client_connection.server.auth_manager.authenticate_user(username, self.client_connection.client_id):
                self.logger.info(f"AuthManager authentication failed for '{username}'")
                self._send_error_message("Authentication failed")
                return
            
            self.logger.info(f"AuthManager authentication successful for '{username}'")
            
            # Set username and authenticate
            self.client_connection.username = username
            self.client_connection.is_authenticated = True
            
            # Add client to server
            self.client_connection.server.add_client(self.client_connection)
            self.logger.info(f"Client {self.client_connection.client_id} added to server")
            
            # Send authentication response FIRST
            auth_response = Message(MessageType.AUTH_RESPONSE, {'username': username, 'status': 'success'})
            self.logger.info(f"Sending AUTH_RESPONSE for user {username}")
            success = self.client_connection.send_message(auth_response)
            self.logger.info(f"AUTH_RESPONSE send result: {success}")
            
            if not success:
                self.logger.error("Failed to send AUTH_RESPONSE!")
                self._send_error_message("Failed to send authentication response")
                return
            
            # Wait a moment to ensure AUTH_RESPONSE is sent before other messages
            time.sleep(0.1)
            
            self._send_system_message(f"Welcome {username}!")
            
            # Message history will be sent when user requests user list (GUI fully initialized)
            
            self.logger.info(f"Client {self.client_connection.client_id} authenticated as {username}")
            self.logger.info(f"Authentication process completed for {username}")
            
        except Exception as e:
            self.logger.error(f"Exception in handle_auth_request: {e}")
            self._send_error_message("Authentication failed")
    
    def handle_disconnect(self, message: Message):
        """Handle client disconnect."""
        self.logger.info(f"Client {self.client_connection.client_id} requested disconnect")
        self.client_connection.disconnect()
    
    def _send_system_message(self, content: str):
        """Send a system message to the client."""
        try:
            from ...shared.message_types import SystemMessage
        except ImportError:
            from shared.message_types import SystemMessage
        
        system_message = SystemMessage(content)
        self.client_connection.send_message(system_message)
    
    def _send_message_history(self, username: str):
        """Send message history to the user after login."""
        try:
            # Get common chat messages
            common_messages = self.client_connection.server.get_messages("common", limit=50)
            self.logger.info(f"Retrieved {len(common_messages)} common messages for {username}")
            if common_messages:
                self.logger.info(f"Sending {len(common_messages)} common messages to {username}")
                for msg in common_messages:
                    # Create a proper ChatMessage for historical message
                    from ...shared.message_types import ChatMessage
                    history_chat_msg = ChatMessage(
                        content=msg['content'],
                        sender=msg['sender'],
                        is_private=False
                    )
                    # Set the original timestamp
                    history_chat_msg.timestamp = msg['timestamp']
                    # Send as a regular chat message
                    self.logger.info(f"Sending historical message: {msg['sender']}: {msg['content']}")
                    success = self.client_connection.send_message(history_chat_msg)
                    self.logger.info(f"Message send result: {success}")
            
            # Get private messages for this user
            private_contexts = self.client_connection.server.get_private_contexts_for_user(username)
            for context_id in private_contexts:
                private_messages = self.client_connection.server.get_messages(context_id, limit=20)
                if private_messages:
                    # Extract the other user from context_id
                    # Context ID format: "private_user1_user2"
                    parts = context_id.split("_")
                    if len(parts) >= 3:
                        user1, user2 = parts[1], parts[2]
                        other_user = user2 if user1 == username else user1
                    else:
                        other_user = "unknown"
                    self.logger.info(f"Sending {len(private_messages)} private messages with {other_user} to {username}")
                    for msg in private_messages:
                        # Create a proper ChatMessage for historical private message
                        from ...shared.message_types import ChatMessage
                        history_chat_msg = ChatMessage(
                            content=msg['content'],
                            sender=msg['sender'],
                            recipient=other_user if msg['sender'] != username else username,
                            is_private=True
                        )
                        # Set the original timestamp
                        history_chat_msg.timestamp = msg['timestamp']
                        # Send as a regular chat message
                        self.client_connection.send_message(history_chat_msg)
            
            # Get file transfer history and send as system messages
            file_transfers = self.client_connection.server.get_file_transfers(username, limit=10)
            if file_transfers:
                self.logger.info(f"Sending {len(file_transfers)} file transfer records to {username}")
                for transfer in file_transfers:
                    history_msg = f"[{transfer['timestamp'].strftime('%H:%M')}] File: {transfer['filename']} ({transfer['status']})"
                    self._send_system_message(history_msg)
            
        except Exception as e:
            self.logger.error(f"Error sending message history to {username}: {e}")
    
    def _send_error_message(self, content: str):
        """Send an error message to the client."""
        system_message = self._create_error_system_message(content)
        self.client_connection.send_message(system_message)
    
    def _create_error_system_message(self, content: str):
        """Create an error system message."""
        try:
            from ...shared.message_types import SystemMessage
        except ImportError:
            from shared.message_types import SystemMessage
        
        return SystemMessage(content, "error")