"""
Message type definitions for the chatroom application.
Legacy compatibility module - imports from organized message modules.
"""

# Import everything from the new organized modules for backward compatibility
from .messages import *

# This file now serves as a compatibility layer
# All new code should import from src.shared.messages directly