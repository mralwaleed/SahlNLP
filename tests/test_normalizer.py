"""Tests for sahlnlp.core.normalizer module."""

import pytest

from sahlnlp.core.normalizer import (
    normalize_hamza,
    normalize_search,
    normalize_taa,
    normalize_yaa,
)


# ---------------------------------------------------------------------------
# normalize_hamza
# ---------------------------------------------------------------------------
class TestNormalizeHamza:
    def test_alef_hamza_above(self):
        assert normalize_hamza("أحمد") == "احمد"

    def test_alef_hamza_below(self):
        assert normalize_hamza("إبراهيم") == "ابراهيم"

    def test_alef_madda(self):
        assert normalize_hamza("آدم") == "ادم"

    def test_mixed_hamza(self):
        assert normalize_hamza("أحمد إبراهيم آدم") == "احمد ابراهيم ادم"

    def test_no_hamza_variants(self):
        text = "احمد ابراهيم ادم"
        assert normalize_hamza(text) == text

    def test_empty_string(self):
        assert normalize_hamza("") == ""

    def test_mixed_arabic_english(self):
        assert normalize_hamza("Hello أحمد") == "Hello احمد"

    def test_type_error(self):
        with pytest.raises(TypeError):
            normalize_hamza(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# normalize_taa
# ---------------------------------------------------------------------------
class TestNormalizeTaa:
    def test_taa_to_haa(self):
        assert normalize_taa("مدرسة") == "مدرسه"

    def test_haa_to_taa(self):
        assert normalize_taa("مدرسه", to_haa=False) == "مدرسة"

    def test_multiple_taa(self):
        assert normalize_taa("مدرسة جامعة") == "مدرسه جامعه"

    def test_no_taa_marbuta(self):
        text = "كتاب"
        assert normalize_taa(text) == text

    def test_empty_string(self):
        assert normalize_taa("") == ""

    def test_mixed_with_english(self):
        assert normalize_taa("school مدرسة") == "school مدرسه"

    def test_type_error(self):
        with pytest.raises(TypeError):
            normalize_taa(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# normalize_yaa
# ---------------------------------------------------------------------------
class TestNormalizeYaa:
    def test_alef_maksura(self):
        assert normalize_yaa("موسى") == "موسي"

    def test_multiple_maksura(self):
        assert normalize_yaa("موسى في مستشفى") == "موسي في مستشفي"

    def test_no_maksura(self):
        text = "موسي"
        assert normalize_yaa(text) == text

    def test_empty_string(self):
        assert normalize_yaa("") == ""

    def test_mixed_with_english(self):
        assert normalize_yaa("Moses موسى") == "Moses موسي"

    def test_type_error(self):
        with pytest.raises(TypeError):
            normalize_yaa(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# normalize_search
# ---------------------------------------------------------------------------
class TestNormalizeSearch:
    def test_combined_normalization(self):
        assert normalize_search("أحمد مُعَلِّمٌ في المدرسة") == "احمد معلم في المدرسه"

    def test_search_normalization_with_maksura(self):
        assert normalize_search("موسى في المستشفى") == "موسي في المستشفي"

    def test_search_with_tatweel(self):
        assert normalize_search("الســــلام") == "السلام"

    def test_empty_string(self):
        assert normalize_search("") == ""

    def test_english_preserved(self):
        result = normalize_search("Hello أحمد")
        assert "Hello" in result

    def test_type_error(self):
        with pytest.raises(TypeError):
            normalize_search(None)  # type: ignore[arg-type]

    def test_comprehensive_search(self):
        text = "أحمد مُعَلِّمٌ في المدرســـــة الكبرى"
        expected = "احمد معلم في المدرسه الكبري"
        assert normalize_search(text) == expected
