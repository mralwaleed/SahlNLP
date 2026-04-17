"""
Text normalization utilities for Arabic text.

Standardizes Arabic character variations to improve search and tokenization.
"""

from __future__ import annotations

from sahlnlp.utils.constants import (
    ALEF,
    ALEF_MAKSURA,
    ALEF_VARIANTS,
    HAA,
    TAA_MARBUTA,
    YAA,
)
from sahlnlp.utils.logger import logger


def normalize_hamza(text: str) -> str:
    """Normalize all Alef variations to a bare Alef (ا).

    Args:
        text: The input Arabic text.

    Returns:
        Text with all Alef variations unified to bare Alef.

    Examples:
        >>> normalize_hamza("أحمد إبراهيم آدم")
        'احمد ابراهيم ادم'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        return text.translate(str.maketrans({v: ALEF for v in ALEF_VARIANTS}))
    except Exception:
        logger.warning("Failed to normalize hamza, returning original text")
        return text


def normalize_taa(text: str, to_haa: bool = True) -> str:
    """Normalize Taa Marbuta (ة) to Haa (ه) or vice versa.

    Args:
        text: The input Arabic text.
        to_haa: If True, convert ة to ه. If False, convert ه to ة.

    Returns:
        Text with Taa/Haa normalized.

    Examples:
        >>> normalize_taa("مدرسة")
        'مدرسه'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        if to_haa:
            return text.replace(TAA_MARBUTA, HAA)
        return text.replace(HAA, TAA_MARBUTA)
    except Exception:
        logger.warning("Failed to normalize taa, returning original text")
        return text


def normalize_yaa(text: str) -> str:
    """Normalize Alef Maksura (ى) to Yaa (ي).

    Args:
        text: The input Arabic text.

    Returns:
        Text with Alef Maksura converted to Yaa.

    Examples:
        >>> normalize_yaa("موسى")
        'موسي'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        return text.replace(ALEF_MAKSURA, YAA)
    except Exception:
        logger.warning("Failed to normalize yaa, returning original text")
        return text


def normalize_search(text: str) -> str:
    """Apply aggressive normalization for search engine indexing.

    Args:
        text: The input Arabic text.

    Returns:
        Heavily normalized text suitable for search indexing.

    Examples:
        >>> normalize_search("أحمد مُعَلِّمٌ في المدرسة")
        'احمد معلم في المدرسه'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        from sahlnlp.core.cleaner import remove_tashkeel, remove_tatweel

        text = remove_tashkeel(text)
        text = remove_tatweel(text)
        text = normalize_hamza(text)
        text = normalize_taa(text, to_haa=True)
        text = normalize_yaa(text)
        return text
    except Exception:
        logger.warning("normalize_search failed, returning original text")
        return text
