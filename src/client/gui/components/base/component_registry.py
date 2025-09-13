"""
Component registration and management system.
"""

from typing import Dict, List, Optional, Type, Any
import logging
from PySide6.QtWidgets import QWidget

from ...core.event_bus import EventBus
from ...core.state_manager import StateManager
from .base_component import BaseComponent

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """Registry for managing GUI components."""
    
    def __init__(self, event_bus: EventBus, state_manager: StateManager):
        """
        Initialize component registry.
        
        Args:
            event_bus: Event bus instance
            state_manager: State manager instance
        """
        self.event_bus = event_bus
        self.state_manager = state_manager
        self._components: Dict[str, BaseComponent] = {}
        self._component_types: Dict[str, Type[BaseComponent]] = {}
        self._component_dependencies: Dict[str, List[str]] = {}
        
    def register_component_type(self, component_type: str, component_class: Type[BaseComponent]) -> None:
        """
        Register a component type.
        
        Args:
            component_type: Type identifier
            component_class: Component class
        """
        if not issubclass(component_class, BaseComponent):
            raise ValueError(f"Component class must inherit from BaseComponent")
        
        self._component_types[component_type] = component_class
        logger.debug(f"Registered component type: {component_type}")
    
    def create_component(self, component_id: str, component_type: str, 
                        parent: QWidget = None, **kwargs) -> BaseComponent:
        """
        Create a new component instance.
        
        Args:
            component_id: Unique identifier for the component
            component_type: Type of component to create
            parent: Parent widget
            **kwargs: Additional arguments for component constructor
            
        Returns:
            Created component instance
        """
        if component_id in self._components:
            raise ValueError(f"Component with ID '{component_id}' already exists")
        
        if component_type not in self._component_types:
            raise ValueError(f"Unknown component type: {component_type}")
        
        try:
            component_class = self._component_types[component_type]
            component = component_class(
                component_id=component_id,
                event_bus=self.event_bus,
                state_manager=self.state_manager,
                parent=parent,
                **kwargs
            )
            
            self._components[component_id] = component
            logger.info(f"Created component: {component_id} (type: {component_type})")
            
            return component
            
        except Exception as e:
            logger.error(f"Failed to create component {component_id}: {e}")
            raise
    
    def get_component(self, component_id: str) -> Optional[BaseComponent]:
        """
        Get a component by ID.
        
        Args:
            component_id: Component identifier
            
        Returns:
            Component instance or None if not found
        """
        return self._components.get(component_id)
    
    def remove_component(self, component_id: str) -> bool:
        """
        Remove a component.
        
        Args:
            component_id: Component identifier
            
        Returns:
            True if component was removed, False if not found
        """
        if component_id not in self._components:
            return False
        
        try:
            component = self._components[component_id]
            
            # Clean up component
            if component.is_initialized():
                component.cleanup()
            
            # Remove from registry
            del self._components[component_id]
            
            logger.info(f"Removed component: {component_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing component {component_id}: {e}")
            return False
    
    def initialize_component(self, component_id: str) -> bool:
        """
        Initialize a component.
        
        Args:
            component_id: Component identifier
            
        Returns:
            True if successful, False otherwise
        """
        component = self.get_component(component_id)
        if not component:
            logger.error(f"Component not found: {component_id}")
            return False
        
        try:
            component.initialize()
            return True
        except Exception as e:
            logger.error(f"Failed to initialize component {component_id}: {e}")
            return False
    
    def initialize_all_components(self) -> Dict[str, bool]:
        """
        Initialize all registered components.
        
        Returns:
            Dictionary mapping component IDs to initialization success
        """
        results = {}
        
        for component_id in self._components:
            results[component_id] = self.initialize_component(component_id)
        
        return results
    
    def cleanup_all_components(self) -> None:
        """Clean up all components."""
        for component_id in list(self._components.keys()):
            self.remove_component(component_id)
    
    def get_component_list(self) -> List[str]:
        """
        Get list of all component IDs.
        
        Returns:
            List of component identifiers
        """
        return list(self._components.keys())
    
    def get_component_info(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a component.
        
        Args:
            component_id: Component identifier
            
        Returns:
            Component information dictionary or None if not found
        """
        component = self.get_component(component_id)
        if not component:
            return None
        
        return component.get_component_info()
    
    def get_all_component_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all components.
        
        Returns:
            Dictionary mapping component IDs to their information
        """
        return {
            component_id: self.get_component_info(component_id)
            for component_id in self._components
        }
    
    def set_component_dependencies(self, component_id: str, dependencies: List[str]) -> None:
        """
        Set dependencies for a component.
        
        Args:
            component_id: Component identifier
            dependencies: List of component IDs this component depends on
        """
        self._component_dependencies[component_id] = dependencies.copy()
        logger.debug(f"Set dependencies for {component_id}: {dependencies}")
    
    def get_component_dependencies(self, component_id: str) -> List[str]:
        """
        Get dependencies for a component.
        
        Args:
            component_id: Component identifier
            
        Returns:
            List of dependency component IDs
        """
        return self._component_dependencies.get(component_id, [])
    
    def get_initialization_order(self) -> List[str]:
        """
        Get the order in which components should be initialized based on dependencies.
        
        Returns:
            List of component IDs in initialization order
        """
        # Simple topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(component_id: str):
            if component_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving {component_id}")
            if component_id in visited:
                return
            
            temp_visited.add(component_id)
            
            # Visit dependencies first
            for dep in self.get_component_dependencies(component_id):
                if dep in self._components:  # Only visit if dependency exists
                    visit(dep)
            
            temp_visited.remove(component_id)
            visited.add(component_id)
            result.append(component_id)
        
        # Visit all components
        for component_id in self._components:
            if component_id not in visited:
                visit(component_id)
        
        return result
    
    def initialize_components_in_order(self) -> Dict[str, bool]:
        """
        Initialize components in dependency order.
        
        Returns:
            Dictionary mapping component IDs to initialization success
        """
        order = self.get_initialization_order()
        results = {}
        
        for component_id in order:
            results[component_id] = self.initialize_component(component_id)
        
        return results


# Global component registry instance
component_registry = None


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry instance."""
    global component_registry
    if component_registry is None:
        from ...core.event_bus import event_bus
        from ...core.state_manager import state_manager
        component_registry = ComponentRegistry(event_bus, state_manager)
    return component_registry
