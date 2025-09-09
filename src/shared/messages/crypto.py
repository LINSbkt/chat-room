"""
Cryptographic message classes.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .base import Message
from .enums import MessageType


class KeyExchangeMessage(Message):
    """Message class for RSA key exchange."""
    
    def __init__(self, public_key: str, sender: str):
        data = {'public_key': public_key}
        super().__init__(
            message_type=MessageType.KEY_EXCHANGE_REQUEST,
            data=data,
            sender=sender
        )
    
    @property
    def public_key(self) -> str:
        return self.data['public_key']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyExchangeMessage':
        """Create KeyExchangeMessage from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            public_key=data['data']['public_key'],
            sender=data['sender']
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message


class AESKeyMessage(Message):
    """Message class for AES key exchange."""
    
    def __init__(self, encrypted_aes_key: str, sender: str, recipient: str):
        data = {'encrypted_aes_key': encrypted_aes_key}
        super().__init__(
            message_type=MessageType.AES_KEY_EXCHANGE,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def encrypted_aes_key(self) -> str:
        return self.data['encrypted_aes_key']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AESKeyMessage':
        """Create AESKeyMessage from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            encrypted_aes_key=data['data']['encrypted_aes_key'],
            sender=data['sender'],
            recipient=data['recipient']
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message


class EncryptedMessage(Message):
    """Message class for encrypted messages."""
    
    def __init__(self, encrypted_content: str, sender: str, recipient: Optional[str] = None, 
                 is_private: bool = False):
        data = {
            'encrypted_content': encrypted_content,
            'is_private': is_private
        }
        
        if is_private and recipient:
            data['recipient'] = recipient
        
        super().__init__(
            message_type=MessageType.ENCRYPTED_MESSAGE,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def encrypted_content(self) -> str:
        return self.data['encrypted_content']
    
    @property
    def is_private(self) -> bool:
        return self.data['is_private']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EncryptedMessage':
        """Create EncryptedMessage from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            encrypted_content=data['data']['encrypted_content'],
            sender=data['sender'],
            recipient=data.get('recipient'),
            is_private=data['data']['is_private']
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message