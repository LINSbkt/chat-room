"""
Message input component with context-aware sending.
"""

from typing import Dict, Any, Optional
import logging
from PySide6.QtWidgets import (QLineEdit, QPushButton, QHBoxLayout,
                               QComboBox, QLabel, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...core.event_bus import EventBus, Event, ChatEvents
from ...core.state_manager import StateManager, StateKeys
from ..base.base_component import BaseComponent
from .emoji_picker import EmojiPicker

logger = logging.getLogger(__name__)


class MessageInput(BaseComponent):
    """Message input component with context-aware sending."""

    # Signals
    message_sent = Signal(dict)  # Emitted when message is sent

    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent=None):
        super().__init__(component_id, event_bus, state_manager, parent)

        self.message_input = None
        self.send_button = None
        self.message_type_combo = None
        self.recipient_combo = None
        self.current_context_id = None

    def setup_ui(self) -> None:
        """Set up the message input UI."""
        layout = QHBoxLayout(self)

        # Message type selection (for future use - currently context determines type)
        message_type_layout = QHBoxLayout()
        message_type_layout.addWidget(QLabel("Type:"))

        self.message_type_combo = QComboBox()
        # Auto-detect based on context
        self.message_type_combo.addItems(["Auto"])
        self.message_type_combo.setEnabled(False)  # Disabled for now
        message_type_layout.addWidget(self.message_type_combo)

        # Recipient selection (hidden for now, context determines recipient)
        message_type_layout.addWidget(QLabel("To:"))
        self.recipient_combo = QComboBox()
        self.recipient_combo.setVisible(False)  # Hidden for now
        message_type_layout.addWidget(self.recipient_combo)

        message_type_layout.addStretch()
        layout.addLayout(message_type_layout)

        # Input area
        input_layout = QHBoxLayout()

        # Message input field
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setFont(QFont("Consolas", 10))
        self.message_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_input)

        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Add Emoji button next to send button
        self.emoji_button = QPushButton("😊")
        self.emoji_button.clicked.connect(self._open_emoji_picker)
        input_layout.addWidget(self.emoji_button)

    def setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.subscribe_to_event(
            ChatEvents.CONTEXT_SWITCHED, self._handle_context_switched)
        self.subscribe_to_event(
            ChatEvents.USER_LIST_UPDATED, self._handle_user_list_updated)

    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions."""
        self.subscribe_to_state(StateKeys.CURRENT_CHAT_CONTEXT)
        self.subscribe_to_state(StateKeys.CURRENT_USER)
        self.subscribe_to_state(StateKeys.USER_LIST)
        self.subscribe_to_state(StateKeys.CONNECTION_STATUS)

    def on_initialize(self) -> None:
        """Initialize the message input."""
        # Update UI based on current state
        self._update_ui_for_context()
        self._update_connection_status()

        logger.info("Message input component initialized")

    def _send_message(self) -> None:
        """Send a message."""
        if not self.message_input:
            return

        content = self.message_input.text().strip()
        if not content:
            return

        current_user = self.get_state(StateKeys.CURRENT_USER)
        if not current_user:
            logger.error("Cannot send message: no current user")
            return

        # Get current context
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
        if not current_context:
            logger.error("Cannot send message: no current context")
            return

        # Determine message type and recipient based on context
        if current_context == "common":
            message_type = "public"
            recipient = None
            logger.debug(
                f"MessageInput: Sending public message from context: {current_context}")
        else:
            message_type = "private"
            # Find the other participant in private context
            recipient = self._get_other_participant(current_context)
            if not recipient:
                logger.error(
                    f"MessageInput: Cannot send private message: no recipient found for context {current_context}")
                return
            logger.debug(
                f"MessageInput: Sending private message to {recipient} from context: {current_context}")

        # Create message data
        message_data = {
            "content": content,
            "sender": current_user,
            "message_type": message_type,
            "timestamp": self._get_current_timestamp(),
            "is_sent": True
        }

        if recipient:
            message_data["recipient"] = recipient

        # Publish message sent event
        self.publish_event(ChatEvents.MESSAGE_SENT, {
            "message": message_data,
            "context_id": current_context
        })

        # Emit signal for other components
        self.message_sent.emit(message_data)

        # Clear input
        self.message_input.clear()

        logger.debug(
            f"MessageInput: Sent {message_type} message: {content} (context: {current_context})")

    def _get_other_participant(self, context_id: str) -> Optional[str]:
        """Get the other participant in a private context."""
        current_user = self.get_state(StateKeys.CURRENT_USER)
        if not current_user:
            return None

        # For now, extract user from context ID (format: private_username_xxxxx)
        if context_id.startswith("private_"):
            # Remove "private_" prefix and extract username
            parts = context_id.split("_")
            if len(parts) >= 2:
                return parts[1]

        return None

    def _get_current_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def _handle_context_switched(self, event: Event) -> None:
        """Handle context switching."""
        new_context_id = event.data.get("new_context_id")
        if new_context_id:
            self._switch_to_context(new_context_id)

    def _handle_user_list_updated(self, event: Event) -> None:
        """Handle user list updates."""
        users = event.data.get("users", [])
        self._update_recipient_combo(users)

    def _switch_to_context(self, context_id: str) -> None:
        """Switch to a different context."""
        if context_id == self.current_context_id:
            return

        self.current_context_id = context_id
        self._update_ui_for_context()

        logger.debug(f"Message input switched to context: {context_id}")

    def _update_ui_for_context(self) -> None:
        """Update UI based on current context."""
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)

        if current_context == "common":
            # Public chat
            self.message_input.setPlaceholderText("Type your message here...")
            self.recipient_combo.setVisible(False)
        else:
            # Private chat
            other_user = self._get_other_participant(current_context)
            if other_user:
                self.message_input.setPlaceholderText(
                    f"Type your private message to {other_user}...")
            else:
                self.message_input.setPlaceholderText(
                    "Type your private message here...")
            self.recipient_combo.setVisible(False)  # Hidden for now

    def _update_recipient_combo(self, users: list) -> None:
        """Update recipient combo box with available users."""
        if not self.recipient_combo:
            return

        current_user = self.get_state(StateKeys.CURRENT_USER)
        if not current_user:
            return

        # Clear and populate with other users
        self.recipient_combo.clear()
        other_users = [user for user in users if user != current_user]
        self.recipient_combo.addItems(other_users)

    def _update_connection_status(self) -> None:
        """Update UI based on connection status."""
        connection_status = self.get_state(StateKeys.CONNECTION_STATUS, False)

        if self.send_button and self.message_input:
            self.send_button.setEnabled(connection_status)
            self.message_input.setEnabled(connection_status)

    def on_state_change(self, change) -> None:
        """Handle state changes."""
        if change.key == StateKeys.CURRENT_CHAT_CONTEXT:
            # Context changed
            new_context = change.new_value
            if new_context and new_context != self.current_context_id:
                self._switch_to_context(new_context)

        elif change.key == StateKeys.USER_LIST:
            # User list updated
            users = change.new_value or []
            self._update_recipient_combo(users)

        elif change.key == StateKeys.CONNECTION_STATUS:
            # Connection status changed
            self._update_connection_status()

        elif change.key == StateKeys.CURRENT_USER:
            # User changed, update UI
            self._update_ui_for_context()
            self._update_connection_status()

    def _open_emoji_picker(self):
        """Open the emoji picker dialog."""
        if not self.message_input:
            return

        emoji_picker = EmojiPicker(self)
        emoji_picker.emoji_selected.connect(self._insert_emoji)
        emoji_picker.exec()

    def _insert_emoji(self, emoji: str):
        """Insert selected emoji into the message input."""
        if not self.message_input:
            return

        cursor_position = self.message_input.cursorPosition()
        current_text = self.message_input.text()
        new_text = current_text[:cursor_position] + emoji + current_text[cursor_position:]
        self.message_input.setText(new_text)
        self.message_input.setCursorPosition(cursor_position + len(emoji))    