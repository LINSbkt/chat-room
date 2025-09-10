"""
Simple file permission management system.
Follows KISS and YAGNI principles.
"""

import os
import logging
from typing import List, Optional


class FilePermissionManager:
    """Manages file permissions using simple folder structure."""
    
    def __init__(self, storage_root: str = "storages"):
        self.storage_root = storage_root
        self.public_dir = os.path.join(storage_root, "public")
        self.private_dir = os.path.join(storage_root, "private")
        self.logger = logging.getLogger(__name__)
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create storage directories if they don't exist."""
        try:
            os.makedirs(self.public_dir, exist_ok=True)
            os.makedirs(self.private_dir, exist_ok=True)
            self.logger.info(f"📁 Storage directories created: {self.storage_root}")
        except Exception as e:
            self.logger.error(f"Failed to create storage directories: {e}")
            raise
    
    def can_user_access_file(self, user: str, file_path: str) -> bool:
        """Check if user can access a file based on folder structure."""
        try:
            # Convert to absolute path for consistent checking
            abs_path = os.path.abspath(file_path)
            
            # Public files - anyone can access
            if self.public_dir in abs_path:
                return True
            
            # Private files - check if user is in folder name
            if self.private_dir in abs_path:
                # Extract folder name from path
                relative_path = os.path.relpath(abs_path, self.private_dir)
                folder_name = relative_path.split(os.sep)[0]
                
                # Check if user is in the folder name (e.g., "user1_user2")
                return user in folder_name.split('_')
            
            # Files outside storage directories - deny access
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking file access for {user}: {e}")
            return False
    
    def get_user_accessible_files(self, user: str) -> List[str]:
        """Get list of files user can access."""
        accessible_files = []
        
        try:
            # Add all public files
            if os.path.exists(self.public_dir):
                for root, dirs, files in os.walk(self.public_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        accessible_files.append(file_path)
            
            # Add private files user has access to
            if os.path.exists(self.private_dir):
                for folder in os.listdir(self.private_dir):
                    folder_path = os.path.join(self.private_dir, folder)
                    if os.path.isdir(folder_path) and user in folder.split('_'):
                        for root, dirs, files in os.walk(folder_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                accessible_files.append(file_path)
            
            return accessible_files
            
        except Exception as e:
            self.logger.error(f"Error getting accessible files for {user}: {e}")
            return []
    
    def get_storage_path(self, filename: str, sender: str, recipient: str, is_public: bool) -> str:
        """Get the storage path for a file based on sender, recipient, and visibility."""
        try:
            if is_public or recipient == "GLOBAL":
                # Public files go to public directory
                return os.path.join(self.public_dir, filename)
            else:
                # Private files go to sender_recipient folder
                # Sort usernames to ensure consistent folder naming
                users = sorted([sender, recipient])
                folder_name = f"{users[0]}_{users[1]}"
                folder_path = os.path.join(self.private_dir, folder_name)
                
                # Create folder if it doesn't exist
                os.makedirs(folder_path, exist_ok=True)
                
                return os.path.join(folder_path, filename)
                
        except Exception as e:
            self.logger.error(f"Error getting storage path: {e}")
            raise
    
    def migrate_existing_file(self, old_path: str, sender: str, recipient: str, is_public: bool) -> str:
        """Migrate an existing file to the new storage structure."""
        try:
            if not os.path.exists(old_path):
                raise FileNotFoundError(f"File not found: {old_path}")
            
            filename = os.path.basename(old_path)
            new_path = self.get_storage_path(filename, sender, recipient, is_public)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            
            # Move file to new location
            import shutil
            shutil.move(old_path, new_path)
            
            self.logger.info(f"📁 Migrated file: {old_path} → {new_path}")
            return new_path
            
        except Exception as e:
            self.logger.error(f"Error migrating file {old_path}: {e}")
            raise
