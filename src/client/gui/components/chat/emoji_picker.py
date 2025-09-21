# ui/components/chat/emoji_picker.py

from PySide6.QtWidgets import (
    QDialog,
    QListWidgetItem,
    QVBoxLayout,
    QListWidget,
    QTabWidget,
    QWidget,
    QLineEdit,
    QGridLayout,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
)
from PySide6.QtCore import Signal, Qt
import json
import os


class EmojiPicker(QDialog):
    """Simple emoji picker dialog."""

    emoji_selected = Signal(str)  # emits the chosen emoji (character)

    def __init__(self, parent=None,
                 username: str = "guest",
                 max_recent_emojis=10):
        super().__init__(parent)
        self.max_recent_emojis = max_recent_emojis
        self.username = username
        self.setWindowTitle("Emoji Picker")
        self.resize(250, 300)
        # Load emoji data
        # All emojis
        self.emoji_map = self.load_emoji_json()
        # Recent used emojis
        self.recent_emojis = self.load_user_recent_emojis_json()
        # Code to emoji mapping for replacement
        self.code_to_emoji = {
            f":{name}:": e
            for category in self.emoji_map.values()
            for name, e in category.items()
        }
        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Recent tab
        self.recent_tab = QWidget()
        self.recent_grid = QGridLayout(self.recent_tab)
        # self.recent_grid.setSpacing(0)
        # self.recent_grid.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.recent_tab, "Recent")

        # All emojis tab
        self.all_tab = QWidget()
        self.all_layout = QVBoxLayout(self.all_tab)
        # Search bar
        self.search_bar = QLineEdit()
        self.all_layout.addWidget(self.search_bar)
        # All Emoji list
        self.emoji_list = QListWidget()
        self.all_layout.addWidget(self.emoji_list)
        self.tabs.addTab(self.all_tab, "All Emojis")
        # Category tabs
        self.category_tabs = {}
        for category, emojis in self.emoji_map.items():
            tab, grid = self._create_grid_tab()
            self.tabs.addTab(tab, category.capitalize())
            self.category_tabs[category] = (tab, grid, emojis)
            self._populate_grid(grid, emojis)

        # Populate emojis
        self.populate_all_list()
        self.update_recent_list()

        # Connect signals
        self.search_bar.textChanged.connect(self.filter_all_list)
        self.emoji_list.itemClicked.connect(self._handle_item_clicked)

    # -----UI utilities-----------
    def _create_grid_tab(self):
        tab = QWidget()
        grid = QGridLayout(tab)
        grid.setSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)
        return tab, grid

    # ----------- Data Handling -----------
    @staticmethod
    def load_emoji_json():
        path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "emoji_dict.json"
        )
        path = os.path.abspath(path)  # normalize to absolute path
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def recent_emojis_json_path(self) -> str:
        """Shared JSON for all users (nested dict by username)."""
        base_dir = os.path.join(os.path.dirname(__file__), "../assets")
        os.makedirs(base_dir, exist_ok=True)  # Ensure folder exists
        return os.path.join(base_dir, "users_recent_emojis.json")

    def load_user_recent_emojis_json(self) -> list:
        path = self.recent_emojis_json_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except (json.JSONDecodeError, IOError):
            data = {}
        return data.get(self.username, [])

    def save_recent_json(self) -> None:
        path = self.recent_emojis_json_path()
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {}
        except (json.JSONDecodeError, IOError):
            data = {}

        data[self.username] = self.recent_emojis

        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)  # atomic replace

    # ----------- UI Population -----------
    def populate_all_list(self, filter_text=""):
        self.emoji_list.clear()
        for category, item in self.emoji_map.items():
            for name, emoji in item.items():
                code = f":{name}:"
                if filter_text.lower() in code.lower():
                    list_item = QListWidgetItem(f"{emoji}  {code}")
                    self.emoji_list.addItem(list_item)

    def _populate_grid(self, grid, emojis):
        cols = 6
        emojis = dict(sorted(emojis.items()))  # sort by name
        for idx, (name, emoji) in enumerate(emojis.items()):
            row = idx // cols
            col = idx % cols
            btn = QPushButton(emoji)
            btn.setToolTip(name)
            btn.setFixedSize(36, 36)
            btn.setFlat(True)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            btn.clicked.connect(lambda checked,
                                e=emoji: self._handle_item_clicked(e))
            grid.addWidget(btn, row, col, Qt.AlignTop | Qt.AlignLeft)

    def filter_all_list(self, text):
        self.populate_all_list(filter_text=text)

    def _clear_layout(self, layout):
        # utility to clean layouts/widgets recursively
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def update_recent_list(self):
        # Clear existing buttons
        self._clear_layout(self.recent_grid)

        cols = 6  # number of columns
        self._populate_grid(
            self.recent_grid,
            {f"recent_{i}": e for i, e in enumerate(self.recent_emojis)},
        )
        # force left align for incomplete rows
        row = len(self.recent_emojis) // cols
        self.recent_grid.addItem(
            QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum),
            row, cols
        )
        self.recent_tab.adjustSize()

    # ----------- Handlers -----------

    def _handle_item_clicked(self, item):
        if isinstance(item, QListWidgetItem):
            emoji = item.text().split()[0]  # get the first part (emoji char)
        else:
            emoji = item  # direct emoji from button
        self.emoji_selected.emit(emoji)
        self._update_recent(emoji)
        self.update_recent_list()
        self.save_recent_json()
        # self.close()

    def _update_recent(self, emoji):
        if emoji in self.recent_emojis:
            self.recent_emojis.remove(emoji)
        self.recent_emojis.insert(0, emoji)
        # keep only last 10
        self.recent_emojis = self.recent_emojis[: self.max_recent_emojis]

