import pytest

from sahlnlp import clean_corpus


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


def test_repeat_reduction_is_applied():
    result = clean_corpus(["هذا نص عااااالي جدا ومفيد"], min_words=1)
    assert "عاالي" in result["cleaned"][0]["text"]
    assert result["operations"][-1] == {
        "operation": "تقليل تكرار الحروف",
        "applied": True,
    }


def test_empty_corpus_returns_empty_rows_and_applied_steps():
    result = clean_corpus([])
    assert result["cleaned"] == []
    assert result["rejected"] == []
    assert all(step["applied"] for step in result["operations"])
    assert set(result) == {"cleaned", "rejected", "operations"}
