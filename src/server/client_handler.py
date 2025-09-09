"""
Client handler for managing individual client connections - refactored to use modular structure.
"""

from .core.client_connection import ClientConnection


class ClientHandler(ClientConnection):
    """
    Main client handler class - now inherits from modular ClientConnection.
    This maintains backward compatibility while using the new modular structure.
    """
    
    def __init__(self, client_socket, client_address, server):
        # Initialize using the modular core
        super().__init__(client_socket, client_address, server)
    
    # All functionality is now handled by the modular components:
    # - Core connection management: ClientConnection
    # - Message handling: ServerMessageHandler
    # - Authentication: ServerAuthHandler  
    # - Chat: ServerChatHandler
    # - File transfer: ServerFileHandler
    
    # Backward compatibility methods that delegate to the base class
    def handle_message(self, message):
        """Handle message - delegates to modular handler."""
        from .handlers.server_message_handler import ServerMessageHandler
        handler = ServerMessageHandler(self)
        handler.handle_message(message)
    
    # Legacy method names for backward compatibility
    def send_error_message(self, content: str):
        """Send error message - backward compatibility."""
        try:
            from ..shared.message_types import SystemMessage
        except ImportError:
            from shared.message_types import SystemMessage
        
        system_message = SystemMessage(content, "error")
        self.send_message(system_message)
    
    def send_system_message(self, content: str):
        """Send system message - backward compatibility."""
        try:
            from ..shared.message_types import SystemMessage
        except ImportError:
            from shared.message_types import SystemMessage
        
        system_message = SystemMessage(content)
        self.send_message(system_message)