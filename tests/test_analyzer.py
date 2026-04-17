"""Tests for sahlnlp.core.analyzer module — dialect detection, TF-IDF, Levenshtein."""

import math

import pytest

from sahlnlp.core.analyzer import (
    _levenshtein_distance,
    _split_documents,
    compute_idf,
    compute_tf,
    detect_dialect,
    extract_keywords,
    suggest_correction,
)


# ===========================================================================
# Feature 1: Dialect Radar
# ===========================================================================
class TestDetectDialect:
    def test_gulf_sentence(self):
        result = detect_dialect("شلونك يا خوي شو مسوي")
        assert result["Gulf"] > 0.5

    def test_gulf_signature_words(self):
        result = detect_dialect("ماكو شي مو زين ياخي")
        assert result["Gulf"] > 0.8

    def test_levantine_sentence(self):
        result = detect_dialect("شو بعمل هيك يا زلمة")
        assert result["Levantine"] > 0.5

    def test_levantine_high_confidence(self):
        # Mixed input with one Gulf word — Levantine must still dominate
        result = detect_dialect("شلونك؟ منيح؟ والله كتير اشتقنا لك يا زلمة")
        assert result["Levantine"] > 0.85

    def test_levantine_signature_words(self):
        result = detect_dialect("هيك منيح ليش نحنا هلق")
        assert result["Levantine"] > 0.9

    def test_egyptian_sentence(self):
        result = detect_dialect("عاوز اروح ازاي عشان كده")
        assert result["Egyptian"] > 0.5

    def test_egyptian_signature_words(self):
        result = detect_dialect("مفيش مش عايز دلوقتي بتاع أوي")
        assert result["Egyptian"] > 0.9

    def test_maghrebi_sentence(self):
        result = detect_dialect("واش كيداير بزاف راهو")
        assert result["Maghrebi"] > 0.5

    def test_maghrebi_signature_words(self):
        result = detect_dialect("بزاف واش كيفاش علاش بصح")
        assert result["Maghrebi"] > 0.9

    def test_bigram_boost_egyptian(self):
        result = detect_dialect("عاوز اروح عامل ايه")
        assert result["Egyptian"] > 0.8

    def test_percentages_sum_to_one(self):
        result = detect_dialect("شلونك يا زلمة عشان كده بزاف")
        total = sum(result.values())
        assert abs(total - 1.0) < 1e-3, f"Percentages sum to {total}, expected 1.0"

    def test_all_values_between_zero_and_one(self):
        result = detect_dialect("شلونك يا زلمة عشان كده بزاف")
        for name, pct in result.items():
            assert 0.0 <= pct <= 1.0, f"{name}={pct} out of [0,1] range"

    def test_empty_string(self):
        result = detect_dialect("")
        total = sum(result.values())
        assert abs(total - 1.0) < 1e-6

    def test_no_markers_equal_distribution(self):
        result = detect_dialect("مرحبا بالعالم اليوم")
        values = list(result.values())
        assert all(abs(v - values[0]) < 1e-6 for v in values)

    def test_mixed_dialect(self):
        result = detect_dialect("شلونك يا زلمة بزاف")
        assert result["Gulf"] > 0.0
        assert result["Levantine"] > 0.0
        assert result["Maghrebi"] > 0.0

    def test_type_error(self):
        with pytest.raises(TypeError):
            detect_dialect(None)  # type: ignore[arg-type]

    def test_returns_four_dialects(self):
        result = detect_dialect("مرحبا")
        assert set(result.keys()) == {"Gulf", "Levantine", "Egyptian", "Maghrebi"}


# ===========================================================================
# Feature 2: TF-IDF Keyword Extraction
# ===========================================================================
class TestComputeTF:
    def test_basic_tf(self):
        tokens = ["كتاب", "كتاب", "قلم"]
        tf = compute_tf(tokens)
        assert abs(tf["كتاب"] - 2 / 3) < 1e-6
        assert abs(tf["قلم"] - 1 / 3) < 1e-6

    def test_single_token(self):
        tf = compute_tf(["حاسوب"])
        assert tf["حاسوب"] == 1.0

    def test_empty(self):
        assert compute_tf([]) == {}

    def test_all_unique(self):
        tokens = ["أ", "ب", "ت"]
        tf = compute_tf(tokens)
        for v in tf.values():
            assert abs(v - 1 / 3) < 1e-6


class TestComputeIDF:
    def test_idf_basic(self):
        docs = [["كتاب", "قلم"], ["كتاب", "حبر"]]
        idf = compute_idf(docs)
        # "كتاب" appears in 2/2 docs -> IDF = log(2/3)
        assert "كتاب" in idf
        assert idf["كتاب"] == math.log(2 / 3)

    def test_rare_term_high_idf(self):
        docs = [["كتاب"], ["قلم"], ["حبر"]]
        idf = compute_idf(docs)
        # Each term appears in 1/3 docs -> IDF = log(3/2)
        for term in idf:
            assert abs(idf[term] - math.log(3 / 2)) < 1e-6

    def test_empty_docs(self):
        assert compute_idf([]) == {}


