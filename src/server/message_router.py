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
                
                # Automatically generate and send shared AES key
                try:
                    encrypted_aes_key = self.server.crypto_manager.encrypt_shared_aes_key_for_client(
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
                # Generate and send shared AES key to client
                encrypted_aes_key = self.server.crypto_manager.encrypt_shared_aes_key_for_client(
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
        """Handle encrypted message - route without decryption."""
        try:
            try:
                from ..shared.message_types import EncryptedMessage
            except ImportError:
                from shared.message_types import EncryptedMessage
            if isinstance(message, EncryptedMessage):
                self.logger.info(f"🔐 ROUTER: Processing encrypted message from {client_handler.username}")
                self.logger.info(f"🔐 SERVER SIDE: Received encrypted message: '{message.encrypted_content}'")
                self.logger.info(f"🔐 SERVER SIDE: Message type: {'Private' if message.is_private else 'Public'}")
                self.logger.info(f"🔐 SERVER SIDE: Routing encrypted message WITHOUT decryption")
                
                # Route the encrypted message directly without decryption
                if message.is_private:
                    self.logger.info(f"🔐 ROUTER: Routing encrypted private message to recipient: {message.recipient}")
                    # Find recipient and send encrypted message directly
                    recipient_client = self.server.get_client_by_username(message.recipient)
                    if not recipient_client:
                        self.logger.error(f"Recipient {message.recipient} not found")
                        return
                    
                    # Send encrypted message directly to recipient
                    recipient_client.send_message(message)
                    self.logger.info(f"🔐 SERVER SIDE: Forwarded encrypted private message to {message.recipient}")
                    self.logger.info(f"🔐 SERVER SIDE: Forwarded encrypted content: '{message.encrypted_content}'")
                else:
                    self.logger.info(f"🔐 ROUTER: Broadcasting encrypted public message")
                    # Broadcast encrypted message to all clients except sender
                    self.server.broadcast_message(message, exclude_client_id=client_handler.client_id)
                    self.logger.info(f"🔐 SERVER SIDE: Broadcasted encrypted public message")
                    self.logger.info(f"🔐 SERVER SIDE: Broadcasted encrypted content: '{message.encrypted_content}'")
        except Exception as e:
            self.logger.error(f"Error handling encrypted message: {e}")
