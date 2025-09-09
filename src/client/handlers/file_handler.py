"""
File transfer message handler.
"""

import logging
import math
try:
    from ...shared.message_types import (FileTransferRequest, FileTransferResponse, 
                                       FileChunk, FileTransferComplete)
except ImportError:
    from shared.message_types import (FileTransferRequest, FileTransferResponse, 
                                    FileChunk, FileTransferComplete)


class FileHandler:
    """Handles file transfer-related messages."""
    
    def __init__(self, client_core):
        self.client_core = client_core
        self.logger = logging.getLogger(__name__)
    
    def handle_file_transfer_request(self, message: FileTransferRequest):
        """Handle incoming file transfer request."""
        try:
            self.logger.info(f"📩 Received file transfer request: {message.filename} from {message.sender}")
            
            transfer_id = message.transfer_id or message.message_id
            if transfer_id:
                success = self.client_core.file_transfer_manager.start_incoming_transfer(
                    transfer_id, message.filename, message.file_size, 
                    message.file_hash, message.sender, self.client_core.username
                )
                # Store whether this was a GLOBAL transfer for later reference
                if success and transfer_id in self.client_core.file_transfer_manager.active_transfers:
                    self.client_core.file_transfer_manager.active_transfers[transfer_id]['is_global'] = not message.is_private
                if success:
                    self.logger.info(f"📥 Set up incoming transfer {transfer_id} for {message.filename}")
                    
                    # For GLOBAL transfers, automatically accept without showing dialog
                    if not message.is_private:  # GLOBAL transfer
                        self.logger.info(f"📥 Auto-accepting GLOBAL file transfer: {message.filename}")
                        self.client_core.signals.system_message.emit(f"📥 Receiving file: {message.filename} from {message.sender}")
                        
                        # Send acceptance response immediately
                        from ...shared.message_types import FileTransferResponse
                        response = FileTransferResponse(transfer_id, True)
                        self.client_core.send_message(response)
                    else:
                        # For private transfers, show the dialog
                        self.client_core.signals.file_transfer_request.emit(message)
                else:
                    self.logger.error(f"Failed to set up incoming transfer {transfer_id}")
                    self.client_core.signals.error_occurred.emit("Failed to prepare for file transfer")
            else:
                self.logger.error("File transfer request missing transfer_id")
                self.client_core.signals.error_occurred.emit("Invalid file transfer request")
        except Exception as e:
            self.logger.error(f"Error handling file transfer request: {e}")
            self.client_core.signals.error_occurred.emit(f"Error handling file transfer request: {e}")
    
    def handle_file_transfer_response(self, message: FileTransferResponse):
        """Handle file transfer response (accept/decline)."""
        try:
            if message.accepted:
                self.logger.info(f"✅ File transfer accepted: {message.transfer_id}")
                self._send_file_chunks(message.transfer_id)
            else:
                self.logger.info(f"❌ File transfer declined: {message.transfer_id} - {message.reason}")
                self.client_core.file_transfer_manager.cleanup_transfer(message.transfer_id)
                self.client_core.signals.system_message.emit(f"File transfer declined: {message.reason}")
        except Exception as e:
            self.logger.error(f"Error handling file transfer response: {e}")
    
    def handle_file_chunk(self, message: FileChunk):
        """Handle incoming file chunk."""
        try:
            self.logger.debug(f"📦 Received chunk {message.chunk_index + 1}/{message.total_chunks}")
            
            success = self.client_core.file_transfer_manager.add_chunk_to_transfer(
                message.transfer_id, message.chunk_index, message.chunk_data
            )
            
            if success:
                transfer = self.client_core.file_transfer_manager.get_transfer_status(message.transfer_id)
                if transfer:
                    if transfer['total_chunks'] == 0:
                        self.client_core.file_transfer_manager.active_transfers[message.transfer_id]['total_chunks'] = message.total_chunks
                    
                    self.client_core.signals.file_transfer_progress.emit(
                        message.transfer_id, transfer['received_chunks'], message.total_chunks
                    )
                    
                    if transfer['received_chunks'] >= message.total_chunks:
                        self._complete_incoming_transfer(message.transfer_id)
            else:
                self.logger.error(f"Failed to add chunk {message.chunk_index}")
        except Exception as e:
            self.logger.error(f"Error handling file chunk: {e}")
    
    def handle_file_transfer_complete(self, message: FileTransferComplete):
        """Handle file transfer completion notification."""
        try:
            # Check if this completion message is relevant to this user
            transfer = self.client_core.file_transfer_manager.get_transfer_status(message.transfer_id)
            
            if message.success:
                self.logger.info(f"✅ File transfer completed successfully: {message.transfer_id}")
                
                # Only emit GUI signal if this user was the recipient (has a received file)
                if transfer and transfer.get('direction') == 'incoming' and 'file_path' in transfer:
                    file_path = transfer['file_path']
                    self.client_core.signals.file_transfer_complete.emit(
                        message.transfer_id, True, file_path
                    )
                else:
                    # This is a completion notification for a file we sent - just log it
                    self.logger.info(f"📤 Received confirmation that sent file was completed: {message.transfer_id}")
            else:
                self.logger.error(f"❌ File transfer failed: {message.transfer_id} - {message.error_message}")
                # Only show error to GUI if this user was involved in the transfer
                if transfer:
                    self.client_core.signals.file_transfer_complete.emit(
                        message.transfer_id, False, message.error_message or "Transfer failed"
                    )
            
            self.client_core.file_transfer_manager.cleanup_transfer(message.transfer_id)
        except Exception as e:
            self.logger.error(f"Error handling file transfer complete: {e}")
    
    def send_file(self, file_path: str, recipient: str) -> bool:
        """Send a file to a recipient."""
        if not self.client_core.connected or not self.client_core.username:
            return False
        
        try:
            import os
            if not os.path.exists(file_path):
                self.client_core.signals.error_occurred.emit(f"File not found: {file_path}")
                return False
            
            filename, file_size, file_hash = self.client_core.file_transfer_manager.get_file_info(file_path)
            if not filename:
                self.client_core.signals.error_occurred.emit("Failed to get file information")
                return False
            
            transfer_id = self.client_core.file_transfer_manager.generate_transfer_id()
            
            success = self.client_core.file_transfer_manager.start_outgoing_transfer(
                transfer_id, file_path, recipient, self.client_core.username
            )
            if not success:
                self.client_core.signals.error_occurred.emit("Failed to start file transfer")
                return False
            
            is_private = (recipient != "GLOBAL")
            request = FileTransferRequest(filename, file_size, file_hash, 
                                        self.client_core.username, recipient, is_private)
            request.set_transfer_id(transfer_id)
            request.message_id = transfer_id
            
            success = self.client_core.send_message(request)
            if success:
                self.logger.info(f"📤 File transfer request sent: {filename} to {recipient}")
                self.client_core.signals.system_message.emit(f"File transfer request sent: {filename} to {recipient}")
            else:
                self.client_core.file_transfer_manager.cleanup_transfer(transfer_id)
                self.client_core.signals.error_occurred.emit("Failed to send file transfer request")
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to send file: {e}")
            self.client_core.signals.error_occurred.emit(f"Failed to send file: {e}")
            return False
    
    def _send_file_chunks(self, transfer_id: str):
        """Send file chunks for an accepted transfer."""
        try:
            if transfer_id not in self.client_core.file_transfer_manager.active_transfers:
                # Transfer might have already completed - this is normal for GLOBAL transfers
                # where multiple acceptance responses arrive after completion
                self.logger.debug(f"Transfer {transfer_id} not found (likely already completed)")
                return
            
            transfer = self.client_core.file_transfer_manager.active_transfers[transfer_id]
            self.logger.info(f"📤 Starting to send {transfer['total_chunks']} chunks")
            
            while True:
                chunk_data = self.client_core.file_transfer_manager.get_next_chunk(transfer_id)
                if not chunk_data:
                    break
                
                chunk_index, chunk_content = chunk_data
                
                chunk_message = FileChunk(
                    transfer_id=transfer_id,
                    chunk_index=chunk_index,
                    total_chunks=transfer['total_chunks'],
                    chunk_data=chunk_content,
                    sender=self.client_core.username,
                    recipient=transfer['recipient']
                )
                
                success = self.client_core.send_message(chunk_message)
                if success:
                    self.client_core.signals.file_transfer_progress.emit(
                        transfer_id, chunk_index + 1, transfer['total_chunks']
                    )
                else:
                    self.logger.error(f"Failed to send chunk {chunk_index}")
                    return
            
            complete_message = FileTransferComplete(
                transfer_id=transfer_id, success=True, final_hash=transfer['file_hash'],
                sender=self.client_core.username, recipient=transfer['recipient']
            )
            
            success = self.client_core.send_message(complete_message)
            if success:
                self.logger.info(f"📤 File transfer completed: {transfer['filename']}")
                self.client_core.signals.file_transfer_complete.emit(transfer_id, True, transfer['file_path'])
            
            self.client_core.file_transfer_manager.cleanup_transfer(transfer_id)
        except Exception as e:
            self.logger.error(f"Error sending file chunks: {e}")
    
    def _complete_incoming_transfer(self, transfer_id: str):
        """Complete an incoming file transfer."""
        try:
            success, file_path = self.client_core.file_transfer_manager.complete_transfer(transfer_id)
            
            if success:
                self.logger.info(f"✅ File transfer completed successfully: {file_path}")
                self.client_core.signals.file_transfer_complete.emit(transfer_id, True, file_path)
                
                # Get transfer info to check if it's GLOBAL
                transfer = self.client_core.file_transfer_manager.get_transfer_status(transfer_id)
                
                # Only send completion notification for private transfers
                # For GLOBAL transfers, don't notify the sender (prevents duplicate dialogs)
                if transfer and not transfer.get('is_global', False):
                    complete_message = FileTransferComplete(transfer_id, True, sender=self.client_core.username)
                    self.client_core.send_message(complete_message)
                else:
                    self.logger.info(f"📋 Skipping completion notification for GLOBAL transfer")
            
            else:
                self.logger.error(f"❌ File transfer failed: {transfer_id}")
                self.client_core.signals.file_transfer_complete.emit(transfer_id, False, "Failed to complete file transfer")
                
                complete_message = FileTransferComplete(transfer_id, False, 
                                                      error_message="Failed to complete transfer", 
                                                      sender=self.client_core.username)
                self.client_core.send_message(complete_message)
            
            self.client_core.file_transfer_manager.cleanup_transfer(transfer_id)
        except Exception as e:
            self.logger.error(f"Error completing file transfer: {e}")
            self.client_core.signals.file_transfer_complete.emit(transfer_id, False, str(e))