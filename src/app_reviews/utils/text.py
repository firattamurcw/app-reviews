"""Text processing utilities."""


def clean_text(text: str) -> str:
    """Strip whitespace and normalize line endings.

    Args:
        text: Raw string to clean.

    Returns:
        Cleaned string with consistent newlines and no surrounding whitespace.
    """
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()
