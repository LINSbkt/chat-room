"""
Main GUI controller for coordinating all components.
"""

from typing import Dict, Any, Optional, List
import logging
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from .event_bus import EventBus, Event, ChatEvents
from .state_manager import StateManager, StateKeys
from ..components.base.component_registry import ComponentRegistry, get_component_registry
from ..components.chat.chat_context_manager import ChatContextManager
from ..components.chat.chat_display import ChatDisplay
from ..components.chat.message_input import MessageInput
from ..components.chat.file_transfer_input import FileTransferInput
from ..components.users.user_list import UserList
from ..components.notifications.notification_manager import NotificationManager
from ..components.files.file_history import FileHistory

logger = logging.getLogger(__name__)


class GUIController:
    """Main controller for coordinating GUI components."""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        """
        Initialize GUI controller.
        
        Args:
            event_bus: Event bus instance
            state_manager: State manager instance
        """
        self.event_bus = event_bus
        self.state_manager = state_manager
        self.component_registry = get_component_registry()
        
        self._components: Dict[str, Any] = {}
        self._initialized = False
        self._chat_client = None
        
        # Register component types
        self._register_component_types()
        
        # Set up event handlers
        self._setup_event_handlers()
    
    def _register_component_types(self) -> None:
        """Register all component types with the registry."""
        self.component_registry.register_component_type("chat_context_manager", ChatContextManager)
        self.component_registry.register_component_type("chat_display", ChatDisplay)
        self.component_registry.register_component_type("message_input", MessageInput)
        self.component_registry.register_component_type("file_transfer_input", FileTransferInput)
        self.component_registry.register_component_type("user_list", UserList)
        self.component_registry.register_component_type("notification_manager", NotificationManager)
        self.component_registry.register_component_type("file_history", FileHistory)
        
        logger.debug("Registered component types")
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for the GUI controller."""
        self.event_bus.subscribe(ChatEvents.MESSAGE_SENT, self._handle_message_sent)
        self.event_bus.subscribe(ChatEvents.FILE_TRANSFER_REQUESTED, self._handle_file_transfer_requested)
        logger.debug("GUI controller event handlers set up")
    
    def create_main_window_components(self, parent_widget: QWidget) -> Dict[str, Any]:
        """
        Create all main window components.
        
        Args:
            parent_widget: Parent widget for components
            
        Returns:
            Dictionary of created components
        """
        try:
            # Create chat context manager (invisible component)
            context_manager = self.component_registry.create_component(
                "chat_context_manager",
                "chat_context_manager",
                parent_widget
            )
            self._components["chat_context_manager"] = context_manager
            
            # Create notification manager (invisible component)
            notification_manager = self.component_registry.create_component(
                "notification_manager",
                "notification_manager",
                parent_widget
            )
            self._components["notification_manager"] = notification_manager
            
            # Create main UI components
            chat_display = self.component_registry.create_component(
                "chat_display",
                "chat_display",
                parent_widget
            )
            self._components["chat_display"] = chat_display
            
            message_input = self.component_registry.create_component(
                "message_input",
                "message_input",
                parent_widget
            )
            self._components["message_input"] = message_input
            
            file_transfer_input = self.component_registry.create_component(
                "file_transfer_input",
                "file_transfer_input",
                parent_widget
            )
            self._components["file_transfer_input"] = file_transfer_input
            
            user_list = self.component_registry.create_component(
                "user_list",
                "user_list",
                parent_widget
            )
            self._components["user_list"] = user_list
            
            file_history = self.component_registry.create_component(
                "file_history",
                "file_history",
                parent_widget
            )
            self._components["file_history"] = file_history
            
            logger.info("Created main window components")
            return self._components
            
        except Exception as e:
            logger.error(f"Failed to create main window components: {e}")
            raise
    
    def initialize_components(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Set up component dependencies
            self._setup_component_dependencies()
            
            # Initialize components in dependency order
            results = self.component_registry.initialize_components_in_order()
            
            # Check for failures
            failed_components = [comp_id for comp_id, success in results.items() if not success]
            if failed_components:
                logger.error(f"Failed to initialize components: {failed_components}")
                return False
            
            self._initialized = True
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            return False
    
    def _setup_component_dependencies(self) -> None:
        """Set up component dependencies."""
        # Chat context manager has no dependencies
        self.component_registry.set_component_dependencies("chat_context_manager", [])
        
        # Chat display depends on context manager
        self.component_registry.set_component_dependencies("chat_display", ["chat_context_manager"])
        
        # Message input depends on context manager
        self.component_registry.set_component_dependencies("message_input", ["chat_context_manager"])
        
        # File transfer input depends on context manager
        self.component_registry.set_component_dependencies("file_transfer_input", ["chat_context_manager"])
        
        # User list depends on context manager
        self.component_registry.set_component_dependencies("user_list", ["chat_context_manager"])
        
        # File history has no dependencies
        self.component_registry.set_component_dependencies("file_history", [])
    
    def setup_main_window_layout(self, parent_widget: QWidget) -> None:
        """
        Set up the main window layout with components.
        
        Args:
            parent_widget: Parent widget to set up layout for
        """
        try:
            # Create main layout
            main_layout = QHBoxLayout(parent_widget)
            
            # Create splitter for resizable panels
            splitter = QSplitter(Qt.Orientation.Horizontal)
            main_layout.addWidget(splitter)
            
            # Left panel - Chat area
            chat_widget = QWidget()
            chat_layout = QVBoxLayout(chat_widget)
            
            # Add chat display
            if "chat_display" in self._components:
                chat_layout.addWidget(self._components["chat_display"])
            
            # Add message input
            if "message_input" in self._components:
                chat_layout.addWidget(self._components["message_input"])
            
            # Add file transfer input
            if "file_transfer_input" in self._components:
                chat_layout.addWidget(self._components["file_transfer_input"])
            
            # Right panel - User list and File history
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            
            # Add user list
            if "user_list" in self._components:
                right_layout.addWidget(self._components["user_list"])
            
            # Add file history
            if "file_history" in self._components:
                right_layout.addWidget(self._components["file_history"])
            
            # Add widgets to splitter
            splitter.addWidget(chat_widget)
            splitter.addWidget(right_widget)
            splitter.setSizes([600, 300])  # Increased right panel size for file history
            
            logger.info("Set up main window layout")
            
        except Exception as e:
            logger.error(f"Failed to set up main window layout: {e}")
            raise
    
    def set_chat_client(self, chat_client, username: str) -> None:
        """
        Set the chat client and connect it to the GUI.
        
        Args:
            chat_client: Chat client instance
            username: Current username
        """
        try:
            # Store chat client reference
            self._chat_client = chat_client
            
            # Set initial state
            self.state_manager.set_state(StateKeys.CURRENT_USER, username, "gui_controller")
            self.state_manager.set_state(StateKeys.CONNECTION_STATUS, True, "gui_controller")
            
            # Connect chat client signals to event bus
            self._connect_chat_client_signals(chat_client)
            
            # Connect chat client to file history component
            if "file_history" in self._components:
                self._components["file_history"].set_chat_client(chat_client)
            
            logger.info(f"Connected chat client for user: {username}")
            
        except Exception as e:
            logger.error(f"Failed to set chat client: {e}")
            raise
    
    def _connect_chat_client_signals(self, chat_client) -> None:
        """Connect chat client signals to event bus."""
        try:
            # Message signals
            chat_client.message_received.connect(self._on_message_received)
            chat_client.user_list_updated.connect(self._on_user_list_updated)
            chat_client.system_message.connect(self._on_system_message)
            chat_client.error_occurred.connect(self._on_error_occurred)
            chat_client.connection_status_changed.connect(self._on_connection_status_changed)
            
            # File transfer signals (if available)
            if hasattr(chat_client, 'file_transfer_request'):
                chat_client.file_transfer_request.connect(self._on_file_transfer_request)
            if hasattr(chat_client, 'file_transfer_progress'):
                chat_client.file_transfer_progress.connect(self._on_file_transfer_progress)
            if hasattr(chat_client, 'file_transfer_complete'):
                chat_client.file_transfer_complete.connect(self._on_file_transfer_complete)
            if hasattr(chat_client, 'file_list_received'):
                chat_client.file_list_received.connect(self._on_file_list_received)
            
            logger.debug("Connected chat client signals")
            
        except Exception as e:
            logger.error(f"Failed to connect chat client signals: {e}")
    
    def _on_message_received(self, message) -> None:
        """Handle message received from chat client."""
        try:
            # Convert message to event data
            message_type = getattr(message, 'message_type', message.data.get('message_type', 'public'))
            
            # Convert MessageType enum to string for GUI components
            if hasattr(message_type, 'name'):
                # It's a MessageType enum
                if message_type.name == 'PUBLIC_MESSAGE':
                    message_type_str = 'public'
                elif message_type.name == 'PRIVATE_MESSAGE':
                    message_type_str = 'private'
                else:
                    message_type_str = 'public'  # Default fallback
            else:
                # It's already a string
                message_type_str = str(message_type)
            
            # Also check for is_private flag in message data
            is_private = getattr(message, 'is_private', message.data.get('is_private', False))
            recipient = getattr(message, 'recipient', message.data.get('recipient', None))
            
            message_data = {
                "content": getattr(message, 'content', message.data.get('content', 'Unknown message')),
                "sender": getattr(message, 'sender', message.data.get('sender', 'Unknown')),
                "message_type": message_type_str,
                "is_private": is_private,
                "recipient": recipient,
                "timestamp": getattr(message, 'timestamp', None)
            }
            
            logger.info(f"🎯 GUI Controller: Received {message_data['message_type']} message from {message_data['sender']}: {message_data['content'][:50]}...")
            logger.info(f"🎯 GUI Controller: Message details - is_private: {message_data['is_private']}, recipient: {message_data['recipient']}")
            
            # Publish message received event
            self.event_bus.publish(Event(
                event_type=ChatEvents.MESSAGE_RECEIVED,
                data={"message": message_data},
                source="gui_controller"
            ))
            
            logger.debug(f"GUI Controller: Published MESSAGE_RECEIVED event for {message_data['message_type']} message from {message_data['sender']}")
            
        except Exception as e:
            logger.error(f"Error handling message received: {e}")
    
    def _on_user_list_updated(self, users: List[str]) -> None:
        """Handle user list update from chat client."""
        try:
            # Update state
            self.state_manager.set_state(StateKeys.USER_LIST, users, "gui_controller")
            
            # Publish user list updated event
            self.event_bus.publish(Event(
                event_type=ChatEvents.USER_LIST_UPDATED,
                data={"users": users},
                source="gui_controller"
            ))
            
        except Exception as e:
            logger.error(f"Error handling user list update: {e}")
    
    def _on_system_message(self, message: str) -> None:
        """Handle system message from chat client."""
        try:
            # Publish system message event
            self.event_bus.publish(Event(
                event_type=ChatEvents.SYSTEM_MESSAGE,
                data={"message": message},
                source="gui_controller"
            ))
            
        except Exception as e:
            logger.error(f"Error handling system message: {e}")
    
    def _on_error_occurred(self, error_message: str) -> None:
        """Handle error from chat client."""
        try:
            # Update state
            self.state_manager.set_state(StateKeys.CONNECTION_ERROR, error_message, "gui_controller")
            
            # Publish error event
            self.event_bus.publish(Event(
                event_type=ChatEvents.ERROR_OCCURRED,
                data={"error": error_message},
                source="gui_controller"
            ))
            
        except Exception as e:
            logger.error(f"Error handling error: {e}")
    
    def _on_connection_status_changed(self, connected: bool) -> None:
        """Handle connection status change from chat client."""
        try:
            # Update state
            self.state_manager.set_state(StateKeys.CONNECTION_STATUS, connected, "gui_controller")
            
            # Publish connection status changed event
            self.event_bus.publish(Event(
                event_type=ChatEvents.CONNECTION_STATUS_CHANGED,
                data={"connected": connected},
                source="gui_controller"
            ))
            
        except Exception as e:
            logger.error(f"Error handling connection status change: {e}")
    
    def _on_file_transfer_request(self, request) -> None:
        """Handle file transfer request."""
        try:
            from PySide6.QtWidgets import QMessageBox
            
            filename = getattr(request, 'filename', request.data.get('filename', 'Unknown file'))
            sender = getattr(request, 'sender', request.data.get('sender', 'Unknown user'))
            file_size = getattr(request, 'file_size', request.data.get('file_size', 0))
            
            # Format file size
            if file_size > 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            elif file_size > 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size} bytes"
            
            # Show dialog asking user to accept or decline
            reply = QMessageBox.question(
                None, 
                "File Transfer Request", 
                f"{sender} wants to send you a file:\n\n"
                f"📁 {filename}\n"
                f"📏 Size: {size_str}\n\n"
                f"Do you want to accept this file?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Accept the file transfer
                transfer_id = getattr(request, 'transfer_id', request.data.get('transfer_id', request.message_id))
                self._chat_client.accept_file_transfer(transfer_id)
                logger.info(f"Accepted file transfer: {filename} from {sender}")
                
                # Show system message
                self.event_bus.publish(Event(
                    event_type=ChatEvents.SYSTEM_MESSAGE,
                    data={"message": f"📥 Accepting file '{filename}' from {sender}"},
                    source="gui_controller"
                ))
            else:
                # Decline the file transfer
                transfer_id = getattr(request, 'transfer_id', request.data.get('transfer_id', request.message_id))
                self._chat_client.decline_file_transfer(transfer_id)
                logger.info(f"Declined file transfer: {filename} from {sender}")
                
                # Show system message
                self.event_bus.publish(Event(
                    event_type=ChatEvents.SYSTEM_MESSAGE,
                    data={"message": f"❌ Declined file '{filename}' from {sender}"},
                    source="gui_controller"
                ))
                
        except Exception as e:
            logger.error(f"Error handling file transfer request: {e}")
    
    def _on_file_transfer_progress(self, transfer_id: str, current: int, total: int) -> None:
        """Handle file transfer progress."""
        progress_percent = (current / total * 100) if total > 0 else 0
        logger.debug(f"File transfer progress: {transfer_id} - {progress_percent:.1f}% ({current}/{total})")
    
    def _on_file_transfer_complete(self, transfer_id: str, success: bool, file_path: str) -> None:
        """Handle file transfer completion."""
        try:
            from PySide6.QtWidgets import QMessageBox
            import os
            
            if success and file_path:
                filename = os.path.basename(file_path)
                logger.info(f"File transfer completed successfully: {filename}")
                
                # Show system message
                self.event_bus.publish(Event(
                    event_type=ChatEvents.SYSTEM_MESSAGE,
                    data={"message": f"✅ File transfer completed: {filename}"},
                    source="gui_controller"
                ))
                
                # Show success message with option to open file
                reply = QMessageBox.question(
                    None, 
                    "File Transfer Complete", 
                    f"File '{filename}' has been downloaded successfully!\n\nWould you like to open it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self._open_file(file_path)
            else:
                logger.error(f"File transfer failed: {transfer_id}")
                
                # Show system message
                self.event_bus.publish(Event(
                    event_type=ChatEvents.SYSTEM_MESSAGE,
                    data={"message": f"❌ File transfer failed: {transfer_id}"},
                    source="gui_controller"
                ))
                
                QMessageBox.warning(
                    None,
                    "File Transfer Failed",
                    f"File transfer failed: {file_path if not success else 'Unknown error'}"
                )
                
        except Exception as e:
            logger.error(f"Error handling file transfer completion: {e}")
    
    def _on_file_list_received(self, file_list: List[Dict[str, Any]]) -> None:
        """Handle file list received."""
        logger.debug(f"File list received: {len(file_list)} files")
        
        # Publish file list received event for components to handle
        self.event_bus.publish(Event(
            event_type=ChatEvents.FILE_LIST_RECEIVED,
            data={"files": file_list},
            source="gui_controller"
        ))
    
    def _open_file(self, file_path: str) -> None:
        """Open a file with the default system application."""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux and others
                subprocess.run(['xdg-open', file_path])
                
            logger.info(f"Opened file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                None,
                "Error Opening File",
                f"Could not open file: {e}"
            )
    
    def _handle_message_sent(self, event: Event) -> None:
        """Handle message sent event and send to chat client."""
        try:
            if not self._chat_client:
                logger.error("Cannot send message: no chat client connected")
                return
            
            message = event.data.get("message")
            if not message:
                logger.error("Cannot send message: no message data")
                return
            
            # Extract message details
            content = message.get("content", "")
            message_type = message.get("message_type", "public")
            recipient = message.get("recipient")
            
            logger.info(f"Sending {message_type} message: {content[:50]}...")
            
            # Send message to chat client
            if message_type == "public":
                # Send public message
                self._chat_client.send_public_message(content)
            elif message_type == "private" and recipient:
                # Send private message
                self._chat_client.send_private_message(content, recipient)
            else:
                logger.error(f"Cannot send message: invalid message type or missing recipient")
                return
            
            logger.debug(f"Message sent successfully to chat client")
            
        except Exception as e:
            logger.error(f"Error sending message to chat client: {e}")
    
    def _handle_file_transfer_requested(self, event: Event) -> None:
        """Handle file transfer request event and send to chat client."""
        try:
            if not self._chat_client:
                logger.error("Cannot send file: no chat client connected")
                return
            
            file_data = event.data.get("file_data")
            if not file_data:
                logger.error("Cannot send file: no file data")
                return
            
            # Extract file details
            file_path = file_data.get("file_path", "")
            filename = file_data.get("filename", "")
            file_size = file_data.get("file_size", 0)
            recipient = file_data.get("recipient", "")
            is_private = file_data.get("is_private", True)
            
            logger.info(f"Sending file: {filename} ({file_size} bytes) to {recipient}")
            
            # Send file transfer request to chat client
            if is_private and recipient != "GLOBAL":
                # Send private file transfer
                success = self._chat_client.send_file(file_path, recipient)
            else:
                # Send public file transfer
                success = self._chat_client.send_file(file_path, "GLOBAL")
            
            if success:
                logger.debug(f"File transfer request sent successfully")
            else:
                logger.error(f"Failed to send file transfer request")
            
        except Exception as e:
            logger.error(f"Error sending file transfer request: {e}")
    
    def cleanup(self) -> None:
        """Clean up the GUI controller and all components."""
        try:
            if self._initialized:
                # Clean up all components
                self.component_registry.cleanup_all_components()
                self._components.clear()
                self._initialized = False
                
                logger.info("GUI controller cleaned up")
                
        except Exception as e:
            logger.error(f"Error cleaning up GUI controller: {e}")
    
    def get_component(self, component_id: str) -> Optional[Any]:
        """Get a component by ID."""
        return self._components.get(component_id)
    
    def is_initialized(self) -> bool:
        """Check if controller is initialized."""
        return self._initialized
