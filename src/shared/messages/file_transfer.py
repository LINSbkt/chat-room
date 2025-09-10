"""
File transfer message classes.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from .base import Message
from .enums import MessageType


class FileTransferRequest(Message):
    """Message class for file transfer requests."""
    
    def __init__(self, filename: str, file_size: int, file_hash: str, 
                 sender: str, recipient: str, is_private: bool = True):
        data = {
            'filename': filename,
            'file_size': file_size,
            'file_hash': file_hash,
            'is_private': is_private,
            'transfer_id': None
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
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            filename=data['data']['filename'],
            file_size=data['data']['file_size'],
            file_hash=data['data']['file_hash'],
            sender=data['sender'],
            recipient=data['recipient'],
            is_private=data['data']['is_private']
        )
        
        if 'transfer_id' in data['data'] and data['data']['transfer_id']:
            message.set_transfer_id(data['data']['transfer_id'])
        
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
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            transfer_id=data['data']['transfer_id'],
            accepted=data['data']['accepted'],
            reason=data['data'].get('reason'),
            sender=data.get('sender'),
            recipient=data.get('recipient')
        )
        
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
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            transfer_id=data['data']['transfer_id'],
            chunk_index=data['data']['chunk_index'],
            total_chunks=data['data']['total_chunks'],
            chunk_data=data['data']['chunk_data'],
            sender=data['sender'],
            recipient=data['recipient']
        )
        
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
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            transfer_id=data['data']['transfer_id'],
            success=data['data']['success'],
            final_hash=data['data'].get('final_hash'),
            error_message=data['data'].get('error_message'),
            sender=data.get('sender'),
            recipient=data.get('recipient')
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message


class FileListRequest(Message):
    """Message class for requesting available files."""
    
    def __init__(self, sender: str):
        data = {}
        
        super().__init__(
            message_type=MessageType.FILE_LIST_REQUEST,
            data=data,
            sender=sender
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileListRequest':
        """Create FileListRequest from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(sender=data['sender'])
        
        if timestamp:
            message.timestamp = timestamp
        
        return message


class FileListResponse(Message):
    """Message class for file list responses."""
    
    def __init__(self, files: list, sender: str = None, recipient: str = None):
        data = {
            'files': files
        }
        
        super().__init__(
            message_type=MessageType.FILE_LIST_RESPONSE,
            data=data,
            sender=sender,
            recipient=recipient
        )
    
    @property
    def files(self) -> list:
        return self.data['files']
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileListResponse':
        """Create FileListResponse from dictionary."""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        message = cls(
            files=data['data']['files'],
            sender=data.get('sender'),
            recipient=data.get('recipient')
        )
        
        if timestamp:
            message.timestamp = timestamp
        
        return message