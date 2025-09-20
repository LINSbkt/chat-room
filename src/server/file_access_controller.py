"""
Simple file access controller for the server.
Follows KISS and YAGNI principles.
"""

import os
import logging
from typing import List, Optional


class FileAccessController:
    """Controls file access based on user permissions."""
    
    def __init__(self, server):
        self.server = server
        self.logger = logging.getLogger(__name__)
    
    def can_user_access_file(self, user: str, file_path: str) -> bool:
        """Check if user can access a file."""
        try:
            # Use the file transfer manager's permission system
            if not (hasattr(self.server, 'file_transfer_manager') and self.server.file_transfer_manager.permission_manager):
                raise RuntimeError("File permission system is required but not available")
            return self.server.file_transfer_manager.can_user_access_file(user, file_path)
        except Exception as e:
            self.logger.error(f"Error checking file access for {user}: {e}")
            return False
    
    def get_user_accessible_files(self, user: str) -> List[str]:
        """Get list of files user can access."""
        try:
            if not (hasattr(self.server, 'file_transfer_manager') and self.server.file_transfer_manager.permission_manager):
                raise RuntimeError("File permission system is required but not available")
            return self.server.file_transfer_manager.get_user_accessible_files(user)
        except Exception as e:
            self.logger.error(f"Error getting accessible files for {user}: {e}")
            return []
    
    def get_file_list_for_user(self, user: str) -> List[dict]:
        """Get a formatted list of files with metadata for a user."""
        try:
            accessible_files = self.get_user_accessible_files(user)
            file_list = []
            
            # Get file transfer history to include sender and timestamp information
            file_history = {}
            if hasattr(self.server, 'file_history_storage'):
                # Get all file transfers for this user
                transfers = self.server.file_history_storage.get_file_transfers(user)
                for transfer in transfers:
                    # Create a key based on filename and path to match with accessible files
                    filename = transfer.get('filename', '')
                    # Try to match with accessible files by filename
                    for file_path in accessible_files:
                        if os.path.basename(file_path) == filename:
                            # Only store if we don't already have a match for this file
                            # This ensures we get the most recent transfer record
                            if file_path not in file_history:
                                file_history[file_path] = transfer
                            break
            
            for file_path in accessible_files:
                if os.path.exists(file_path):
                    try:
                        filename = os.path.basename(file_path)
                        file_size = os.path.getsize(file_path)
                        
                        # Determine if it's public or private based on path
                        # Use os.path to handle cross-platform path separators
                        normalized_path = os.path.normpath(file_path)
                        is_public = 'storages' + os.sep + 'public' in normalized_path
                        
                        # Get additional metadata from file history if available
                        transfer_info = file_history.get(file_path, {})
                        sender = transfer_info.get('sender', 'Unknown')
                        timestamp = transfer_info.get('timestamp')
                        
                        # Format timestamp for display
                        if timestamp:
                            if hasattr(timestamp, 'strftime'):
                                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                timestamp_str = str(timestamp)
                        else:
                            # Fallback to file modification time
                            import time
                            mod_time = os.path.getmtime(file_path)
                            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mod_time))
                        
                        file_info = {
                            'filename': filename,
                            'file_path': file_path,
                            'file_size': file_size,
                            'is_public': is_public,
                            'accessible': True,
                            'sender': sender,
                            'timestamp': timestamp_str
                        }
                        file_list.append(file_info)
                    except Exception as e:
                        self.logger.warning(f"Error getting info for file {file_path}: {e}")
                        continue
            
            return file_list
            
        except Exception as e:
            self.logger.error(f"Error getting file list for {user}: {e}")
            return []
