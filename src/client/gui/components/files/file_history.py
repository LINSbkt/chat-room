"""
File history component for viewing and managing received files.
"""

from typing import Dict, Any, Optional, List
import logging
import os
from datetime import datetime
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QVBoxLayout, 
                              QLabel, QWidget, QPushButton, QHBoxLayout,
                              QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

from ...core.event_bus import EventBus, Event, ChatEvents
from ...core.state_manager import StateManager, StateKeys
from ..base.base_component import BaseComponent

logger = logging.getLogger(__name__)


class FileHistory(BaseComponent):
    """Component for viewing and managing received files."""
    
    # Signals
    file_opened = Signal(str)  # Emitted when a file is opened
    file_saved_as = Signal(str, str)  # Emitted when a file is saved as (file_path, new_path)
    
    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent=None):
        super().__init__(component_id, event_bus, state_manager, parent)
        
        self.file_list = None
        self.refresh_button = None
        self.open_button = None
        self.save_as_button = None
        self.current_user = None
        self.files = []  # List of file info dictionaries
    
    def setup_ui(self) -> None:
        """Set up the file history UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("📁 Received Files:")
        title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self._refresh_file_list)
        self.refresh_button.setToolTip("Refresh the list of received files")
        button_layout.addWidget(self.refresh_button)
        
        # Open button
        self.open_button = QPushButton("📂 Open")
        self.open_button.clicked.connect(self._open_selected_file)
        self.open_button.setEnabled(False)
        self.open_button.setToolTip("Open the selected file")
        button_layout.addWidget(self.open_button)
        
        # Save As button
        self.save_as_button = QPushButton("💾 Save As")
        self.save_as_button.clicked.connect(self._save_selected_file_as)
        self.save_as_button.setEnabled(False)
        self.save_as_button.setToolTip("Save the selected file to a different location")
        button_layout.addWidget(self.save_as_button)
        
        layout.addLayout(button_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.file_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.file_list)
        
        # Status label
        self.status_label = QLabel("No files received yet")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)
    
    def setup_event_handlers(self) -> None:
        """Set up event handlers."""
        self.subscribe_to_event(ChatEvents.FILE_LIST_RECEIVED, self._handle_file_list_received)
        self.subscribe_to_event(ChatEvents.FILE_TRANSFER_COMPLETE, self._handle_file_transfer_complete)
    
    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions."""
        self.subscribe_to_state(StateKeys.CURRENT_USER)
    
    def on_initialize(self) -> None:
        """Initialize the file history component."""
        # Load initial data
        self._load_current_user()
        self._refresh_file_list()
        logger.info("File history component initialized")
    
    def _load_current_user(self) -> None:
        """Load current user from state."""
        self.current_user = self.get_state(StateKeys.CURRENT_USER)
    
    def _refresh_file_list(self) -> None:
        """Refresh the file list by requesting from server."""
        if not self.current_user:
            logger.warning("Cannot refresh file list: no current user")
            return
        
        # Request file list from server
        if hasattr(self, '_chat_client') and self._chat_client:
            self._chat_client.request_file_list()
        else:
            logger.warning("Cannot refresh file list: no chat client available")
    
    def _on_selection_changed(self) -> None:
        """Handle file list selection change."""
        has_selection = len(self.file_list.selectedItems()) > 0
        self.open_button.setEnabled(has_selection)
        self.save_as_button.setEnabled(has_selection)
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle file list item double-click."""
        if item:
            self._open_selected_file()
    
    def _open_selected_file(self) -> None:
        """Open the selected file."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file could not be found:\n{file_path}"
            )
            return
        
        try:
            # Open file with default system application
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux and others
                subprocess.run(['xdg-open', file_path])
            
            logger.info(f"Opened file: {file_path}")
            self.file_opened.emit(file_path)
            
        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            QMessageBox.warning(
                self,
                "Error Opening File",
                f"Could not open file:\n{e}"
            )
    
    def _save_selected_file_as(self) -> None:
        """Save the selected file to a different location."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file could not be found:\n{file_path}"
            )
            return
        
        # Get original filename
        original_filename = os.path.basename(file_path)
        
        # Open save dialog
        new_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            original_filename,
            "All Files (*.*)"
        )
        
        if new_path:
            try:
                import shutil
                shutil.copy2(file_path, new_path)
                logger.info(f"Saved file as: {new_path}")
                self.file_saved_as.emit(file_path, new_path)
                
                QMessageBox.information(
                    self,
                    "File Saved",
                    f"File saved successfully to:\n{new_path}"
                )
                
            except Exception as e:
                logger.error(f"Error saving file: {e}")
                QMessageBox.warning(
                    self,
                    "Error Saving File",
                    f"Could not save file:\n{e}"
                )
    
    def _handle_file_list_received(self, event: Event) -> None:
        """Handle file list received from server."""
        file_list = event.data.get("files", [])
        self._update_file_list(file_list)
    
    def _handle_file_transfer_complete(self, event: Event) -> None:
        """Handle file transfer completion."""
        transfer_id = event.data.get("transfer_id")
        success = event.data.get("success", False)
        file_path = event.data.get("file_path")
        
        if success and file_path:
            # Refresh file list to include the new file
            self._refresh_file_list()
            logger.info(f"File transfer completed, refreshing file list: {file_path}")
    
    def _update_file_list(self, file_list: List[Dict[str, Any]]) -> None:
        """Update the file list display."""
        self.files = file_list
        self.file_list.clear()
        
        if not file_list:
            self.status_label.setText("No files received yet")
            return
        
        # Sort files by date (newest first)
        sorted_files = sorted(file_list, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for file_info in sorted_files:
            filename = file_info.get('filename', 'Unknown')
            file_path = file_info.get('file_path', '')
            is_public = file_info.get('is_public', False)
            sender = file_info.get('sender', 'Unknown')
            timestamp = file_info.get('timestamp', '')
            
            # Create display text
            if is_public:
                display_text = f"🌐 {filename}"
                tooltip = f"Public file from {sender}\nReceived: {timestamp}\nPath: {file_path}"
            else:
                display_text = f"🔒 {filename}"
                tooltip = f"Private file from {sender}\nReceived: {timestamp}\nPath: {file_path}"
            
            # Create item and add to list
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setToolTip(tooltip)
            self.file_list.addItem(item)
        
        # Update status
        self.status_label.setText(f"📁 {len(file_list)} files received")
        logger.info(f"Updated file list with {len(file_list)} files")
    
    def on_state_change(self, change) -> None:
        """Handle state changes."""
        if change.key == StateKeys.CURRENT_USER:
            # User changed, update current user and refresh file list
            self.current_user = change.new_value
            if self.current_user:
                self._refresh_file_list()
    
    def set_chat_client(self, chat_client) -> None:
        """Set the chat client for requesting file lists."""
        self._chat_client = chat_client
