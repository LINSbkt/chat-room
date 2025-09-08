"""
Message type definitions for the chatroom application.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime


class MessageType(Enum):
    """Enumeration of message types."""
    # Connection messages
    CONNECT = "CONNECT"
    DISCONNECT = "DISCONNECT"
    
    # Authentication messages
    AUTH_REQUEST = "AUTH_REQUEST"
    AUTH_RESPONSE = "AUTH_RESPONSE"
    
    # Messaging
    PUBLIC_MESSAGE = "PUBLIC_MESSAGE"
    PRIVATE_MESSAGE = "PRIVATE_MESSAGE"
    
    # User management
    USER_LIST_REQUEST = "USER_LIST_REQUEST"
    USER_LIST_RESPONSE = "USER_LIST_RESPONSE"
    USER_JOINED = "USER_JOINED"
    USER_LEFT = "USER_LEFT"
    
    # File transfer
    FILE_TRANSFER_REQUEST = "FILE_TRANSFER_REQUEST"
    FILE_TRANSFER_RESPONSE = "FILE_TRANSFER_RESPONSE"
    FILE_CHUNK = "FILE_CHUNK"
    FILE_TRANSFER_COMPLETE = "FILE_TRANSFER_COMPLETE"
    
    # System messages
    SYSTEM_MESSAGE = "SYSTEM_MESSAGE"
    ERROR_MESSAGE = "ERROR_MESSAGE"


class Message:
    """Base message class for all communication."""
    
    def __init__(self, message_type: MessageType, data: Dict[str, Any], 
                 sender: Optional[str] = None, recipient: Optional[str] = None):
        self.message_type = message_type
        self.data = data
        self.sender = sender
        self.recipient = recipient
        self.timestamp = datetime.now()
        self.message_id = self._generate_message_id()
    
    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        import uuid
        return str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            'message_type': self.message_type.value,
            'data': self.data,
            'sender': self.sender,
            'recipient': self.recipient,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            message_type=MessageType(data['message_type']),
            data=data['data'],
            sender=data.get('sender'),
            recipient=data.get('recipient')
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message
    
    def __str__(self) -> str:
        return f"Message({self.message_type.value}, from={self.sender}, to={self.recipient})"


class ChatMessage(Message):
    """Message class for chat messages."""
    
    def __init__(self, content: str, sender: str, recipient: Optional[str] = None, 
                 is_private: bool = False):
        data = {
            'content': content,
            'is_private': is_private
        }
        
        # Add recipient to data if it's a private message
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


class UserListMessage(Message):
    """Message class for user list updates."""
    
    def __init__(self, users: list, sender: Optional[str] = None):
        data = {
            'users': users
        }
        super().__init__(
            message_type=MessageType.USER_LIST_RESPONSE,
            data=data,
            sender=sender
        )
    
    @property
    def users(self) -> list:
        return self.data['users']
