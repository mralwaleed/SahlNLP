"""Tests for sahlnlp.core.converter module — full grammar tafkeet."""

import pytest

from sahlnlp.core.converter import arabic_to_indic, indic_to_arabic, tafkeet


# ===========================================================================
# Indic <-> Arabic digit conversion (unchanged)
# ===========================================================================
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


# ===========================================================================
# Tafkeet — Basic Numbers (0-19)
# ===========================================================================
class TestTafkeetBasic:
    def test_zero(self):
        assert tafkeet(0) == "صفر"

    def test_one(self):
        assert tafkeet(1) == "واحد"

    def test_two_nominative(self):
        assert tafkeet(2) == "اثنان"

    def test_two_accusative(self):
        assert tafkeet(2, case='accusative') == "اثنين"

    def test_two_genitive(self):
        assert tafkeet(2, case='genitive') == "اثنين"

    def test_ten(self):
        assert tafkeet(10) == "عشرة"

    def test_eleven(self):
        assert tafkeet(11) == "أحد عشر"

    def test_eleven_does_not_inflect(self):
        # 11 is مبني — same form in all cases
        assert tafkeet(11, case='accusative') == "أحد عشر"
        assert tafkeet(11, case='genitive') == "أحد عشر"

    def test_twelve_nominative(self):
        assert tafkeet(12) == "اثنا عشر"

    def test_twelve_accusative(self):
        assert tafkeet(12, case='accusative') == "اثني عشر"

    def test_twelve_genitive(self):
        assert tafkeet(12, case='genitive') == "اثني عشر"

    def test_thirteen(self):
        assert tafkeet(13) == "ثلاثة عشر"

    def test_nineteen(self):
        assert tafkeet(19) == "تسعة عشر"


# ===========================================================================
# Tafkeet — Tens (20-99) with Case
# ===========================================================================
class TestTafkeetTens:
    def test_twenty_nominative(self):
        assert tafkeet(20, case='nominative') == "عشرون"

    def test_twenty_accusative(self):
        assert tafkeet(20, case='accusative') == "عشرين"

    def test_twenty_genitive(self):
        assert tafkeet(20, case='genitive') == "عشرين"

    def test_twenty_one_nominative(self):
        assert tafkeet(21) == "واحد وعشرون"

    def test_twenty_one_accusative(self):
        assert tafkeet(21, case='accusative') == "واحد وعشرين"

    def test_twenty_two_nominative(self):
        assert tafkeet(22) == "اثنان وعشرون"

    def test_twenty_two_accusative(self):
        assert tafkeet(22, case='accusative') == "اثنين وعشرين"

    def test_twenty_two_genitive(self):
        assert tafkeet(22, case='genitive') == "اثنين وعشرين"

    def test_fifty_nominative(self):
        assert tafkeet(50) == "خمسون"

    def test_fifty_accusative(self):
        assert tafkeet(50, case='accusative') == "خمسين"

    def test_ninety_nine_nominative(self):
        assert tafkeet(99) == "تسعة وتسعون"

    def test_ninety_nine_accusative(self):
        assert tafkeet(99, case='accusative') == "تسعة وتسعين"


# ===========================================================================
# Tafkeet — Hundreds (100-999) with Case
# ===========================================================================
class TestTafkeetHundreds:
    def test_one_hundred(self):
        assert tafkeet(100) == "مائة"

    def test_one_hundred_one(self):
        assert tafkeet(101) == "مائة وواحد"

    def test_one_hundred_two_nominative(self):
        assert tafkeet(102) == "مائة واثنان"

    def test_one_hundred_two_accusative(self):
        assert tafkeet(102, case='accusative') == "مائة واثنين"

    def test_one_hundred_fifty(self):
        assert tafkeet(150) == "مائة وخمسون"

    def test_two_hundred_nominative(self):
        assert tafkeet(200, case='nominative') == "مائتان"

    def test_two_hundred_accusative(self):
        assert tafkeet(200, case='accusative') == "مائتين"

    def test_three_hundred(self):
        assert tafkeet(300) == "ثلاثمائة"

    def test_nine_hundred_ninety_nine(self):
        result = tafkeet(999)
        assert "تسعمائة" in result
        assert "تسعة" in result
        assert "تسعون" in result

    def test_750(self):
        result = tafkeet(750)
        assert "سبعمائة" in result
        assert "خمسون" in result


