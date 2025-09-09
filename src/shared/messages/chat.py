"""
Chat-related message classes.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .base import Message
from .enums import MessageType


class ChatMessage(Message):
    """Message class for chat messages."""
    
    def __init__(self, content: str, sender: str, recipient: Optional[str] = None, 
                 is_private: bool = False):
        data = {
            'content': content,
            'is_private': is_private
        }
        
        if is_private and recipient:
            data['recipient'] = recipient
        
        super().__init__(
            message_type=MessageType.PRIVATE_MESSAGE if is_private else MessageType.PUBLIC_MESSAGE,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def content(self) -> str:
        return self.data['content']
    
    @property
    def is_private(self) -> bool:
        return self.data['is_private']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create ChatMessage from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            content=data['data']['content'],
            sender=data['sender'],
            recipient=data.get('recipient'),
            is_private=data['data']['is_private']
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message


class SystemMessage(Message):
    """Message class for system notifications."""
    
    def __init__(self, content: str, message_type: str = "info"):
        data = {
            'content': content,
            'system_message_type': message_type
        }
        super().__init__(
            message_type=MessageType.SYSTEM_MESSAGE,
            data=data
        )
    
    @property
    def content(self) -> str:
        return self.data['content']
    
    @property
    def system_message_type(self) -> str:
        return self.data['system_message_type']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemMessage':
        """Create SystemMessage from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            content=data['data']['content'],
            message_type=data['data']['system_message_type']
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message


class UserListMessage(Message):
    """Message class for user list updates."""
    
    def __init__(self, users: list, sender: Optional[str] = None):
        data = {'users': users}
        super().__init__(
            message_type=MessageType.USER_LIST_RESPONSE,
            data=data,
            sender=sender
        )
    
    @property
    def users(self) -> list:
        return self.data['users']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserListMessage':
        """Create UserListMessage from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            users=data['data']['users'],
            sender=data.get('sender')
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message