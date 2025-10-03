"""
Chat display component with context switching support.
"""

from typing import Dict, Any, Optional
import logging
from datetime import datetime
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QLabel, QScrollBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QTextCursor

from ...core.event_bus import EventBus, Event, ChatEvents
from ...core.state_manager import StateManager, StateKeys
from ..base.base_component import BaseComponent
from qt_material import QtStyleTools

logger = logging.getLogger(__name__)


class ChatDisplay(BaseComponent):
    """Chat display component with context switching support."""

    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent=None):
        super().__init__(component_id, event_bus, state_manager, parent)

        self.message_display = None
        self.current_context_id = None
        self.message_formatter = None

    def setup_ui(self) -> None:
        """Set up the chat display UI."""
        layout = QVBoxLayout(self)

        # Title label
        self.title_label = QLabel("Messages:")
        layout.addWidget(self.title_label)

        # Message display
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setFont(QFont("Consolas", 12))
        self.message_display.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.message_display)

        # Set up auto-scrolling
        self.message_display.verticalScrollBar().rangeChanged.connect(
            self._auto_scroll_to_bottom)

    def setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.subscribe_to_event(
            ChatEvents.MESSAGE_RECEIVED, self._handle_message_received)
        self.subscribe_to_event(ChatEvents.MESSAGE_SENT,
                                self._handle_message_sent)
        self.subscribe_to_event(
            ChatEvents.CONTEXT_SWITCHED, self._handle_context_switched)
        self.subscribe_to_event(ChatEvents.SYSTEM_MESSAGE,
                                self._handle_system_message)

    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions."""
        self.subscribe_to_state(StateKeys.CURRENT_CHAT_CONTEXT)
        self.subscribe_to_state(StateKeys.CHAT_HISTORIES)
        self.subscribe_to_state(StateKeys.CURRENT_USER)

    def on_initialize(self) -> None:
        """Initialize the chat display."""
        # Initialize message formatter
        self.message_formatter = MessageFormatter()

        # Load current context messages
        self._load_current_context_messages()

        logger.info("Chat display component initialized")

    def _handle_message_received(self, event: Event) -> None:
        """Handle received message."""
        message = event.data.get("message")
        if not message:
            logger.debug("ChatDisplay: No message data in event")
            return

        # Only display if it's for the current context
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
        if not current_context:
            logger.info(
                f"🚫 ChatDisplay: No current context, ignoring message from {message.get('sender', 'unknown')}")
            return

        # Determine if message belongs to current context
        message_type = message.get("message_type", "public")
        is_private = message.get("is_private", False)
        sender = message.get("sender")
        current_user = self.get_state(StateKeys.CURRENT_USER)

        logger.info(
            f"📺 ChatDisplay: Received {message_type} message from {sender} in context {current_context} (is_private: {is_private})")

        # STRICT CONTEXT CHECKING: Only display messages that belong to current context
        if message_type == "public" and not is_private:
            # Public messages ONLY belong in common context
            if current_context == "common":
                is_sent = (sender == current_user)
                logger.info(
                    f"✅ ChatDisplay: Displaying public message from {sender} in common context")
                self._display_message(message, is_sent=is_sent)
            else:
                logger.debug(
                    f"ChatDisplay: Ignoring public message from {sender} - not in common context (current: {current_context})")
        elif message_type == "private" or is_private:
            # Private messages ONLY belong in their specific private context
            if current_context != "common":
                # Check if this is a message to/from the other participant in current context
                other_participant = self._get_other_participant(
                    current_context)
                if other_participant and (sender == current_user or sender == other_participant):
                    is_sent = (sender == current_user)
                    logger.debug(
                        f"ChatDisplay: Displaying private message from {sender} in private context with {other_participant}")
                    self._display_message(message, is_sent=is_sent)
                else:
                    logger.debug(
                        f"ChatDisplay: Ignoring private message from {sender} - not for current private context (other_participant: {other_participant})")
            else:
                logger.debug(
                    f"ChatDisplay: Ignoring private message from {sender} - not in private context (current: {current_context})")
        else:
            logger.warning(
                f"ChatDisplay: Unknown message type: {message_type}")

    def _handle_message_sent(self, event: Event) -> None:
        """Handle sent message."""
        message = event.data.get("message")
        if not message:
            logger.debug("ChatDisplay: No message data in MESSAGE_SENT event")
            return

        # Get current context
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
        if not current_context:
            logger.debug("ChatDisplay: No current context for sent message")
            return

        # Determine if this sent message belongs to current context
        message_type = message.get("message_type", "public")
        is_private = message.get("is_private", False)
        sender = message.get("sender")
        current_user = self.get_state(StateKeys.CURRENT_USER)

        logger.debug(
            f"ChatDisplay: Handling sent {message_type} message from {sender} in context {current_context}")

        # Check if this sent message belongs to current context
        if message_type == "public" and not is_private:
            # Public messages belong in common context
            if current_context == "common":
                logger.debug(
                    f"ChatDisplay: Displaying sent public message from {sender} in common context")
                self._display_message(message, is_sent=True)
            else:
                logger.debug(
                    f"ChatDisplay: Ignoring sent public message - not in common context (current: {current_context})")
        elif message_type == "private" or is_private:
            # Private messages belong in their specific private context
            if current_context != "common":
                # Check if this is a message to the other participant in current context
                other_participant = self._get_other_participant(
                    current_context)
                recipient = message.get("recipient")
                if other_participant and recipient == other_participant:
                    logger.debug(
                        f"ChatDisplay: Displaying sent private message to {recipient} in private context")
                    self._display_message(message, is_sent=True)
                else:
                    logger.debug(
                        f"ChatDisplay: Ignoring sent private message - not for current private context (recipient: {recipient}, other_participant: {other_participant})")
            else:
                logger.debug(
                    f"ChatDisplay: Ignoring sent private message - not in private context (current: {current_context})")
        else:
            logger.warning(
                f"ChatDisplay: Unknown sent message type: {message_type}")

    def _handle_context_switched(self, event: Event) -> None:
        """Handle context switching."""
        new_context_id = event.data.get("new_context_id")
        if new_context_id:
            self._switch_to_context(new_context_id)

    def _handle_system_message(self, event: Event) -> None:
        """Handle system message."""
        message_text = event.data.get("message", "")
        if message_text:
            self._display_system_message(message_text)

    def _switch_to_context(self, context_id: str) -> None:
        """Switch to a different chat context."""
        if context_id == self.current_context_id:
            return

        # Clear current display
        self.message_display.clear()

        # Update current context
        self.current_context_id = context_id

        # Update title
        if context_id == "common":
            self.title_label.setText("Messages (Common Chat):")
        else:
            self.title_label.setText(f"Messages (Private):")

        # Load messages for new context
        self._load_context_messages(context_id)

        logger.debug(f"Switched chat display to context: {context_id}")

    def _load_current_context_messages(self) -> None:
        """Load messages for the current context."""
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
        if current_context:
            self._load_context_messages(current_context)

    def _load_context_messages(self, context_id: str) -> None:
        """Load messages for a specific context."""
        chat_histories = self.get_state(StateKeys.CHAT_HISTORIES, {})
        messages = chat_histories.get(context_id, [])

        # Display all messages
        for message in messages:
            is_sent = message.get("is_sent", False)
            self._display_message(
                message, is_sent=is_sent, add_to_history=False)

    def _display_message(self, message: Dict[str, Any], is_sent: bool = False, add_to_history: bool = True) -> None:
        """Display a message in the chat."""
        if not self.message_display:
            return

        # Format the message
        formatted_message = self.message_formatter.format_message(
            message, is_sent)

        # Add to display
        message_type = message.get("message_type", "public")
        if message_type != "system":
            # Color coding based on sender and message type
            sender = message.get("sender", "Unknown")
            color = self.message_formatter.get_sender_color(sender, is_sent)
            self.message_display.setTextColor(color)
        self.message_display.append(formatted_message)

        # Auto-scroll to bottom
        self._scroll_to_bottom()

        logger.debug(
            f"ChatDisplay: Displayed message from {message.get('sender', 'Unknown')}: {message.get('content', '')[:50]}...")

    def _display_system_message(self, message_text: str) -> None:
        """Display a system message."""
        if not self.message_display:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"(System) ({timestamp}) {message_text}"

        # Add to display with color coding
        # self.message_display.setTextColor(QColor(0, 200, 180))  # Blue for system messages
        self.message_display.append(formatted_message)
        # self.message_display.setTextColor(QColor(255, 255, 255))  # Reset to black

        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the message display."""
        if self.message_display:
            scrollbar = self.message_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _auto_scroll_to_bottom(self, min_val: int, max_val: int) -> None:
        """Auto-scroll to bottom when new content is added."""
        if self.message_display:
            scrollbar = self.message_display.verticalScrollBar()
            # Only auto-scroll if we're already near the bottom
            if scrollbar.value() >= scrollbar.maximum() - 100:
                scrollbar.setValue(max_val)

    def on_state_change(self, change) -> None:
        """Handle state changes."""
        if change.key == StateKeys.CURRENT_CHAT_CONTEXT:
            # Context changed, switch display
            new_context = change.new_value
            if new_context and new_context != self.current_context_id:
                self._switch_to_context(new_context)

        elif change.key == StateKeys.CHAT_HISTORIES:
            # Message history updated - don't reload all messages to prevent duplicates
            # Messages are already displayed when received via _handle_message_received
            logger.info(
                f"📺 ChatDisplay: Chat histories updated with {len(change.new_value)} contexts, but not reloading to prevent duplicates")

        elif change.key == StateKeys.CURRENT_USER:
            # User changed, clear display
            self.message_display.clear()
            self.current_context_id = None

    def _get_other_participant(self, context_id: str) -> Optional[str]:
        """Get the other participant in a private context."""
        if context_id.startswith("private_"):
            # Extract username from context ID (format: private_username_xxxxx)
            parts = context_id.split("_")
            if len(parts) >= 2:
                return parts[1]
        return None


