"""
Main window GUI for the chat client.
"""

import sys
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTextEdit, QLineEdit, QPushButton, QListWidget, 
                            QLabel, QSplitter, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QColor
try:
    from ..chat_client import ChatClient
    from ..shared.message_types import MessageType, ChatMessage
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from client.chat_client import ChatClient
    from shared.message_types import MessageType, ChatMessage


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.chat_client: ChatClient = None
        self.username = ""
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Chatroom Application")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Chat area
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        # Message display
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setFont(QFont("Consolas", 10))
        chat_layout.addWidget(QLabel("Messages:"))
        chat_layout.addWidget(self.message_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        chat_layout.addLayout(input_layout)
        
        # Right panel - User list
        user_widget = QWidget()
        user_layout = QVBoxLayout(user_widget)
        
        user_layout.addWidget(QLabel("Online Users:"))
        self.user_list = QListWidget()
        user_layout.addWidget(self.user_list)
        
        # Add widgets to splitter
        splitter.addWidget(chat_widget)
        splitter.addWidget(user_widget)
        splitter.setSizes([600, 200])
        
        # Status bar
        self.status_label = QLabel("Disconnected")
        self.statusBar().addWidget(self.status_label)
    
    def setup_connections(self):
        """Set up signal connections."""
        # These will be connected when chat_client is created
        pass
    
    def set_chat_client(self, chat_client: ChatClient, username: str):
        """Set the chat client and connect signals."""
        self.chat_client = chat_client
        self.username = username
        
        print(f"DEBUG: Setting up signals for client {username}")
        
        # Connect signals
        chat_client.message_received.connect(self.on_message_received)
        chat_client.user_list_updated.connect(self.on_user_list_updated)
        chat_client.system_message.connect(self.on_system_message)
        chat_client.error_occurred.connect(self.on_error_occurred)
        chat_client.connection_status_changed.connect(self.on_connection_status_changed)
        
        print("DEBUG: All signals connected")
        
        # Check if already connected and update status accordingly
        if hasattr(chat_client, 'connected') and chat_client.connected:
            print("DEBUG: Client already connected, updating status")
            self.on_connection_status_changed(True)
        
        # Update window title
        self.setWindowTitle(f"Chatroom Application - {username}")
        
        # Request user list after connection
        print("DEBUG: Requesting user list")
        chat_client.request_user_list()
    
    @pyqtSlot(object)
    def on_message_received(self, message):
        """Handle received message."""
        if message.message_type == MessageType.PUBLIC_MESSAGE:
            self.display_public_message(message)
        elif message.message_type == MessageType.PRIVATE_MESSAGE:
            self.display_private_message(message)
    
    def display_public_message(self, message):
        """Display a public message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Handle both ChatMessage and generic Message objects
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = message.data.get('content', 'Unknown message')
        
        sender = message.sender or 'Unknown'
        formatted_message = f"(Global) ({timestamp}) {sender}: {content}"
        
        # Add to display
        self.message_display.append(formatted_message)
        self.scroll_to_bottom()
    
    def display_public_message_sent(self, content: str):
        """Display a message sent by this client."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"(Global) ({timestamp}) {self.username}: {content}"
        
        # Add to display
        self.message_display.append(formatted_message)
        self.scroll_to_bottom()
    
    def display_private_message(self, message):
        """Display a private message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Handle both ChatMessage and generic Message objects
        if hasattr(message, 'content'):
            content = message.content
        else:
            content = message.data.get('content', 'Unknown message')
        
        sender = message.sender or 'Unknown'
        formatted_message = f"(Private) (From {sender}) ({timestamp}): {content}"
        
        # Add to display with different color (if possible)
        self.message_display.append(formatted_message)
        self.scroll_to_bottom()
    
    @pyqtSlot(list)
    def on_user_list_updated(self, users):
        """Handle user list update."""
        print(f"DEBUG: User list updated with {len(users)} users: {users}")
        self.user_list.clear()
        
        # Sort users with current user first
        sorted_users = sorted(users)
        if self.username in sorted_users:
            sorted_users.remove(self.username)
            sorted_users.insert(0, self.username)
        
        for user in sorted_users:
            if user == self.username:
                # Mark current user with special formatting
                item_text = f"👤 {user} (You)"
            else:
                item_text = f"👤 {user}"
            
            self.user_list.addItem(item_text)
            print(f"DEBUG: Added user to list: {user}")
    
    @pyqtSlot(str)
    def on_system_message(self, message):
        """Handle system message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check if it's a user join/leave notification
        if "joined the chat" in message:
            formatted_message = f"(System) ({timestamp}) 🟢 {message}"
        elif "left the chat" in message:
            formatted_message = f"(System) ({timestamp}) 🔴 {message}"
        else:
            formatted_message = f"(System) ({timestamp}) {message}"
        
        self.message_display.append(formatted_message)
        self.scroll_to_bottom()
    
    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        """Handle error message."""
        print(f"DEBUG: Error occurred: {error_message}")
        
        # Check if it's an authentication error
        if "already taken" in error_message or "Authentication failed" in error_message or "Not authenticated" in error_message:
            # Show error dialog and close window to allow retry
            QMessageBox.warning(self, "Authentication Failed", 
                              f"Authentication failed: {error_message}\n\nPlease try again with a different username.")
            self.close()  # Close the window to allow retry
        else:
            # Show regular error message
            QMessageBox.warning(self, "Error", error_message)
            self.status_label.setText(f"Error: {error_message}")
    
    @pyqtSlot(bool)
    def on_connection_status_changed(self, connected):
        """Handle connection status change."""
        print(f"DEBUG: Connection status changed to: {connected}")
        if connected:
            self.status_label.setText("Connected")
            self.send_button.setEnabled(True)
            self.message_input.setEnabled(True)
            print("DEBUG: UI enabled for sending messages")
        else:
            self.status_label.setText("Disconnected")
            self.send_button.setEnabled(False)
            self.message_input.setEnabled(False)
            print("DEBUG: UI disabled - not connected")
    
    def send_message(self):
        """Send a message."""
        print(f"DEBUG: send_message called, client={self.chat_client}, connected={self.chat_client.connected if self.chat_client else None}")
        
        if not self.chat_client or not self.chat_client.connected:
            print("DEBUG: Cannot send message - no client or not connected")
            return
        
        content = self.message_input.text().strip()
        if not content:
            print("DEBUG: Cannot send message - empty content")
            return
        
        print(f"DEBUG: Sending message: {content}")
        
        # Send public message
        success = self.chat_client.send_public_message(content)
        
        if success:
            print("DEBUG: Message sent successfully")
            # Display the sent message in the chat window
            self.display_public_message_sent(content)
            self.message_input.clear()
        else:
            print("DEBUG: Failed to send message")
            QMessageBox.warning(self, "Error", "Failed to send message")
    
    def scroll_to_bottom(self):
        """Scroll message display to bottom."""
        scrollbar = self.message_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.chat_client:
            self.chat_client.disconnect()
        event.accept()
