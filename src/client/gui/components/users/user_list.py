"""
Selectable user list component for chat context creation.
"""

from typing import Dict, Any, Optional, List
import logging
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QVBoxLayout, 
                              QLabel, QWidget, QHBoxLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QBrush

from ...core.event_bus import EventBus, Event, ChatEvents
from ...core.state_manager import StateManager, StateKeys
from ..base.base_component import BaseComponent

logger = logging.getLogger(__name__)


class UserList(BaseComponent):
    """Selectable user list component for chat context creation."""
    
    # Signals
    user_selected = Signal(str)  # Emitted when a user is selected
    common_chat_selected = Signal()  # Emitted when common chat is selected
    
    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent=None):
        super().__init__(component_id, event_bus, state_manager, parent)
        
        self.user_list = None
        self.current_user = None
        self.users = []
        self.selected_item = None
    
    def setup_ui(self) -> None:
        """Set up the user list UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Chat Rooms:")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # User list
        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.user_list.itemClicked.connect(self._on_item_clicked)
        self.user_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.user_list)
    
    def setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.subscribe_to_event(ChatEvents.USER_LIST_UPDATED, self._handle_user_list_updated)
        self.subscribe_to_event(ChatEvents.CONTEXT_SWITCHED, self._handle_context_switched)
    
    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions."""
        self.subscribe_to_state(StateKeys.CURRENT_USER)
        self.subscribe_to_state(StateKeys.USER_LIST)
        self.subscribe_to_state(StateKeys.CURRENT_CHAT_CONTEXT)
        self.subscribe_to_state(StateKeys.UNREAD_COUNTS)
    
    def on_initialize(self) -> None:
        """Initialize the user list."""
        # Load initial data
        self._load_users()
        self._load_current_context()
        
        # Force update the user list display
        self._update_user_list()
        
        # Ensure Common Chat is always available and selected by default
        if not self.get_state(StateKeys.CURRENT_CHAT_CONTEXT):
            self.publish_event(ChatEvents.COMMON_CHAT_SELECTED, {
                "context_id": "common"
            })
        
        logger.info("User list component initialized")
    
    def _load_users(self) -> None:
        """Load users from state."""
        users = self.get_state(StateKeys.USER_LIST, [])
        current_user = self.get_state(StateKeys.CURRENT_USER)
        
        if users != self.users or current_user != self.current_user:
            self.users = users.copy()
            self.current_user = current_user
            self._update_user_list()
    
    def _load_current_context(self) -> None:
        """Load current context and update selection."""
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
        if current_context:
            self._select_context_item(current_context)
    
    def _update_user_list(self) -> None:
        """Update the user list display."""
        if not self.user_list:
            logger.warning("User list widget is None, cannot update")
            return
        
        logger.info(f"Updating user list - users: {self.users}, current_user: {self.current_user}")
        
        self.user_list.clear()
        
        # Add "Common Chat" option first
        unread_counts = self.get_state(StateKeys.UNREAD_COUNTS, {})
        common_unread_count = unread_counts.get("common", 0)
        
        if common_unread_count > 0:
            common_text = "🌐 Common Chat 🔴"
            common_tooltip = f"Public chat room for all users ({common_unread_count} new messages)"
        else:
            common_text = "🌐 Common Chat"
            common_tooltip = "Public chat room for all users"
        
        common_item = QListWidgetItem(common_text)
        common_item.setData(Qt.ItemDataRole.UserRole, "common")
        common_item.setToolTip(common_tooltip)
        self.user_list.addItem(common_item)
        logger.debug(f"Added Common Chat item (unread: {common_unread_count})")
        
        # Add separator
        separator_item = QListWidgetItem("─" * 20)
        separator_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non-selectable
        separator_item.setForeground(Qt.GlobalColor.gray)
        self.user_list.addItem(separator_item)
        
        # Add users (excluding current user)
        if self.users:
            # Sort users alphabetically
            sorted_users = sorted(self.users)
            logger.debug(f"Sorted users: {sorted_users}")
            
            # Add other users (excluding current user)
            for user in sorted_users:
                if user != self.current_user:  # Don't show current user in the list
                    # Check for notifications
                    unread_counts = self.get_state(StateKeys.UNREAD_COUNTS, {})
                    context_id = f"private_{user}_{self.current_user}" if user < self.current_user else f"private_{self.current_user}_{user}"
                    unread_count = unread_counts.get(context_id, 0)
                    
                    # Create item text with notification indicator
                    if unread_count > 0:
                        item_text = f"👤 {user} 🔴"
                        tooltip = f"Click to start private chat with {user} ({unread_count} new messages)"
                    else:
                        item_text = f"👤 {user}"
                        tooltip = f"Click to start private chat with {user}"
                    
                    user_item = QListWidgetItem(item_text)
                    user_item.setData(Qt.ItemDataRole.UserRole, f"user_{user}")
                    user_item.setToolTip(tooltip)
                    self.user_list.addItem(user_item)
                    logger.debug(f"Added user item: {user} (unread: {unread_count})")
        
        # If no users, add a placeholder
        if not self.users:
            placeholder_item = QListWidgetItem("No other users online")
            placeholder_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Non-selectable
            placeholder_item.setForeground(Qt.GlobalColor.gray)
            self.user_list.addItem(placeholder_item)
            logger.debug("Added placeholder item")
        
        logger.info(f"Updated user list with {len(self.users)} users, total items: {self.user_list.count()}")
    
    def _select_context_item(self, context_id: str) -> None:
        """Select the item corresponding to the current context."""
        if not self.user_list:
            return
        
        # Find and select the appropriate item
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole):
                item_data = item.data(Qt.ItemDataRole.UserRole)
                
                if context_id == "common" and item_data == "common":
                    self.user_list.setCurrentItem(item)
                    self.selected_item = item
                    item.setBackground(Qt.GlobalColor.blue)
                    logger.debug("Selected Common Chat item")
                    break
                elif context_id.startswith("private_") and item_data.startswith("user_"):
                    # Extract username from context ID
                    context_user = self._extract_user_from_context(context_id)
                    item_user = item_data.replace("user_", "")
                    if context_user == item_user:
                        self.user_list.setCurrentItem(item)
                        self.selected_item = item
                        item.setBackground(Qt.GlobalColor.blue)
                        logger.debug(f"Selected private chat item for user: {context_user}")
                        break
        
        # Clear selection from other items
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            if item and item != self.selected_item:
                item.setBackground(Qt.GlobalColor.white)
    
    def _extract_user_from_context(self, context_id: str) -> Optional[str]:
        """Extract username from private context ID."""
        if context_id.startswith("private_"):
            parts = context_id.split("_")
            if len(parts) >= 2:
                return parts[1]
        return None
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click."""
        if not item or not item.data(Qt.ItemDataRole.UserRole):
            return
        
        item_data = item.data(Qt.ItemDataRole.UserRole)
        self.selected_item = item
        
        # Visual feedback
        item.setBackground(Qt.GlobalColor.blue)
        
        if item_data == "common":
            # Common chat selected
            logger.debug("User clicked on Common Chat")
            self._select_common_chat()
        elif item_data.startswith("user_"):
            # User selected for private chat
            username = item_data.replace("user_", "")
            logger.debug(f"User clicked on user: {username}")
            self._select_user(username)
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double-click (same as single click for now)."""
        self._on_item_clicked(item)
    
    def _select_common_chat(self) -> None:
        """Select common chat."""
        # Publish common chat selected event
        self.publish_event(ChatEvents.COMMON_CHAT_SELECTED, {
            "context_id": "common"
        })
        
        # Emit signal
        self.common_chat_selected.emit()
        
        logger.info(f"🔔 UserList: Published COMMON_CHAT_SELECTED event for context: common")
    
    def _select_user(self, username: str) -> None:
        """Select a user for private chat."""
        if username == self.current_user:
            logger.warning("Cannot start private chat with yourself")
            return
        
        # Publish user selected event
        self.publish_event(ChatEvents.USER_SELECTED, {
            "user": username,
            "action": "start_private_chat"
        })
        
        # Emit signal
        self.user_selected.emit(username)
        
        logger.info(f"🔔 UserList: Published USER_SELECTED event for user: {username}")
    
    def _handle_user_list_updated(self, event: Event) -> None:
        """Handle user list updates."""
        users = event.data.get("users", [])
        if users != self.users:
            self.users = users.copy()
            self._update_user_list()
            # Re-select current context
            current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
            if current_context:
                self._select_context_item(current_context)
    
    def _handle_context_switched(self, event: Event) -> None:
        """Handle context switching."""
        new_context_id = event.data.get("new_context_id")
        if new_context_id:
            self._select_context_item(new_context_id)
    
    def on_state_change(self, change) -> None:
        """Handle state changes."""
        if change.key == StateKeys.USER_LIST:
            # User list updated
            users = change.new_value or []
            if users != self.users:
                self.users = users.copy()
                self._update_user_list()
                # Re-select current context
                current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
                if current_context:
                    self._select_context_item(current_context)
        
        elif change.key == StateKeys.CURRENT_USER:
            # Current user changed
            current_user = change.new_value
            if current_user != self.current_user:
                self.current_user = current_user
                self._update_user_list()
        
        elif change.key == StateKeys.UNREAD_COUNTS:
            # Notification counts changed, update display
            self._update_user_list()
            logger.info(f"🔔 Updated user list due to notification count changes")
        
        elif change.key == StateKeys.CURRENT_CHAT_CONTEXT:
            # Current context changed
            current_context = change.new_value
            if current_context:
                self._select_context_item(current_context)
    
    def get_selected_user(self) -> Optional[str]:
        """Get the currently selected user."""
        if self.selected_item and self.selected_item.data(Qt.ItemDataRole.UserRole):
            item_data = self.selected_item.data(Qt.ItemDataRole.UserRole)
            if item_data.startswith("user_"):
                return item_data.replace("user_", "")
        return None
    
    def get_selected_context_type(self) -> Optional[str]:
        """Get the type of currently selected context."""
        if self.selected_item and self.selected_item.data(Qt.ItemDataRole.UserRole):
            item_data = self.selected_item.data(Qt.ItemDataRole.UserRole)
            if item_data == "common":
                return "public"
            elif item_data.startswith("user_"):
                return "private"
        return None
