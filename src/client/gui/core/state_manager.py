"""
Centralized state management for the GUI application.
"""

from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging
import threading
from copy import deepcopy

logger = logging.getLogger(__name__)


@dataclass
class StateChange:
    """Represents a state change event."""
    key: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = None


class StateManager:
    """Centralized state management with change notifications."""
    
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._subscribers: Dict[str, List[Callable]] = {}
        self._change_history: List[StateChange] = []
        self._max_history = 1000
        self._lock = threading.RLock()  # Thread-safe access
        
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get state value by key.
        
        Args:
            key: State key
            default: Default value if key doesn't exist
            
        Returns:
            State value or default
        """
        with self._lock:
            return self._state.get(key, default)
    
    def set_state(self, key: str, value: Any, source: str = None) -> None:
        """
        Set state value and notify subscribers.
        
        Args:
            key: State key
            value: New value
            source: Source of the change (for debugging)
        """
        with self._lock:
            old_value = self._state.get(key)
            
            # Only update if value actually changed
            if old_value != value:
                self._state[key] = deepcopy(value)  # Store deep copy
                
                # Record change
                change = StateChange(
                    key=key,
                    old_value=old_value,
                    new_value=deepcopy(value),
                    source=source
                )
                self._add_to_history(change)
                
                # Notify subscribers
                self._notify_subscribers(change)
                
                logger.debug(f"State changed: {key} = {value} (source: {source})")
    
    def update_state(self, updates: Dict[str, Any], source: str = None) -> None:
        """
        Update multiple state values at once.
        
        Args:
            updates: Dictionary of key-value pairs to update
            source: Source of the change
        """
        with self._lock:
            changes = []
            
            for key, value in updates.items():
                old_value = self._state.get(key)
                if old_value != value:
                    self._state[key] = deepcopy(value)
                    
                    change = StateChange(
                        key=key,
                        old_value=old_value,
                        new_value=deepcopy(value),
                        source=source
                    )
                    changes.append(change)
            
            # Add all changes to history
            for change in changes:
                self._add_to_history(change)
            
            # Notify subscribers for each change
            for change in changes:
                self._notify_subscribers(change)
            
            if changes:
                logger.debug(f"Batch state update: {len(changes)} changes (source: {source})")
    
    def subscribe_to_state(self, key: str, callback: Callable[[StateChange], None]) -> None:
        """
        Subscribe to state changes for a specific key.
        
        Args:
            key: State key to monitor
            callback: Function to call when state changes
        """
        with self._lock:
            if key not in self._subscribers:
                self._subscribers[key] = []
            self._subscribers[key].append(callback)
        
        logger.debug(f"Subscribed to state changes for key: {key}")
    
    def unsubscribe_from_state(self, key: str, callback: Callable[[StateChange], None]) -> None:
        """
        Unsubscribe from state changes for a specific key.
        
        Args:
            key: State key
            callback: Function to remove from subscribers
        """
        with self._lock:
            if key in self._subscribers:
                try:
                    self._subscribers[key].remove(callback)
                except ValueError:
                    logger.warning(f"Callback not found in subscribers for key: {key}")
        
        logger.debug(f"Unsubscribed from state changes for key: {key}")
    
    def get_full_state(self) -> Dict[str, Any]:
        """
        Get a deep copy of the entire state.
        
        Returns:
            Deep copy of all state
        """
        with self._lock:
            return deepcopy(self._state)
    
    def clear_state(self, keys: Optional[List[str]] = None) -> None:
        """
        Clear state values.
        
        Args:
            keys: List of keys to clear (None to clear all)
        """
        with self._lock:
            if keys is None:
                # Clear all state
                changes = []
                for key, value in self._state.items():
                    change = StateChange(
                        key=key,
                        old_value=value,
                        new_value=None,
                        source="clear_all"
                    )
                    changes.append(change)
                
                self._state.clear()
                
                for change in changes:
                    self._add_to_history(change)
                    self._notify_subscribers(change)
                
                logger.debug("All state cleared")
            else:
                # Clear specific keys
                changes = []
                for key in keys:
                    if key in self._state:
                        old_value = self._state.pop(key)
                        change = StateChange(
                            key=key,
                            old_value=old_value,
                            new_value=None,
                            source="clear_specific"
                        )
                        changes.append(change)
                
                for change in changes:
                    self._add_to_history(change)
                    self._notify_subscribers(change)
                
                if changes:
                    logger.debug(f"Cleared state keys: {[c.key for c in changes]}")
    
    def _notify_subscribers(self, change: StateChange) -> None:
        """Notify all subscribers of a state change."""
        if change.key in self._subscribers:
            for callback in self._subscribers[change.key]:
                try:
                    callback(change)
                except Exception as e:
                    logger.error(f"Error in state change callback for {change.key}: {e}")
    
    def _add_to_history(self, change: StateChange) -> None:
        """Add state change to history, maintaining size limit."""
        self._change_history.append(change)
        if len(self._change_history) > self._max_history:
            self._change_history.pop(0)
    
    def get_change_history(self, key: Optional[str] = None, limit: int = 100) -> List[StateChange]:
        """
        Get state change history.
        
        Args:
            key: Filter by state key (None for all)
            limit: Maximum number of changes to return
            
        Returns:
            List of recent state changes
        """
        with self._lock:
            changes = self._change_history
            if key:
                changes = [c for c in changes if c.key == key]
            
            return changes[-limit:] if limit > 0 else changes
    
    def clear_history(self) -> None:
        """Clear state change history."""
        with self._lock:
            self._change_history.clear()
            logger.debug("State change history cleared")


# Predefined state keys for chat functionality
class StateKeys:
    """Predefined state keys for the chat application."""
    
    # User state
    CURRENT_USER = "user.current"
    USER_LIST = "user.list"
    SELECTED_USER = "user.selected"
    
    # Chat context state
    CURRENT_CHAT_CONTEXT = "chat.context.current"
    CHAT_CONTEXTS = "chat.contexts"
    CHAT_HISTORIES = "chat.histories"
    
    # Message state
    MESSAGE_TYPE = "message.type"
    INPUT_TEXT = "message.input.text"
    
    # Connection state
    CONNECTION_STATUS = "connection.status"
    CONNECTION_ERROR = "connection.error"
    
    # UI state
    WINDOW_GEOMETRY = "ui.window.geometry"
    SPLITTER_SIZES = "ui.splitter.sizes"
    
    # File transfer state
    ACTIVE_TRANSFERS = "file.transfers.active"
    DOWNLOADED_FILES = "file.downloads.list"


# Global state manager instance
state_manager = StateManager()
