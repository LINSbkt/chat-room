# tests/test_client/gui/components/chat/test_emoji_picker.py

import os
import unittest
import tempfile
from PySide6.QtWidgets import QApplication, QListWidgetItem

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "src"))

from client.gui.components.chat.emoji_picker import EmojiPicker


class TestEmojiPicker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Create a temporary file for recent emojis
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        tmp_file.close()  # Close it so EmojiPicker can open it
        self.temp_recent_path = tmp_file.name

        # Create EmojiPicker using temp recent file
        self.picker = EmojiPicker(username="testuser", recent_file_path=self.temp_recent_path)

    def tearDown(self):
        if os.path.exists(self.temp_recent_path):
            os.remove(self.temp_recent_path)

    def test_emoji_map_loaded(self):
        self.assertIsInstance(self.picker.emoji_map, dict)

    def test_recent_emojis_initialized(self):
        self.assertIsInstance(self.picker.recent_emojis, list)
        self.assertEqual(self.picker.recent_emojis, [])

    def test_populate_all_list_adds_items(self):
        self.picker.emoji_map = {"smileys": {"smile": "😄", "wink": "😉"}}
        self.picker.populate_all_list()
        self.assertEqual(self.picker.emoji_list.count(), 2)
        self.assertIn("😄", self.picker.emoji_list.item(0).text())

    def test_filter_all_list_filters_items(self):
        self.picker.emoji_map = {"smileys": {"smile": "😄", "wink": "😉"}}
        self.picker.populate_all_list(filter_text="wink")
        self.assertEqual(self.picker.emoji_list.count(), 1)
        self.assertIn("😉", self.picker.emoji_list.item(0).text())

    def test_emoji_selected_signal_emitted(self):
        received = []

        def handler(emoji):
            received.append(emoji)

        self.picker.emoji_selected.connect(handler)
        self.picker._handle_item_clicked("😄")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], "😄")

    def test_update_recent_adds_to_recent_list(self):
        self.picker._handle_item_clicked("😄")
        self.assertIn("😄", self.picker.recent_emojis)
        self.picker._handle_item_clicked("😉")
        self.assertEqual(self.picker.recent_emojis[0], "😉")
        self.assertEqual(self.picker.recent_emojis[1], "😄")

    def test_recent_emojis_limited_to_max(self):
        self.picker.max_recent_emojis = 3
        emojis = ["😀", "😄", "😉", "😊"]
        for e in emojis:
            self.picker._handle_item_clicked(e)
        self.assertEqual(len(self.picker.recent_emojis), 3)
        self.assertEqual(self.picker.recent_emojis, ["😊", "😉", "😄"])


if __name__ == "__main__":
    unittest.main()
'''
$env:PYTHONPATH = "src"
python -m unittest tests.test_client.gui.components.chat.test_emoji_picker
'''