class TestSplitDocuments:
    def test_split_on_period(self):
        docs = _split_documents("جملة أولى. جملة ثانية")
        assert len(docs) == 2

    def test_split_on_arabic_punct(self):
        docs = _split_documents("جملة أولى؟ جملة ثانية! جملة ثالثة")
        assert len(docs) == 3

    def test_empty_input(self):
        assert _split_documents("") == []

    def test_single_sentence(self):
        docs = _split_documents("جملة واحدة")
        assert len(docs) == 1


class TestExtractKeywords:
    def test_basic_extraction(self):
        text = "الذكاء الاصطناعي هو فرع من علوم الحاسوب. الذكاء الاصطناعي مهم جدا."
        keywords = extract_keywords(text, top_n=3)
        assert len(keywords) <= 3
        assert all(isinstance(k, tuple) and len(k) == 2 for k in keywords)

    def test_scores_descending(self):
        text = "الحاسوب الحاسوب الحاسوب البرمجة البيانات الحاسوب. البرمجة مهمة."
        keywords = extract_keywords(text, top_n=5)
        for i in range(len(keywords) - 1):
            assert keywords[i][1] >= keywords[i + 1][1]

    def test_stop_words_filtered(self):
        text = "من في على الى هل هو هي"
        keywords = extract_keywords(text, top_n=5)
        # All input is stop-words -> should return empty or very few
        assert len(keywords) == 0

    def test_empty_string(self):
        assert extract_keywords("") == []

    def test_top_n_validation(self):
        with pytest.raises(ValueError):
            extract_keywords("نص", top_n=0)

    def test_type_error(self):
        with pytest.raises(TypeError):
            extract_keywords(None)  # type: ignore[arg-type]

    def test_repeated_term_scores_high(self):
        # TF-IDF rewards discriminative terms (appearing in few docs).
        # "مهمة" only in doc1, "جديدة" only in doc2 -> high IDF.
        # "البيانات" in all docs -> low IDF (not discriminative).
        text = "البيانات البيانات البيانات مهمة. البيانات جديدة. البيانات كبيرة."
        keywords = extract_keywords(text, top_n=3)
        ranked_words = [kw[0] for kw in keywords]
        # Discriminative terms should rank higher than ubiquitous ones
        assert (
            "جديدة" in ranked_words
            or "كبيرة" in ranked_words
            or "مهمة" in ranked_words
        )


# ===========================================================================
# Feature 3: Levenshtein Fuzzy Matcher
# ===========================================================================
class TestLevenshteinDistance:
    def test_identical_strings(self):
        assert _levenshtein_distance("مدرسة", "مدرسة") == 0.0

    def test_single_substitution(self):
        assert _levenshtein_distance("مدرية", "مدرسة") == 1.0

    def test_single_deletion(self):
        assert _levenshtein_distance("مدرسسة", "مدرسة") == 1.0

    def test_single_insertion(self):
        assert _levenshtein_distance("مدرسة", "مدرسسة") == 1.0

    def test_completely_different(self):
        dist = _levenshtein_distance("abc", "xyz")
        assert dist == 3.0

    def test_empty_strings(self):
        assert _levenshtein_distance("", "") == 0.0

    def test_one_empty(self):
        assert _levenshtein_distance("abc", "") == 3.0
        assert _levenshtein_distance("", "abc") == 3.0

    def test_keyboard_adjacent_lower_penalty(self):
        # ب and ي are adjacent on Arabic keyboard row 2
        dist_adjacent = _levenshtein_distance("با", "يا", use_keyboard=True)
        dist_normal = _levenshtein_distance("با", "يا", use_keyboard=False)
        assert dist_adjacent < dist_normal


class TestSuggestCorrection:
    def test_common_typo_madrasa(self):
        result = suggest_correction("مدرية", ["مدرسة", "مدينة", "مربية"])
        assert result == "مدرسة"

    def test_common_typo_maktaba(self):
        result = suggest_correction("مكتية", ["مكتبة", "مكتب", "مكية"])
        assert result == "مكتبة"

    def test_exact_match(self):
        result = suggest_correction("مدرسة", ["مدرسة", "مدينة"])
        assert result == "مدرسة"

    def test_empty_dictionary_raises(self):
        with pytest.raises(ValueError):
            suggest_correction("كلمة", [])

    def test_type_error_word(self):
        with pytest.raises(TypeError):
            suggest_correction(None, ["كلمة"])  # type: ignore[arg-type]

    def test_type_error_dictionary(self):
        with pytest.raises(TypeError):
            suggest_correction("كلمة", "not a list")  # type: ignore[arg-type]

    def test_single_candidate(self):
        result = suggest_correction("كلمه", ["كلمة"])
        assert result == "كلمة"

    def test_keyboard_mode_toggle(self):
        dict_list = ["مدرسة", "مكتبة"]
        # Both should still find the closest match
        r1 = suggest_correction("مدرية", dict_list, use_keyboard=True)
        r2 = suggest_correction("مدرية", dict_list, use_keyboard=False)
        assert r1 == "مدرسة"
        assert r2 == "مدرسة"

    def test_insertion_error(self):
        result = suggest_correction("كتابا", ["كتاب", "كاتب"])
        assert result == "كتاب"
