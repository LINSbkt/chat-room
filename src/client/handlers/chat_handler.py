"""
Chat message handler.
"""

import logging
try:
    from ...shared.message_types import (MessageType, ChatMessage, EncryptedMessage, 
                                       AESKeyMessage)
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import (MessageType, ChatMessage, EncryptedMessage, 
                                    AESKeyMessage)


class ChatHandler:
    """Handles chat-related messages."""
    
    def __init__(self, client_core):
        self.client_core = client_core
        self.logger = logging.getLogger(__name__)
    
    def handle_public_message(self, message):
        """Handle public message."""
        self.client_core.signals.message_received.emit(message)
    
    def handle_private_message(self, message):
        """Handle private message."""
        self.client_core.signals.message_received.emit(message)
    
    def handle_system_message(self, message):
        """Handle system message."""
        system_type = message.data.get('system_message_type', 'info')
        content = message.data.get('content', '')
        
        if system_type == 'error':
            self.client_core.connected = False
            self.client_core.auth_success = False
            self.client_core.auth_event.set()
            self.client_core.signals.error_occurred.emit(content)
        else:
            self.client_core.signals.system_message.emit(content)
    
    def handle_user_list_response(self, message):
        """Handle user list response."""
        self.client_core.signals.user_list_updated.emit(message.data['users'])
    
    def handle_error_message(self, message):
        """Handle error message."""
        self.client_core.signals.error_occurred.emit(message.data['content'])
    
    def handle_aes_key_exchange(self, message):
        """Handle AES key exchange."""
        if isinstance(message, AESKeyMessage):
            try:
                self.client_core.crypto_manager.setup_aes_encryption(message.encrypted_aes_key)
                self.logger.info("AES encryption setup completed")
            except Exception as e:
                self.logger.error(f"Failed to setup AES encryption: {e}")
    
    def handle_encrypted_message(self, message):
        """Handle encrypted message."""
        if isinstance(message, EncryptedMessage):
            try:
                self.logger.info(f"📥 CLIENT RECEIVE: Received encrypted message from {message.sender}")
                
                decrypted_content = self.client_core.crypto_manager.decrypt_message(message.encrypted_content)
                self.logger.info(f"📥 CLIENT RECEIVE: Successfully decrypted message: '{decrypted_content}'")
                
                # Create a regular message with decrypted content
                decrypted_message = ChatMessage(
                    decrypted_content,
                    message.sender,
                    message.recipient,
                    message.is_private
                )
                self.client_core.signals.message_received.emit(decrypted_message)
                self.logger.info(f"📥 CLIENT RECEIVE: Emitted decrypted message to GUI")
            except Exception as e:
                self.logger.error(f"Failed to decrypt message: {e}")
    
    def send_public_message(self, content: str) -> bool:
        """Send a public message."""
        if not self.client_core.connected or not self.client_core.username:
            return False
        
        try:
            self.logger.info(f"📤 CLIENT SEND: Preparing to send public message: '{content}'")
            
            # Check if encryption is available
            if self.client_core.crypto_manager.is_ready_for_encryption():
                self.logger.info(f"📤 CLIENT SEND: Encryption enabled, encrypting message")
                encrypted_content = self.client_core.crypto_manager.encrypt_message(content)
                message = EncryptedMessage(encrypted_content, self.client_core.username, is_private=False)
                self.logger.info(f"📤 CLIENT SEND: Sending encrypted public message")
            else:
                self.logger.info(f"📤 CLIENT SEND: Encryption not available, sending plaintext")
                message = ChatMessage(content, self.client_core.username, is_private=False)
            
            success = self.client_core.send_message(message)
            if success:
                self.logger.info(f"📤 CLIENT SEND: Public message sent successfully")
            else:
                self.logger.error(f"📤 CLIENT SEND: Failed to send public message")
            return success
        except Exception as e:
            self.logger.error(f"Failed to send public message: {e}")
            return False
    
    def send_private_message(self, content: str, recipient: str) -> bool:
        """Send a private message."""
        if not self.client_core.connected or not self.client_core.username:
            return False
        
        try:
            self.logger.info(f"📤 CLIENT SEND: Preparing to send private message to '{recipient}': '{content}'")
            
            # Check if encryption is available
            if self.client_core.crypto_manager.is_ready_for_encryption():
                self.logger.info(f"📤 CLIENT SEND: Encryption enabled, encrypting private message")
                encrypted_content = self.client_core.crypto_manager.encrypt_message(content)
                message = EncryptedMessage(encrypted_content, self.client_core.username, recipient, is_private=True)
                self.logger.info(f"📤 CLIENT SEND: Sending encrypted private message to '{recipient}'")
            else:
                self.logger.info(f"📤 CLIENT SEND: Encryption not available, sending plaintext private message")
                message = ChatMessage(content, self.client_core.username, recipient, is_private=True)
            
            success = self.client_core.send_message(message)
            if success:
                self.logger.info(f"📤 CLIENT SEND: Private message sent successfully to '{recipient}'")
            else:
                self.logger.error(f"📤 CLIENT SEND: Failed to send private message to '{recipient}'")
            return success
        except Exception as e:
            self.logger.error(f"Failed to send private message: {e}")
            return False