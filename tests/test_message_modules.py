"""
Tests for the refactored message modular structure.
"""

import os
import sys
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shared.messages.enums import MessageType
from shared.messages.base import Message
from shared.messages.auth import AuthRequest, AuthResponse
from shared.messages.chat import ChatMessage, SystemMessage, UserListMessage
from shared.messages.crypto import KeyExchangeMessage, AESKeyMessage, EncryptedMessage
from shared.messages.file_transfer import FileTransferRequest, FileTransferResponse, FileChunk, FileTransferComplete


class TestMessageModules(unittest.TestCase):
    """Test the new modular message structure."""
    
    def test_message_type_enum(self):
        """Test MessageType enum."""
        self.assertEqual(MessageType.AUTH_REQUEST.value, "AUTH_REQUEST")
        self.assertEqual(MessageType.PUBLIC_MESSAGE.value, "PUBLIC_MESSAGE")
        self.assertEqual(MessageType.FILE_TRANSFER_REQUEST.value, "FILE_TRANSFER_REQUEST")
    
    def test_base_message(self):
        """Test base Message class."""
        msg = Message(MessageType.AUTH_REQUEST, {"username": "test"}, "sender")
        
        self.assertEqual(msg.message_type, MessageType.AUTH_REQUEST)
        self.assertEqual(msg.data["username"], "test")
        self.assertEqual(msg.sender, "sender")
        self.assertIsNotNone(msg.message_id)
        self.assertIsNotNone(msg.timestamp)
    
    def test_auth_messages(self):
        """Test authentication message classes."""
        # Test AuthRequest
        auth_req = AuthRequest("testuser")
        self.assertEqual(auth_req.message_type, MessageType.AUTH_REQUEST)
        self.assertEqual(auth_req.username, "testuser")
        
        # Test AuthResponse
        auth_resp = AuthResponse("success", "Welcome!")
        self.assertEqual(auth_resp.message_type, MessageType.AUTH_RESPONSE)
        self.assertEqual(auth_resp.status, "success")
        self.assertEqual(auth_resp.auth_message, "Welcome!")
    
    def test_chat_messages(self):
        """Test chat message classes."""
        # Test ChatMessage
        chat_msg = ChatMessage("Hello world", "user1")
        self.assertEqual(chat_msg.message_type, MessageType.PUBLIC_MESSAGE)
        self.assertEqual(chat_msg.content, "Hello world")
        self.assertFalse(chat_msg.is_private)
        
        # Test private ChatMessage
        private_msg = ChatMessage("Private message", "user1", "user2", True)
        self.assertEqual(private_msg.message_type, MessageType.PRIVATE_MESSAGE)
        self.assertTrue(private_msg.is_private)
        
        # Test SystemMessage
        sys_msg = SystemMessage("System notification", "info")
        self.assertEqual(sys_msg.message_type, MessageType.SYSTEM_MESSAGE)
        self.assertEqual(sys_msg.content, "System notification")
        self.assertEqual(sys_msg.system_message_type, "info")
        
        # Test UserListMessage
        user_list = UserListMessage(["user1", "user2", "user3"])
        self.assertEqual(user_list.message_type, MessageType.USER_LIST_RESPONSE)
        self.assertEqual(user_list.users, ["user1", "user2", "user3"])
    
    def test_crypto_messages(self):
        """Test cryptographic message classes."""
        # Test KeyExchangeMessage
        key_msg = KeyExchangeMessage("public_key_data", "sender")
        self.assertEqual(key_msg.message_type, MessageType.KEY_EXCHANGE_REQUEST)
        self.assertEqual(key_msg.public_key, "public_key_data")
        
        # Test AESKeyMessage
        aes_msg = AESKeyMessage("encrypted_aes_key", "sender", "recipient")
        self.assertEqual(aes_msg.message_type, MessageType.AES_KEY_EXCHANGE)
        self.assertEqual(aes_msg.encrypted_aes_key, "encrypted_aes_key")
        
        # Test EncryptedMessage
        enc_msg = EncryptedMessage("encrypted_content", "sender", "recipient", True)
        self.assertEqual(enc_msg.message_type, MessageType.ENCRYPTED_MESSAGE)
        self.assertEqual(enc_msg.encrypted_content, "encrypted_content")
        self.assertTrue(enc_msg.is_private)
    
    def test_file_transfer_messages(self):
        """Test file transfer message classes."""
        # Test FileTransferRequest
        file_req = FileTransferRequest("test.txt", 1024, "hash123", "sender", "recipient")
        self.assertEqual(file_req.message_type, MessageType.FILE_TRANSFER_REQUEST)
        self.assertEqual(file_req.filename, "test.txt")
        self.assertEqual(file_req.file_size, 1024)
        self.assertEqual(file_req.file_hash, "hash123")
        
        # Test FileTransferResponse
        file_resp = FileTransferResponse("transfer123", True, "Accepted")
        self.assertEqual(file_resp.message_type, MessageType.FILE_TRANSFER_RESPONSE)
        self.assertEqual(file_resp.transfer_id, "transfer123")
        self.assertTrue(file_resp.accepted)
        self.assertEqual(file_resp.reason, "Accepted")
        
        # Test FileChunk
        chunk = FileChunk("transfer123", 0, 5, "chunk_data", "sender", "recipient")
        self.assertEqual(chunk.message_type, MessageType.FILE_CHUNK)
        self.assertEqual(chunk.transfer_id, "transfer123")
        self.assertEqual(chunk.chunk_index, 0)
        self.assertEqual(chunk.total_chunks, 5)
        
        # Test FileTransferComplete
        complete = FileTransferComplete("transfer123", True, "final_hash")
        self.assertEqual(complete.message_type, MessageType.FILE_TRANSFER_COMPLETE)
        self.assertEqual(complete.transfer_id, "transfer123")
        self.assertTrue(complete.success)
        self.assertEqual(complete.final_hash, "final_hash")
    
    def test_backward_compatibility(self):
        """Test that old imports still work through compatibility layer."""
        # This tests the compatibility layer in message_types.py
        from shared.message_types import MessageType as OldMessageType
        from shared.message_types import ChatMessage as OldChatMessage
        
        # Create message using old import
        old_msg = OldChatMessage("test", "user1")
        
        # Should work exactly the same as new import
        from shared.messages.chat import ChatMessage as NewChatMessage
        new_msg = NewChatMessage("test", "user1")
        
        self.assertEqual(old_msg.message_type, new_msg.message_type)
        self.assertEqual(old_msg.content, new_msg.content)
        self.assertEqual(old_msg.sender, new_msg.sender)
    
    def test_serialization(self):
        """Test message serialization/deserialization still works."""
        # Test with a complex message
        chat_msg = ChatMessage("Hello world", "user1", "user2", True)
        
        # Serialize to dict
        msg_dict = chat_msg.to_dict()
        
        # Deserialize back
        restored_msg = ChatMessage.from_dict(msg_dict)
        
        # Should be identical
        self.assertEqual(chat_msg.content, restored_msg.content)
        self.assertEqual(chat_msg.sender, restored_msg.sender)
        self.assertEqual(chat_msg.recipient, restored_msg.recipient)
        self.assertEqual(chat_msg.is_private, restored_msg.is_private)
        self.assertEqual(chat_msg.message_type, restored_msg.message_type)


if __name__ == '__main__':
    unittest.main()