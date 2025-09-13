"""
Refactored main window using the new modular architecture.
"""

import logging
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QStatusBar
from PySide6.QtCore import Qt

from .core.event_bus import event_bus
from .core.state_manager import state_manager, StateKeys
from .core.gui_controller import GUIController

logger = logging.getLogger(__name__)


class RefactoredMainWindow(QMainWindow):
    """Refactored main window using modular architecture."""
    
    def __init__(self):
        super().__init__()
        
        self.chat_client = None
        self.username = ""
        self.gui_controller = None
        
        self.setup_ui()
        self.setup_controller()
    
    def setup_ui(self) -> None:
        """Set up the main window UI."""
        self.setWindowTitle("Chatroom Application")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Status bar
        self.status_label = QLabel("Disconnected")
        self.statusBar().addWidget(self.status_label)
        
        logger.debug("Set up main window UI")
    
    def setup_controller(self) -> None:
        """Set up the GUI controller."""
        try:
            # Create GUI controller
            self.gui_controller = GUIController(event_bus, state_manager)
            
            # Create main window components
            central_widget = self.centralWidget()
            self.gui_controller.create_main_window_components(central_widget)
            
            # Set up layout
            self.gui_controller.setup_main_window_layout(central_widget)
            
            # Initialize components
            if not self.gui_controller.initialize_components():
                raise RuntimeError("Failed to initialize GUI components")
            
            # Subscribe to state changes for status updates
            state_manager.subscribe_to_state(StateKeys.CONNECTION_STATUS, self._on_connection_status_changed)
            state_manager.subscribe_to_state(StateKeys.CONNECTION_ERROR, self._on_connection_error)
            
            logger.info("GUI controller set up successfully")
            
        except Exception as e:
            logger.error(f"Failed to set up GUI controller: {e}")
            raise
    
    def set_chat_client(self, chat_client, username: str) -> None:
        """
        Set the chat client and connect it to the GUI.
        
        Args:
            chat_client: Chat client instance
            username: Current username
        """
        try:
            self.chat_client = chat_client
            self.username = username
            
            # Connect chat client to GUI controller
            self.gui_controller.set_chat_client(chat_client, username)
            
            # Update window title
            self.setWindowTitle(f"Chatroom Application - {username}")
            
            logger.info(f"Set chat client for user: {username}")
            
        except Exception as e:
            logger.error(f"Failed to set chat client: {e}")
            raise
    
    def _on_connection_status_changed(self, change) -> None:
        """Handle connection status changes."""
        connected = change.new_value
        if connected:
            self.status_label.setText("Connected")
        else:
            self.status_label.setText("Disconnected")
    
    def _on_connection_error(self, change) -> None:
        """Handle connection errors."""
        error_message = change.new_value
        if error_message:
            self.status_label.setText(f"Error: {error_message}")
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        try:
            if self.chat_client:
                # Disconnect gracefully
                self.chat_client.disconnect(intentional=True)
            
            if self.gui_controller:
                # Clean up GUI controller
                self.gui_controller.cleanup()
            
            event.accept()
            logger.info("Main window closed")
            
        except Exception as e:
            logger.error(f"Error closing main window: {e}")
            event.accept()  # Accept anyway to allow window to close
