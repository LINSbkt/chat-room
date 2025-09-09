"""
Authentication message classes.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .base import Message
from .enums import MessageType


class AuthRequest(Message):
    """Authentication request message."""
    
    def __init__(self, username: str):
        data = {'username': username}
        super().__init__(
            message_type=MessageType.AUTH_REQUEST,
            data=data,
            sender=username
        )
    
    @property
    def username(self) -> str:
        return self.data['username']


class AuthResponse(Message):
    """Authentication response message."""
    
    def __init__(self, status: str, message: str = "", sender: Optional[str] = None):
        data = {
            'status': status,
            'message': message
        }
        super().__init__(
            message_type=MessageType.AUTH_RESPONSE,
            data=data,
            sender=sender
        )
    
    @property
    def status(self) -> str:
        return self.data['status']
    
    @property
    def auth_message(self) -> str:
        return self.data.get('message', '')