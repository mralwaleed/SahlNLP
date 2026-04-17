#!/usr/bin/env python3
"""
SahlNLP Performance Benchmark Suite.

Measures throughput (ops/sec) and latency (ms/op) for core functions
against naive Python regex implementations. No external dependencies.

Usage:
    python benchmarks/bench.py
"""

import re
import time
import statistics

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------
SAMPLE_CLEAN = "مَرْحَباً بـكـــــم في <b>موقعنا</b> https://example.com يرجى التواصل على 0551234567"
SAMPLE_NORMALIZE = "أحمد مُعَلِّمٌ في المدرسة الكبرى"
SAMPLE_KEYWORDS = (
    "الذكاء الاصطناعي هو فرع من علوم الحاسوب. الذكاء الاصطناعي مهم جداً في العصر الحديث. "
    "تطبيقات الذكاء الاصطناعي تشمل معالجة اللغات الطبيعية والرؤية الحاسوبية."
) * 5
SAMPLE_PII = (
    "السيد أحمد محمد رقمه 0551234567 وهويته 1234567890 "
    "والآيبان SA0380000000608010167519 والبريد user@example.com"
)
SAMPLE_DIALECT = "شلونك يا خوي وش مسوي الحين"
SAMPLE_TAfkeet_NUMBERS = [0, 7, 11, 42, 150, 999, 1001, 250000, 1000000]

# Naive regex (no pre-compilation, no deduplication)
_NAIVE_TASHKEEL = re.compile(r'[\u064B-\u065F]')
_NAIVE_TATWEEL = re.compile(r'\u0640+')


def _naive_clean(text: str) -> str:
    """Baseline: inline regex without pre-compilation or optimization."""
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\u0640+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text


# ---------------------------------------------------------------------------
# Benchmark harness
# ---------------------------------------------------------------------------
def _bench(func, *args, iterations: int = 10000, label: str = "") -> dict:
    """Run a function N times and return timing stats."""
    # Warmup
    for _ in range(100):
        func(*args)

    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        func(*args)
        times.append(time.perf_counter() - t0)

    ops_sec = iterations / sum(times)
    avg_ms = statistics.mean(times) * 1000
    med_ms = statistics.median(times) * 1000
    p95_ms = sorted(times)[int(0.95 * len(times))] * 1000

    return {
        "label": label,
        "iterations": iterations,
        "ops_sec": round(ops_sec),
        "avg_ms": round(avg_ms, 4),
        "med_ms": round(med_ms, 4),
        "p95_ms": round(p95_ms, 4),
    }


def _print_row(result: dict) -> None:
    print(
        f"  {result['label']:<40} "
        f"{result['ops_sec']:>10,} ops/s  "
        f"avg {result['avg_ms']:>8.4f} ms  "
        f"med {result['med_ms']:>8.4f} ms  "
        f"p95 {result['p95_ms']:>8.4f} ms"
    )


def main() -> None:
    import sahlnlp

    print("=" * 85)
    print("SahlNLP Performance Benchmark")
    print("=" * 85)
    print()

    # --- Cleaner ---
    print("CLEANER")
    print("-" * 85)
    r1 = _bench(sahlnlp.clean_all, SAMPLE_CLEAN, iterations=20000, label="clean_all()")
    r2 = _bench(_naive_clean, SAMPLE_CLEAN, iterations=20000, label="naive regex baseline")
    _print_row(r1)
    _print_row(r2)
    speedup = r1["ops_sec"] / max(r2["ops_sec"], 1)
    print(f"  >>> Speedup: {speedup:.2f}x vs naive regex")
    print()

    # --- Individual cleaners ---
    print("CLEANER (individual functions)")
    print("-" * 85)
    _print_row(_bench(sahlnlp.remove_tashkeel, SAMPLE_CLEAN, iterations=50000, label="remove_tashkeel()"))
    _print_row(_bench(sahlnlp.remove_tatweel, SAMPLE_CLEAN, iterations=50000, label="remove_tatweel()"))
    _print_row(_bench(sahlnlp.remove_html_and_links, SAMPLE_CLEAN, iterations=50000, label="remove_html_and_links()"))
    _print_row(_bench(sahlnlp.remove_repeated_chars, SAMPLE_CLEAN, iterations=50000, label="remove_repeated_chars()"))
    print()

    # --- Normalizer ---
    print("NORMALIZER")
    print("-" * 85)
    _print_row(_bench(sahlnlp.normalize_hamza, SAMPLE_NORMALIZE, iterations=50000, label="normalize_hamza()"))
    _print_row(_bench(sahlnlp.normalize_taa, SAMPLE_NORMALIZE, iterations=50000, label="normalize_taa()"))
    _print_row(_bench(sahlnlp.normalize_yaa, SAMPLE_NORMALIZE, iterations=50000, label="normalize_yaa()"))
    _print_row(_bench(sahlnlp.normalize_search, SAMPLE_NORMALIZE, iterations=20000, label="normalize_search()"))
    print()

    # --- Converter ---
    print("CONVERTER (number to words)")
    print("-" * 85)
    _print_row(_bench(sahlnlp.indic_to_arabic, "٣ أبريل ٢٠٢٥", iterations=50000, label="indic_to_arabic()"))
    _print_row(_bench(sahlnlp.arabic_to_indic, "3 أبريل 2025", iterations=50000, label="arabic_to_indic()"))
    for n in SAMPLE_TAfkeet_NUMBERS:
        _print_row(_bench(sahlnlp.tafkeet, n, iterations=10000, label=f"tafkeet({n:>10,})"))
    print()

    # --- Analyzer ---
    print("ANALYZER")
    print("-" * 85)
    _print_row(_bench(sahlnlp.detect_dialect, SAMPLE_DIALECT, iterations=10000, label="detect_dialect()"))
    _print_row(_bench(sahlnlp.extract_keywords, SAMPLE_KEYWORDS, iterations=2000, label="extract_keywords()"))
    _print_row(
        _bench(sahlnlp.suggest_correction, "مدرية", ["مدرسة", "مدينة", "مربية"], iterations=10000,
               label="suggest_correction()")
    )
    print()

    # --- Guardian ---
    print("GUARDIAN (PII Masking)")
    print("-" * 85)
    _print_row(_bench(sahlnlp.mask_sensitive_info, SAMPLE_PII, iterations=10000,
                       label="mask_sensitive_info(tag)"))
    _print_row(_bench(sahlnlp.mask_sensitive_info, SAMPLE_PII, iterations=10000,
                       label="mask_sensitive_info(mask)", ))
    print()

    print("=" * 85)
    print("Benchmark complete. Zero external dependencies used.")


if __name__ == "__main__":
    main()
