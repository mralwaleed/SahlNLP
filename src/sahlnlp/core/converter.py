"""
Number conversion utilities for Arabic text.

Handles Hindi/Arabic numeral conversion and number-to-words
with full Arabic grammar support: case (إعراب), dual forms, and currency.
"""

from __future__ import annotations

from sahlnlp.utils.logger import logger
from sahlnlp.utils.constants import (
    ARABIC_HUNDREDS_ACCUSATIVE,
    ARABIC_HUNDREDS_NOMINATIVE,
    ARABIC_ONES,
    ARABIC_SCALE_ACCUSATIVE,
    ARABIC_SCALE_GENITIVE,
    ARABIC_SCALE_NOMINATIVE,
    ARABIC_TENS_ACCUSATIVE,
    ARABIC_TENS_NOMINATIVE,
    ARABIC_TO_INDIC_MAP,
    INDIC_TO_ARABIC_MAP,
    RE_ARABIC_DIGITS,
    RE_INDIC_DIGITS,
)

_VALID_CASES = frozenset({'nominative', 'accusative', 'genitive'})


# ---------------------------------------------------------------------------
# Case-aware lookup helpers
# ---------------------------------------------------------------------------

def _inflect_ones(n: int, case: str) -> str:
    """Return the word for number *n* (0-19) inflected for grammatical case.

    Only 2 and 12 change with case:
      - 2: اثنان (nom) / اثنين (acc, gen)
      - 12: اثنا عشر (nom) / اثني عشر (acc, gen)
    All other ones (including 11: أحد عشر) are invariable.
    """
    if case != 'nominative':
        if n == 2:
            return 'اثنين'
        if n == 12:
            return 'اثني عشر'
    return ARABIC_ONES[n]


def _get_tens(case: str) -> dict:
    if case == 'nominative':
        return ARABIC_TENS_NOMINATIVE
    return ARABIC_TENS_ACCUSATIVE


def _get_hundreds(case: str) -> dict:
    if case == 'nominative':
        return ARABIC_HUNDREDS_NOMINATIVE
    return ARABIC_HUNDREDS_ACCUSATIVE


def _get_scale(case: str) -> dict:
    if case == 'nominative':
        return ARABIC_SCALE_NOMINATIVE
    if case == 'genitive':
        return ARABIC_SCALE_GENITIVE
    return ARABIC_SCALE_ACCUSATIVE


# ---------------------------------------------------------------------------
# Digit conversion (Indic ↔ Arabic)
# ---------------------------------------------------------------------------

def indic_to_arabic(text: str) -> str:
    """Convert Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) to standard Arabic numerals (0-9).

    Args:
        text: The input text containing Hindi/Indic digits.

    Returns:
        Text with Indic digits replaced by standard numerals.

    Examples:
        >>> indic_to_arabic("٣ أبريل ٢٠٢٥")
        '3 أبريل 2025'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        return RE_INDIC_DIGITS.sub(lambda m: INDIC_TO_ARABIC_MAP[m.group()], text)
    except Exception:
        logger.warning("indic_to_arabic failed, returning original text")
        return text


def arabic_to_indic(text: str) -> str:
    """Convert standard Arabic numerals (0-9) to Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩).

    Args:
        text: The input text containing standard numerals.

    Returns:
        Text with standard numerals replaced by Indic digits.

    Examples:
        >>> arabic_to_indic("3 أبريل 2025")
        '٣ أبريل ٢٠٢٥'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    try:
        return RE_ARABIC_DIGITS.sub(lambda m: ARABIC_TO_INDIC_MAP[m.group()], text)
    except Exception:
        logger.warning("arabic_to_indic failed, returning original text")
        return text


# ---------------------------------------------------------------------------
# Core number-to-words
# ---------------------------------------------------------------------------

def _convert_below_1000(n: int, case: str = 'nominative') -> str:
    """Convert an integer 0-999 to Arabic words with grammatical case."""
    if n == 0:
        return ""

    hundreds_map = _get_hundreds(case)
    tens_map = _get_tens(case)

    parts: list[str] = []

    hundreds = n // 100
    remainder = n % 100

    if hundreds > 0:
        parts.append(hundreds_map[hundreds])

    if remainder == 0:
        return " ".join(parts)

    if remainder < 20:
        parts.append(_inflect_ones(remainder, case))
    else:
        tens_val = remainder // 10
        ones_val = remainder % 10
        if ones_val == 0:
            parts.append(tens_map[tens_val])
        else:
            parts.append(f"{_inflect_ones(ones_val, case)} و{tens_map[tens_val]}")

    return " و".join(parts)


