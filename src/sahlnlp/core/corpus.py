"""Practical cleaning and filtering for Arabic text corpora."""

from __future__ import annotations

import re

from sahlnlp.core.analyzer import detect_dialect
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
    max_dialect_drift: float = 0.08,
) -> dict[str, object]:
    """Clean Arabic corpus lines and report accepted and rejected records.

    Cleans common noise, filters empty/short/non-Arabic lines, and optionally
    removes exact duplicates. Character flooding is reduced only when the
    aggregate dialect profile remains within ``max_dialect_drift``.
    """
    if not isinstance(texts, list) or any(not isinstance(text, str) for text in texts):
        raise TypeError("texts must be a list of strings")
    if not isinstance(min_words, int) or isinstance(min_words, bool) or min_words < 0:
        raise ValueError("min_words must be a non-negative integer")
    if not 0 <= min_arabic_ratio <= 1:
        raise ValueError("min_arabic_ratio must be between 0 and 1")
    if not 0 <= max_dialect_drift <= 1:
        raise ValueError("max_dialect_drift must be between 0 and 1")

    def dialect_scores(records: list[str]) -> list[dict[str, float]]:
        return [detect_dialect(text) for text in records]

    def dialect_profile(records: list[str]) -> dict[str, float]:
        if not records:
            return {}
        totals: dict[str, float] = {}
        for scores in dialect_scores(records):
            for dialect, score in scores.items():
                totals[dialect] = totals.get(dialect, 0.0) + score
        return {
            dialect: round(score / len(records), 4) for dialect, score in totals.items()
        }

    stage_texts = list(texts)
    operations: list[dict[str, object]] = []
    protected_operations: list[str] = []

    def apply_guarded(name: str, transform) -> None:
        nonlocal stage_texts
        if not stage_texts:
            operations.append(
                {
                    "operation": name,
                    "applied": True,
                    "distribution_shift": 0.0,
                    "confident_label_flip_rate": 0.0,
                }
            )
            return
        before = dialect_scores(stage_texts)
        candidate_texts = [transform(text) for text in stage_texts]
        after = dialect_scores(candidate_texts)
        before_profile = dialect_profile_from_scores(before)
        after_profile = dialect_profile_from_scores(after)
        shift = max(
            (
                abs(before_profile.get(key, 0.0) - after_profile.get(key, 0.0))
                for key in before_profile.keys() | after_profile.keys()
            ),
            default=0.0,
        )
        confident = [
            i
            for i, scores in enumerate(before)
            if max(scores.values(), default=0) >= 0.6
        ]
        flips = sum(
            max(before[i], key=before[i].get) != max(after[i], key=after[i].get)
            for i in confident
        )
        flip_rate = flips / len(confident) if confident else 0.0
        applied = shift <= max_dialect_drift and flip_rate <= max_dialect_drift
        operations.append(
            {
                "operation": name,
                "applied": applied,
                "distribution_shift": round(shift, 4),
                "confident_label_flip_rate": round(flip_rate, 4),
            }
        )
        if applied:
            stage_texts = candidate_texts
        else:
            protected_operations.append(name)

    def dialect_profile_from_scores(
        scores_by_text: list[dict[str, float]],
    ) -> dict[str, float]:
        if not scores_by_text:
            return {}
        totals: dict[str, float] = {}
        for scores in scores_by_text:
            for dialect, score in scores.items():
                totals[dialect] = totals.get(dialect, 0.0) + score
        return {
            dialect: score / len(scores_by_text) for dialect, score in totals.items()
        }

    apply_guarded("إزالة التشكيل", remove_tashkeel)
    apply_guarded("إزالة التطويل", remove_tatweel)
    if remove_links:
        apply_guarded("إزالة الروابط ووسوم HTML", remove_html_and_links)
    apply_guarded("توحيد المسافات", lambda text: _SPACE.sub(" ", text).strip())
    if reduce_repeated_chars:
        apply_guarded("تقليل تكرار الحروف", remove_repeated_chars)

    cleaned_records: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    quality_accepted: list[str] = []
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

        quality_accepted.append(cleaned)
        duplicate_key = cleaned.casefold()
        if deduplicate and duplicate_key in seen:
            rejected.append(
                {"index": index, "text": original, "reason": "مكرر بعد التنظيف"}
            )
            continue
        seen.add(duplicate_key)
        changed = cleaned != original
        scores_for_line = detect_dialect(cleaned)
        cleaned_records.append(
            {
                "index": index,
                "original": original,
                "text": cleaned,
                "changed": changed,
                "reason": "نُظّف النص وأُبقي" if changed else "اجتاز الفلاتر دون تغيير",
                "dialect": max(scores_for_line, key=scores_for_line.get),
            }
        )

    retained_texts = [str(record["text"]) for record in cleaned_records]
    input_profile = dialect_profile(quality_accepted)
    output_profile = dialect_profile(retained_texts)
    profile_drift = max(
        (
            abs(input_profile.get(key, 0.0) - output_profile.get(key, 0.0))
            for key in input_profile.keys() | output_profile.keys()
        ),
        default=0.0,
    )
    warnings = []
    if profile_drift > max_dialect_drift:
        warnings.append(
            "تغيّر توزيع اللهجات في الناتج أكثر من الحد المحدد، غالبًا بسبب "
            "الفلترة أو إزالة التكرار."
        )
    return {
        "cleaned": cleaned_records,
        "rejected": rejected,
        "dialect_report": {
            "before": input_profile,
            "after": output_profile,
            "scope": "النصوص التي اجتازت فلاتر الطول ونسبة العربية، قبل إزالة التكرار",
            "max_distribution_shift": round(profile_drift, 4),
            "protected_operations": protected_operations,
            "operations": operations,
            "warnings": warnings,
            "note": "التقرير تقديري ويعتمد على كاشف اللهجات المضمّن.",
        },
    }
