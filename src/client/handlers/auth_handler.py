"""
Authentication message handler.
"""

import logging
try:
    from ...shared.message_types import MessageType, KeyExchangeMessage
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import MessageType, KeyExchangeMessage


class AuthHandler:
    """Handles authentication-related messages."""
    
    def __init__(self, client_core):
        self.client_core = client_core
        self.logger = logging.getLogger(__name__)
    
    def handle_auth_response(self, message):
        """Handle authentication response."""
        self.logger.info("Received AUTH_RESPONSE message")
        
        if message.data.get('status') == 'success':
            self.logger.info("Authentication successful")
            self.client_core.auth_success = True
            self.client_core.auth_event.set()
            self.client_core.signals.connection_status_changed.emit(True)
            
            # Send key exchange after successful authentication
            self._send_key_exchange()
            
            # Request file list after authentication
            self._request_file_list()
        else:
            self.logger.info("Authentication failed - status not success")
            self.client_core.auth_success = False
            self.client_core.auth_event.set()
            self.client_core.signals.error_occurred.emit("Authentication failed")
    
    def _send_key_exchange(self):
        """Send key exchange after successful authentication."""
        try:
            if self.client_core.crypto_manager.has_rsa_keys():
                public_key_pem = self.client_core.crypto_manager.get_public_key_pem()
                key_exchange_message = KeyExchangeMessage(public_key_pem, self.client_core.username)
                self.client_core.connection_manager.send_message(key_exchange_message)
                self.logger.info("Key exchange sent after authentication")
        except Exception as e:
            self.logger.error(f"Failed to send key exchange: {e}")
    
    def _request_file_list(self):
        """Request file list after successful authentication."""
        try:
            # Import here to avoid circular imports
            from .file_handler import FileHandler
            file_handler = FileHandler(self.client_core)
            file_handler.request_file_list()
        except Exception as e:
            self.logger.error(f"Failed to request file list: {e}")