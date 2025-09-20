"""
File transfer history storage system for chat room persistence.
"""

import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime
try:
    from ...shared.message_types import FileTransferRequest
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import FileTransferRequest


class FileHistoryStorage:
    """Stores file transfer history in server memory for persistence across user sessions."""
    
    def __init__(self, max_transfers_per_user: int = 500):
        self.max_transfers_per_user = max_transfers_per_user
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Storage structure: username -> list of file transfers
        self.file_transfers: Dict[str, List[dict]] = {}
        
        # Track transfer counts per user
        self.transfer_counts: Dict[str, int] = {}
    
    def store_file_transfer(self, transfer_request: FileTransferRequest, sender: str, 
                          recipient: str, status: str = "completed"):
        """Store a file transfer record."""
        with self.lock:
            # Store for sender
            if sender not in self.file_transfers:
                self.file_transfers[sender] = []
                self.transfer_counts[sender] = 0
            
            transfer_record = {
                'filename': transfer_request.filename,
                'file_size': transfer_request.file_size,
                'sender': sender,
                'recipient': recipient,
                'timestamp': datetime.now(),
                'status': status,
                'transfer_type': 'private' if recipient != 'GLOBAL' else 'public'
            }
            
            self.file_transfers[sender].append(transfer_record)
            self.transfer_counts[sender] += 1
            
            # Maintain max transfer limit
            if len(self.file_transfers[sender]) > self.max_transfers_per_user:
                self.file_transfers[sender].pop(0)
                self.transfer_counts[sender] -= 1
            
            # Store for recipient if it's a private transfer
            if recipient != 'GLOBAL' and recipient != sender:
                if recipient not in self.file_transfers:
                    self.file_transfers[recipient] = []
                    self.transfer_counts[recipient] = 0
                
                # Create recipient record (received file)
                recipient_record = transfer_record.copy()
                recipient_record['status'] = 'received'
                
                self.file_transfers[recipient].append(recipient_record)
                self.transfer_counts[recipient] += 1
                
                # Maintain max transfer limit for recipient
                if len(self.file_transfers[recipient]) > self.max_transfers_per_user:
                    self.file_transfers[recipient].pop(0)
                    self.transfer_counts[recipient] -= 1
            
            self.logger.debug(f"Stored file transfer: {sender} -> {recipient}, {transfer_request.filename}")
    
    def store_public_file_for_user(self, transfer_request: FileTransferRequest, sender: str, recipient: str):
        """Store a public file transfer record for a specific user (when they accept it)."""
        with self.lock:
            if recipient not in self.file_transfers:
                self.file_transfers[recipient] = []
                self.transfer_counts[recipient] = 0
            
            transfer_record = {
                'filename': transfer_request.filename,
                'file_size': transfer_request.file_size,
                'sender': sender,
                'recipient': recipient,
                'timestamp': datetime.now(),
                'status': 'received',
                'transfer_type': 'public'
            }
            
            self.file_transfers[recipient].append(transfer_record)
            self.transfer_counts[recipient] += 1
            
            # Maintain max transfer limit
            if len(self.file_transfers[recipient]) > self.max_transfers_per_user:
                self.file_transfers[recipient].pop(0)
                self.transfer_counts[recipient] -= 1
            
            self.logger.debug(f"Stored public file transfer for user {recipient}: {transfer_request.filename}")
    
    def get_file_transfers(self, username: str, limit: Optional[int] = None) -> List[dict]:
        """Get file transfer history for a user."""
        with self.lock:
            if username not in self.file_transfers:
                return []
            
            transfers = self.file_transfers[username].copy()
            
            if limit and len(transfers) > limit:
                transfers = transfers[-limit:]  # Get most recent transfers
            
            return transfers
    
    def get_sent_files(self, username: str, limit: Optional[int] = None) -> List[dict]:
        """Get files sent by a user."""
        transfers = self.get_file_transfers(username, limit)
        return [t for t in transfers if t['status'] in ['completed', 'sent']]
    
    def get_received_files(self, username: str, limit: Optional[int] = None) -> List[dict]:
        """Get files received by a user."""
        transfers = self.get_file_transfers(username, limit)
        return [t for t in transfers if t['status'] == 'received']
    
    def get_public_files(self, username: str, limit: Optional[int] = None) -> List[dict]:
        """Get public files that a user has access to."""
        transfers = self.get_file_transfers(username, limit)
        return [t for t in transfers if t['transfer_type'] == 'public']
    
    def get_private_files(self, username: str, limit: Optional[int] = None) -> List[dict]:
        """Get private files for a user."""
        transfers = self.get_file_transfers(username, limit)
        return [t for t in transfers if t['transfer_type'] == 'private']
    
    def get_transfer_count(self, username: str) -> int:
        """Get the number of file transfers for a user."""
        with self.lock:
            return self.transfer_counts.get(username, 0)
    
    def clear_user_history(self, username: str):
        """Clear file transfer history for a specific user."""
        with self.lock:
            if username in self.file_transfers:
                del self.file_transfers[username]
                del self.transfer_counts[username]
                self.logger.info(f"Cleared file transfer history for user '{username}'")
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        with self.lock:
            total_transfers = sum(self.transfer_counts.values())
            return {
                'total_users': len(self.file_transfers),
                'total_transfers': total_transfers,
                'users': {user: count for user, count in self.transfer_counts.items()}
            }
