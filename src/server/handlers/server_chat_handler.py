"""
Server chat message handler.
"""

import logging
try:
    from ...shared.message_types import (Message, ChatMessage, SystemMessage, 
                                       UserListMessage, MessageType, EncryptedMessage)
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import (Message, ChatMessage, SystemMessage, 
                                    UserListMessage, MessageType, EncryptedMessage)


class ServerChatHandler:
    """Handles server-side chat functionality."""
    
    def __init__(self, client_connection):
        self.client_connection = client_connection
        self.logger = logging.getLogger(__name__)
    
    def handle_public_message(self, message: Message):
        """Handle public message."""
        self.logger.info(f"Received PUBLIC_MESSAGE from {self.client_connection.username} (authenticated: {self.client_connection.is_authenticated})")
        
        if not self.client_connection.is_authenticated:
            self.logger.warning(f"Rejecting message from unauthenticated client {self.client_connection.client_id}")
            self._send_error_message("Not authenticated")
            return
        
        try:
            content = message.data.get('content', '').strip()
            self.logger.debug(f"Message content: '{content}'")
            
            if not content:
                self.logger.warning("Empty message content, ignoring")
                return
            
            # Create new message with proper formatting
            chat_message = ChatMessage(content, self.client_connection.username, is_private=False)
            self.logger.info(f"Created ChatMessage: {chat_message}")
            
            # Check active clients count
            active_count = len(self.client_connection.server.client_manager.active_clients)
            self.logger.info(f"Server has {active_count} active clients")
            
            # Broadcast to all clients except sender
            self.logger.info(f"Broadcasting message from {self.client_connection.username} (exclude {self.client_connection.client_id})")
            self.client_connection.server.broadcast_message(chat_message, 
                                                          exclude_client_id=self.client_connection.client_id)
            
            self.logger.info(f"Broadcast completed for message from {self.client_connection.username}")
            
        except Exception as e:
            self.logger.error(f"Error handling public message: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def handle_private_message(self, message: Message):
        """Handle private message."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            content = message.data.get('content', '').strip()
            recipient = message.data.get('recipient', '').strip()
            
            if not content or not recipient:
                return
            
            # Find recipient client
            recipient_client = self.client_connection.server.get_client_by_username(recipient)
            if not recipient_client:
                self._send_error_message(f"User {recipient} not found")
                return
            
            # Create private message
            private_message = ChatMessage(content, self.client_connection.username, 
                                        recipient, is_private=True)
            
            # Send to recipient
            recipient_client.send_message(private_message)
            
            self.logger.info(f"Sent private message from {self.client_connection.username} to {recipient}")
            
        except Exception as e:
            self.logger.error(f"Error handling private message: {e}")
    
    def handle_user_list_request(self, message: Message):
        """Handle user list request."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            # Get list of authenticated users
            users = [client.username for client in self.client_connection.server.get_authenticated_clients() 
                    if client.username]
            
            # Send user list response
            user_list_message = UserListMessage(users)
            self.client_connection.send_message(user_list_message)
            
            self.logger.debug(f"Sent user list to {self.client_connection.username}: {users}")
            
        except Exception as e:
            self.logger.error(f"Error handling user list request: {e}")
    
    def handle_encrypted_message(self, message: EncryptedMessage):
        """Handle encrypted message - treat as either public or private based on is_private flag."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            # The server doesn't decrypt - it just forwards encrypted messages
            # Determine if it's public or private based on the message's is_private flag
            if message.is_private and message.recipient:
                # Handle as private encrypted message
                recipient_client = self.client_connection.server.get_client_by_username(message.recipient)
                if not recipient_client:
                    self._send_error_message(f"User {message.recipient} not found")
                    return
                
                # Forward encrypted message to recipient
                recipient_client.send_message(message)
                self.logger.info(f"Forwarded encrypted private message from {self.client_connection.username} to {message.recipient}")
            else:
                # Handle as public encrypted message - broadcast to all except sender
                self.client_connection.server.broadcast_message(message, 
                                                              exclude_client_id=self.client_connection.client_id)
                self.logger.info(f"Broadcasted encrypted public message from {self.client_connection.username}")
            
        except Exception as e:
            self.logger.error(f"Error handling encrypted message: {e}")
    
    def _send_error_message(self, content: str):
        """Send an error message to the client."""
        system_message = SystemMessage(content, "error")
        self.client_connection.send_message(system_message)