class MessageFormatter:
    """Formats messages for display in the chat."""

    def __init__(self):
        self.colors = {
            "public": QColor(0, 100, 0),      # Dark green for public messages
            "private": QColor(150, 0, 150),   # Purple for private messages
            # "system": QColor(0, 0, 150),      # Blue for system messages
            "sent": QColor(255, 255, 255),          # White for sent messages
        }

        # Assign color to each user
        self.user_palette = [
            QColor(255, 0, 0),    # Red
            QColor(0, 255, 0),    # Green
            QColor(0, 0, 255),    # Blue
            QColor(255, 165, 0),  # Orange
            QColor(128, 0, 128),  # Purple
            QColor(0, 255, 255),  # Cyan
            QColor(255, 192, 203)  # Pink
        ]
        self.user_colors = {}  # username -> QColor mapping
        self.next_color_idx = 0

    def format_message(self, message: Dict[str, Any], is_sent: bool = False) -> str:
        """
        Format a message for display.

        Args:
            message: Message data
            is_sent: Whether this message was sent by current user

        Returns:
            Formatted message string
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Extract message content
        content = message.get("content", "Unknown message")
        sender = message.get("sender", "Unknown")
        message_type = message.get("message_type", "public")

        # Format based on message type and sender
        if message_type == "public":
            if is_sent:
                formatted = f"(Global) ({timestamp}) {sender}: {content}"
            else:
                formatted = f"(Global) ({timestamp}) {sender}: {content}"
        else:  # private
            if is_sent:
                recipient = message.get("recipient", "Unknown")
                formatted = f"(Private) (To {recipient}) ({timestamp}) {sender}: {content}"
            else:
                formatted = f"(Private) (From {sender}) ({timestamp}): {content}"

        return formatted

    def get_sender_color(self, sender: str, is_sent: bool = False) -> QColor:
        """Assign and return a consistent color for each sender."""
        if is_sent:
            return self.colors["sent"]  # your own messages always white

        if sender not in self.user_colors:
            # Assign the next color in the palette (wrap around if needed)
            color = self.user_palette[self.next_color_idx %
                                      len(self.user_palette)]
            self.user_colors[sender] = color
            self.next_color_idx += 1

        return self.user_colors[sender]

    def get_message_color(self, message_type: str, is_sent: bool = False) -> QColor:
        """Get the appropriate color for a message type."""
        if is_sent:
            return self.colors["sent"]
        return self.colors.get(message_type, self.colors["sent"])
