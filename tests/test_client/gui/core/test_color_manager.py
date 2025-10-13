# tests/test_client/gui/core/test_color_manager.py
"""
Unit tests for ColorManager using unittest.
"""

import unittest
import sys
import os
from PySide6.QtGui import QColor

# Adjust import path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from src.client.gui.core.color_manager import ColorManager


class TestColorManager(unittest.TestCase):
    """Unit tests for ColorManager functionality."""

    @classmethod
    def setUpClass(cls):
        """Create a single ColorManager instance for all tests."""
        cls.color_manager = ColorManager()

    def test_user_color_assignment(self):
        """Test user colors are assigned correctly and consistently."""
        users = ["Alice", "Bob", "Charlie", "David", "Eve"]
        current_user = "Alice"

        colors = {}
        for user in users:
            color = self.color_manager.get_user_color(user, current_user)
            self.assertIsInstance(color, QColor)
            colors[user] = color.name()

        # Check consistency
        for user in users:
            self.assertEqual(
                self.color_manager.get_user_color(user, current_user).name(),
                colors[user]
            )

    def test_system_message_colors(self):
        """Test system message colors are valid QColor objects."""
        messages = [
            "User Alice joined the chat",
            "User Bob left the chat",
            "Welcome to the chatroom!",
            "Server is restarting..."
        ]
        for msg in messages:
            color = self.color_manager.get_system_color(msg)
            self.assertIsInstance(color, QColor)
            self.assertTrue(color.isValid())

    def test_message_color_determination(self):
        """Test color assignment for different message types."""
        current_user = "Alice"
        test_messages = [
            {"message_type": "public", "content": "Hello everyone!", "sender": "Bob"},
            {"message_type": "private", "content": "Hi Alice!", "sender": "Charlie", "recipient": "Alice"},
            {"message_type": "system", "content": "User David joined the chat", "sender": "system"},
        ]

        for msg in test_messages:
            color = self.color_manager.get_message_color(msg, current_user)
            self.assertIsInstance(color, QColor)
            self.assertTrue(color.isValid())

    def test_color_info(self):
        """Test color manager info dictionary contents."""
        info = self.color_manager.get_color_info()
        self.assertIn("theme", info)
        self.assertIn("palette_size", info)
        self.assertIn("user_colors", info)
        self.assertIn("system_colors", info)


if __name__ == "__main__":
    unittest.main()
'''
$env:PYTHONPATH = "src"
python -m unittest tests.test_client.gui.core.test_color_manager
'''