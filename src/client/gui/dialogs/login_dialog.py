"""
Login dialog for username input.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt


class LoginDialog(QDialog):
    """Login dialog for username input."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login to Chatroom")
        self.setModal(True)
        self.setFixedSize(300, 150)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Username input
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.returnPressed.connect(self.accept_login)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.accept_login)
        self.login_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # Focus on username input
        self.username_input.setFocus()
    
    def accept_login(self):
        """Handle login button click."""
        username = self.username_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, "Invalid Username", "Please enter a username.")
            return
        
        if len(username) < 2:
            QMessageBox.warning(self, "Invalid Username", "Username must be at least 2 characters long.")
            return
        
        if len(username) > 20:
            QMessageBox.warning(self, "Invalid Username", "Username must be less than 20 characters.")
            return
        
        # Check for invalid characters
        invalid_chars = ['<', '>', '&', '"', "'", '\\', '/']
        if any(char in username for char in invalid_chars):
            QMessageBox.warning(self, "Invalid Username", "Username contains invalid characters.")
            return
        
        self.accept()
    
    def get_username(self) -> str:
        """Get the entered username."""
        return self.username_input.text().strip()

