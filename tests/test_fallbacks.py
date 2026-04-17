"""Tests for exception fallback branches — defensive error handlers."""

from unittest.mock import patch

from sahlnlp.core import analyzer, cleaner, converter, guardian, normalizer


# ===========================================================================
# Cleaner fallbacks
# ===========================================================================
class TestCleanerFallbacks:
    @patch.object(cleaner, "RE_TASHKEEL")
    def test_remove_tashkeel_fallback(self, mock_re):
        mock_re.sub.side_effect = RuntimeError("boom")
        assert cleaner.remove_tashkeel("test") == "test"

    @patch.object(cleaner, "RE_TATWEEL")
    def test_remove_tatweel_fallback(self, mock_re):
        mock_re.sub.side_effect = RuntimeError("boom")
        assert cleaner.remove_tatweel("test") == "test"

    @patch.object(cleaner, "RE_URL")
    def test_remove_html_fallback(self, mock_re):
        mock_re.sub.side_effect = RuntimeError("boom")
        assert cleaner.remove_html_and_links("test") == "test"

    @patch.object(cleaner, "RE_REPEATED_CHAR")
    def test_remove_repeated_fallback(self, mock_re):
        mock_re.sub.side_effect = RuntimeError("boom")
        assert cleaner.remove_repeated_chars("test") == "test"

    @patch.object(cleaner, "remove_tashkeel")
    def test_clean_all_fallback(self, mock_fn):
        mock_fn.side_effect = RuntimeError("boom")
        assert cleaner.clean_all("test") == "test"


# ===========================================================================
# Normalizer fallbacks
# ===========================================================================
class TestNormalizerFallbacks:
    @patch.object(normalizer, "ALEF_VARIANTS")
    def test_normalize_hamza_fallback(self, mock_vars):
        mock_vars.__contains__ = lambda s, x: (
            _ for _ in ()
        ).throw(RuntimeError("boom"))
        assert normalizer.normalize_hamza("test") == "test"

    @patch.object(normalizer, "TAA_MARBUTA")
    def test_normalize_taa_fallback(self, mock_taa):
        type(mock_taa).__eq__ = lambda s, x: (_ for _ in ()).throw(RuntimeError("boom"))
        assert normalizer.normalize_taa("test") == "test"

    @patch.object(normalizer, "ALEF_MAKSURA")
    def test_normalize_yaa_fallback(self, mock_yaa):
        type(mock_yaa).__eq__ = lambda s, x: (_ for _ in ()).throw(RuntimeError("boom"))
        assert normalizer.normalize_yaa("test") == "test"

    def test_normalize_search_fallback(self):
        # normalize_search uses a lazy import inside the function body,
        # so patch the import path where it's actually resolved.
        with patch(
            "sahlnlp.core.cleaner.remove_tashkeel",
            side_effect=RuntimeError("boom"),
        ):
            assert normalizer.normalize_search("test") == "test"


# ===========================================================================
# Converter fallbacks
# ===========================================================================
class TestConverterFallbacks:
    @patch.object(converter, "RE_INDIC_DIGITS")
    def test_indic_to_arabic_fallback(self, mock_re):
        mock_re.sub.side_effect = RuntimeError("boom")
        assert converter.indic_to_arabic("test") == "test"

    @patch.object(converter, "RE_ARABIC_DIGITS")
    def test_arabic_to_indic_fallback(self, mock_re):
        mock_re.sub.side_effect = RuntimeError("boom")
        assert converter.arabic_to_indic("test") == "test"


# ===========================================================================
# Analyzer fallbacks
# ===========================================================================
class TestAnalyzerFallbacks:
    @patch.object(analyzer, "_tokenize")
    def test_detect_dialect_fallback(self, mock_tok):
        mock_tok.side_effect = RuntimeError("boom")
        result = analyzer.detect_dialect("test")
        # Should return equal distribution
        assert len(result) == 4
        assert all(v > 0 for v in result.values())

    @patch.object(analyzer, "_tokenize")
    def test_extract_keywords_fallback(self, mock_tok):
        mock_tok.side_effect = RuntimeError("boom")
        result = analyzer.extract_keywords("test")
        assert result == []


# ===========================================================================
# Guardian fallback
# ===========================================================================
class TestGuardianFallback:
    @patch.object(guardian, "RE_SA_IBAN")
    def test_mask_sensitive_info_fallback(self, mock_re):
        mock_re.sub.side_effect = RuntimeError("boom")
        assert guardian.mask_sensitive_info("test") == "test"
