"""
Chat context manager for handling multiple chat conversations.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid

from ...core.event_bus import EventBus, Event, ChatEvents
from ...core.state_manager import StateManager, StateKeys
from ..base.base_component import BaseComponent

logger = logging.getLogger(__name__)


@dataclass
class ChatContext:
    """Represents a chat context (conversation)."""
    context_id: str
    context_type: str  # "public" or "private"
    name: str
    participants: List[str] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ChatContextManager(BaseComponent):
    """Manages chat contexts and switching between conversations."""
    
    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent=None):
        super().__init__(component_id, event_bus, state_manager, parent)
        
        self._contexts: Dict[str, ChatContext] = {}
        self._current_context_id: Optional[str] = None
        
        # Initialize with common chat context
        self._create_common_chat_context()
    
    def setup_ui(self) -> None:
        """Set up UI (not needed for context manager)."""
        pass
    
    def setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.subscribe_to_event(ChatEvents.USER_SELECTED, self._handle_user_selected)
        self.subscribe_to_event(ChatEvents.COMMON_CHAT_SELECTED, self._handle_common_chat_selected)
        self.subscribe_to_event(ChatEvents.MESSAGE_RECEIVED, self._handle_message_received)
        self.subscribe_to_event(ChatEvents.MESSAGE_SENT, self._handle_message_sent)
    
    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions."""
        self.subscribe_to_state(StateKeys.CURRENT_USER)
        self.subscribe_to_state(StateKeys.USER_LIST)
    
    def on_initialize(self) -> None:
        """Initialize the context manager."""
        # Set initial state
        self._update_state()
        logger.info("Chat context manager initialized")
    
    def _create_common_chat_context(self) -> None:
        """Create the common (public) chat context."""
        common_context = ChatContext(
            context_id="common",
            context_type="public",
            name="Common Chat",
            participants=["all"],  # All users
            metadata={"is_common": True}
        )
        
        self._contexts["common"] = common_context
        self._current_context_id = "common"
        
        logger.debug("Created common chat context")
    
    def create_private_context(self, user: str) -> str:
        """
        Create a private chat context with a user.
        
        Args:
            user: Username to create private chat with
            
        Returns:
            Context ID of the created context
        """
        current_user = self.get_state(StateKeys.CURRENT_USER)
        if not current_user:
            logger.error("Cannot create private context: no current user")
            return None
        
        # Check if context already exists
        existing_context = self._find_private_context_with_user(user)
        if existing_context:
            logger.debug(f"Private context with {user} already exists: {existing_context.context_id}")
            return existing_context.context_id
        
        # Create new private context
        context_id = f"private_{user}_{uuid.uuid4().hex[:8]}"
        private_context = ChatContext(
            context_id=context_id,
            context_type="private",
            name=f"Private: {user}",
            participants=[current_user, user],
            metadata={"private_with": user}
        )
        
        self._contexts[context_id] = private_context
        
        # Publish context created event
        self.publish_event(ChatEvents.CONTEXT_CREATED, {
            "context_id": context_id,
            "context_type": "private",
            "user": user
        })
        
        logger.info(f"Created private context with {user}: {context_id}")
        return context_id
    
    def switch_to_context(self, context_id: str) -> bool:
        """
        Switch to a specific chat context.
        
        Args:
            context_id: ID of the context to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if context_id not in self._contexts:
            logger.error(f"Context not found: {context_id}")
            return False
        
        old_context_id = self._current_context_id
        self._current_context_id = context_id
        
        # Update last activity for old context
        if old_context_id and old_context_id in self._contexts:
            self._contexts[old_context_id].last_activity = datetime.now()
        
        # Update state
        self._update_state()
        
        # Publish context switched event
        self.publish_event(ChatEvents.CONTEXT_SWITCHED, {
            "old_context_id": old_context_id,
            "new_context_id": context_id,
            "context_type": self._contexts[context_id].context_type
        })
        
        logger.info(f"Switched to context: {context_id} (from {old_context_id})")
        return True
    
    def get_current_context(self) -> Optional[ChatContext]:
        """Get the current chat context."""
        if self._current_context_id:
            return self._contexts.get(self._current_context_id)
        return None
    
    def get_context(self, context_id: str) -> Optional[ChatContext]:
        """Get a specific chat context."""
        return self._contexts.get(context_id)
    
    def get_all_contexts(self) -> Dict[str, ChatContext]:
        """Get all chat contexts."""
        return self._contexts.copy()
    
    def get_context_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all contexts for UI display.
        
        Returns:
            List of context information dictionaries
        """
        contexts = []
        
        for context in self._contexts.values():
            contexts.append({
                "context_id": context.context_id,
                "name": context.name,
                "type": context.context_type,
                "participants": context.participants,
                "message_count": len(context.messages),
                "last_activity": context.last_activity,
                "is_current": context.context_id == self._current_context_id
            })
        
        # Sort by last activity (most recent first)
        contexts.sort(key=lambda x: x["last_activity"], reverse=True)
        
        return contexts
    
    def add_message_to_context(self, context_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a message to a specific context.
        
        Args:
            context_id: ID of the context
            message: Message data
            
        Returns:
            True if successful, False otherwise
        """
        if context_id not in self._contexts:
            logger.error(f"Context not found: {context_id}")
            return False
        
        context = self._contexts[context_id]
        context.messages.append(message)
        context.last_activity = datetime.now()
        
        # Limit message history (keep last 1000 messages)
        if len(context.messages) > 1000:
            context.messages = context.messages[-1000:]
        
        # Update state if this is the current context
        if context_id == self._current_context_id:
            self._update_state()
        
        logger.debug(f"Added message to context {context_id}")
        return True
    
    def get_context_messages(self, context_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get messages from a specific context.
        
        Args:
            context_id: ID of the context
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        if context_id not in self._contexts:
            return []
        
        messages = self._contexts[context_id].messages
        if limit:
            return messages[-limit:]
        return messages
    
    def delete_context(self, context_id: str) -> bool:
        """
        Delete a chat context.
        
        Args:
            context_id: ID of the context to delete
            
        Returns:
            True if successful, False otherwise
        """
        if context_id not in self._contexts:
            return False
        
        # Cannot delete common context
        if context_id == "common":
            logger.warning("Cannot delete common chat context")
            return False
        
        # If deleting current context, switch to common
        if self._current_context_id == context_id:
            self.switch_to_context("common")
        
        # Remove context
        del self._contexts[context_id]
        
        # Publish context deleted event
        self.publish_event(ChatEvents.CONTEXT_DELETED, {
            "context_id": context_id
        })
        
        # Update state
        self._update_state()
        
        logger.info(f"Deleted context: {context_id}")
        return True
    
    def _find_private_context_with_user(self, user: str) -> Optional[ChatContext]:
        """Find existing private context with a specific user."""
        current_user = self.get_state(StateKeys.CURRENT_USER)
        
        for context in self._contexts.values():
            if (context.context_type == "private" and 
                current_user in context.participants and 
                user in context.participants):
                return context
        
        return None
    
    def _update_state(self) -> None:
        """Update state manager with current context information."""
        current_context = self.get_current_context()
        
        state_updates = {
            StateKeys.CURRENT_CHAT_CONTEXT: self._current_context_id,
            StateKeys.CHAT_CONTEXTS: self.get_context_list()
        }
        
        if current_context:
            state_updates[StateKeys.CHAT_HISTORIES] = {
                self._current_context_id: current_context.messages
            }
        
        self.update_multiple_state(state_updates)
    
    def _handle_user_selected(self, event: Event) -> None:
        """Handle user selection for private chat."""
        user = event.data.get("user")
        if not user:
            logger.warning("No user specified in user selection event")
            return
        
        logger.info(f"Handling user selection for private chat with: {user}")
        
        # Create or switch to private context with user
        context_id = self.create_private_context(user)
        if context_id:
            logger.info(f"Created/switched to private context: {context_id}")
            self.switch_to_context(context_id)
        else:
            logger.error(f"Failed to create private context with user: {user}")
    
    def _handle_common_chat_selected(self, event: Event) -> None:
        """Handle common chat selection."""
        logger.info("Handling common chat selection")
        self.switch_to_context("common")
    
    def _handle_message_received(self, event: Event) -> None:
        """Handle received message."""
        message = event.data.get("message")
        if not message:
            logger.debug("ChatContextManager: No message data in event")
            return
        
        # Determine which context this message belongs to
        message_type = message.get("message_type", "public")
        sender = message.get("sender")
        current_user = self.get_state(StateKeys.CURRENT_USER)
        
        logger.debug(f"ChatContextManager: Received {message_type} message from {sender} (current user: {current_user})")
        
        if message_type == "public":
            # Public messages always go to common context
            context_id = "common"
            logger.debug(f"ChatContextManager: Routing public message from {sender} to common context")
        else:
            # Private message - find or create context with sender
            if sender and sender != current_user:
                existing_context = self._find_private_context_with_user(sender)
                if existing_context:
                    context_id = existing_context.context_id
                    logger.debug(f"ChatContextManager: Found existing private context with {sender}: {context_id}")
                else:
                    context_id = self.create_private_context(sender)
                    logger.debug(f"ChatContextManager: Created new private context with {sender}: {context_id}")
            else:
                logger.warning(f"ChatContextManager: Cannot route private message: invalid sender {sender} or self-message")
                return
        
        if context_id:
            success = self.add_message_to_context(context_id, message)
            if success:
                logger.debug(f"ChatContextManager: Successfully added {message_type} message from {sender} to context: {context_id}")
            else:
                logger.error(f"ChatContextManager: Failed to add message to context: {context_id}")
        else:
            logger.error(f"ChatContextManager: No context determined for {message_type} message from {sender}")
    
    def _handle_message_sent(self, event: Event) -> None:
        """Handle sent message."""
        message = event.data.get("message")
        if not message:
            return
        
        # Route message to appropriate context based on message type
        message_type = message.get("message_type", "public")
        
        if message_type == "public":
            # Public messages always go to common context
            context_id = "common"
        else:
            # Private messages go to the private context with the recipient
            recipient = message.get("recipient")
            if recipient:
                # Find or create private context with recipient
                existing_context = self._find_private_context_with_user(recipient)
                if existing_context:
                    context_id = existing_context.context_id
                else:
                    context_id = self.create_private_context(recipient)
            else:
                logger.error("Cannot route private message: no recipient specified")
                return
        
        if context_id:
            self.add_message_to_context(context_id, message)
            logger.debug(f"Added sent message to context: {context_id}")
    
    def on_state_change(self, change) -> None:
        """Handle state changes."""
        if change.key == StateKeys.CURRENT_USER:
            # User changed, reset contexts
            self._contexts.clear()
            self._create_common_chat_context()
            self._update_state()
        
        elif change.key == StateKeys.USER_LIST:
            # User list updated, update context participants if needed
            self._update_state()
