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
    
    # Encryption messages
    KEY_EXCHANGE_REQUEST = "KEY_EXCHANGE_REQUEST"
    KEY_EXCHANGE_RESPONSE = "KEY_EXCHANGE_RESPONSE"
    AES_KEY_EXCHANGE = "AES_KEY_EXCHANGE"
    ENCRYPTED_MESSAGE = "ENCRYPTED_MESSAGE"


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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create ChatMessage from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            content=data['data']['content'],
            sender=data['sender'],
            recipient=data.get('recipient'),
            is_private=data['data']['is_private']
        )
        
        # Set timestamp if provided
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
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            content=data['data']['content'],
            message_type=data['data']['system_message_type']
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message


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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserListMessage':
        """Create UserListMessage from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            users=data['data']['users'],
            sender=data.get('sender')
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message


class KeyExchangeMessage(Message):
    """Message class for RSA key exchange."""
    
    def __init__(self, public_key: str, sender: str):
        data = {
            'public_key': public_key
        }
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
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            public_key=data['data']['public_key'],
            sender=data['sender']
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message


class AESKeyMessage(Message):
    """Message class for AES key exchange."""
    
    def __init__(self, encrypted_aes_key: str, sender: str, recipient: str):
        data = {
            'encrypted_aes_key': encrypted_aes_key
        }
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
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            encrypted_aes_key=data['data']['encrypted_aes_key'],
            sender=data['sender'],
            recipient=data['recipient']
        )
        
        # Set timestamp if provided
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
        
        # Add recipient to data if it's a private message
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
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            encrypted_content=data['data']['encrypted_content'],
            sender=data['sender'],
            recipient=data.get('recipient'),
            is_private=data['data']['is_private']
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message


class FileTransferRequest(Message):
    """Message class for file transfer requests."""
    
    def __init__(self, filename: str, file_size: int, file_hash: str, 
                 sender: str, recipient: str, is_private: bool = True):
        data = {
            'filename': filename,
            'file_size': file_size,
            'file_hash': file_hash,
            'is_private': is_private,
            'transfer_id': None  # Will be set by the client
        }
        
        super().__init__(
            message_type=MessageType.FILE_TRANSFER_REQUEST,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def filename(self) -> str:
        return self.data['filename']
    
    @property
    def file_size(self) -> int:
        return self.data['file_size']
    
    @property
    def file_hash(self) -> str:
        return self.data['file_hash']
    
    @property
    def is_private(self) -> bool:
        return self.data['is_private']
    
    @property
    def transfer_id(self) -> Optional[str]:
        return self.data.get('transfer_id')
    
    def set_transfer_id(self, transfer_id: str):
        """Set the transfer ID for this request."""
        self.data['transfer_id'] = transfer_id
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileTransferRequest':
        """Create FileTransferRequest from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            filename=data['data']['filename'],
            file_size=data['data']['file_size'],
            file_hash=data['data']['file_hash'],
            sender=data['sender'],
            recipient=data['recipient'],
            is_private=data['data']['is_private']
        )
        
        # Set transfer_id if provided
        if 'transfer_id' in data['data'] and data['data']['transfer_id']:
            message.set_transfer_id(data['data']['transfer_id'])
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message


class FileTransferResponse(Message):
    """Message class for file transfer responses (accept/decline)."""
    
    def __init__(self, transfer_id: str, accepted: bool, reason: Optional[str] = None,
                 sender: str = None, recipient: str = None):
        data = {
            'transfer_id': transfer_id,
            'accepted': accepted,
            'reason': reason
        }
        
        super().__init__(
            message_type=MessageType.FILE_TRANSFER_RESPONSE,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def transfer_id(self) -> str:
        return self.data['transfer_id']
    
    @property
    def accepted(self) -> bool:
        return self.data['accepted']
    
    @property
    def reason(self) -> Optional[str]:
        return self.data.get('reason')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileTransferResponse':
        """Create FileTransferResponse from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            transfer_id=data['data']['transfer_id'],
            accepted=data['data']['accepted'],
            reason=data['data'].get('reason'),
            sender=data.get('sender'),
            recipient=data.get('recipient')
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message


class FileChunk(Message):
    """Message class for file data chunks."""
    
    def __init__(self, transfer_id: str, chunk_index: int, total_chunks: int, 
                 chunk_data: str, sender: str, recipient: str):
        data = {
            'transfer_id': transfer_id,
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'chunk_data': chunk_data
        }
        
        super().__init__(
            message_type=MessageType.FILE_CHUNK,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def transfer_id(self) -> str:
        return self.data['transfer_id']
    
    @property
    def chunk_index(self) -> int:
        return self.data['chunk_index']
    
    @property
    def total_chunks(self) -> int:
        return self.data['total_chunks']
    
    @property
    def chunk_data(self) -> str:
        return self.data['chunk_data']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileChunk':
        """Create FileChunk from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            transfer_id=data['data']['transfer_id'],
            chunk_index=data['data']['chunk_index'],
            total_chunks=data['data']['total_chunks'],
            chunk_data=data['data']['chunk_data'],
            sender=data['sender'],
            recipient=data['recipient']
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message


class FileTransferComplete(Message):
    """Message class for file transfer completion notifications."""
    
    def __init__(self, transfer_id: str, success: bool, final_hash: Optional[str] = None,
                 error_message: Optional[str] = None, sender: str = None, recipient: str = None):
        data = {
            'transfer_id': transfer_id,
            'success': success,
            'final_hash': final_hash,
            'error_message': error_message
        }
        
        super().__init__(
            message_type=MessageType.FILE_TRANSFER_COMPLETE,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def transfer_id(self) -> str:
        return self.data['transfer_id']
    
    @property
    def success(self) -> bool:
        return self.data['success']
    
    @property
    def final_hash(self) -> Optional[str]:
        return self.data.get('final_hash')
    
    @property
    def error_message(self) -> Optional[str]:
        return self.data.get('error_message')
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileTransferComplete':
        """Create FileTransferComplete from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            transfer_id=data['data']['transfer_id'],
            success=data['data']['success'],
            final_hash=data['data'].get('final_hash'),
            error_message=data['data'].get('error_message'),
            sender=data.get('sender'),
            recipient=data.get('recipient')
        )
        
        # Set timestamp if provided
        if timestamp:
            message.timestamp = timestamp
        
        return message
