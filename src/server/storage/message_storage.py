"""
Message storage system for chat room persistence.
"""

import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime
try:
    from ...shared.message_types import ChatMessage, SystemMessage
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from shared.message_types import ChatMessage, SystemMessage


class MessageStorage:
    """Stores chat messages in server memory for persistence across user sessions."""
    
    def __init__(self, max_messages_per_context: int = 1000):
        self.max_messages_per_context = max_messages_per_context
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Storage structure: context_id -> list of messages
        # context_id can be "common" for public messages or "private_user1_user2" for private messages
        self.messages: Dict[str, List[dict]] = {}
        
        # Track message counts per context
        self.message_counts: Dict[str, int] = {}
    
    def store_message(self, message, context_id: str = "common"):
        """Store a message in the specified context."""
        with self.lock:
            if context_id not in self.messages:
                self.messages[context_id] = []
                self.message_counts[context_id] = 0
            
            # Create message record
            message_record = {
                'content': message.content if hasattr(message, 'content') else str(message),
                'sender': message.sender if hasattr(message, 'sender') else 'system',
                'timestamp': datetime.now(),
                'message_type': 'chat' if isinstance(message, ChatMessage) else 'system',
                'is_private': getattr(message, 'is_private', False)
            }
            
            # Add to storage
            self.messages[context_id].append(message_record)
            self.message_counts[context_id] += 1
            
            # Maintain max message limit
            if len(self.messages[context_id]) > self.max_messages_per_context:
                self.messages[context_id].pop(0)  # Remove oldest message
                self.message_counts[context_id] -= 1
            
            self.logger.debug(f"Stored message in context '{context_id}': {message_record['content'][:50]}...")
    
    def get_messages(self, context_id: str = "common", limit: Optional[int] = None) -> List[dict]:
        """Get messages from the specified context."""
        with self.lock:
            if context_id not in self.messages:
                return []
            
            messages = self.messages[context_id].copy()
            
            if limit and len(messages) > limit:
                messages = messages[-limit:]  # Get most recent messages
            
            return messages
    
    def get_private_contexts_for_user(self, username: str) -> List[str]:
        """Get all private contexts that involve the specified user."""
        with self.lock:
            private_contexts = []
            for context_id in self.messages.keys():
                if context_id != "common" and username in context_id:
                    private_contexts.append(context_id)
            return private_contexts
    
    def get_all_contexts(self) -> List[str]:
        """Get all available contexts."""
        with self.lock:
            return list(self.messages.keys())
    
    def get_message_count(self, context_id: str = "common") -> int:
        """Get the number of messages in a context."""
        with self.lock:
            return self.message_counts.get(context_id, 0)
    
    def clear_context(self, context_id: str):
        """Clear all messages from a specific context."""
        with self.lock:
            if context_id in self.messages:
                del self.messages[context_id]
                del self.message_counts[context_id]
                self.logger.info(f"Cleared context '{context_id}'")
    
    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        with self.lock:
            total_messages = sum(self.message_counts.values())
            return {
                'total_contexts': len(self.messages),
                'total_messages': total_messages,
                'contexts': {context: count for context, count in self.message_counts.items()}
            }
