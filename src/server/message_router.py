"""
Message router for handling message routing and broadcasting.
"""

import logging
from typing import Dict, Optional
try:
    from ..shared.message_types import Message, MessageType
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared.message_types import Message, MessageType


class MessageRouter:
    """Routes messages to appropriate handlers."""
    
    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger(__name__)
        
        # Message handlers mapping
        self.message_handlers = {
            MessageType.CONNECT: self.handle_connect,
            MessageType.DISCONNECT: self.handle_disconnect,
            MessageType.AUTH_REQUEST: self.handle_auth_request,
            MessageType.PUBLIC_MESSAGE: self.handle_public_message,
            MessageType.PRIVATE_MESSAGE: self.handle_private_message,
            MessageType.USER_LIST_REQUEST: self.handle_user_list_request,
        }
    
    def route_message(self, message: Message, client_handler) -> bool:
        """Route message to appropriate handler."""
        try:
            handler = self.message_handlers.get(message.message_type)
            if handler:
                handler(message, client_handler)
                return True
            else:
                self.logger.warning(f"No handler for message type: {message.message_type}")
                return False
        except Exception as e:
            self.logger.error(f"Error routing message: {e}")
            return False
    
    def handle_connect(self, message: Message, client_handler):
        """Handle client connection."""
        self.logger.info(f"Client {client_handler.client_id} connected")
    
    def handle_disconnect(self, message: Message, client_handler):
        """Handle client disconnection."""
        self.logger.info(f"Client {client_handler.client_id} disconnected")
        client_handler.disconnect()
    
    def handle_auth_request(self, message: Message, client_handler):
        """Handle authentication request."""
        # This is handled directly in ClientHandler
        pass
    
    def handle_public_message(self, message: Message, client_handler):
        """Handle public message broadcasting."""
        # This is handled directly in ClientHandler
        pass
    
    def handle_private_message(self, message: Message, client_handler):
        """Handle private message routing."""
        # This is handled directly in ClientHandler
        pass
    
    def handle_user_list_request(self, message: Message, client_handler):
        """Handle user list request."""
        # This is handled directly in ClientHandler
        pass
