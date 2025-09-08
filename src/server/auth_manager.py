"""
Authentication manager for handling user authentication and session management.
"""

import logging
import threading
from typing import Dict, Set, Optional
from datetime import datetime, timedelta
try:
    from ..shared.exceptions import AuthenticationError
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from shared.exceptions import AuthenticationError


class AuthManager:
    """Manages user authentication and sessions."""
    
    def __init__(self):
        self.active_users: Dict[str, dict] = {}  # username -> user_info
        self.user_sessions: Dict[str, str] = {}  # client_id -> username
        self.lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def validate_username(self, username: str) -> bool:
        """Validate username format and availability."""
        if not username:
            return False
        
        # Remove whitespace and check length
        username = username.strip()
        if len(username) < 1 or len(username) > 20:
            return False
        
        # Check for invalid characters (alphanumeric, spaces, underscores, hyphens only)
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-')
        if not all(c in allowed_chars for c in username):
            return False
        
        # Check if username is already taken
        with self.lock:
            return username not in self.active_users
    
    def authenticate_user(self, username: str, client_id: str) -> bool:
        """Authenticate a user and create a session."""
        username = username.strip()
        
        if not self.validate_username(username):
            self.logger.warning(f"Authentication failed for username: '{username}'")
            return False
        
        with self.lock:
            # Check if client already has a session
            if client_id in self.user_sessions:
                old_username = self.user_sessions[client_id]
                self.logger.info(f"Client {client_id} already authenticated as {old_username}")
                return True
            
            # Create user session
            self.active_users[username] = {
                'client_id': client_id,
                'join_time': datetime.now(),
                'last_activity': datetime.now()
            }
            self.user_sessions[client_id] = username
            
            self.logger.info(f"User '{username}' authenticated with client {client_id}")
            return True
    
    def get_username(self, client_id: str) -> Optional[str]:
        """Get username for a client ID."""
        with self.lock:
            return self.user_sessions.get(client_id)
    
    def get_client_id(self, username: str) -> Optional[str]:
        """Get client ID for a username."""
        with self.lock:
            user_info = self.active_users.get(username)
            return user_info['client_id'] if user_info else None
    
    def get_active_usernames(self) -> list:
        """Get list of all active usernames."""
        with self.lock:
            return list(self.active_users.keys())
    
    def get_user_count(self) -> int:
        """Get number of active users."""
        with self.lock:
            return len(self.active_users)
    
    def disconnect_user(self, client_id: str) -> Optional[str]:
        """Disconnect a user and clean up their session."""
        with self.lock:
            username = self.user_sessions.pop(client_id, None)
            if username:
                self.active_users.pop(username, None)
                self.logger.info(f"User '{username}' disconnected (client {client_id})")
                return username
            return None
    
    def update_activity(self, username: str):
        """Update last activity time for a user."""
        with self.lock:
            if username in self.active_users:
                self.active_users[username]['last_activity'] = datetime.now()
    
    def is_user_online(self, username: str) -> bool:
        """Check if a user is currently online."""
        with self.lock:
            return username in self.active_users
    
    def get_user_info(self, username: str) -> Optional[dict]:
        """Get user information."""
        with self.lock:
            return self.active_users.get(username)
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 30):
        """Clean up inactive sessions (for future use)."""
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        with self.lock:
            inactive_users = []
            for username, user_info in self.active_users.items():
                if user_info['last_activity'] < cutoff_time:
                    inactive_users.append(username)
            
            for username in inactive_users:
                user_info = self.active_users.pop(username, None)
                if user_info:
                    self.user_sessions.pop(user_info['client_id'], None)
                    self.logger.info(f"Cleaned up inactive session for user '{username}'")
