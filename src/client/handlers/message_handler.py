"""
Main message handler dispatcher.
"""

import logging
from .auth_handler import AuthHandler
from .chat_handler import ChatHandler
from .file_handler import FileHandler

try:
    from ...shared.message_types import MessageType
except ImportError:
    from shared.message_types import MessageType


class MessageHandler:
    """Main message handler that dispatches to specific handlers."""
    
    def __init__(self, client_core):
        self.client_core = client_core
        self.logger = logging.getLogger(__name__)
        
        # Initialize specific handlers
        self.auth_handler = AuthHandler(client_core)
        self.chat_handler = ChatHandler(client_core)
        self.file_handler = FileHandler(client_core)
    
    def handle_message(self, message):
        """Dispatch message to appropriate handler."""
        try:
            self.logger.info(f"Received message type: {message.message_type}")
            
            if message.message_type == MessageType.AUTH_RESPONSE:
                self.auth_handler.handle_auth_response(message)
            elif message.message_type == MessageType.PUBLIC_MESSAGE:
                self.chat_handler.handle_public_message(message)
            elif message.message_type == MessageType.PRIVATE_MESSAGE:
                self.chat_handler.handle_private_message(message)
            elif message.message_type == MessageType.SYSTEM_MESSAGE:
                self.chat_handler.handle_system_message(message)
            elif message.message_type == MessageType.USER_LIST_RESPONSE:
                self.chat_handler.handle_user_list_response(message)
            elif message.message_type == MessageType.ERROR_MESSAGE:
                self.chat_handler.handle_error_message(message)
            elif message.message_type == MessageType.AES_KEY_EXCHANGE:
                self.chat_handler.handle_aes_key_exchange(message)
            elif message.message_type == MessageType.ENCRYPTED_MESSAGE:
                self.chat_handler.handle_encrypted_message(message)
            elif message.message_type == MessageType.FILE_TRANSFER_REQUEST:
                self.file_handler.handle_file_transfer_request(message)
            elif message.message_type == MessageType.FILE_TRANSFER_RESPONSE:
                self.file_handler.handle_file_transfer_response(message)
            elif message.message_type == MessageType.FILE_CHUNK:
                self.file_handler.handle_file_chunk(message)
            elif message.message_type == MessageType.FILE_TRANSFER_COMPLETE:
                self.file_handler.handle_file_transfer_complete(message)
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            self.client_core.signals.error_occurred.emit(f"Error handling message: {e}")