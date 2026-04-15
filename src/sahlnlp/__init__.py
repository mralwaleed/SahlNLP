"""
SahlNLP - A zero-dependency, ultra-fast Arabic NLP toolkit.

Provides text cleaning, normalization, number conversion, advanced
analysis utilities (dialect detection, keyword extraction, fuzzy matching),
and PII masking for Arabic text processing.

Quick Start::

    import sahlnlp

    # Clean text
    sahlnlp.clean_all("مَرْحَباً بالعالم")

    # Normalize for search
    sahlnlp.normalize_search("أحمد مُعَلِّمٌ في المدرسة")

    # Convert numbers to Arabic words
    sahlnlp.tafkeet(150)

    # Detect dialect
    sahlnlp.detect_dialect("شلونك يا خوي")

    # Extract keywords
    sahlnlp.extract_keywords("الذكاء الاصطناعي فرع مهم")

    # Fuzzy match
    sahlnlp.suggest_correction("مدرية", ["مدرسة", "مدينة"])

    # Mask PII
    sahlnlp.mask_sensitive_info("اتصل على 0551234567", mode="tag")
"""

__version__ = "0.4.0"

from sahlnlp.core.analyzer import (
    compute_idf,
    compute_tf,
    detect_dialect,
    extract_keywords,
    suggest_correction,
)
from sahlnlp.core.cleaner import (
    clean_all,
    remove_html_and_links,
    remove_repeated_chars,
    remove_tashkeel,
    remove_tatweel,
)
from sahlnlp.core.converter import arabic_to_indic, indic_to_arabic, tafkeet
from sahlnlp.core.guardian import mask_sensitive_info
from sahlnlp.core.normalizer import (
    normalize_hamza,
    normalize_search,
    normalize_taa,
    normalize_yaa,
)

__all__ = [
    # Cleaner
    "clean_all",
    "remove_tashkeel",
    "remove_tatweel",
    "remove_html_and_links",
    "remove_repeated_chars",
    # Normalizer
    "normalize_hamza",
    "normalize_taa",
    "normalize_yaa",
    "normalize_search",
    # Converter
    "indic_to_arabic",
    "arabic_to_indic",
    "tafkeet",
    # Analyzer
    "detect_dialect",
    "extract_keywords",
    "suggest_correction",
    "compute_tf",
    "compute_idf",
    # Guardian (PII)
    "mask_sensitive_info",
]
