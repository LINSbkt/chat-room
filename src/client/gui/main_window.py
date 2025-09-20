"""
Main window GUI for the chat client.
"""

import sys
import os
import subprocess
import platform
from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTextEdit, QLineEdit, QPushButton, QListWidget, 
                            QLabel, QSplitter, QMessageBox, QApplication,
                            QComboBox, QCheckBox, QFileDialog, QProgressBar,
                            QListWidgetItem)
from PySide6.QtCore import Qt, Slot, QUrl
from PySide6.QtGui import QFont, QColor, QDesktopServices
try:
    from ..chat_client import ChatClient
    from ...shared.messages.enums import MessageType
    from ...shared.messages.chat import ChatMessage
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from client.chat_client import ChatClient
    from shared.messages.enums import MessageType
    from shared.messages.chat import ChatMessage


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
        
        # Message type selection
        message_type_layout = QHBoxLayout()
        message_type_layout.addWidget(QLabel("Message Type:"))
        
        self.message_type_combo = QComboBox()
        self.message_type_combo.addItems(["Public", "Private"])
        self.message_type_combo.currentTextChanged.connect(self.on_message_type_changed)
        message_type_layout.addWidget(self.message_type_combo)
        
        # Recipient selection (initially hidden)
        message_type_layout.addWidget(QLabel("To:"))
        self.recipient_combo = QComboBox()
        self.recipient_combo.setVisible(False)
        message_type_layout.addWidget(self.recipient_combo)
        
        message_type_layout.addStretch()
        chat_layout.addLayout(message_type_layout)
        
        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        # File transfer button
        self.file_button = QPushButton("📁 Send File")
        self.file_button.clicked.connect(self.send_file)
        input_layout.addWidget(self.file_button)
        
        chat_layout.addLayout(input_layout)
        
        # Right panel - User list
        user_widget = QWidget()
        user_layout = QVBoxLayout(user_widget)
        
        user_layout.addWidget(QLabel("Online Users:"))
        self.user_list = QListWidget()
        user_layout.addWidget(self.user_list)
        
        # File transfer progress area
        user_layout.addWidget(QLabel("File Transfers:"))
        self.file_transfer_list = QListWidget()
        self.file_transfer_list.setMaximumHeight(100)
        self.file_transfer_list.itemDoubleClicked.connect(self.on_file_transfer_item_clicked)
        user_layout.addWidget(self.file_transfer_list)
        
        # Files area
        files_layout = QHBoxLayout()
        files_layout.addWidget(QLabel("Available Files:"))
        self.open_downloads_button = QPushButton("📂 Open Folder")
        self.open_downloads_button.clicked.connect(self.open_downloads_folder)
        files_layout.addWidget(self.open_downloads_button)
        user_layout.addLayout(files_layout)
        
        self.downloads_list = QListWidget()
        self.downloads_list.setMaximumHeight(100)
        self.downloads_list.itemDoubleClicked.connect(self.on_download_item_clicked)
        user_layout.addWidget(self.downloads_list)
        
        # Load existing downloads
        self.load_existing_downloads()
        
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
        
        # Connect file transfer signals
        chat_client.file_transfer_request.connect(self.on_file_transfer_request)
        chat_client.file_transfer_progress.connect(self.on_file_transfer_progress)
        chat_client.file_transfer_complete.connect(self.on_file_transfer_complete)
        chat_client.file_list_received.connect(self.on_file_list_received)
        
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
    
    @Slot(object)
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
        
        # Add to display with color coding
        self.message_display.setTextColor(QColor(0, 100, 0))  # Dark green for public messages
        self.message_display.append(formatted_message)
        self.message_display.setTextColor(QColor(0, 0, 0))  # Reset to black
        self.scroll_to_bottom()
    
    def display_public_message_sent(self, content: str):
        """Display a message sent by this client."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"(Global) ({timestamp}) {self.username}: {content}"
        
        # Add to display with color coding
        self.message_display.setTextColor(QColor(0, 100, 0))  # Dark green for public messages
        self.message_display.append(formatted_message)
        self.message_display.setTextColor(QColor(0, 0, 0))  # Reset to black
        self.scroll_to_bottom()
    
    def display_private_message_sent(self, content: str, recipient: str):
        """Display a private message sent by this client."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"(Private) (To {recipient}) ({timestamp}) {self.username}: {content}"
        
        # Add to display with color coding
        self.message_display.setTextColor(QColor(150, 0, 150))  # Purple for private messages
        self.message_display.append(formatted_message)
        self.message_display.setTextColor(QColor(0, 0, 0))  # Reset to black
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
        
        # Add to display with color coding
        self.message_display.setTextColor(QColor(150, 0, 150))  # Purple for private messages
        self.message_display.append(formatted_message)
        self.message_display.setTextColor(QColor(0, 0, 0))  # Reset to black
        self.scroll_to_bottom()
    
    @Slot(list)
    def on_user_list_updated(self, users):
        """Handle user list update."""
        print(f"DEBUG: User list updated with {len(users)} users: {users}")
        self.user_list.clear()
        
        # Sort users with current user first
        sorted_users = sorted(users)
        if self.username in sorted_users:
            sorted_users.remove(self.username)
            sorted_users.insert(0, self.username)
        
        # Update recipient combo box (exclude current user)
        self.recipient_combo.clear()
        other_users = [user for user in sorted_users if user != self.username]
        self.recipient_combo.addItems(other_users)
        
        for user in sorted_users:
            if user == self.username:
                # Mark current user with special formatting
                item_text = f"👤 {user} (You)"
            else:
                item_text = f"👤 {user}"
            
            self.user_list.addItem(item_text)
            print(f"DEBUG: Added user to list: {user}")
    
    @Slot(str)
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
        
        # Add to display with color coding
        self.message_display.setTextColor(QColor(0, 0, 150))  # Blue for system messages
        self.message_display.append(formatted_message)
        self.message_display.setTextColor(QColor(0, 0, 0))  # Reset to black
        self.scroll_to_bottom()
    
    @Slot(str)
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
    
    @Slot(bool)
    def on_connection_status_changed(self, connected):
        """Handle connection status change."""
        print(f"DEBUG: Connection status changed to: {connected}")
        if connected:
            self.status_label.setText("Connected")
            self.send_button.setEnabled(True)
            self.message_input.setEnabled(True)
            self.file_button.setEnabled(True)
            print("DEBUG: UI enabled for sending messages and files")
        else:
            self.status_label.setText("Disconnected")
            self.send_button.setEnabled(False)
            self.message_input.setEnabled(False)
            self.file_button.setEnabled(False)
            print("DEBUG: UI disabled - not connected")
    
    def on_message_type_changed(self, message_type: str):
        """Handle message type change."""
        if message_type == "Private":
            self.recipient_combo.setVisible(True)
            self.message_input.setPlaceholderText("Type your private message here...")
        else:
            self.recipient_combo.setVisible(False)
            self.message_input.setPlaceholderText("Type your message here...")
    
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
        
        message_type = self.message_type_combo.currentText()
        print(f"DEBUG: Sending {message_type.lower()} message: {content}")
        
        success = False
        if message_type == "Public":
            # Send public message
            success = self.chat_client.send_public_message(content)
            if success:
                # Display the sent message in the chat window
                self.display_public_message_sent(content)
        else:
            # Send private message
            recipient = self.recipient_combo.currentText()
            if not recipient:
                QMessageBox.warning(self, "Error", "Please select a recipient for private message")
                return
            
            success = self.chat_client.send_private_message(content, recipient)
            if success:
                # Display the sent private message in the chat window
                self.display_private_message_sent(content, recipient)
        
        if success:
            print("DEBUG: Message sent successfully")
            self.message_input.clear()
        else:
            print("DEBUG: Failed to send message")
            QMessageBox.warning(self, "Error", "Failed to send message")
    
    def scroll_to_bottom(self):
        """Scroll message display to bottom."""
        scrollbar = self.message_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_file(self):
        """Send a file to a user."""
        if not self.chat_client or not self.chat_client.connected:
            QMessageBox.warning(self, "Error", "Not connected to server")
            return
        
        # Get recipient - allow global file transfers
        message_type = self.message_type_combo.currentText()
        if message_type == "Public":
            recipient = "GLOBAL"  # Send to all users
        else:
            recipient = self.recipient_combo.currentText()
            if not recipient:
                QMessageBox.warning(self, "Error", "Please select a recipient for private file transfer")
                return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select File to Send", 
            "", 
            "All Files (*.*)"
        )
        
        if file_path:
            # Send the file
            success = self.chat_client.send_file(file_path, recipient)
            if success:
                filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
                self.display_system_message(f"📤 Sending file '{filename}' to {recipient}...")
            else:
                QMessageBox.warning(self, "Error", "Failed to send file")
    
    @Slot(object)
    def on_file_transfer_request(self, request):
        """Handle incoming file transfer request - now auto-accepted, so this is just for logging."""
        filename = request.filename  # Use property, not data dict
        sender = request.sender or 'Unknown user'
        
        # File transfers are now auto-accepted, so we just log this
        print(f"DEBUG: File transfer request received and auto-accepted: {filename} from {sender}")
    
    @Slot(str, int, int)
    def on_file_transfer_progress(self, transfer_id, current, total):
        """Handle file transfer progress update."""
        progress_percent = (current / total * 100) if total > 0 else 0
        
        # Update or add progress item in file transfer list
        for i in range(self.file_transfer_list.count()):
            item = self.file_transfer_list.item(i)
            if transfer_id in item.text():
                item.setText(f"📁 {transfer_id}: {progress_percent:.1f}% ({current}/{total})")
                break
        else:
            # Add new item if not found
            self.file_transfer_list.addItem(f"📁 {transfer_id}: {progress_percent:.1f}% ({current}/{total})")
    
    @Slot(str, bool, str)
    def on_file_transfer_complete(self, transfer_id, success, file_path):
        """Handle file transfer completion."""
        
        # Remove progress item
        for i in range(self.file_transfer_list.count()):
            item = self.file_transfer_list.item(i)
            if transfer_id in item.text():
                self.file_transfer_list.takeItem(i)
                break
        
        if success and file_path:
            filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
            self.display_system_message(f"✅ File transfer completed: {filename}")
            
            # Add to downloads list
            self.add_to_downloads_list(filename, file_path)
            
            # File transfer completed successfully - no dialog needed
            # Users can open files from the received files box if they want
            print(f"DEBUG: File transfer completed successfully: {filename}")
        else:
            self.display_system_message(f"❌ File transfer failed: {transfer_id}")
    
    @Slot(list)
    def on_file_list_received(self, file_list):
        """Handle received file list from server."""
        print(f"DEBUG: Received file list with {len(file_list)} files")
        
        # Clear existing downloads list
        self.downloads_list.clear()
        
        # Add files to downloads list
        for file_info in file_list:
            filename = file_info.get('filename', 'Unknown')
            file_path = file_info.get('file_path', '')
            is_public = file_info.get('is_public', False)
            
            # Create display text with public/private indicator
            if is_public:
                display_text = f"🌐 {filename}"
                tooltip = f"Public file\nPath: {file_path}"
            else:
                display_text = f"🔒 {filename}"
                tooltip = f"Private file\nPath: {file_path}"
            
            # Create item and add to list
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            item.setToolTip(tooltip)
            self.downloads_list.addItem(item)
        
        # Show system message
        if len(file_list) > 0:
            self.display_system_message(f"📋 Loaded {len(file_list)} accessible files")
        else:
            self.display_system_message("📋 No accessible files found")
    
    def display_system_message(self, message):
        """Display a system message in the chat."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"(System) ({timestamp}) {message}"
        
        # Add to display with color coding
        self.message_display.setTextColor(QColor(0, 0, 150))  # Blue for system messages
        self.message_display.append(formatted_message)
        self.message_display.setTextColor(QColor(0, 0, 0))  # Reset to black
        self.scroll_to_bottom()
    
    def add_to_downloads_list(self, filename, file_path):
        """Add a file to the downloads list."""
        # Create a custom item with file path stored as data
        item = QListWidgetItem(f"📄 {filename}")
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        item.setToolTip(f"Double-click to open\nPath: {file_path}")
        self.downloads_list.addItem(item)
    
    def open_file(self, file_path):
        """Open a file using the system default application."""
        try:
            if os.path.exists(file_path):
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', file_path])
            else:
                QMessageBox.warning(self, "File Not Found", f"The file could not be found:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error Opening File", f"Could not open file:\n{str(e)}")
    
    def open_downloads_folder(self):
        """Open the storages folder in the system file manager."""
        storages_dir = os.path.join(os.getcwd(), "storages")
        
        # Create storages directory if it doesn't exist
        os.makedirs(storages_dir, exist_ok=True)
        
        try:
            if platform.system() == 'Windows':
                os.startfile(storages_dir)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', storages_dir])
            else:  # Linux
                subprocess.run(['xdg-open', storages_dir])
        except Exception as e:
            QMessageBox.critical(self, "Error Opening Folder", f"Could not open storages folder:\n{str(e)}")
    
    def on_file_transfer_item_clicked(self, item):
        """Handle double-click on file transfer item."""
        # This could be used to show more details about the transfer
        pass
    
    def on_download_item_clicked(self, item):
        """Handle double-click on download item."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            self.open_file(file_path)
    
    def load_existing_downloads(self):
        """Load existing files from the storages folder."""
        # This method is now replaced by on_file_list_received
        # The file list will be loaded automatically when the client connects
        # and receives the file list from the server
        pass
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.chat_client:
            # Disconnect gracefully without showing error messages
            self.chat_client.disconnect(intentional=True)
        event.accept()
