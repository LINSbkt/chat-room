"""
Message broadcasting management.
"""

import logging
from typing import Optional
try:
    from ...shared.message_types import SystemMessage, UserListMessage
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import SystemMessage, UserListMessage


class BroadcastManager:
    """Manages broadcasting messages to clients."""
    
    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger(__name__)
    
    def broadcast_message(self, message, exclude_client_id: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        sent_count = 0
        total_clients = len(self.server.client_manager.active_clients)
        
        self.logger.debug(f"Broadcasting message to {total_clients} clients (excluding {exclude_client_id})")
        
        for client_id, client_handler in self.server.client_manager.active_clients.items():
            if client_id != exclude_client_id:
                try:
                    success = client_handler.send_message(message)
                    if success:
                        sent_count += 1
                        self.logger.debug(f"✓ Successfully sent message to client {client_id} ({client_handler.username})")
                    else:
                        self.logger.warning(f"✗ Failed to send message to client {client_id} ({client_handler.username}) - send_message returned False")
                except Exception as e:
                    self.logger.error(f"✗ Exception sending message to client {client_id} ({client_handler.username}): {e}")
        
        self.logger.info(f"Broadcast complete: {sent_count}/{total_clients - (1 if exclude_client_id else 0)} messages sent")
    
    def send_private_message(self, message, recipient_username: str):
        """Send a private message to a specific user."""
        recipient = self.server.client_manager.get_client_by_username(recipient_username)
        if recipient:
            try:
                recipient.send_message(message)
                return True
            except Exception as e:
                self.logger.error(f"Failed to send private message to {recipient_username}: {e}")
        return False
    
    def broadcast_system_message(self, content: str):
        """Broadcast a system message to all clients."""
        system_message = SystemMessage(content, "info")
        self.broadcast_message(system_message)
    
    def broadcast_user_list(self):
        """Broadcast updated user list to all clients."""
        users = self.server.client_manager.get_user_list()
        user_list_message = UserListMessage(users)
        self.broadcast_message(user_list_message)
    
    def broadcast_file_transfer_request(self, message, exclude_user: Optional[str] = None):
        """Broadcast a file transfer request to all clients except the sender."""
        success_count = 0
        total_clients = 0
        
        self.logger.info(f"📤 Broadcasting file transfer request, excluding user: {exclude_user}")
        
        for client_handler in self.server.client_manager.active_clients.values():
            if client_handler.username:
                if client_handler.username != exclude_user:
                    total_clients += 1
                    self.logger.debug(f"📤 Sending file transfer request to {client_handler.username}")
                    if client_handler.send_message(message):
                        success_count += 1
                else:
                    self.logger.debug(f"📤 Excluding sender {client_handler.username} from file transfer request")
        
        self.logger.info(f"📤 Broadcasted file transfer request to {success_count}/{total_clients} clients (excluded: {exclude_user})")
        return success_count > 0