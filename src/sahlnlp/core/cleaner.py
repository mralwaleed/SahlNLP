"""
Text cleaning utilities for Arabic text.

Removes diacritics, tatweel, HTML tags, URLs, and repeated characters.
"""

from __future__ import annotations

from sahlnlp.utils.constants import (
    RE_HTML_TAGS,
    RE_REPEATED_CHAR,
    RE_TASHKEEL,
    RE_TATWEEL,
    RE_URL,
)
from sahlnlp.utils.logger import logger


def remove_tashkeel(text: str) -> str:
    """Remove all Arabic diacritical marks (tashkeel) from text.

    Args:
        text: The input Arabic text.

    Returns:
        Text with all diacritics stripped.

    Examples:
        >>> remove_tashkeel("مَرْحَباً")
        'مرحبا'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        return RE_TASHKEEL.sub('', text)
    except Exception:
        logger.warning("Failed to remove tashkeel, returning original text")
        return text


def remove_tatweel(text: str) -> str:
    """Remove tatweel (kashida) characters from text.

    Args:
        text: The input Arabic text.

    Returns:
        Text with tatweel characters removed.

    Examples:
        >>> remove_tatweel("الســــلام")
        'السلام'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        return RE_TATWEEL.sub('', text)
    except Exception:
        logger.warning("Failed to remove tatweel, returning original text")
        return text


def remove_html_and_links(text: str) -> str:
    """Remove HTML tags and URLs from text.

    Args:
        text: The input text potentially containing HTML/URLs.

    Returns:
        Cleaned text with HTML tags and URLs removed.

    Examples:
        >>> remove_html_and_links("visit <b>http://example.com</b>")
        'visit '
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        text = RE_URL.sub('', text)
        text = RE_HTML_TAGS.sub('', text)
        return text
    except Exception:
        logger.warning("Failed to remove HTML/links, returning original text")
        return text


def remove_repeated_chars(text: str, max_repeat: int = 2) -> str:
    """Reduce character flooding to a maximum number of repetitions.

    Args:
        text: The input text.
        max_repeat: Maximum allowed consecutive repetitions (default 2).

    Returns:
        Text with character flooding reduced.

    Examples:
        >>> remove_repeated_chars("مرحباًاااا", max_repeat=2)
        'مرحباًا'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    if max_repeat < 1:
        raise ValueError("max_repeat must be >= 1")

    def _replace(match) -> str:
        char = match.group(1)
        return char * max_repeat

    try:
        return RE_REPEATED_CHAR.sub(_replace, text)
    except Exception:
        logger.warning("Failed to remove repeated chars, returning original text")
        return text


def clean_all(
    text: str,
    remove_tashkeel_flag: bool = True,
    remove_tatweel_flag: bool = True,
    remove_html_flag: bool = True,
    remove_repeated_flag: bool = True,
    max_repeat: int = 2,
) -> str:
    """Apply all cleaning operations to Arabic text.

    Args:
        text: The input Arabic text.
        remove_tashkeel_flag: Whether to remove diacritics (default True).
        remove_tatweel_flag: Whether to remove tatweel (default True).
        remove_html_flag: Whether to remove HTML/URLs (default True).
        remove_repeated_flag: Whether to reduce character flooding (default True).
        max_repeat: Max consecutive repetitions allowed (default 2).

    Returns:
        Fully cleaned text.

    Examples:
        >>> clean_all("مَرْحَباً يا صديقي")
        'مرحبا يا صديقي'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    try:
        if remove_tashkeel_flag:
            text = remove_tashkeel(text)
        if remove_tatweel_flag:
            text = remove_tatweel(text)
        if remove_html_flag:
            text = remove_html_and_links(text)
        if remove_repeated_flag:
            text = remove_repeated_chars(text, max_repeat=max_repeat)
        return text
    except Exception:
        logger.warning("clean_all failed, returning original text")
        return text
