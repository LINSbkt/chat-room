"""
File transfer management utilities for the chatroom application.
"""

import os
import hashlib
import base64
import uuid
from typing import Dict, Optional, Tuple, BinaryIO, List
from datetime import datetime
import logging


class FileTransferManager:
    """Manages file transfer operations and state."""
    
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size
        self.active_transfers: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize file permission manager
        try:
            from .file_permission_manager import FilePermissionManager
            self.permission_manager = FilePermissionManager()
        except ImportError:
            self.permission_manager = None
            self.logger.warning("File permission manager not available")
    
    def generate_transfer_id(self) -> str:
        """Generate a unique transfer ID."""
        return str(uuid.uuid4())
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating file hash: {e}")
            return ""
    
    def get_file_info(self, file_path: str) -> Tuple[str, int, str]:
        """Get file information (filename, size, hash)."""
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_hash = self.calculate_file_hash(file_path)
            return filename, file_size, file_hash
        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return "", 0, ""
    
    def split_file_into_chunks(self, file_path: str) -> list:
        """Split file into base64-encoded chunks."""
        chunks = []
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    # Encode chunk to base64
                    chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                    chunks.append(chunk_b64)
            return chunks
        except Exception as e:
            self.logger.error(f"Error splitting file into chunks: {e}")
            return []
    
    def reassemble_file_from_chunks(self, chunks: list, output_path: str) -> bool:
        """Reassemble file from base64-encoded chunks."""
        try:
            with open(output_path, "wb") as f:
                for chunk_b64 in chunks:
                    chunk_data = base64.b64decode(chunk_b64)
                    f.write(chunk_data)
            return True
        except Exception as e:
            self.logger.error(f"Error reassembling file: {e}")
            return False
    
    def start_outgoing_transfer(self, transfer_id: str, file_path: str, 
                              recipient: str, sender: str) -> bool:
        """Start an outgoing file transfer."""
        try:
            filename, file_size, file_hash = self.get_file_info(file_path)
            if not filename:
                return False
            
            chunks = self.split_file_into_chunks(file_path)
            if not chunks:
                return False
            
            self.active_transfers[transfer_id] = {
                'type': 'outgoing',
                'file_path': file_path,
                'filename': filename,
                'file_size': file_size,
                'file_hash': file_hash,
                'chunks': chunks,
                'total_chunks': len(chunks),
                'sent_chunks': 0,
                'recipient': recipient,
                'sender': sender,
                'start_time': datetime.now(),
                'status': 'pending'
            }
            
            self.logger.info(f"📤 Started outgoing transfer {transfer_id}: {filename} ({file_size} bytes, {len(chunks)} chunks)")
            return True
        except Exception as e:
            self.logger.error(f"Error starting outgoing transfer: {e}")
            return False
    
    def start_incoming_transfer(self, transfer_id: str, filename: str, 
                              file_size: int, file_hash: str, 
                              sender: str, recipient: str, is_public: bool = False) -> bool:
        """Start an incoming file transfer."""
        try:
            # Use permission manager to get proper storage path
            if not self.permission_manager:
                raise RuntimeError("File permission manager is required but not available")
            
            # Determine if this is a public or private file
            is_public_file = is_public or recipient == "GLOBAL"
            output_path = self.permission_manager.get_storage_path(
                filename, sender, recipient, is_public_file
            )
            
            # Generate unique filename to avoid conflicts
            base_name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(output_path):
                new_filename = f"{base_name}_{counter}{ext}"
                output_path = self.permission_manager.get_storage_path(
                    new_filename, sender, recipient, is_public_file
                )
                counter += 1
            
            self.logger.info(f"📁 Storage path: {output_path}")
            
            self.active_transfers[transfer_id] = {
                'type': 'incoming',
                'output_path': output_path,
                'filename': filename,
                'file_size': file_size,
                'file_hash': file_hash,
                'chunks': [],
                'total_chunks': 0,
                'received_chunks': 0,
                'sender': sender,
                'recipient': recipient,
                'is_public': is_public or recipient == "GLOBAL",
                'start_time': datetime.now(),
                'status': 'receiving'
            }
            
            self.logger.info(f"📥 Started incoming transfer {transfer_id}: {filename} ({file_size} bytes)")
            return True
        except Exception as e:
            self.logger.error(f"Error starting incoming transfer: {e}")
            return False
    
    def add_chunk_to_transfer(self, transfer_id: str, chunk_index: int, 
                            chunk_data: str) -> bool:
        """Add a chunk to an incoming transfer."""
        if transfer_id not in self.active_transfers:
            return False
        
        transfer = self.active_transfers[transfer_id]
        if transfer['type'] != 'incoming':
            return False
        
        # Ensure chunks list is large enough
        while len(transfer['chunks']) <= chunk_index:
            transfer['chunks'].append(None)
        
        transfer['chunks'][chunk_index] = chunk_data
        transfer['received_chunks'] += 1
        
        self.logger.debug(f"📥 Received chunk {chunk_index + 1}/{transfer['total_chunks']} for transfer {transfer_id}")
        return True
    
    def is_transfer_complete(self, transfer_id: str) -> bool:
        """Check if a transfer is complete."""
        if transfer_id not in self.active_transfers:
            return False
        
        transfer = self.active_transfers[transfer_id]
        
        if transfer['type'] == 'outgoing':
            return transfer['sent_chunks'] >= transfer['total_chunks']
        elif transfer['type'] == 'incoming':
            return transfer['received_chunks'] >= transfer['total_chunks']
        
        return False
    
    def complete_transfer(self, transfer_id: str) -> Tuple[bool, Optional[str]]:
        """Complete a transfer and return success status and file path."""
        if transfer_id not in self.active_transfers:
            return False, None
        
        transfer = self.active_transfers[transfer_id]
        
        try:
            if transfer['type'] == 'incoming':
                # Reassemble file from chunks
                success = self.reassemble_file_from_chunks(transfer['chunks'], transfer['output_path'])
                if success:
                    # Verify file hash
                    received_hash = self.calculate_file_hash(transfer['output_path'])
                    if received_hash == transfer['file_hash']:
                        transfer['status'] = 'completed'
                        self.logger.info(f"✅ Transfer {transfer_id} completed successfully: {transfer['filename']}")
                        return True, transfer['output_path']
                    else:
                        transfer['status'] = 'hash_mismatch'
                        self.logger.error(f"❌ Transfer {transfer_id} failed: hash mismatch")
                        return False, None
                else:
                    transfer['status'] = 'failed'
                    self.logger.error(f"❌ Transfer {transfer_id} failed: could not reassemble file")
                    return False, None
            
            elif transfer['type'] == 'outgoing':
                transfer['status'] = 'completed'
                self.logger.info(f"✅ Outgoing transfer {transfer_id} completed: {transfer['filename']}")
                return True, transfer['file_path']
            
        except Exception as e:
            self.logger.error(f"Error completing transfer {transfer_id}: {e}")
            transfer['status'] = 'failed'
            return False, None
        
        return False, None
    
    def get_next_chunk(self, transfer_id: str) -> Optional[Tuple[int, str]]:
        """Get the next chunk for an outgoing transfer."""
        if transfer_id not in self.active_transfers:
            return None
        
        transfer = self.active_transfers[transfer_id]
        if transfer['type'] != 'outgoing':
            return None
        
        if transfer['sent_chunks'] >= transfer['total_chunks']:
            return None
        
        chunk_index = transfer['sent_chunks']
        chunk_data = transfer['chunks'][chunk_index]
        transfer['sent_chunks'] += 1
        
        return chunk_index, chunk_data
    
    def cleanup_transfer(self, transfer_id: str):
        """Clean up a completed or failed transfer."""
        if transfer_id in self.active_transfers:
            transfer = self.active_transfers[transfer_id]
            self.logger.debug(f"🧹 Cleaning up transfer {transfer_id}: {transfer['filename']}")
            del self.active_transfers[transfer_id]
    
    def get_transfer_status(self, transfer_id: str) -> Optional[Dict]:
        """Get the status of a transfer."""
        if transfer_id not in self.active_transfers:
            return None
        
        transfer = self.active_transfers[transfer_id].copy()
        # Remove chunks from status to avoid large data in logs
        if 'chunks' in transfer:
            del transfer['chunks']
        return transfer
    
    def get_all_transfers(self) -> Dict[str, Dict]:
        """Get all active transfers."""
        return {tid: self.get_transfer_status(tid) for tid in self.active_transfers.keys()}
    
    def can_user_access_file(self, user: str, file_path: str) -> bool:
        """Check if user can access a file."""
        if not self.permission_manager:
            raise RuntimeError("File permission manager is required but not available")
        return self.permission_manager.can_user_access_file(user, file_path)
    
    def get_user_accessible_files(self, user: str) -> List[str]:
        """Get list of files user can access."""
        if not self.permission_manager:
            raise RuntimeError("File permission manager is required but not available")
        return self.permission_manager.get_user_accessible_files(user)