def tafkeet(
    number: int | float,
    case: str = 'nominative',
    currency: str | None = None,
) -> str:
    """Convert a number to grammatically correct Arabic words.

    Supports full Arabic grammar: case inflection (إعراب), dual forms
    for thousands/millions, proper و placement, and optional currency.

    Args:
        number: The number to convert (int or float).
        case: Grammatical case for inflection.
            - ``'nominative'`` (مرفوع): عشرون، مائتان، ألفان
            - ``'accusative'`` (منصوب): عشرين، مائتين، ألفين
            - ``'genitive'`` (مجرور): عشرين، مائتين، ألفين
        currency: Optional currency code.
            - ``'SAR'``: appends ريال(s) / هللة for decimals.

    Returns:
        The number spelled out in grammatically correct Arabic words.

    Raises:
        TypeError: If the input is not a number.
        ValueError: If the number is negative or case is invalid.

    Examples:
        >>> tafkeet(0)
        'صفر'
        >>> tafkeet(101)
        'مائة وواحد'
        >>> tafkeet(2000, case='nominative')
        'ألفان'
        >>> tafkeet(2000, case='accusative')
        'ألفين'
        >>> tafkeet(1011)
        'ألف وأحد عشر'
        >>> tafkeet(250000)
        'مائتان وخمسون ألفاً'
        >>> tafkeet(150, currency='SAR')
        'مائة وخمسون ريالاً'
    """
    if not isinstance(number, (int, float)):
        raise TypeError(f"Expected int or float, got {type(number).__name__}")
    if case not in _VALID_CASES:
        raise ValueError(f"case must be one of {_VALID_CASES}, got '{case}'")

    # Handle float: split into integer and decimal parts
    if isinstance(number, float):
        int_part = int(number)
        dec_part = round((number - int_part) * 100)
        int_words = tafkeet(int_part, case=case, currency=None)
        if dec_part > 0:
            if currency == 'SAR':
                dec_words = tafkeet(dec_part, case=case, currency=None)
                return f"{int_words} ريالاً و{dec_words} هللة"
            dec_words = tafkeet(dec_part, case=case)
            return f"{int_words} فاصلة {dec_words}"
        if currency == 'SAR' and int_part > 0:
            return f"{int_words} ريالاً"
        return int_words

    if number < 0:
        raise ValueError("Negative numbers are not supported")

    if number == 0:
        if currency == 'SAR':
            return "صفر ريال"
        return ARABIC_ONES[0]

    if number < 20:
        result = _inflect_ones(number, case)
        if currency == 'SAR':
            return f"{result} ريالاً"
        return result

    # 20-99
    if number < 100:
        tens_map = _get_tens(case)
        tens_val = number // 10
        ones_val = number % 10
        if ones_val == 0:
            result = tens_map[tens_val]
        else:
            result = f"{_inflect_ones(ones_val, case)} و{tens_map[tens_val]}"
        if currency == 'SAR':
            return f"{result} ريالاً"
        return result

    # 100-999
    if number < 1000:
        result = _convert_below_1000(number, case)
        if currency == 'SAR':
            return f"{result} ريالاً"
        return result

    # Large numbers: process in groups of 3 digits
    scale_map = _get_scale(case)
    nom_singular = {
        idx: ARABIC_SCALE_NOMINATIVE[idx][0]
        for idx in ARABIC_SCALE_NOMINATIVE
    }

    groups: list[tuple[int, int]] = []  # (value, scale_index)
    remaining = number
    scale_idx = 0
    while remaining > 0:
        group_val = remaining % 1000
        if group_val > 0:
            groups.append((group_val, scale_idx))
        remaining //= 1000
        scale_idx += 1

    parts: list[str] = []
    for group_val, sidx in reversed(groups):
        if sidx == 0:
            # Base group (ones): just spell out
            parts.append(_convert_below_1000(group_val, case))
            continue

        singular, dual, plural = scale_map[sidx]

        if group_val == 1:
            parts.append(singular)
        elif group_val == 2:
            parts.append(dual)
        elif 3 <= group_val <= 10:
            # 3-10: plural form (آلاف, ملايين) — number precedes scale
            group_text = _convert_below_1000(group_val, case)
            parts.append(f"{group_text} {plural}")
        elif 11 <= group_val <= 99:
            # 11-99: singular accusative (tamyez) — always ألفاً
            group_acc = _convert_below_1000(group_val, 'accusative')
            parts.append(f"{group_acc} {nom_singular[sidx]}اً")
        else:
            # 100-999: scale word form depends on the remainder
            group_text = _convert_below_1000(group_val, case)
            remainder = group_val % 100
            if remainder >= 11:
                # Teens/tens: scale word is tamyez → always accusative
                parts.append(f"{group_text} {nom_singular[sidx]}اً")
            else:
                # Clean hundred or remainder 1-10: singular, no tanween
                parts.append(f"{group_text} {singular}")

    result = " و".join(parts)

    if currency == 'SAR':
        return f"{result} ريالاً"

    return result
