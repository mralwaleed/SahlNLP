import pytest

from sahlnlp import clean_corpus
from sahlnlp.core import corpus


def test_cleans_arabic_lines_and_tracks_changes():
    result = clean_corpus(["مَرْحَبــا   بالعالم اليوم"])
    assert result["cleaned"][0]["text"] == "مرحبا بالعالم اليوم"
    assert result["cleaned"][0]["changed"] is True
    assert result["cleaned"][0]["index"] == 0


def test_filters_short_non_arabic_and_duplicates():
    result = clean_corpus(
        [
            "مرحبا",
            "This is a long English sentence",
            "هذا نص عربي مفيد للتدريب",
            "هذا نص عربي مفيد للتدريب",
        ]
    )
    assert len(result["cleaned"]) == 1
    assert [row["reason"] for row in result["rejected"]] == [
        "أقصر من الحد الأدنى للكلمات",
        "نسبة الأحرف العربية أقل من الحد المحدد",
        "مكرر بعد التنظيف",
    ]


def test_can_preserve_links_and_duplicates():
    rows = ["هذا نص عربي طويل مفيد للتدريب https://example.com"] * 2
    result = clean_corpus(rows, remove_links=False, deduplicate=False)
    assert len(result["cleaned"]) == 2
    assert "https://example.com" in result["cleaned"][0]["text"]


def test_validates_input_and_options():
    with pytest.raises(TypeError):
        clean_corpus(["ok", None])
    with pytest.raises(ValueError):
        clean_corpus(["ok"], min_arabic_ratio=1.5)
    with pytest.raises(ValueError):
        clean_corpus(["ok"], min_words=-1)
    with pytest.raises(ValueError):
        clean_corpus(["ok"], max_dialect_drift=1.5)


def test_skips_repeat_reduction_when_it_changes_dialect_profile(monkeypatch):
    def fake_dialect(text):
        if "اااا" in text:
            return {"Gulf": 1.0, "Egyptian": 0.0}
        return {"Gulf": 0.0, "Egyptian": 1.0}

    monkeypatch.setattr(corpus, "detect_dialect", fake_dialect)
    result = clean_corpus(["هذا عااااالي جدا باللهجة"], min_words=1)
    assert "عاااا" in result["cleaned"][0]["text"]
    assert result["dialect_report"]["protected_operations"]
    assert result["dialect_report"]["max_distribution_shift"] == 0.0


def test_empty_corpus_returns_empty_profiles_and_audited_steps():
    result = clean_corpus([])
    assert result["cleaned"] == []
    assert result["rejected"] == []
    assert result["dialect_report"]["before"] == {}
    assert all(step["applied"] for step in result["dialect_report"]["operations"])


def test_reports_dialect_shift_caused_by_deduplication(monkeypatch):
    def fake_dialect(text):
        gulf = "ABC" in text
        return {"Gulf": 1.0 if gulf else 0.0, "Egyptian": 0.0 if gulf else 1.0}

    monkeypatch.setattr(corpus, "detect_dialect", fake_dialect)
    result = clean_corpus(
        ["هذا نص عربي طويل ومفيد ABC", "هذا نص عربي طويل ومفيد abc"],
        min_words=1,
    )
    assert len(result["cleaned"]) == 1
    assert result["dialect_report"]["max_distribution_shift"] == 0.5
    assert result["dialect_report"]["warnings"]
