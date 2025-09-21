# utils/fonts.py
import emoji
import re


def replace_text_codes_with_emojis(content: str, code_to_emoji: dict = None) -> str:
    """
    Convert text codes to emojis.
    - First, use the `emoji` library for standard aliases
    - Then use a custom map if provided
    """
    # Standard conversion
    content = emoji.emojize(content, language="alias")

    # Custom mapping
    if code_to_emoji:
        pattern = re.compile(r":([a-z0-9_]+):")
        content = pattern.sub(lambda m: code_to_emoji.get(f":{m.group(1)}:", m.group(0)), content)

    return content
