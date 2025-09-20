"""
Server file transfer handler.
"""

import logging
from datetime import datetime
try:
    from ...shared.message_types import (FileTransferRequest, FileTransferResponse, 
                                       FileChunk, FileTransferComplete, FileListRequest, 
                                       FileListResponse, SystemMessage)
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import (FileTransferRequest, FileTransferResponse, 
                                    FileChunk, FileTransferComplete, FileListRequest,
                                    FileListResponse, SystemMessage)


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
            
            # Store file transfer record for the sender
            self.client_connection.server.store_file_transfer(
                message, self.client_connection.username, message.recipient, "sent"
            )
            
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
                        # Send info message instead of error
                        self._send_error_message("No other users online to receive the file")
                    else:
                        self.logger.warning("📤 Failed to broadcast file transfer request to some users")
                        # Send info message instead of error to avoid disconnection
                        self._send_error_message("File transfer request sent, but some users may not receive it")
            else:
                # Handle private file transfers
                recipient_handler = self.client_connection.server.get_client_by_username(message.recipient)
                if not recipient_handler:
                    self._send_error_message(f"User {message.recipient} is not online")
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
                    self._send_error_message("Failed to send file transfer request to recipient")
                
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
            
            # Note: File transfer records will be stored when the transfer completes successfully
            # This ensures we have all the file information available and avoids complex error handling
            
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
                self.logger.warning("Failed to forward file chunk - transfer may have completed")
                
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
            
            # If successful, store a simple file transfer record for the recipient
            if message.success:
                try:
                    # Get transfer info from the server manager
                    transfer_info = self.client_connection.server.file_transfer_server_manager.active_file_transfers.get(message.transfer_id)
                    if transfer_info:
                        sender = transfer_info.get('sender')
                        recipient = transfer_info.get('recipient')
                        
                        # Create a simple file transfer record for the recipient
                        # We'll use basic information and let the file access controller handle the rest
                        if hasattr(self.client_connection.server, 'file_history_storage'):
                            try:
                                # Create a minimal transfer record
                                transfer_record = {
                                    'filename': 'unknown',  # Will be filled in by file access controller
                                    'file_size': 0,         # Will be filled in by file access controller
                                    'sender': sender or 'unknown',
                                    'recipient': recipient or 'unknown',
                                    'timestamp': datetime.now(),
                                    'status': 'completed',
                                    'transfer_type': 'private' if recipient != 'GLOBAL' else 'public'
                                }
                                
                                # Add to recipient's file history
                                if self.client_connection.username not in self.client_connection.server.file_history_storage.file_transfers:
                                    self.client_connection.server.file_history_storage.file_transfers[self.client_connection.username] = []
                                    self.client_connection.server.file_history_storage.transfer_counts[self.client_connection.username] = 0
                                
                                self.client_connection.server.file_history_storage.file_transfers[self.client_connection.username].append(transfer_record)
                                self.client_connection.server.file_history_storage.transfer_counts[self.client_connection.username] += 1
                                
                                # Maintain max transfer limit
                                if len(self.client_connection.server.file_history_storage.file_transfers[self.client_connection.username]) > self.client_connection.server.file_history_storage.max_transfers_per_user:
                                    self.client_connection.server.file_history_storage.file_transfers[self.client_connection.username].pop(0)
                                    self.client_connection.server.file_history_storage.transfer_counts[self.client_connection.username] -= 1
                                
                                self.logger.info(f"📋 Stored completed file transfer record for {self.client_connection.username} from {sender}")
                            except Exception as e:
                                self.logger.error(f"Error creating file transfer record: {e}")
                        else:
                            self.logger.warning("File history storage not available")
                except Exception as e:
                    self.logger.error(f"Error storing file transfer completion record: {e}")
            
            # Forward completion notification
            success = self.client_connection.server.forward_file_transfer_complete(
                message, self.client_connection.username)
            
            if not success:
                self.logger.warning(f"Could not forward file transfer completion for transfer {message.transfer_id} - transfer may have already completed")
            
            # FileTransferServerManager handles cleanup automatically
                
        except Exception as e:
            self.logger.error(f"Error handling file transfer complete: {e}")
            self._send_error_message("Error processing file transfer completion")
    
    def handle_file_list_request(self, message: FileListRequest):
        """Handle file list request."""
        if not self.client_connection.is_authenticated:
            self._send_error_message("Not authenticated")
            return
        
        try:
            self.logger.info(f"📋 File list request from {self.client_connection.username}")
            
            # Get accessible files for the user
            if hasattr(self.client_connection.server, 'file_access_controller'):
                file_list = self.client_connection.server.file_access_controller.get_file_list_for_user(
                    self.client_connection.username
                )
                
                # Send file list response
                response = FileListResponse(file_list, "server", self.client_connection.username)
                success = self.client_connection.send_message(response)
                
                if success:
                    self.logger.info(f"📋 Sent file list to {self.client_connection.username}: {len(file_list)} files")
                else:
                    self.logger.error(f"📋 Failed to send file list to {self.client_connection.username}")
            else:
                self._send_error_message("File access controller not available")
                
        except Exception as e:
            self.logger.error(f"Error handling file list request: {e}")
            self._send_error_message("Error processing file list request")
    
    def _send_error_message(self, content: str):
        """Send an error message to the client."""
        # For file transfer errors, send as info instead of error to avoid disconnection
        system_message = SystemMessage(content, "info")
        self.client_connection.send_message(system_message)