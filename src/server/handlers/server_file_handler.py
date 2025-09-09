"""
Server file transfer handler.
"""

import logging
try:
    from ...shared.message_types import (FileTransferRequest, FileTransferResponse, 
                                       FileChunk, FileTransferComplete, SystemMessage)
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import (FileTransferRequest, FileTransferResponse, 
                                    FileChunk, FileTransferComplete, SystemMessage)


class ServerFileHandler:
    """Handles server-side file transfer functionality."""
    
    def __init__(self, client_connection):
        self.client_connection = client_connection
        self.logger = logging.getLogger(__name__)
    
    def handle_file_transfer_request(self, message: FileTransferRequest):
        """Handle file transfer request."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            self.logger.info(f"📤 File transfer request from {self.client_connection.username}: "
                           f"{message.filename} ({message.file_size} bytes) to {message.recipient}")
            
            # Handle global file transfers
            if message.recipient == "GLOBAL":
                # Broadcast to all connected users except sender
                success = self.client_connection.server.broadcast_file_transfer_request(
                    message, exclude_user=self.client_connection.username)
                
                if success:
                    self.logger.info("📤 Broadcasted file transfer request to all users")
                    # Track the GLOBAL file transfer for response forwarding
                    transfer_id = message.transfer_id
                    if transfer_id:
                        self.client_connection.server.file_transfer_server_manager.track_transfer(
                            transfer_id, self.client_connection.username, "GLOBAL")
                        self.logger.info(f"📤 Tracking GLOBAL transfer {transfer_id}")
                else:
                    # Check if there are any other users to send to
                    other_users = [client.username for client in self.client_connection.server.active_clients.values() 
                                 if client.username and client.username != self.client_connection.username]
                    if not other_users:
                        self.logger.info("📤 No other users online to receive file transfer")
                        # Don't send error message if no other users are online
                    else:
                        self._send_error_message("Failed to broadcast file transfer request")
            else:
                # Handle private file transfers
                recipient_handler = self.client_connection.server.get_client_by_username(message.recipient)
                if not recipient_handler:
                    self._send_error_message(f"User {message.recipient} not found")
                    return
                
                # Forward the request to the recipient
                success = recipient_handler.send_message(message)
                if success:
                    # Track the file transfer using FileTransferServerManager
                    transfer_id = message.transfer_id
                    if transfer_id:
                        self.client_connection.server.file_transfer_server_manager.track_transfer(
                            transfer_id, self.client_connection.username, message.recipient)
                        self.logger.info(f"📤 Forwarded file transfer request to {message.recipient}, "
                                       f"tracking transfer {transfer_id}")
                    else:
                        self.logger.info(f"📤 Forwarded file transfer request to {message.recipient}")
                else:
                    self._send_error_message("Failed to send file transfer request")
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer request: {e}")
            self._send_error_message("Error processing file transfer request")
    
    def handle_file_transfer_response(self, message: FileTransferResponse):
        """Handle file transfer response (accept/decline)."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            self.logger.info(f"📥 File transfer response from {self.client_connection.username}: "
                           f"{'accepted' if message.accepted else 'declined'}")
            
            # Find the original sender and forward the response
            success = self.client_connection.server.forward_file_transfer_response(
                message, self.client_connection.username)
            
            if not success:
                # Don't send error message that causes disconnection
                # Just log the warning - the transfer might have already completed or been cancelled
                self.logger.warning(f"Could not forward file transfer response for transfer {message.transfer_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer response: {e}")
            self._send_error_message("Error processing file transfer response")
    
    def handle_file_chunk(self, message: FileChunk):
        """Handle file chunk."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            self.logger.debug(f"📦 Received file chunk {message.chunk_index + 1}/{message.total_chunks} "
                            f"for transfer {message.transfer_id}")
            
            # Forward the chunk to the recipient
            success = self.client_connection.server.forward_file_chunk(message, self.client_connection.username)
            if not success:
                self._send_error_message("Failed to forward file chunk")
                
        except Exception as e:
            self.logger.error(f"Error handling file chunk: {e}")
            self._send_error_message("Error processing file chunk")
    
    def handle_file_transfer_complete(self, message: FileTransferComplete):
        """Handle file transfer completion."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            self.logger.info(f"📋 File transfer complete from {self.client_connection.username}: "
                           f"{'success' if message.success else 'failed'} for transfer {message.transfer_id}")
            
            # Forward completion notification
            success = self.client_connection.server.forward_file_transfer_complete(
                message, self.client_connection.username)
            
            if not success:
                self.logger.warning(f"Could not forward file transfer completion for transfer {message.transfer_id}")
            
            # FileTransferServerManager handles cleanup automatically
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer complete: {e}")
            self._send_error_message("Error processing file transfer completion")
    
    def _send_error_message(self, content: str):
        """Send an error message to the client."""
        system_message = SystemMessage(content, "error")
        self.client_connection.send_message(system_message)