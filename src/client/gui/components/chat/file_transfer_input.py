"""
File transfer input component for sending files.
"""

from typing import Dict, Any, Optional
import logging
import os
from PySide6.QtWidgets import (QPushButton, QHBoxLayout, QFileDialog, 
                              QMessageBox, QLabel, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...core.event_bus import EventBus, Event, ChatEvents
from ...core.state_manager import StateManager, StateKeys
from ..base.base_component import BaseComponent

logger = logging.getLogger(__name__)


class FileTransferInput(BaseComponent):
    """File transfer input component for sending files."""
    
    # Signals
    file_transfer_requested = Signal(dict)  # Emitted when file transfer is requested
    
    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent=None):
        super().__init__(component_id, event_bus, state_manager, parent)
        
        self.file_button = None
        self.current_context_id = None
    
    def setup_ui(self) -> None:
        """Set up the file transfer input UI."""
        layout = QHBoxLayout(self)
        
        # File transfer button
        self.file_button = QPushButton("📁 Send File")
        self.file_button.setFont(QFont("Consolas", 10))
        self.file_button.clicked.connect(self._send_file)
        layout.addWidget(self.file_button)
        
        # Add stretch to push button to the right
        layout.addStretch()
    
    def setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.subscribe_to_event(ChatEvents.CONTEXT_SWITCHED, self._handle_context_switched)
        self.subscribe_to_event(ChatEvents.USER_LIST_UPDATED, self._handle_user_list_updated)
    
    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions."""
        self.subscribe_to_state(StateKeys.CURRENT_CHAT_CONTEXT)
        self.subscribe_to_state(StateKeys.CURRENT_USER)
        self.subscribe_to_state(StateKeys.USER_LIST)
        self.subscribe_to_state(StateKeys.CONNECTION_STATUS)
    
    def on_initialize(self) -> None:
        """Initialize the file transfer input."""
        # Update UI based on current state
        self._update_ui_for_context()
        self._update_connection_status()
        
        logger.info("File transfer input component initialized")
    
    def _send_file(self) -> None:
        """Send a file."""
        if not self.file_button:
            return
        
        current_user = self.get_state(StateKeys.CURRENT_USER)
        if not current_user:
            logger.error("Cannot send file: no current user")
            QMessageBox.warning(self, "Error", "You must be logged in to send files")
            return
        
        # Get current context
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
        if not current_context:
            logger.error("Cannot send file: no current context")
            QMessageBox.warning(self, "Error", "No active chat context")
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Send",
            "",
            "All Files (*.*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        # Check if file exists and get file info
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Error", "Selected file does not exist")
            return
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            QMessageBox.warning(self, "Error", "Cannot send empty file")
            return
        
        # Check file size limit (10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            QMessageBox.warning(self, "Error", f"File too large. Maximum size is {max_size // (1024*1024)}MB")
            return
        
        # Determine recipient based on context
        if current_context == "common":
            # Public file transfer - send to all users
            recipient = "GLOBAL"
            is_private = False
            logger.debug(f"FileTransferInput: Sending public file from context: {current_context}")
        else:
            # Private file transfer - send to specific user
            recipient = self._get_other_participant(current_context)
            if not recipient:
                logger.error(f"FileTransferInput: Cannot send private file: no recipient found for context {current_context}")
                QMessageBox.warning(self, "Error", "Cannot determine recipient for private file transfer")
                return
            is_private = True
            logger.debug(f"FileTransferInput: Sending private file to {recipient} from context: {current_context}")
        
        # Create file transfer request data
        file_data = {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "file_size": file_size,
            "sender": current_user,
            "recipient": recipient,
            "is_private": is_private,
            "context_id": current_context
        }
        
        # Publish file transfer request event
        self.publish_event(ChatEvents.FILE_TRANSFER_REQUESTED, {
            "file_data": file_data,
            "context_id": current_context
        })
        
        # Emit signal for other components
        self.file_transfer_requested.emit(file_data)
        
        logger.debug(f"FileTransferInput: Requested {('private' if is_private else 'public')} file transfer: {os.path.basename(file_path)} (context: {current_context})")
    
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
    
    def _handle_context_switched(self, event: Event) -> None:
        """Handle context switching."""
        new_context_id = event.data.get("new_context_id")
        if new_context_id:
            self._switch_to_context(new_context_id)
    
    def _handle_user_list_updated(self, event: Event) -> None:
        """Handle user list updates."""
        # Could be used to update recipient options in the future
        pass
    
    def _switch_to_context(self, context_id: str) -> None:
        """Switch to a different context."""
        if context_id == self.current_context_id:
            return
        
        self.current_context_id = context_id
        self._update_ui_for_context()
        
        logger.debug(f"File transfer input switched to context: {context_id}")
    
    def _update_ui_for_context(self) -> None:
        """Update UI based on current context."""
        current_context = self.get_state(StateKeys.CURRENT_CHAT_CONTEXT)
        
        if current_context == "common":
            # Public file transfer
            self.file_button.setText("📁 Send File (Public)")
            self.file_button.setToolTip("Send file to all users")
        else:
            # Private file transfer
            other_user = self._get_other_participant(current_context)
            if other_user:
                self.file_button.setText(f"📁 Send File (To {other_user})")
                self.file_button.setToolTip(f"Send private file to {other_user}")
            else:
                self.file_button.setText("📁 Send File (Private)")
                self.file_button.setToolTip("Send private file")
    
    def _update_connection_status(self) -> None:
        """Update UI based on connection status."""
        connection_status = self.get_state(StateKeys.CONNECTION_STATUS, False)
        
        if self.file_button:
            self.file_button.setEnabled(connection_status)
    
    def on_state_change(self, change) -> None:
        """Handle state changes."""
        if change.key == StateKeys.CURRENT_CHAT_CONTEXT:
            # Context changed
            new_context = change.new_value
            if new_context and new_context != self.current_context_id:
                self._switch_to_context(new_context)
        
        elif change.key == StateKeys.USER_LIST:
            # User list updated
            self._handle_user_list_updated(Event(
                event_type=ChatEvents.USER_LIST_UPDATED,
                data={"users": change.new_value or []},
                source="state_manager"
            ))
        
        elif change.key == StateKeys.CONNECTION_STATUS:
            # Connection status changed
            self._update_connection_status()
        
        elif change.key == StateKeys.CURRENT_USER:
            # User changed, update UI
            self._update_ui_for_context()
            self._update_connection_status()
