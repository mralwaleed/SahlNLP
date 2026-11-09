#!/usr/bin/env python3
"""Check whether corpus cleaning restores dialect signals after synthetic noise."""

from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sahlnlp import clean_corpus, detect_dialect  # noqa: E402
from sahlnlp.utils.dialect_corpus import DIALECT_CORPUS  # noqa: E402


def winner(text: str) -> str:
    scores = detect_dialect(text)
    return max(scores, key=scores.get)


def main() -> None:
    random.seed(13)
    texts: list[str] = []
    labels: list[str] = []
    for label, examples in DIALECT_CORPUS.items():
        for text in examples:
            noisy = text
            if random.random() < 0.5:
                noisy = "ـ".join(noisy)
            if random.random() < 0.5:
                noisy = noisy.replace("ا", "ااا")
            if random.random() < 0.5:
                noisy += " <b>رابط</b> https://example.com"
            texts.append(noisy)
            labels.append(label)

    before = sum(winner(text) == label for text, label in zip(texts, labels)) / len(
        texts
    )
    result = clean_corpus(
        texts,
        min_words=0,
        min_arabic_ratio=0,
        deduplicate=False,
        max_dialect_drift=0.08,
    )
    cleaned_by_index = {row["index"]: str(row["text"]) for row in result["cleaned"]}
    after = sum(
        winner(cleaned_by_index[index]) == labels[index]
        for index in range(len(texts))
        if index in cleaned_by_index
    ) / len(cleaned_by_index)

    print("SahlNLP dialect preservation smoke benchmark")
    print(
        f"Corpus: {len(texts)} bundled labeled sentences with synthetic noise, "
        "fixed seed 13"
    )
    print(f"Label accuracy before cleanup: {before:.2%}")
    print(f"Label accuracy after cleanup:  {after:.2%}")
    print(f"Kept lines: {len(cleaned_by_index)}/{len(texts)}")
    print(
        "Final dialect distribution shift: "
        f"{result['dialect_report']['max_distribution_shift']:.4f}"
    )
    print(f"Skipped operations: {result['dialect_report']['protected_operations']}")
    print("This tests synthetic corruption recovery, not real-world data quality.")


if __name__ == "__main__":
    main()
