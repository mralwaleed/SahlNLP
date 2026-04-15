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


def normalize_hamza(text: str) -> str:
    """Normalize all Alef variations to a bare Alef (ا).

    Converts أ (Alef with hamza above), إ (Alef with hamza below),
    and آ (Alef with madda) to plain ا (Alef).

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
    return text.translate(str.maketrans({v: ALEF for v in ALEF_VARIANTS}))


def normalize_taa(text: str, to_haa: bool = True) -> str:
    """Normalize Taa Marbuta (ة) to Haa (ه) or vice versa.

    Args:
        text: The input Arabic text.
        to_haa: If True, convert ة to ه. If False, convert ه to ة.
            Defaults to True.

    Returns:
        Text with Taa/Haa normalized.

    Examples:
        >>> normalize_taa("مدرسة")
        'مدرسه'
        >>> normalize_taa("مدرسه", to_haa=False)
        'مدرسة'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    if to_haa:
        return text.replace(TAA_MARBUTA, HAA)
    return text.replace(HAA, TAA_MARBUTA)


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
    return text.replace(ALEF_MAKSURA, YAA)


def normalize_search(text: str) -> str:
    """Apply aggressive normalization for search engine indexing.

    Combines hamza normalization, taa normalization (to haa),
    yaa normalization, diacritics removal, and tatweel removal.

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
    from sahlnlp.core.cleaner import remove_tashkeel, remove_tatweel

    text = remove_tashkeel(text)
    text = remove_tatweel(text)
    text = normalize_hamza(text)
    text = normalize_taa(text, to_haa=True)
    text = normalize_yaa(text)
    return text
