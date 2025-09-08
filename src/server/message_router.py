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
            # AUTH_REQUEST is handled directly in ClientHandler
            # MessageType.AUTH_REQUEST: self.handle_auth_request,
            # PUBLIC_MESSAGE and PRIVATE_MESSAGE are handled directly in ClientHandler
            # MessageType.PUBLIC_MESSAGE: self.handle_public_message,
            # MessageType.PRIVATE_MESSAGE: self.handle_private_message,
            # USER_LIST_REQUEST is handled directly in ClientHandler
            # MessageType.USER_LIST_REQUEST: self.handle_user_list_request,
            # FILE_TRANSFER_REQUEST is handled directly in ClientHandler
            # MessageType.FILE_TRANSFER_REQUEST: self.handle_file_transfer_request,
            MessageType.KEY_EXCHANGE_REQUEST: self.handle_key_exchange_request,
            MessageType.AES_KEY_EXCHANGE: self.handle_aes_key_exchange,
            MessageType.ENCRYPTED_MESSAGE: self.handle_encrypted_message,
        }
    
    def route_message(self, message: Message, client_handler) -> bool:
        """Route message to appropriate handler."""
        try:
            handler = self.message_handlers.get(message.message_type)
            if handler:
                handler(message, client_handler)
                return True
            else:
                # Don't log warning for messages handled directly by client handler
                expected_direct_handlers = {
                    MessageType.AUTH_REQUEST,
                    MessageType.AUTH_RESPONSE,
                    MessageType.PUBLIC_MESSAGE,
                    MessageType.PRIVATE_MESSAGE,
                    MessageType.USER_LIST_REQUEST,
                    MessageType.FILE_TRANSFER_REQUEST,
                    MessageType.FILE_TRANSFER_RESPONSE,
                    MessageType.FILE_CHUNK,
                    MessageType.FILE_TRANSFER_COMPLETE
                }
                if message.message_type not in expected_direct_handlers:
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
    
    
    
    def handle_key_exchange_request(self, message: Message, client_handler):
        """Handle RSA key exchange request."""
        try:
            try:
                from ..shared.message_types import KeyExchangeMessage
            except ImportError:
                from shared.message_types import KeyExchangeMessage
            if isinstance(message, KeyExchangeMessage):
                # Store the client's public key
                self.server.crypto_manager.add_client_public_key(
                    client_handler.username, 
                    message.public_key
                )
                self.logger.info(f"Stored public key for client: {client_handler.username}")
                
                # Automatically generate and send AES key
                try:
                    encrypted_aes_key = self.server.crypto_manager.generate_and_encrypt_aes_key(
                        client_handler.username
                    )
                    
                    # Send encrypted AES key back to client
                    try:
                        from ..shared.message_types import AESKeyMessage
                    except ImportError:
                        from shared.message_types import AESKeyMessage
                    
                    aes_key_message = AESKeyMessage(
                        encrypted_aes_key, 
                        "server", 
                        client_handler.username
                    )
                    
                    success = client_handler.send_message(aes_key_message)
                    self.logger.info(f"Sent encrypted AES key to client: {client_handler.username}")
                except Exception as e:
                    self.logger.error(f"Failed to send AES key to {client_handler.username}: {e}")
        except Exception as e:
            self.logger.error(f"Error handling key exchange request: {e}")
    
    def handle_aes_key_exchange(self, message: Message, client_handler):
        """Handle AES key exchange."""
        try:
            try:
                from ..shared.message_types import AESKeyMessage
            except ImportError:
                from shared.message_types import AESKeyMessage
            if isinstance(message, AESKeyMessage):
                # Generate and send AES key to client
                encrypted_aes_key = self.server.crypto_manager.generate_and_encrypt_aes_key(
                    client_handler.username
                )
                
                # Send encrypted AES key back to client
                aes_key_message = AESKeyMessage(
                    encrypted_aes_key, 
                    "server", 
                    client_handler.username
                )
                client_handler.send_message(aes_key_message)
                self.logger.info(f"Sent encrypted AES key to client: {client_handler.username}")
        except Exception as e:
            self.logger.error(f"Error handling AES key exchange: {e}")
    
    def handle_encrypted_message(self, message: Message, client_handler):
        """Handle encrypted message."""
        try:
            try:
                from ..shared.message_types import EncryptedMessage, ChatMessage
            except ImportError:
                from shared.message_types import EncryptedMessage, ChatMessage
            if isinstance(message, EncryptedMessage):
                self.logger.info(f"🔐 ROUTER: Processing encrypted message from {client_handler.username}")
                self.logger.info(f"🔐 ROUTER: Encrypted content: {message.encrypted_content}")
                self.logger.info(f"🔐 ROUTER: Message type: {'Private' if message.is_private else 'Public'}")
                
                # Decrypt the message
                decrypted_content = self.server.crypto_manager.decrypt_message_from_client(
                    message.encrypted_content, 
                    client_handler.username
                )
                
                # Create a regular message with decrypted content
                decrypted_message = ChatMessage(
                    decrypted_content,
                    client_handler.username,
                    message.recipient,
                    message.is_private
                )
                
                self.logger.info(f"🔐 ROUTER: Decrypted message: '{decrypted_content}'")
                
                # Route the decrypted message normally through client handler
                if message.is_private:
                    self.logger.info(f"🔐 ROUTER: Routing decrypted private message to recipient: {message.recipient}")
                    client_handler.handle_private_message(decrypted_message)
                else:
                    self.logger.info(f"🔐 ROUTER: Routing decrypted public message for broadcast")
                    client_handler.handle_public_message(decrypted_message)
        except Exception as e:
            self.logger.error(f"Error handling encrypted message: {e}")
