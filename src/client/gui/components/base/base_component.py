"""
Abstract base component class for all GUI components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal

from ...core.event_bus import EventBus, Event
from ...core.state_manager import StateManager, StateChange

logger = logging.getLogger(__name__)


class BaseComponent(QWidget):
    """Abstract base class for all GUI components."""
    
    # Signals for component lifecycle
    component_initialized = Signal(str)  # component_id
    component_cleaned_up = Signal(str)   # component_id
    
    def __init__(self, component_id: str, event_bus: EventBus, state_manager: StateManager, parent: QWidget = None):
        """
        Initialize base component.
        
        Args:
            component_id: Unique identifier for this component
            event_bus: Event bus for communication
            state_manager: State manager for state access
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.component_id = component_id
        self.event_bus = event_bus
        self.state_manager = state_manager
        self._initialized = False
        self._event_handlers: Dict[str, callable] = {}
        self._state_subscriptions: List[str] = []
        
        logger.debug(f"Initializing component: {component_id}")
    
    def initialize(self) -> None:
        """Initialize the component. Must be called after construction."""
        if self._initialized:
            logger.warning(f"Component {self.component_id} already initialized")
            return
        
        try:
            # Set up UI
            self.setup_ui()
            
            # Set up event handlers
            self.setup_event_handlers()
            
            # Set up state subscriptions
            self.setup_state_subscriptions()
            
            # Set up connections
            self.setup_connections()
            
            # Perform component-specific initialization
            self.on_initialize()
            
            self._initialized = True
            self.component_initialized.emit(self.component_id)
            
            logger.info(f"Component {self.component_id} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize component {self.component_id}: {e}")
            raise
    
    def cleanup(self) -> None:
        """Clean up the component."""
        if not self._initialized:
            return
        
        try:
            # Perform component-specific cleanup
            self.on_cleanup()
            
            # Unsubscribe from events
            for event_type, handler in self._event_handlers.items():
                self.event_bus.unsubscribe(event_type, handler)
            
            # Unsubscribe from state changes
            for key in self._state_subscriptions:
                self.state_manager.unsubscribe_from_state(key, self._handle_state_change)
            
            self._event_handlers.clear()
            self._state_subscriptions.clear()
            
            self._initialized = False
            self.component_cleaned_up.emit(self.component_id)
            
            logger.info(f"Component {self.component_id} cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error cleaning up component {self.component_id}: {e}")
    
    @abstractmethod
    def setup_ui(self) -> None:
        """Set up the user interface. Must be implemented by subclasses."""
        pass
    
    def setup_event_handlers(self) -> None:
        """Set up event handlers. Override in subclasses to add event subscriptions."""
        pass
    
    def setup_state_subscriptions(self) -> None:
        """Set up state subscriptions. Override in subclasses to subscribe to state changes."""
        pass
    
    def setup_connections(self) -> None:
        """Set up signal connections. Override in subclasses to connect Qt signals."""
        pass
    
    def on_initialize(self) -> None:
        """Component-specific initialization. Override in subclasses."""
        pass
    
    def on_cleanup(self) -> None:
        """Component-specific cleanup. Override in subclasses."""
        pass
    
    def handle_event(self, event: Event) -> None:
        """
        Handle incoming events. Override in subclasses.
        
        Args:
            event: The event to handle
        """
        logger.debug(f"Component {self.component_id} received event: {event.event_type}")
    
    def update_state(self, state: Dict[str, Any]) -> None:
        """
        Update component state. Override in subclasses.
        
        Args:
            state: New state values
        """
        logger.debug(f"Component {self.component_id} state updated")
    
    def _handle_state_change(self, change: StateChange) -> None:
        """Internal handler for state changes."""
        try:
            self.on_state_change(change)
        except Exception as e:
            logger.error(f"Error handling state change in {self.component_id}: {e}")
    
    def on_state_change(self, change: StateChange) -> None:
        """
        Handle state changes. Override in subclasses.
        
        Args:
            change: The state change
        """
        pass
    
    def subscribe_to_event(self, event_type: str, handler: callable = None) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Handler function (defaults to handle_event)
        """
        if handler is None:
            handler = self.handle_event
        
        self.event_bus.subscribe(event_type, handler)
        self._event_handlers[event_type] = handler
        
        logger.debug(f"Component {self.component_id} subscribed to {event_type}")
    
    def unsubscribe_from_event(self, event_type: str) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
        """
        if event_type in self._event_handlers:
            handler = self._event_handlers[event_type]
            self.event_bus.unsubscribe(event_type, handler)
            del self._event_handlers[event_type]
            
            logger.debug(f"Component {self.component_id} unsubscribed from {event_type}")
    
    def subscribe_to_state(self, key: str) -> None:
        """
        Subscribe to state changes for a specific key.
        
        Args:
            key: State key to monitor
        """
        self.state_manager.subscribe_to_state(key, self._handle_state_change)
        self._state_subscriptions.append(key)
        
        logger.debug(f"Component {self.component_id} subscribed to state: {key}")
    
    def publish_event(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """
        Publish an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if data is None:
            data = {}
        
        event = Event(
            event_type=event_type,
            data=data,
            source=self.component_id
        )
        
        self.event_bus.publish(event)
    
    def publish_async_event(self, event_type: str, data: Dict[str, Any] = None) -> None:
        """
        Publish an async event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if data is None:
            data = {}
        
        event = Event(
            event_type=event_type,
            data=data,
            source=self.component_id
        )
        
        self.event_bus.publish_async(event)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get state value.
        
        Args:
            key: State key
            default: Default value
            
        Returns:
            State value
        """
        return self.state_manager.get_state(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        Set state value.
        
        Args:
            key: State key
            value: New value
        """
        self.state_manager.set_state(key, value, self.component_id)
    
    def update_multiple_state(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple state values.
        
        Args:
            updates: Dictionary of key-value pairs
        """
        self.state_manager.update_state(updates, self.component_id)
    
    def is_initialized(self) -> bool:
        """Check if component is initialized."""
        return self._initialized
    
    def get_component_info(self) -> Dict[str, Any]:
        """
        Get component information.
        
        Returns:
            Dictionary with component information
        """
        return {
            "component_id": self.component_id,
            "initialized": self._initialized,
            "event_subscriptions": list(self._event_handlers.keys()),
            "state_subscriptions": self._state_subscriptions.copy(),
            "parent": self.parent() is not None
        }
