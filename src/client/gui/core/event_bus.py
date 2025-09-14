"""
Event bus system for loose coupling between GUI components.
"""

import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Base event class for all GUI events."""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = None
    source: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class EventBus:
    """Centralized event system for component communication."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._async_subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000  # Limit event history size
        
    def subscribe(self, event_type: str, handler: Callable, async_handler: bool = False) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: Function to call when event is published
            async_handler: Whether the handler is async
        """
        if async_handler:
            if event_type not in self._async_subscribers:
                self._async_subscribers[event_type] = []
            self._async_subscribers[event_type].append(handler)
        else:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
        
        logger.debug(f"Subscribed {handler.__name__} to {event_type} events")
    
    def unsubscribe(self, event_type: str, handler: Callable, async_handler: bool = False) -> None:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: Function to remove from subscribers
            async_handler: Whether the handler is async
        """
        if async_handler:
            if event_type in self._async_subscribers:
                try:
                    self._async_subscribers[event_type].remove(handler)
                except ValueError:
                    logger.warning(f"Handler {handler.__name__} not found in async subscribers for {event_type}")
        else:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(handler)
                except ValueError:
                    logger.warning(f"Handler {handler.__name__} not found in subscribers for {event_type}")
        
        logger.debug(f"Unsubscribed {handler.__name__} from {event_type} events")
    
    def publish(self, event: Event) -> None:
        """
        Publish an event synchronously.
        
        Args:
            event: The event to publish
        """
        self._add_to_history(event)
        
        # Call synchronous handlers
        if event.event_type in self._subscribers:
            for handler in self._subscribers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__} for {event.event_type}: {e}")
        
        logger.debug(f"Published event {event.event_type} from {event.source}")
    
    def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: The event to publish
        """
        self._add_to_history(event)
        
        # Call async handlers
        if event.event_type in self._async_subscribers:
            for handler in self._async_subscribers[event.event_type]:
                try:
                    # Create task for async handler
                    asyncio.create_task(self._call_async_handler(handler, event))
                except Exception as e:
                    logger.error(f"Error creating async task for {handler.__name__} in {event.event_type}: {e}")
        
        logger.debug(f"Published async event {event.event_type} from {event.source}")
    
    async def _call_async_handler(self, handler: Callable, event: Event) -> None:
        """Call an async handler safely."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in async event handler {handler.__name__} for {event.event_type}: {e}")
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history, maintaining size limit."""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """
        Get event history, optionally filtered by type.
        
        Args:
            event_type: Filter by event type (None for all)
            limit: Maximum number of events to return
            
        Returns:
            List of recent events
        """
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:] if limit > 0 else events
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.debug("Event history cleared")
    
    def get_subscriber_count(self, event_type: str) -> int:
        """Get the number of subscribers for an event type."""
        sync_count = len(self._subscribers.get(event_type, []))
        async_count = len(self._async_subscribers.get(event_type, []))
        return sync_count + async_count


# Predefined event types for chat functionality
class ChatEvents:
    """Predefined chat-related event types."""
    
    # Chat context events
    CONTEXT_CREATED = "chat.context.created"
    CONTEXT_SWITCHED = "chat.context.switched"
    CONTEXT_DELETED = "chat.context.deleted"
    
    # Message events
    MESSAGE_RECEIVED = "chat.message.received"
    MESSAGE_SENT = "chat.message.sent"
    MESSAGE_TYPE_CHANGED = "chat.message.type.changed"
    
    # User events
    USER_SELECTED = "chat.user.selected"
    USER_LIST_UPDATED = "chat.user.list.updated"
    COMMON_CHAT_SELECTED = "chat.common.selected"
    
    # File transfer events
    FILE_TRANSFER_REQUESTED = "chat.file.transfer.requested"
    FILE_TRANSFER_PROGRESS = "chat.file.transfer.progress"
    FILE_TRANSFER_COMPLETE = "chat.file.transfer.complete"
    
    # System events
    CONNECTION_STATUS_CHANGED = "system.connection.changed"
    ERROR_OCCURRED = "system.error.occurred"
    SYSTEM_MESSAGE = "system.message"


# Global event bus instance
event_bus = EventBus()
