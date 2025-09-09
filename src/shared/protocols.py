"""
Communication protocols for the chatroom application.
"""

import json
import socket
from typing import Optional, Dict, Any
from .message_types import Message


class Protocol:
    """Base protocol class for message serialization and network communication."""
    
    @staticmethod
    def serialize_message(message: Message) -> bytes:
        """Serialize a message to bytes for network transmission."""
        try:
            message_dict = message.to_dict()
            json_str = json.dumps(message_dict, ensure_ascii=False)
            # Add message length prefix
            length = len(json_str.encode('utf-8'))
            return f"{length:10d}{json_str}".encode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to serialize message: {e}")
    
    @staticmethod
    def deserialize_message(data: bytes) -> Message:
        """Deserialize bytes to a message object."""
        try:
            # Extract message length
            length_str = data[:10].decode('utf-8')
            length = int(length_str)
            
            # Extract JSON data
            json_data = data[10:10+length].decode('utf-8')
            message_dict = json.loads(json_data)
            
            # Create the appropriate message type based on message_type
            message_type_str = message_dict.get('message_type')
            if message_type_str:
                from .message_types import (MessageType, ChatMessage, SystemMessage, UserListMessage, 
                                          KeyExchangeMessage, AESKeyMessage, EncryptedMessage,
                                          FileTransferRequest, FileTransferResponse, FileChunk, FileTransferComplete)
                
                message_type = MessageType(message_type_str)
                
                # Create the appropriate message class based on type
                if message_type == MessageType.PUBLIC_MESSAGE or message_type == MessageType.PRIVATE_MESSAGE:
                    return ChatMessage.from_dict(message_dict)
                elif message_type == MessageType.SYSTEM_MESSAGE:
                    return SystemMessage.from_dict(message_dict)
                elif message_type == MessageType.USER_LIST_RESPONSE:
                    return UserListMessage.from_dict(message_dict)
                elif message_type == MessageType.KEY_EXCHANGE_REQUEST:
                    return KeyExchangeMessage.from_dict(message_dict)
                elif message_type == MessageType.AES_KEY_EXCHANGE:
                    return AESKeyMessage.from_dict(message_dict)
                elif message_type == MessageType.ENCRYPTED_MESSAGE:
                    return EncryptedMessage.from_dict(message_dict)
                elif message_type == MessageType.FILE_TRANSFER_REQUEST:
                    return FileTransferRequest.from_dict(message_dict)
                elif message_type == MessageType.FILE_TRANSFER_RESPONSE:
                    return FileTransferResponse.from_dict(message_dict)
                elif message_type == MessageType.FILE_CHUNK:
                    return FileChunk.from_dict(message_dict)
                elif message_type == MessageType.FILE_TRANSFER_COMPLETE:
                    return FileTransferComplete.from_dict(message_dict)
                elif message_type == MessageType.AUTH_RESPONSE:
                    # AUTH_RESPONSE is a generic Message type
                    return Message.from_dict(message_dict)
                elif message_type == MessageType.AUTH_REQUEST:
                    # AUTH_REQUEST is a generic Message type
                    return Message.from_dict(message_dict)
                elif message_type == MessageType.ERROR_MESSAGE:
                    # ERROR_MESSAGE is a generic Message type
                    return Message.from_dict(message_dict)
                elif message_type == MessageType.USER_LIST_REQUEST:
                    # USER_LIST_REQUEST is a generic Message type
                    return Message.from_dict(message_dict)
                elif message_type == MessageType.DISCONNECT:
                    # DISCONNECT is a generic Message type
                    return Message.from_dict(message_dict)
            
            # Fallback to generic Message
            return Message.from_dict(message_dict)
        except Exception as e:
            raise ValueError(f"Failed to deserialize message: {e}")
    
    @staticmethod
    def send_message(socket: socket.socket, message: Message) -> bool:
        """Send a message through a socket."""
        try:
            data = Protocol.serialize_message(message)
            socket.sendall(data)
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
    
    @staticmethod
    def receive_message(socket: socket.socket) -> Optional[Message]:
        """Receive a message from a socket."""
        try:
            # First, receive the length prefix
            length_data = b''
            while len(length_data) < 10:
                chunk = socket.recv(10 - len(length_data))
                if not chunk:
                    return None
                length_data += chunk
            
            length = int(length_data.decode('utf-8'))
            
            # Then receive the actual message
            message_data = b''
            while len(message_data) < length:
                chunk = socket.recv(min(4096, length - len(message_data)))
                if not chunk:
                    return None
                message_data += chunk
            
            return Protocol.deserialize_message(length_data + message_data)
        except Exception as e:
            print(f"Failed to receive message: {e}")
            return None


class ConnectionManager:
    """Manages socket connections and message handling."""
    
    def __init__(self, socket: socket.socket):
        self.socket = socket
        self.connected = True
    
    def send_message(self, message: Message) -> bool:
        """Send a message through the connection."""
        if not self.connected:
            return False
        return Protocol.send_message(self.socket, message)
    
    def receive_message(self) -> Optional[Message]:
        """Receive a message from the connection."""
        if not self.connected:
            return None
        return Protocol.receive_message(self.socket)
    
    def close(self):
        """Close the connection."""
        self.connected = False
        try:
            self.socket.close()
        except:
            pass
    
    def is_connected(self) -> bool:
        """Check if the connection is still active."""
        if not self.connected:
            return False
        
        # Check if socket is still connected by trying to get socket info
        try:
            # This will raise an exception if the socket is closed
            self.socket.getpeername()
            return True
        except (OSError, socket.error):
            self.connected = False
            return False

