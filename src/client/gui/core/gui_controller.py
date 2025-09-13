"""
Main GUI controller for coordinating all components.
"""

from typing import Dict, Any, Optional, List
import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from .event_bus import EventBus, Event, ChatEvents
from .state_manager import StateManager, StateKeys
from ..components.base.component_registry import ComponentRegistry, get_component_registry
from ..components.chat.chat_context_manager import ChatContextManager
from ..components.chat.chat_display import ChatDisplay
from ..components.chat.message_input import MessageInput
from ..components.users.user_list import UserList

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
        self.component_registry.register_component_type("user_list", UserList)
        
        logger.debug("Registered component types")
    
    def _setup_event_handlers(self) -> None:
        """Set up event handlers for the GUI controller."""
        self.event_bus.subscribe(ChatEvents.MESSAGE_SENT, self._handle_message_sent)
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
            
            user_list = self.component_registry.create_component(
                "user_list",
                "user_list",
                parent_widget
            )
            self._components["user_list"] = user_list
            
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
        
        # User list depends on context manager
        self.component_registry.set_component_dependencies("user_list", ["chat_context_manager"])
    
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
            
            # Right panel - User list
            user_widget = QWidget()
            user_layout = QVBoxLayout(user_widget)
            
            # Add user list
            if "user_list" in self._components:
                user_layout.addWidget(self._components["user_list"])
            
            # Add widgets to splitter
            splitter.addWidget(chat_widget)
            splitter.addWidget(user_widget)
            splitter.setSizes([600, 200])  # Default sizes
            
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
            message_data = {
                "content": getattr(message, 'content', message.data.get('content', 'Unknown message')),
                "sender": getattr(message, 'sender', message.data.get('sender', 'Unknown')),
                "message_type": getattr(message, 'message_type', message.data.get('message_type', 'public')),
                "timestamp": getattr(message, 'timestamp', None)
            }
            
            logger.debug(f"GUI Controller: Received {message_data['message_type']} message from {message_data['sender']}: {message_data['content'][:50]}...")
            
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
        """Handle file transfer request (placeholder for future)."""
        logger.debug("File transfer request received (placeholder)")
    
    def _on_file_transfer_progress(self, transfer_id: str, current: int, total: int) -> None:
        """Handle file transfer progress (placeholder for future)."""
        logger.debug(f"File transfer progress: {transfer_id} ({current}/{total})")
    
    def _on_file_transfer_complete(self, transfer_id: str, success: bool, file_path: str) -> None:
        """Handle file transfer completion (placeholder for future)."""
        logger.debug(f"File transfer complete: {transfer_id}, success: {success}")
    
    def _on_file_list_received(self, file_list: List[Dict[str, Any]]) -> None:
        """Handle file list received (placeholder for future)."""
        logger.debug(f"File list received: {len(file_list)} files")
    
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
