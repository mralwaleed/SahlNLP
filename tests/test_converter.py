"""Tests for sahlnlp.core.converter module."""

import pytest

from sahlnlp.core.converter import arabic_to_indic, indic_to_arabic, tafkeet


# ---------------------------------------------------------------------------
# indic_to_arabic
# ---------------------------------------------------------------------------
class TestIndicToArabic:
    def test_single_digit(self):
        assert indic_to_arabic("٣") == "3"

    def test_full_number(self):
        assert indic_to_arabic("٢٠٢٥") == "2025"

    def test_mixed_text(self):
        assert indic_to_arabic("٣ أبريل ٢٠٢٥") == "3 أبريل 2025"

    def test_no_indic_digits(self):
        text = "2025"
        assert indic_to_arabic(text) == text

    def test_empty_string(self):
        assert indic_to_arabic("") == ""

    def test_all_indic_digits(self):
        assert indic_to_arabic("٠١٢٣٤٥٦٧٨٩") == "0123456789"

    def test_type_error(self):
        with pytest.raises(TypeError):
            indic_to_arabic(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# arabic_to_indic
# ---------------------------------------------------------------------------
class TestArabicToIndic:
    def test_single_digit(self):
        assert arabic_to_indic("3") == "٣"

    def test_full_number(self):
        assert arabic_to_indic("2025") == "٢٠٢٥"

    def test_mixed_text(self):
        assert arabic_to_indic("3 أبريل 2025") == "٣ أبريل ٢٠٢٥"

    def test_no_arabic_digits(self):
        text = "مرحبا"
        assert arabic_to_indic(text) == text

    def test_empty_string(self):
        assert arabic_to_indic("") == ""

    def test_roundtrip(self):
        original = "٠١٢٣٤٥٦٧٨٩"
        assert indic_to_arabic(arabic_to_indic("0123456789")) == "0123456789"
        assert arabic_to_indic(indic_to_arabic(original)) == original

    def test_type_error(self):
        with pytest.raises(TypeError):
            arabic_to_indic(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# tafkeet
# ---------------------------------------------------------------------------
class TestTafkeet:
    # --- Basic numbers ---
    def test_zero(self):
        assert tafkeet(0) == "صفر"

    def test_one(self):
        assert tafkeet(1) == "واحد"

    def test_two(self):
        assert tafkeet(2) == "اثنان"

    def test_ten(self):
        assert tafkeet(10) == "عشرة"

    def test_eleven(self):
        assert tafkeet(11) == "أحد عشر"

    def test_twelve(self):
        assert tafkeet(12) == "اثنا عشر"

    def test_thirteen(self):
        assert tafkeet(13) == "ثلاثة عشر"

    def test_nineteen(self):
        assert tafkeet(19) == "تسعة عشر"

    # --- Tens ---
    def test_twenty(self):
        assert tafkeet(20) == "عشرون"

    def test_twenty_one(self):
        assert tafkeet(21) == "واحد وعشرون"

    def test_fifty(self):
        assert tafkeet(50) == "خمسون"

    def test_ninety_nine(self):
        assert tafkeet(99) == "تسعة وتسعون"

    # --- Hundreds ---
    def test_one_hundred(self):
        assert tafkeet(100) == "مائة"

    def test_one_hundred_fifty(self):
        assert tafkeet(150) == "مائة وخمسون"

    def test_two_hundred(self):
        assert tafkeet(200) == "مائتان"

    def test_three_hundred(self):
        assert tafkeet(300) == "ثلاثمائة"

    def test_nine_hundred_ninety_nine(self):
        result = tafkeet(999)
        assert "تسعمائة" in result
        assert "تسعة" in result
        assert "وتسعون" in result

    # --- Thousands ---
    def test_one_thousand(self):
        assert tafkeet(1000) == "ألف"

    def test_one_thousand_one(self):
        result = tafkeet(1001)
        assert "ألف" in result
        assert "واحد" in result

    def test_two_thousand(self):
        assert tafkeet(2000) == "ألفان"

    def test_five_thousand(self):
        result = tafkeet(5000)
        assert "خمسمائة" in result or "خمسة" in result

    def test_ten_thousand(self):
        result = tafkeet(10000)
        assert "عشرة" in result
        assert "ألف" in result

    def test_one_hundred_thousand(self):
        result = tafkeet(100000)
        assert "مائة" in result
        assert "ألف" in result

    # --- Millions ---
    def test_one_million(self):
        assert tafkeet(1000000) == "مليون"

    def test_two_million(self):
        assert tafkeet(2000000) == "مليونان"

    # --- Edge cases ---
    def test_float_basic(self):
        result = tafkeet(1.5)
        assert "واحد" in result
        assert "فاصلة" in result

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            tafkeet(-1)

    def test_type_error_string(self):
        with pytest.raises(TypeError):
            tafkeet("123")  # type: ignore[arg-type]

    def test_type_error_none(self):
        with pytest.raises(TypeError):
            tafkeet(None)  # type: ignore[arg-type]

    def test_type_error_list(self):
        with pytest.raises(TypeError):
            tafkeet([1, 2, 3])  # type: ignore[arg-type]
