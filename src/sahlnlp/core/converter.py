"""
Number conversion utilities for Arabic text.

Handles Hindi/Arabic numeral conversion and number-to-words (tafkeet).
"""

from __future__ import annotations

from sahlnlp.utils.constants import (
    ARABIC_HUNDREDS,
    ARABIC_ONES,
    ARABIC_SCALE,
    ARABIC_TENS,
    ARABIC_TO_INDIC_MAP,
    INDIC_TO_ARABIC_MAP,
    RE_ARABIC_DIGITS,
    RE_INDIC_DIGITS,
)


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
    return RE_INDIC_DIGITS.sub(lambda m: INDIC_TO_ARABIC_MAP[m.group()], text)


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
    return RE_ARABIC_DIGITS.sub(lambda m: ARABIC_TO_INDIC_MAP[m.group()], text)


def _convert_below_1000(n: int) -> str:
    """Convert an integer 0-999 to Arabic words (internal helper)."""
    if n == 0:
        return ""

    parts: list[str] = []

    # Hundreds
    hundreds = n // 100
    remainder = n % 100

    if hundreds > 0:
        parts.append(ARABIC_HUNDREDS[hundreds])

    if remainder == 0:
        return " ".join(parts)

    # 1-19
    if remainder < 20:
        parts.append(ARABIC_ONES[remainder])
    else:
        tens_val = remainder // 10
        ones_val = remainder % 10
        if ones_val == 0:
            parts.append(ARABIC_TENS[tens_val])
        else:
            parts.append(f"{ARABIC_ONES[ones_val]} و{ARABIC_TENS[tens_val]}")

    return " و".join(parts)


def tafkeet(number: int | float) -> str:
    """Convert a number to its written Arabic word form.

    Supports integers from 0 up to trillions, and basic decimal fractions.

    Args:
        number: The number to convert (int or float).

    Returns:
        The number spelled out in Arabic words.

    Raises:
        TypeError: If the input is not a number.
        ValueError: If the number is negative or too large.

    Examples:
        >>> tafkeet(0)
        'صفر'
        >>> tafkeet(150)
        'مائة وخمسون'
        >>> tafkeet(1001)
        'ألف وواحد'
    """
    if not isinstance(number, (int, float)):
        raise TypeError(f"Expected int or float, got {type(number).__name__}")

    if isinstance(number, float):
        int_part = int(number)
        dec_part = round((number - int_part) * 100)
        int_words = tafkeet(int_part)
        if dec_part > 0:
            dec_words = tafkeet(dec_part)
            return f"{int_words} فاصلة {dec_words}"
        return int_words

    if number < 0:
        raise ValueError("Negative numbers are not supported")

    if number == 0:
        return ARABIC_ONES[0]

    if number < 20:
        return ARABIC_ONES[number]

    if number < 100:
        tens_val = number // 10
        ones_val = number % 10
        if ones_val == 0:
            return ARABIC_TENS[tens_val]
        return f"{ARABIC_ONES[ones_val]} و{ARABIC_TENS[tens_val]}"

    if number < 1000:
        return _convert_below_1000(number)

    # Process in groups of 3 digits (thousands, millions, billions, trillions)
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
    for group_val, scale_idx in reversed(groups):
        if scale_idx == 0:
            parts.append(_convert_below_1000(group_val))
        else:
            singular, dual, plural = ARABIC_SCALE[scale_idx]
            group_text = _convert_below_1000(group_val)

            if group_val == 1:
                parts.append(singular)
            elif group_val == 2:
                parts.append(dual)
            elif group_val <= 10:
                parts.append(f"{group_text} {singular}")
            elif group_val < 100:
                parts.append(f"{group_text} {plural}")
            else:
                parts.append(f"{group_text} {singular}")

    result = " و".join(parts)
    return result
