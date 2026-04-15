"""Tests for sahlnlp.core.cleaner module."""

import pytest

from sahlnlp.core.cleaner import (
    clean_all,
    remove_html_and_links,
    remove_repeated_chars,
    remove_tashkeel,
    remove_tatweel,
)


# ---------------------------------------------------------------------------
# remove_tashkeel
# ---------------------------------------------------------------------------
class TestRemoveTashkeel:
    def test_fatha(self):
        assert remove_tashkeel("كِتَاب") == "كتاب"

    def test_shadda(self):
        assert remove_tashkeel("مُعَلِّم") == "معلم"

    def test_sukun(self):
        assert remove_tashkeel("مَرْحَباً") == "مرحبا"

    def test_no_diacritics(self):
        text = "مرحبا بالعالم"
        assert remove_tashkeel(text) == text

    def test_empty_string(self):
        assert remove_tashkeel("") == ""

    def test_mixed_arabic_english(self):
        assert remove_tashkeel("Hello مَرْحَبا World") == "Hello مرحبا World"

    def test_type_error_none(self):
        with pytest.raises(TypeError):
            remove_tashkeel(None)  # type: ignore[arg-type]

    def test_type_error_int(self):
        with pytest.raises(TypeError):
            remove_tashkeel(123)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# remove_tatweel
# ---------------------------------------------------------------------------
class TestRemoveTatweel:
    def test_basic_tatweel(self):
        assert remove_tatweel("الســــلام") == "السلام"

    def test_multiple_tatweel_groups(self):
        assert remove_tatweel("عـــــظيـــــم") == "عظيم"

    def test_no_tatweel(self):
        text = "سلام"
        assert remove_tatweel(text) == text

    def test_empty_string(self):
        assert remove_tatweel("") == ""

    def test_type_error_none(self):
        with pytest.raises(TypeError):
            remove_tatweel(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# remove_html_and_links
# ---------------------------------------------------------------------------
class TestRemoveHtmlAndLinks:
    def test_html_tags(self):
        assert remove_html_and_links("<b>مرحبا</b>") == "مرحبا"

    def test_url_http(self):
        assert remove_html_and_links("زوروا http://example.com") == "زوروا "

    def test_url_https(self):
        assert remove_html_and_links("رابط https://example.com هنا") == "رابط  هنا"

    def test_url_www(self):
        assert remove_html_and_links("موقع www.example.com") == "موقع "

    def test_combined_html_url(self):
        result = remove_html_and_links('اضغط <a href="http://x.com">هنا</a>')
        assert "http" not in result
        assert "<a" not in result

    def test_empty_string(self):
        assert remove_html_and_links("") == ""

    def test_no_html_no_links(self):
        text = "نص عادي"
        assert remove_html_and_links(text) == text

    def test_type_error(self):
        with pytest.raises(TypeError):
            remove_html_and_links(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# remove_repeated_chars
# ---------------------------------------------------------------------------
class TestRemoveRepeatedChars:
    def test_basic_flooding(self):
        # اااا (4 alefs after ً) -> اا (max_repeat=2); first ا before ً is separate
        assert remove_repeated_chars("مرحباًاااا") == "مرحباًاا"

    def test_english_flooding(self):
        # ssss (4 s's) -> ss (max_repeat=2)
        assert remove_repeated_chars("yessss") == "yess"

    def test_max_repeat_1(self):
        # اااا (4 alefs after ً) -> ا (max_repeat=1); first ا before ً is separate
        assert remove_repeated_chars("مرحباًاااا", max_repeat=1) == "مرحباًا"

    def test_max_repeat_3(self):
        assert remove_repeated_chars("ههههههه", max_repeat=3) == "ههه"

    def test_no_repeats(self):
        text = "مرحبا"
        assert remove_repeated_chars(text) == text

    def test_empty_string(self):
        assert remove_repeated_chars("") == ""

    def test_invalid_max_repeat_zero(self):
        with pytest.raises(ValueError):
            remove_repeated_chars("مرحبا", max_repeat=0)

    def test_type_error(self):
        with pytest.raises(TypeError):
            remove_repeated_chars(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# clean_all
# ---------------------------------------------------------------------------
class TestCleanAll:
    def test_combined_cleaning(self):
        text = "مَرْحَباً يا صديقي"
        result = clean_all(text)
        assert result == "مرحبا يا صديقي"

    def test_with_tatweel_and_html(self):
        result = clean_all("<p>الســــلام</p> عَلَيْكُم")
        assert "ـ" not in result
        assert "<p>" not in result
        assert "َ" not in result

    def test_preserves_english(self):
        text = "Hello مَرْحَباً World 123"
        result = clean_all(text)
        assert "Hello" in result
        assert "World" in result
        assert "123" in result

    def test_preserves_emojis(self):
        text = "مَرْحَباً 🌍"
        result = clean_all(text)
        assert "🌍" in result

    def test_flag_disable_tashkeel(self):
        text = "كِتَاب"
        result = clean_all(text, remove_tashkeel_flag=False)
        assert "ِ" in result  # kasra should remain
        assert "َ" in result  # fatha should remain

    def test_flag_disable_html(self):
        text = "<b>مرحبا</b>"
        result = clean_all(text, remove_html_flag=False)
        assert "<b>" in result

    def test_empty_string(self):
        assert clean_all("") == ""

    def test_type_error(self):
        with pytest.raises(TypeError):
            clean_all(None)  # type: ignore[arg-type]

    def test_mixed_noise_text(self):
        text = "مَرْحَباًااا بـكـــــم في <b>موقعنا</b> https://example.com"
        result = clean_all(text)
        assert "َ" not in result
        assert "ـ" not in result
        assert "<b>" not in result
        assert "https" not in result
        assert "مرحبا" in result
