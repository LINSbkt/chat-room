"""
Tests for EmojiPicker dialog.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# Add src to path for imports (adjust path if needed)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from PySide6.QtWidgets import QApplication
from client.gui.components.chat.emoji_picker import EmojiPicker, emoji_map


class TestEmojiPicker(unittest.TestCase):
    """Test EmojiPicker functionality."""

    @classmethod
    def setUpClass(cls):
        """Ensure QApplication exists once for all tests."""
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        """Set up a new EmojiPicker for each test."""
        self.picker = EmojiPicker()

    def test_emoji_list_populated(self):
        """Test that all emojis from emoji_map are loaded in the list."""
        count_in_list = self.picker.emoji_list.count()
        count_in_map = len(emoji_map)
        self.assertEqual(count_in_list, count_in_map)

        # Verify the first item looks correct
        first_item_text = self.picker.emoji_list.item(0).text()
        first_emoji, first_code = list(emoji_map.items())[0]
        self.assertIn(first_code, first_item_text)
        self.assertIn(first_emoji, first_item_text)

    def test_emoji_selected_signal(self):
        """Test that selecting an emoji emits the correct signal."""
        received = []

        def on_selected(emoji):
            received.append(emoji)

        self.picker.emoji_selected.connect(on_selected)

        # Simulate clicking the first item
        first_item = self.picker.emoji_list.item(0)
        self.picker._handle_item_clicked(first_item)

        # Assert signal was emitted with correct emoji
        self.assertEqual(len(received), 1)
        expected_emoji = list(emoji_map.values())[0]
        self.assertEqual(received[0], expected_emoji)


if __name__ == "__main__":
    unittest.main()
