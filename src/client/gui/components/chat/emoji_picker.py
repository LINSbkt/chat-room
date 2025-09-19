# ui/components/chat/emoji_picker.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Signal

# Define a small emoji map (can expand later or import from a shared file)
emoji_map = {
    ":smile:": "😄",
    ":heart:": "❤️",
    ":thumbsup:": "👍",
    ":fire:": "🔥",
    ":star:": "⭐",
    ":cry:": "😢",
    ":laugh:": "😂",
}


class EmojiPicker(QDialog):
    """Simple emoji picker dialog."""
    emoji_selected = Signal(str)  # emits the chosen emoji (character)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Emoji Picker")
        self.resize(250, 300)

        layout = QVBoxLayout(self)

        # List of emojis
        self.emoji_list = QListWidget()
        for code, emoji in emoji_map.items():
            item = QListWidgetItem(f"{emoji}  {code}")
            self.emoji_list.addItem(item)

        layout.addWidget(self.emoji_list)

        # Connect selection
        self.emoji_list.itemClicked.connect(self._handle_item_clicked)

    def _handle_item_clicked(self, item):
        emoji = item.text().split()[0]  # get the first part (emoji char)
        self.emoji_selected.emit(emoji)
        self.close()
