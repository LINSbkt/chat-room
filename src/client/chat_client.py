"""
Main chat client implementation - refactored to use modular structure.
"""

from .core.client_core import ClientCore
from .handlers.chat_handler import ChatHandler
from .handlers.file_handler import FileHandler


class ChatClient:
    """Main chat client class - now a facade over modular components."""
    
    def __init__(self, server_host: str = 'localhost', server_port: int = 8888):
        # Initialize core functionality
        self.core = ClientCore(server_host, server_port)
        
        # Initialize handlers
        self.chat_handler = ChatHandler(self.core)
        self.file_handler = FileHandler(self.core)
        
        # Expose signals for backward compatibility
        self.message_received = self.core.signals.message_received
        self.user_list_updated = self.core.signals.user_list_updated
        self.system_message = self.core.signals.system_message
        self.error_occurred = self.core.signals.error_occurred
        self.connection_status_changed = self.core.signals.connection_status_changed
        self.file_transfer_request = self.core.signals.file_transfer_request
        self.file_transfer_progress = self.core.signals.file_transfer_progress
        self.file_transfer_complete = self.core.signals.file_transfer_complete
    
    # Connection methods
    def connect(self, username: str) -> bool:
        """Connect to the server."""
        return self.core.connect(username)
    
    def wait_for_authentication(self, timeout: float = 5.0) -> bool:
        """Wait for authentication response from server."""
        return self.core.wait_for_authentication(timeout)
    
    def disconnect(self, intentional: bool = True):
        """Disconnect from the server."""
        self.core.disconnect(intentional)
    
    # Chat methods - delegate to chat handler
    def send_public_message(self, content: str) -> bool:
        """Send a public message."""
        return self.chat_handler.send_public_message(content)
    
    def send_private_message(self, content: str, recipient: str) -> bool:
        """Send a private message."""
        return self.chat_handler.send_private_message(content, recipient)
    
    def request_user_list(self) -> bool:
        """Request updated user list."""
        return self.core.request_user_list()
    
    # File transfer methods - delegate to file handler
    def send_file(self, file_path: str, recipient: str) -> bool:
        """Send a file to a recipient."""
        return self.file_handler.send_file(file_path, recipient)
    
    def accept_file_transfer(self, transfer_id: str) -> bool:
        """Accept an incoming file transfer."""
        return self.respond_to_file_transfer(transfer_id, True)
    
    def decline_file_transfer(self, transfer_id: str, reason: str = "Declined by user") -> bool:
        """Decline an incoming file transfer."""
        return self.respond_to_file_transfer(transfer_id, False, reason)
    
    def respond_to_file_transfer(self, transfer_id: str, accept: bool, reason: str = "", request_message=None):
        """Respond to a file transfer request."""
        try:
            from ..shared.message_types import FileTransferResponse
        except ImportError:
            from shared.message_types import FileTransferResponse
        
        try:
            response = FileTransferResponse(transfer_id, accept, reason or ("Accepted" if accept else "Declined"), 
                                          self.core.username, "")
            success = self.core.send_message(response)
            
            if success:
                self.core.logger.info(f"📤 File transfer response sent: {'Accepted' if accept else 'Declined'}")
                if not accept:
                    self.core.file_transfer_manager.cleanup_transfer(transfer_id)
            else:
                self.core.logger.error("Failed to send file transfer response")
                return False
            
            return True
        except Exception as e:
            self.core.logger.error(f"Error responding to file transfer: {e}")
            return False
    
    # Properties for backward compatibility
    @property
    def connected(self) -> bool:
        """Check if connected to server."""
        return self.core.connected
    
    @property
    def username(self) -> str:
        """Get current username."""
        return self.core.username