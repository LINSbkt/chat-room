"""
Qt signals for the chat client.
"""

from PySide6.QtCore import QObject, Signal as pyqtSignal


class ClientSignals(QObject):
    """Container for all client Qt signals."""
    
    message_received = pyqtSignal(object)  # Message object
    user_list_updated = pyqtSignal(list)   # List of usernames
    system_message = pyqtSignal(str)       # System message content
    error_occurred = pyqtSignal(str)       # Error message
    connection_status_changed = pyqtSignal(bool)  # Connected status
    file_transfer_request = pyqtSignal(object)  # FileTransferRequest object
    file_transfer_progress = pyqtSignal(str, int, int)  # transfer_id, current, total
    file_transfer_complete = pyqtSignal(str, bool, str)  # transfer_id, success, file_path