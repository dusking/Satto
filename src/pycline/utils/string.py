"""String utility functions for processing text from AI model outputs."""

def fix_model_html_escaping(text: str) -> str:
    """
    Fixes incorrectly escaped HTML entities in AI model outputs.

    Args:
        text: String potentially containing incorrectly escaped HTML entities from AI models

    Returns:
        String with HTML entities converted back to normal characters
    """
    replacements = {
        "&gt;": ">",
        "&lt;": "<",
        "&quot;": '"',
        "&amp;": "&",
        "&apos;": "'"
    }
    for entity, char in replacements.items():
        text = text.replace(entity, char)
    return text

def remove_invalid_chars(text: str) -> str:
    """
    Removes invalid characters (like the replacement character �) from a string.

    Args:
        text: String potentially containing invalid characters

    Returns:
        String with invalid characters removed
    """
    return text.replace("\uFFFD", "")
