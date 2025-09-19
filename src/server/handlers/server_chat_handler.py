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
            
            # Store message in server storage for persistence
            self.client_connection.server.store_message(chat_message, "common")
            self.logger.debug(f"Stored public message in server storage")
            
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
            
            # Store private message in server storage for persistence
            # Create context ID for private conversation
            context_id = f"private_{self.client_connection.username}_{recipient}"
            self.client_connection.server.store_message(private_message, context_id)
            self.logger.debug(f"Stored private message in server storage: {context_id}")
            
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
            
            # Send message history after user list (GUI is now fully initialized)
            self.logger.info(f"Sending message history to {self.client_connection.username} after user list request")
            self._send_message_history(self.client_connection.username)
            
        except Exception as e:
            self.logger.error(f"Error handling user list request: {e}")
    
    
    def _send_message_history(self, username: str):
        """Send message history to the user after GUI is initialized."""
        try:
            # Get common chat messages
            common_messages = self.client_connection.server.get_messages("common", limit=50)
            self.logger.info(f"Retrieved {len(common_messages)} common messages for {username}")
            if common_messages:
                self.logger.info(f"Sending {len(common_messages)} common messages to {username}")
                for msg in common_messages:
                    # Create a proper ChatMessage for historical message
                    history_chat_msg = ChatMessage(
                        content=msg['content'],
                        sender=msg['sender'],
                        is_private=False
                    )
                    # Set the original timestamp (override the auto-generated one)
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
                        # For private messages, recipient should be the other user in the conversation
                        if msg['sender'] == username:
                            # This message was sent by the current user, so recipient is the other user
                            recipient = other_user
                        else:
                            # This message was sent to the current user, so recipient is the current user
                            recipient = username
                        
                        history_chat_msg = ChatMessage(
                            content=msg['content'],
                            sender=msg['sender'],
                            recipient=recipient,
                            is_private=True
                        )
                        # Set the original timestamp (override the auto-generated one)
                        history_chat_msg.timestamp = msg['timestamp']
                        # Send as a regular chat message
                        self.logger.info(f"Sending historical private message: {msg['sender']}: {msg['content']}")
                        success = self.client_connection.send_message(history_chat_msg)
                        self.logger.info(f"Private message send result: {success}")
            
            # Get file transfer history and send as system messages
            file_transfers = self.client_connection.server.get_file_transfers(username, limit=10)
            if file_transfers:
                self.logger.info(f"Sending {len(file_transfers)} file transfer records to {username}")
                for transfer in file_transfers:
                    history_msg = f"[{transfer['timestamp'].strftime('%H:%M')}] File: {transfer['filename']} ({transfer['status']})"
                    self._send_system_message(history_msg)
            
        except Exception as e:
            self.logger.error(f"Error sending message history to {username}: {e}")
    
    def _send_system_message(self, content: str):
        """Send a system message to the client."""
        system_message = SystemMessage(content)
        self.client_connection.send_message(system_message)
    
    def _send_error_message(self, content: str):
        """Send an error message to the client."""
        system_message = SystemMessage(content, "error")
        self.client_connection.send_message(system_message)