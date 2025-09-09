"""
Base message classes.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .enums import MessageType


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
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            message_type=MessageType(data['message_type']),
            data=data['data'],
            sender=data.get('sender'),
            recipient=data.get('recipient')
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message
    
    def __str__(self) -> str:
        return f"Message({self.message_type.value}, from={self.sender}, to={self.recipient})"