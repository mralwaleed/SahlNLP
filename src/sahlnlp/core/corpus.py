"""Practical cleaning and filtering for Arabic text corpora."""

from __future__ import annotations

import re

from sahlnlp.core.cleaner import (
    remove_html_and_links,
    remove_repeated_chars,
    remove_tashkeel,
    remove_tatweel,
)

_ARABIC = re.compile(r"[\u0600-\u06ff]")
_WORD = re.compile(r"[^\W_]+", re.UNICODE)
_SPACE = re.compile(r"\s+")


def clean_corpus(
    texts: list[str],
    *,
    min_words: int = 3,
    min_arabic_ratio: float = 0.25,
    remove_links: bool = True,
    deduplicate: bool = True,
    reduce_repeated_chars: bool = True,
) -> dict[str, object]:
    """Clean Arabic corpus lines and report accepted and rejected records.

    Cleans common noise, filters empty/short/non-Arabic lines, and optionally
    removes exact duplicates. The result includes a record for every accepted
    and rejected line, plus the cleaning steps that were applied.
    """
    if not isinstance(texts, list) or any(not isinstance(text, str) for text in texts):
        raise TypeError("texts must be a list of strings")
    if not isinstance(min_words, int) or isinstance(min_words, bool) or min_words < 0:
        raise ValueError("min_words must be a non-negative integer")
    if not 0 <= min_arabic_ratio <= 1:
        raise ValueError("min_arabic_ratio must be between 0 and 1")

    stage_texts = list(texts)
    operations: list[dict[str, object]] = []

    def apply(name: str, transform) -> None:
        nonlocal stage_texts
        stage_texts = [transform(text) for text in stage_texts]
        operations.append({"operation": name, "applied": True})

    apply("إزالة التشكيل", remove_tashkeel)
    apply("إزالة التطويل", remove_tatweel)
    if remove_links:
        apply("إزالة الروابط ووسوم HTML", remove_html_and_links)
    apply("توحيد المسافات", lambda text: _SPACE.sub(" ", text).strip())
    if reduce_repeated_chars:
        apply("تقليل تكرار الحروف", remove_repeated_chars)

    cleaned_records: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    seen: set[str] = set()

    for index, (original, cleaned) in enumerate(zip(texts, stage_texts)):
        words = _WORD.findall(cleaned)
        if not cleaned:
            reason = "فارغ بعد التنظيف"
        elif len(words) < min_words:
            reason = "أقصر من الحد الأدنى للكلمات"
        else:
            letters = [char for char in cleaned if char.isalpha()]
            ratio = sum(bool(_ARABIC.fullmatch(char)) for char in letters) / max(
                len(letters), 1
            )
            reason = (
                "نسبة الأحرف العربية أقل من الحد المحدد"
                if ratio < min_arabic_ratio
                else ""
            )

        if reason:
            rejected.append({"index": index, "text": original, "reason": reason})
            continue

        duplicate_key = cleaned.casefold()
        if deduplicate and duplicate_key in seen:
            rejected.append(
                {"index": index, "text": original, "reason": "مكرر بعد التنظيف"}
            )
            continue
        seen.add(duplicate_key)
        changed = cleaned != original
        cleaned_records.append(
            {
                "index": index,
                "original": original,
                "text": cleaned,
                "changed": changed,
                "reason": "نُظّف النص وأُبقي" if changed else "اجتاز الفلاتر دون تغيير",
            }
        )

    return {"cleaned": cleaned_records, "rejected": rejected, "operations": operations}
