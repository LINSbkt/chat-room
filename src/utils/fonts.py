# utils/fonts.py
import sys
from PySide6.QtGui import QFont, QFontDatabase


def get_emoji_font(size=11):
    db = QFontDatabase()
    families = set(db.families())

    if sys.platform.startswith("win"):
        candidates = ["Segoe UI Emoji", "Segoe UI Symbol", "Segoe UI"]
    elif sys.platform == "darwin":
        candidates = ["Apple Color Emoji", "Helvetica Neue"]
    else:
        candidates = ["Noto Color Emoji", "EmojiOne Color", "DejaVu Sans"]

    for fam in candidates:
        if fam in families:
            return QFont(fam, size)

    return QFont("Sans Serif", size)  # fallback
