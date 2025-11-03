"""
File transfer dialog component.
"""

import logging
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox

logger = logging.getLogger(__name__)

class FileTransferDialog(QDialog):
    """Dialog for accepting/declining file transfers."""
    
    def __init__(self, filename: str, sender: str, file_size: str = None, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("File Transfer Request")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Message
        size_text = f" ({file_size})" if file_size else ""
        message = QLabel(f"User '{sender}' wants to send you the file:\n\n{filename}{size_text}\n\nAccept the file?")
        layout.addWidget(message)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        accept_button = QPushButton("Accept")
        accept_button.clicked.connect(self.accept)
        button_layout.addWidget(accept_button)
        
        decline_button = QPushButton("Decline")
        decline_button.clicked.connect(self.reject)
        button_layout.addWidget(decline_button)
        
        layout.addLayout(button_layout)
        
        logger.debug(f"Created file transfer dialog for {filename} from {sender}")