# ===========================================================================
# Tafkeet — Thousands with Dual Forms
# ===========================================================================
class TestTafkeetThousands:
    def test_one_thousand(self):
        assert tafkeet(1000) == "ألف"

    def test_one_thousand_accusative(self):
        assert tafkeet(1000, case='accusative') == "ألفاً"

    def test_one_thousand_genitive(self):
        assert tafkeet(1000, case='genitive') == "ألف"

    def test_one_thousand_one(self):
        result = tafkeet(1001)
        assert "ألف" in result
        assert "واحد" in result

    def test_two_thousand_nominative(self):
        assert tafkeet(2000, case='nominative') == "ألفان"

    def test_two_thousand_accusative(self):
        assert tafkeet(2000, case='accusative') == "ألفين"

    def test_two_thousand_genitive(self):
        assert tafkeet(2000, case='genitive') == "ألفين"

    def test_five_thousand(self):
        result = tafkeet(5000)
        assert "خمسة" in result
        assert "آلاف" in result

    def test_ten_thousand(self):
        result = tafkeet(10000)
        assert "عشرة" in result
        assert "آلاف" in result

    def test_eleven_thousand(self):
        result = tafkeet(11000)
        assert "أحد عشر" in result
        assert "ألفاً" in result

    def test_one_hundred_thousand_nominative(self):
        # 100 × 1000 = clean hundred → singular without tanween
        result = tafkeet(100000)
        assert "مائة" in result
        assert "ألف" in result
        assert "ألفاً" not in result  # no accusative tanween for clean hundred

    def test_one_hundred_thousand_accusative(self):
        # Clean hundred: scale word is counted noun (genitive) regardless of case
        result = tafkeet(100000, case='accusative')
        assert "مائة" in result
        assert "ألف" in result

    def test_two_hundred_fifty_thousand(self):
        # 250 × 1000 — has tens (خمسون) → tamyez → accusative
        result = tafkeet(250000)
        assert "مائتان" in result
        assert "خمسون" in result
        assert "ألفاً" in result


# ===========================================================================
# Tafkeet — Millions with Dual Forms
# ===========================================================================
class TestTafkeetMillions:
    def test_one_million(self):
        assert tafkeet(1000000) == "مليون"

    def test_one_million_accusative(self):
        assert tafkeet(1000000, case='accusative') == "مليوناً"

    def test_one_million_genitive(self):
        assert tafkeet(1000000, case='genitive') == "مليون"

    def test_two_million_nominative(self):
        assert tafkeet(2000000, case='nominative') == "مليونان"

    def test_two_million_accusative(self):
        assert tafkeet(2000000, case='accusative') == "مليونين"

    def test_two_million_genitive(self):
        assert tafkeet(2000000, case='genitive') == "مليونين"

    def test_five_million(self):
        result = tafkeet(5000000)
        assert "خمسة" in result
        assert "ملايين" in result

    def test_twenty_million(self):
        result = tafkeet(20000000)
        assert "عشرين" in result
        assert "مليوناً" in result


# ===========================================================================
# Tafkeet — Billions
# ===========================================================================
class TestTafkeetBillions:
    def test_one_billion(self):
        assert tafkeet(1000000000) == "مليار"

    def test_one_billion_accusative(self):
        assert tafkeet(1000000000, case='accusative') == "ملياراً"

    def test_one_billion_genitive(self):
        assert tafkeet(1000000000, case='genitive') == "مليار"

    def test_two_billion_nominative(self):
        assert tafkeet(2000000000, case='nominative') == "ملياران"

    def test_two_billion_genitive(self):
        assert tafkeet(2000000000, case='genitive') == "مليارين"


# ===========================================================================
# Tafkeet — "Wa" (و) Connectivity
# ===========================================================================
class TestTafkeetWaConnectivity:
    def test_101(self):
        assert tafkeet(101) == "مائة وواحد"

    def test_1011(self):
        assert tafkeet(1011) == "ألف وأحد عشر"

    def test_750_nominative(self):
        result = tafkeet(750)
        assert "سبعمائة وخمسون" in result

    def test_750_accusative(self):
        result = tafkeet(750, case='accusative')
        assert "سبعمائة وخمسين" in result


# ===========================================================================
# Tafkeet — Currency (SAR)
# ===========================================================================
class TestTafkeetCurrency:
    def test_zero_sar(self):
        assert tafkeet(0, currency='SAR') == "صفر ريال"

    def test_one_sar(self):
        assert tafkeet(1, currency='SAR') == "واحد ريالاً"

    def test_150_sar(self):
        result = tafkeet(150, currency='SAR')
        assert "ريالاً" in result
        assert "مائة وخمسون" in result

    def test_float_sar(self):
        result = tafkeet(1.5, currency='SAR')
        assert "ريالاً" in result
        assert "هللة" in result

    def test_thousand_sar(self):
        result = tafkeet(1000, currency='SAR')
        assert "ألف" in result
        assert "ريالاً" in result


# ===========================================================================
# Tafkeet — Floats (no currency)
# ===========================================================================
class TestTafkeetFloat:
    def test_float_basic(self):
        result = tafkeet(1.5)
        assert "واحد" in result
        assert "فاصلة" in result

    def test_float_whole(self):
        result = tafkeet(5.0)
        assert result == "خمسة"


# ===========================================================================
# Tafkeet — Error Handling
# ===========================================================================
class TestTafkeetErrors:
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

    def test_invalid_case(self):
        with pytest.raises(ValueError):
            tafkeet(100, case='dative')
