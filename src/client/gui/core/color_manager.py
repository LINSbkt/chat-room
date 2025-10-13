"""
Centralized color management for the chat application.
"""

from typing import Dict, Optional
from PySide6.QtGui import QColor
import logging

logger = logging.getLogger(__name__)


class ColorManager:
    """Manages colors for users and system messages with theme awareness."""

    def __init__(self):
        # Initialize color palettes
        self._setup_color_palettes()

        # User color mapping
        self.user_colors: Dict[str, QColor] = {}
        self.next_color_idx = 0

        # Detect current theme (assume dark theme for now)
        self.is_dark_theme = True

        logger.info("ColorManager initialized")

    def _setup_color_palettes(self):
        """Set up color palettes for light and dark themes."""
        # Light theme colors (more saturated)
        self.light_user_palette = [
            QColor(220, 50, 50),    # Red
            QColor(50, 220, 50),   # Green
            QColor(50, 50, 220),   # Blue
            QColor(220, 150, 50),  # Orange
            QColor(150, 50, 220),  # Purple
            QColor(50, 220, 220),  # Cyan
            QColor(220, 50, 150),  # Pink
            QColor(150, 220, 50),  # Lime
            QColor(220, 150, 150),  # Light red
            QColor(150, 220, 150),  # Light green
        ]

        # Dark theme colors (less saturated, more visible)
        self.dark_user_palette = [
            QColor(120, 120, 255),  # Light blue
            QColor(255, 200, 120),  # Light orange
            QColor(200, 120, 255),  # Light purple
            QColor(120, 255, 255),  # Light cyan
            QColor(255, 120, 200),  # Light pink
            QColor(200, 255, 120),  # Light lime
        ]

        # System colors for light theme
        self.light_system_colors = {
            "join": QColor(0, 150, 0),        # Green for joins
            "leave": QColor(200, 0, 0),      # Red for leaves
            "system": QColor(100, 100, 100),  # Gray for system messages
            "sent": QColor(80, 80, 80),       # Dark gray for your messages
        }

        # System colors for dark theme
        self.dark_system_colors = {
            "join": QColor(0, 255, 0),        # Bright green for joins
            "leave": QColor(255, 100, 100),   # Light red for leaves
            "system": QColor(180, 180, 180),  # Light gray for system messages
            "sent": QColor(200, 200, 200),    # Light gray for your messages
        }

        # Set current palette based on theme
        self.current_user_palette = self.dark_user_palette
        self.current_system_colors = self.dark_system_colors

    def get_user_color(self, username: str, current_user: str) -> QColor:
        """Get color for a specific user."""
        if username == current_user:
            return self.current_system_colors["sent"]

        if username not in self.user_colors:
            self._assign_user_color(username)

        return self.user_colors[username]

    def get_system_color(self, message_content: str) -> QColor:
        """Get color for system messages based on content."""
        if "joined the chat" in message_content:
            return self.current_system_colors["join"]
        elif "left the chat" in message_content:
            return self.current_system_colors["leave"]
        else:
            return self.current_system_colors["system"]

    def get_message_color(self, message: Dict, current_user: str) -> QColor:
        """Get appropriate color for any message."""
        message_type = message.get("message_type", "public")
        content = message.get("content", "")
        sender = message.get("sender", "")

        # System messages
        if message_type == "system" or "joined the chat" in content or "left the chat" in content:
            return self.get_system_color(content)

        # User messages
        return self.get_user_color(sender, current_user)

    def adapt_to_theme(self, is_dark: bool):
        """Adapt colors to the current theme."""
        self.is_dark_theme = is_dark

        if is_dark:
            self.current_user_palette = self.dark_user_palette
            self.current_system_colors = self.dark_system_colors
        else:
            self.current_user_palette = self.light_user_palette
            self.current_system_colors = self.light_system_colors

        # Reassign colors to maintain consistency
        self._reassign_user_colors()

        logger.info(
            f"Colors adapted to {'dark' if is_dark else 'light'} theme")

    def _assign_user_color(self, username: str) -> QColor:
        """Assign a color to a new user."""
        color = self.current_user_palette[self.next_color_idx % len(
            self.current_user_palette)]
        self.user_colors[username] = color
        self.next_color_idx += 1

        logger.debug(f"Assigned color {color.name()} to user {username}")
        return color

    def _reassign_user_colors(self):
        """Reassign colors to all users with current theme palette."""
        usernames = list(self.user_colors.keys())
        self.user_colors.clear()
        self.next_color_idx = 0

        for username in usernames:
            self._assign_user_color(username)

        logger.info(f"Reassigned colors for {len(usernames)} users")

    def get_color_info(self) -> Dict:
        """Get information about current color assignments."""
        return {
            "theme": "dark" if self.is_dark_theme else "light",
            "user_colors": {user: color.name() for user, color in self.user_colors.items()},
            "system_colors": {key: color.name() for key, color in self.current_system_colors.items()},
            "palette_size": len(self.current_user_palette)
        }
