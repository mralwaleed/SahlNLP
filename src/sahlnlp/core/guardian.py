"""
PII (Personally Identifiable Information) detection and masking for Arabic text.

Detects Saudi phone numbers, national IDs, IBANs, emails, and Arabic names
using pre-compiled regex patterns. Zero external dependencies.
"""

from __future__ import annotations

import re

from sahlnlp.utils.logger import logger
from sahlnlp.utils.constants import (
    RE_AR_NAME_THEOPHORIC,
    RE_AR_NAME_TITLED,
    RE_EMAIL,
    RE_SA_IBAN,
    RE_SA_ID,
    RE_SA_PHONE,
)


def _mask_preserve(text: str, mask_char: str = "*", keep_start: int = 2, keep_end: int = 3) -> str:
    """Mask the middle of a string, preserving start and end characters.

    Args:
        text: The string to mask.
        mask_char: Character used for masking.
        keep_start: Number of leading characters to preserve.
        keep_end: Number of trailing characters to preserve.

    Returns:
        Masked string with middle replaced by mask_char.
    """
    if len(text) < keep_start + keep_end:
        return mask_char * len(text)
    if len(text) == keep_start + keep_end:
        return text
    masked_len = len(text) - keep_start - keep_end
    return text[:keep_start] + mask_char * masked_len + text[-keep_end:]


def mask_sensitive_info(
    text: str,
    mode: str = "tag",
    mask_char: str = "*",
) -> str:
    """Detect and redact PII from Arabic text.

    Identifies Saudi phone numbers, national IDs, IBANs, emails, and Arabic
    names, then replaces them according to the chosen mode.

    Args:
        text: The input text containing potential PII.
        mode: Redaction mode.
            - ``'tag'``: Replace with entity labels like [PHONE], [ID], [IBAN],
              [EMAIL], [NAME].
            - ``'mask'``: Replace with ``mask_char`` while preserving first/last
              characters for context (e.g., ``055****123``).
        mask_char: Character used for masking in ``'mask'`` mode (default ``*``).

    Returns:
        Text with PII redacted according to the chosen mode.

    Raises:
        TypeError: If text is not a string.
        ValueError: If mode is not ``'tag'`` or ``'mask'``.

    Examples:
        >>> mask_sensitive_info("اتصل على 0551234567", mode="tag")
        'اتصل على [PHONE]'
        >>> mask_sensitive_info("اتصل على 0551234567", mode="mask")
        'اتصل على 05*****567'
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    if mode not in ("tag", "mask"):
        raise ValueError(f"mode must be 'tag' or 'mask', got '{mode}'")

    original = text
    try:
        def _replace_iban(m: re.Match) -> str:
            return "[IBAN]" if mode == "tag" else _mask_preserve(m.group(), mask_char, 2, 2)

        text = RE_SA_IBAN.sub(_replace_iban, text)

        # 2. Phone numbers
        def _replace_phone(m: re.Match) -> str:
            return "[PHONE]" if mode == "tag" else _mask_preserve(m.group(), mask_char, 2, 3)

        text = RE_SA_PHONE.sub(_replace_phone, text)

        # 3. National ID
        def _replace_id(m: re.Match) -> str:
            return "[ID]" if mode == "tag" else _mask_preserve(m.group(), mask_char, 1, 2)

        text = RE_SA_ID.sub(_replace_id, text)

        # 4. Email
        def _replace_email(m: re.Match) -> str:
            return "[EMAIL]" if mode == "tag" else _mask_preserve(m.group(), mask_char, 2, 4)

        text = RE_EMAIL.sub(_replace_email, text)

        # 5. Arabic names — titled names first (highest confidence)
        def _replace_titled_name(m: re.Match) -> str:
            return "[NAME]" if mode == "tag" else mask_char * len(m.group())

        text = RE_AR_NAME_TITLED.sub(_replace_titled_name, text)

        # 6. Arabic names — theophoric/patronymic (عبد X, بن X)
        def _replace_theo_name(m: re.Match) -> str:
            return "[NAME]" if mode == "tag" else mask_char * len(m.group())

        text = RE_AR_NAME_THEOPHORIC.sub(_replace_theo_name, text)

        return text
    except Exception:
        logger.warning("mask_sensitive_info failed, returning original text")
        return original
