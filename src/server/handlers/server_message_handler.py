"""
Main server message handler dispatcher.
"""

import logging
from .server_auth_handler import ServerAuthHandler
from .server_chat_handler import ServerChatHandler
from .server_file_handler import ServerFileHandler

try:
    from ...shared.message_types import MessageType
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import MessageType


class ServerMessageHandler:
    """Main server message handler that dispatches to specific handlers."""
    
    def __init__(self, client_connection):
        self.client_connection = client_connection
        self.logger = logging.getLogger(__name__)
        
        # Initialize specific handlers
        self.auth_handler = ServerAuthHandler(client_connection)
        self.chat_handler = ServerChatHandler(client_connection)
        self.file_handler = ServerFileHandler(client_connection)
    
    def handle_message(self, message):
        """Dispatch message to appropriate handler."""
        try:
            self.logger.debug(f"Received message: {message.message_type}")
            
            # Route all messages through the message router first
            if self.client_connection.server.message_router.route_message(message, self.client_connection):
                return  # Message was handled by router
            
            # Fallback to direct handling for messages not handled by router
            if message.message_type == MessageType.CONNECT:
                self.auth_handler.handle_connect(message)
            elif message.message_type == MessageType.AUTH_REQUEST:
                self.auth_handler.handle_auth_request(message)
            elif message.message_type == MessageType.PUBLIC_MESSAGE:
                self.chat_handler.handle_public_message(message)
            elif message.message_type == MessageType.PRIVATE_MESSAGE:
                self.chat_handler.handle_private_message(message)
            elif message.message_type == MessageType.ENCRYPTED_MESSAGE:
                self.chat_handler.handle_encrypted_message(message)
            elif message.message_type == MessageType.USER_LIST_REQUEST:
                self.chat_handler.handle_user_list_request(message)
            elif message.message_type == MessageType.FILE_TRANSFER_REQUEST:
                self.file_handler.handle_file_transfer_request(message)
            elif message.message_type == MessageType.FILE_TRANSFER_RESPONSE:
                self.file_handler.handle_file_transfer_response(message)
            elif message.message_type == MessageType.FILE_CHUNK:
                self.file_handler.handle_file_chunk(message)
            elif message.message_type == MessageType.FILE_TRANSFER_COMPLETE:
                self.file_handler.handle_file_transfer_complete(message)
            elif message.message_type == MessageType.DISCONNECT:
                self.auth_handler.handle_disconnect(message)
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            self._send_error_message(f"Error processing message: {e}")
    
    def _send_error_message(self, content: str):
        """Send an error message to the client."""
        try:
            from ...shared.message_types import SystemMessage
        except ImportError:
            from shared.message_types import SystemMessage
        
        system_message = SystemMessage(content, "error")
        self.client_connection.send_message(system_message)