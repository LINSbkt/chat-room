"""
Login dialog for username input.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class LoginDialog(QDialog):
    """Login dialog for username input."""
    
    # Signal emitted when login is attempted
    login_attempted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to Chatroom")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Welcome to Chatroom")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Username input
        username_layout = QVBoxLayout()
        username_layout.addWidget(QLabel("Enter your username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username (1-20 characters, alphanumeric + spaces, _, -)")
        self.username_input.setMaxLength(20)
        self.username_input.returnPressed.connect(self.accept_login)
        self.username_input.textChanged.connect(self.validate_username_realtime)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.accept_login)
        self.login_button.setDefault(True)
        self.login_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Focus on username input
        self.username_input.setFocus()
    
    def validate_username_realtime(self):
        """Validate username in real-time as user types."""
        username = self.username_input.text().strip()
        
        if not username:
            self.status_label.setText("")
            self.login_button.setEnabled(False)
            return
        
        if len(username) < 1:
            self.status_label.setText("Username must be at least 1 character")
            self.login_button.setEnabled(False)
            return
        
        if len(username) > 20:
            self.status_label.setText("Username too long (max 20 characters)")
            self.login_button.setEnabled(False)
            return
        
        # Check for invalid characters (alphanumeric, spaces, underscores, hyphens only)
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-')
        if not all(c in allowed_chars for c in username):
            self.status_label.setText("Username contains invalid characters")
            self.login_button.setEnabled(False)
            return
        
        # Username is valid
        self.status_label.setText("✓ Username looks good!")
        self.status_label.setStyleSheet("color: green; font-size: 10px;")
        self.login_button.setEnabled(True)
    
    def accept_login(self):
        """Handle login button click."""
        username = self.username_input.text().strip()
        
        if not self.validate_username_final(username):
            return
        
        # Emit signal for external handling
        self.login_attempted.emit(username)
        self.accept()
    
    def validate_username_final(self, username: str) -> bool:
        """Final validation before login attempt."""
        if not username:
            QMessageBox.warning(self, "Invalid Username", "Please enter a username.")
            return False
        
        if len(username) < 1:
            QMessageBox.warning(self, "Invalid Username", "Username must be at least 1 character long.")
            return False
        
        if len(username) > 20:
            QMessageBox.warning(self, "Invalid Username", "Username must be less than 20 characters.")
            return False
        
        # Check for invalid characters
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-')
        if not all(c in allowed_chars for c in username):
            QMessageBox.warning(self, "Invalid Username", "Username contains invalid characters. Only letters, numbers, spaces, underscores, and hyphens are allowed.")
            return False
        
        return True
    
    def get_username(self) -> str:
        """Get the entered username."""
        return self.username_input.text().strip()

