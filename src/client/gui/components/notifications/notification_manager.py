"""
Notification manager for tracking new messages and unread counts.
"""

from typing import Dict, Any, Optional, Set
import logging
from PySide6.QtCore import QObject, Signal

from ...core.event_bus import EventBus, Event, ChatEvents
from ...core.state_manager import StateManager, StateKeys
from ..base.base_component import BaseComponent

logger = logging.getLogger(__name__)


class NotificationManager(BaseComponent):
    """Manages message notifications and unread counts."""
    
    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent=None):
        super().__init__(component_id, event_bus, state_manager, parent)
        
        # Track notifications for each context
        self._notifications: Dict[str, Set[str]] = {}  # context_id -> set of message_ids
        self._unread_counts: Dict[str, int] = {}  # context_id -> count
    
    def setup_ui(self) -> None:
        """Set up UI (not needed for notification manager)."""
        pass
    
    def setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.subscribe_to_event(ChatEvents.MESSAGE_RECEIVED, self._handle_message_received)
        self.subscribe_to_event(ChatEvents.CONTEXT_SWITCHED, self._handle_context_switched)
        self.subscribe_to_event(ChatEvents.COMMON_CHAT_SELECTED, self._handle_common_chat_selected)
        self.subscribe_to_event(ChatEvents.USER_SELECTED, self._handle_user_selected)
        self.subscribe_to_event(ChatEvents.MESSAGE_SENT, self._handle_message_sent)
    
    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions."""
        self.subscribe_to_state(StateKeys.CURRENT_CHAT_CONTEXT)
        self.subscribe_to_state(StateKeys.CURRENT_USER)
    
    def on_initialize(self) -> None:
        """Initialize the notification manager."""
        # Initialize notification state
        self._update_notification_state()
        logger.info("Notification manager initialized")
    
    def _handle_message_received(self, event: Event) -> None:
        """Handle received message to update notifications."""
        message = event.data.get("message")
        if not message:
            return
        
        current_user = self.get_state(StateKeys.CURRENT_USER)
        if not current_user:
            return
        
        # Don't show notifications for messages sent by current user
        sender = message.get("sender")
        if sender == current_user:
            return
        
        # Determine which context this message belongs to
        message_type = message.get("message_type", "public")
        is_private = message.get("is_private", False)
        
        if message_type == "public" and not is_private:
            context_id = "common"
        else:
            # For private messages, find the context with the sender
            context_id = f"private_{sender}_{current_user}" if sender < current_user else f"private_{current_user}_{sender}"
        
        # Add notification for this context
        self._add_notification(context_id, message.get("content", ""))
        
        logger.info(f"🔔 Added notification for context: {context_id}")
    
    def _handle_context_switched(self, event: Event) -> None:
        """Handle context switch to clear notifications."""
        new_context_id = event.data.get("new_context_id")
        if new_context_id:
            self._clear_notifications(new_context_id)
            logger.info(f"🔔 Cleared notifications for context: {new_context_id}")
    
    def _handle_common_chat_selected(self, event: Event) -> None:
        """Handle common chat selection to clear notifications."""
        context_id = event.data.get("context_id", "common")
        self._clear_notifications(context_id)
        logger.info(f"🔔 Cleared notifications for common chat: {context_id}")
    
    def _handle_user_selected(self, event: Event) -> None:
        """Handle user selection to clear notifications."""
        user = event.data.get("user")
        if not user:
            return
        
        current_user = self.get_state(StateKeys.CURRENT_USER)
        if not current_user:
            return
        
        # Create context ID for private chat with this user
        context_id = f"private_{user}_{current_user}" if user < current_user else f"private_{current_user}_{user}"
        self._clear_notifications(context_id)
        logger.info(f"🔔 Cleared notifications for user chat: {context_id}")
    
    def _handle_message_sent(self, event: Event) -> None:
        """Handle message sent to clear notifications for that context."""
        context_id = event.data.get("context_id")
        if context_id:
            self._clear_notifications(context_id)
            logger.info(f"🔔 Cleared notifications for sent message context: {context_id}")
    
    def _add_notification(self, context_id: str, message_content: str) -> None:
        """Add a notification for a specific context."""
        if context_id not in self._notifications:
            self._notifications[context_id] = set()
        
        # Use message content as a simple identifier (in real app, use message ID)
        message_id = f"{context_id}_{message_content}_{len(self._notifications[context_id])}"
        self._notifications[context_id].add(message_id)
        
        # Update unread count
        self._unread_counts[context_id] = len(self._notifications[context_id])
        
        # Update state
        self._update_notification_state()
    
    def _clear_notifications(self, context_id: str) -> None:
        """Clear notifications for a specific context."""
        if context_id in self._notifications:
            self._notifications[context_id].clear()
            self._unread_counts[context_id] = 0
            self._update_notification_state()
    
    def _update_notification_state(self) -> None:
        """Update the notification state in the state manager."""
        self.set_state(StateKeys.MESSAGE_NOTIFICATIONS, self._notifications.copy())
        self.set_state(StateKeys.UNREAD_COUNTS, self._unread_counts.copy())
    
    def get_unread_count(self, context_id: str) -> int:
        """Get unread count for a specific context."""
        return self._unread_counts.get(context_id, 0)
    
    def has_notifications(self, context_id: str) -> bool:
        """Check if a context has notifications."""
        return self.get_unread_count(context_id) > 0
    
    def get_all_notifications(self) -> Dict[str, int]:
        """Get all notification counts."""
        return self._unread_counts.copy()
