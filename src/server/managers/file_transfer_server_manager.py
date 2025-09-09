"""
Server-side file transfer management.
"""

import logging
from typing import Dict
try:
    from ...shared.message_types import FileTransferResponse, FileChunk, FileTransferComplete
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import FileTransferResponse, FileChunk, FileTransferComplete


class FileTransferServerManager:
    """Manages server-side file transfer operations."""
    
    def __init__(self, server):
        self.server = server
        self.active_file_transfers: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
    
    def track_transfer(self, transfer_id: str, sender: str, recipient: str):
        """Track a file transfer."""
        self.active_file_transfers[transfer_id] = {
            'sender': sender,
            'recipient': recipient,
            'accepted_by': []  # Track multiple recipients for GLOBAL transfers
        }
        self.logger.info(f"📋 Tracking transfer {transfer_id}: {sender} → {recipient}")
    
    def cleanup_transfer(self, transfer_id: str):
        """Clean up a completed or failed transfer."""
        if transfer_id in self.active_file_transfers:
            del self.active_file_transfers[transfer_id]
            self.logger.info(f"📋 Cleaned up transfer {transfer_id}")
    
    def get_accepted_recipients(self, transfer_id: str):
        """Get list of users who accepted a GLOBAL transfer."""
        if transfer_id in self.active_file_transfers:
            return self.active_file_transfers[transfer_id].get('accepted_by', [])
        return []
    
    def forward_file_transfer_response(self, message: FileTransferResponse, sender_username: str) -> bool:
        """Forward file transfer response to the original sender."""
        try:
            transfer_id = message.transfer_id
            
            # Look up the transfer in our tracking
            if transfer_id in self.active_file_transfers:
                transfer_info = self.active_file_transfers[transfer_id]
                original_sender = transfer_info['sender']
                
                # For GLOBAL transfers, add the user to the accepted list instead of replacing recipient
                if transfer_info['recipient'] == 'GLOBAL' and message.accepted:
                    if sender_username not in transfer_info['accepted_by']:
                        transfer_info['accepted_by'].append(sender_username)
                        self.logger.info(f"📋 Added {sender_username} to GLOBAL transfer {transfer_id} recipients")
                        self.logger.info(f"📋 Current accepted recipients: {transfer_info['accepted_by']}")
                    else:
                        self.logger.info(f"📋 User {sender_username} already in GLOBAL transfer {transfer_id} recipients")
                elif transfer_info['recipient'] == 'GLOBAL' and not message.accepted:
                    self.logger.info(f"📋 User {sender_username} declined GLOBAL transfer {transfer_id}")
                
                # Find the original sender client
                sender_handler = self.server.client_manager.get_client_by_username(original_sender)
                if sender_handler:
                    success = sender_handler.send_message(message)
                    if success:
                        self.logger.info(f"📤 Forwarded file transfer response to {original_sender}")
                        # Keep tracking for potential chunk transfers
                        return True
                    else:
                        self.logger.error(f"Failed to send file transfer response to {original_sender}")
                        return False
                else:
                    self.logger.warning(f"Original sender {original_sender} not found")
                    # Clean up the transfer since sender is gone
                    self.cleanup_transfer(transfer_id)
                    return False
            else:
                self.logger.warning(f"Transfer {transfer_id} not found in active transfers")
                return False
            
        except Exception as e:
            self.logger.error(f"Error forwarding file transfer response: {e}")
            return False
    
    def forward_file_chunk(self, message: FileChunk, sender_username: str) -> bool:
        """Forward file chunk to the recipient."""
        try:
            transfer_id = message.transfer_id
            
            # Use server-side transfer tracking to find the recipient
            if transfer_id in self.active_file_transfers:
                transfer_info = self.active_file_transfers[transfer_id]
                
                # Determine recipient based on who sent the chunk
                if sender_username == transfer_info['sender']:
                    # Sender is sending chunk, forward to recipient(s)
                    recipient_name = transfer_info['recipient']
                    
                    if recipient_name == 'GLOBAL':
                        # For GLOBAL transfers, send to all users who accepted
                        accepted_recipients = transfer_info['accepted_by']
                        
                        self.logger.info(f"📦 Forwarding GLOBAL chunk to accepted recipients: {accepted_recipients}")
                        
                        if not accepted_recipients:
                            self.logger.warning(f"Cannot forward chunk to GLOBAL - no users have accepted yet")
                            return False
                        
                        success_count = 0
                        for recipient in accepted_recipients:
                            recipient_handler = self.server.client_manager.get_client_by_username(recipient)
                            if recipient_handler:
                                success = recipient_handler.send_message(message)
                                if success:
                                    success_count += 1
                                    self.logger.info(f"📦 ✓ Forwarded file chunk to {recipient}")
                                else:
                                    self.logger.error(f"📦 ✗ Failed to send chunk to {recipient}")
                            else:
                                self.logger.warning(f"📦 Recipient {recipient} not found")
                        
                        self.logger.info(f"📦 GLOBAL chunk forwarded to {success_count}/{len(accepted_recipients)} recipients")
                        return success_count > 0
                    else:
                        # Private transfer to single recipient
                        recipient_handler = self.server.client_manager.get_client_by_username(recipient_name)
                        
                        if recipient_handler:
                            success = recipient_handler.send_message(message)
                            if success:
                                self.logger.debug(f"📦 Forwarded file chunk to {recipient_name}")
                            else:
                                self.logger.error(f"Failed to send chunk to {recipient_name}")
                            return success
                        else:
                            self.logger.warning(f"Recipient {recipient_name} not found")
                            return False
                else:
                    # This shouldn't happen in normal file transfers
                    self.logger.warning(f"Unexpected chunk sender {sender_username} for transfer {transfer_id}")
                    return False
            else:
                self.logger.warning(f"Transfer {transfer_id} not found in server tracking")
                return False
            
        except Exception as e:
            self.logger.error(f"Error forwarding file chunk: {e}")
            return False
    
    def forward_file_transfer_complete(self, message: FileTransferComplete, sender_username: str) -> bool:
        """Forward file transfer completion to the recipient."""
        try:
            transfer_id = message.transfer_id
            
            # Find recipient from tracked transfers or by searching active client transfers
            recipient_handler = None
            
            # First try to find from tracked transfers
            if transfer_id in self.active_file_transfers:
                transfer_info = self.active_file_transfers[transfer_id]
                
                # Determine recipient based on who sent the completion message
                if sender_username == transfer_info['sender']:
                    # Sender is notifying completion, send to recipient(s)
                    recipient_name = transfer_info['recipient']
                    if recipient_name == 'GLOBAL':
                        # For GLOBAL transfers, send completion to all who accepted
                        accepted_recipients = transfer_info['accepted_by']
                        success_count = 0
                        for recipient in accepted_recipients:
                            recipient_handler = self.server.client_manager.get_client_by_username(recipient)
                            if recipient_handler:
                                success = recipient_handler.send_message(message)
                                if success:
                                    success_count += 1
                                    self.logger.info(f"📋 Forwarded file transfer completion to {recipient}")
                        
                        if success_count > 0:
                            self.cleanup_transfer(transfer_id)
                            return True
                        return False
                    else:
                        # Private transfer to single recipient
                        recipient_handler = self.server.client_manager.get_client_by_username(recipient_name)
                else:
                    # Recipient is notifying completion, send to sender
                    sender_name = transfer_info['sender']
                    recipient_handler = self.server.client_manager.get_client_by_username(sender_name)
            
            # If still no recipient found, search by active transfers
            if not recipient_handler:
                for client_handler in self.server.client_manager.active_clients.values():
                    if (client_handler.username and client_handler.username != sender_username and
                        transfer_id in client_handler.file_transfer_manager.active_transfers):
                        recipient_handler = client_handler
                        break
            
            if recipient_handler:
                success = recipient_handler.send_message(message)
                if success:
                    self.logger.info(f"📋 Forwarded file transfer completion to {recipient_handler.username}")
                    # Clean up the transfer
                    self.cleanup_transfer(transfer_id)
                    return True
                else:
                    self.logger.error(f"Failed to send completion message to {recipient_handler.username}")
                    return False
            else:
                self.logger.warning(f"Could not find recipient for transfer completion {transfer_id}")
                # Clean up anyway
                self.cleanup_transfer(transfer_id)
                return False
            
        except Exception as e:
            self.logger.error(f"Error forwarding file transfer completion: {e}")
            return False