"""
Core client connection management.
"""

import logging
from typing import Optional
try:
    from ...shared.message_types import Message
    from ...shared.protocols import ConnectionManager
    from ...shared.file_transfer_manager import FileTransferManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import Message
    from shared.protocols import ConnectionManager
    from shared.file_transfer_manager import FileTransferManager


class ClientConnection:
    """Manages core client connection state and basic operations."""
    
    def __init__(self, client_socket, client_address, server):
        self.client_socket = client_socket
        self.client_address = client_address
        self.server = server
        self.client_id = self._generate_client_id()
        self.username: Optional[str] = None
        self.is_authenticated = False
        self.connected = True
        self.connection_manager = ConnectionManager(client_socket)
        self.file_transfer_manager = FileTransferManager()
        
        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.client_id}")
    
    def _generate_client_id(self) -> str:
        """Generate a unique client ID."""
        import uuid
        return str(uuid.uuid4())
    
    def run(self):
        """Main client handling loop."""
        try:
            self.logger.info(f"Client handler started for {self.client_address}")
            
            while self.connected and self.connection_manager.is_connected():
                try:
                    message = self.connection_manager.receive_message()
                    if message is None:
                        break
                    
                    # Import message handler to avoid circular imports
                    from ..handlers.server_message_handler import ServerMessageHandler
                    handler = ServerMessageHandler(self)
                    handler.handle_message(message)
                    
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
        finally:
            self.disconnect()
    
    def send_message(self, message: Message) -> bool:
        """Send a message to the client."""
        if not self.connected:
            return False
        
        try:
            return self.connection_manager.send_message(message)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
    
    def disconnect(self):
        """Disconnect the client."""
        if not self.connected:
            return
        
        self.logger.info(f"Disconnecting client {self.client_id}")
        self.connected = False
        
        # Remove from server's client list
        if self.server:
            self.server.remove_client(self)
        
        # Close connection
        if self.connection_manager:
            self.connection_manager.close()
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
    
    def is_connected(self) -> bool:
        """Check if client is still connected."""
        return self.connected and self.connection_manager.is_connected()