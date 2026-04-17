"""
Advanced Arabic text analysis algorithms.

Provides dialect detection, keyword extraction (TF-IDF), and fuzzy matching
(Levenshtein distance) — all built from scratch with zero external dependencies.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from sahlnlp.utils.logger import logger
from sahlnlp.utils.dictionaries import (
    ALL_DIALECTS,
    KEYBOARD_NEIGHBORS,
    STOP_WORDS,
)


# ---------------------------------------------------------------------------
# Feature 1: Dialect Radar
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    # Remove diacritics, tatweel, and split on non-word chars
    text = re.sub(r'[\u064B-\u065F]', '', text)  # remove tashkeel
    text = re.sub(r'\u0640', '', text)             # remove tatweel
    tokens = re.findall(r'[^\s\W]+', text, flags=re.UNICODE)
    return [t for t in tokens if t]


def detect_dialect(text: str) -> dict[str, float]:
    """Detect the most likely Arabic dialect in the text using weighted lexicons.

    Tokenizes the input, cross-references each token against dialect dictionaries,
    tallies weighted scores, and returns normalized percentages.

    Args:
        text: The input Arabic text (any dialect).

    Returns:
        A dictionary mapping dialect names to likelihood percentages (0.0-1.0).
        Values sum to 1.0. Returns equal distribution for text with no markers.

    Examples:
        >>> detect_dialect("شلونك يا خوي")
        {'Gulf': 1.0, 'Levantine': 0.0, 'Egyptian': 0.0, 'Maghrebi': 0.0}
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    try:
        tokens = _tokenize(text)

        scores: dict[str, float] = {name: 0.0 for name in ALL_DIALECTS}

        # Also check bigrams (2-word phrases) for multi-word markers
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        search_tokens = tokens + bigrams

        for token in search_tokens:
            for dialect_name, dialect_dict in ALL_DIALECTS.items():
                if token in dialect_dict:
                    scores[dialect_name] += dialect_dict[token]

        total = sum(scores.values())

        if total == 0:
            # No dialect markers found — return equal distribution
            equal = 1.0 / len(ALL_DIALECTS)
            return {name: round(equal, 4) for name in ALL_DIALECTS}

        return {name: round(score / total, 4) for name, score in scores.items()}
    except Exception:
        logger.warning("detect_dialect failed, returning equal distribution")
        equal = 1.0 / len(ALL_DIALECTS)
        return {name: round(equal, 4) for name in ALL_DIALECTS}


# ---------------------------------------------------------------------------
# Feature 2: TF-IDF Keyword Extractor
# ---------------------------------------------------------------------------

def _split_documents(text: str) -> list[str]:
    """Split text into pseudo-documents (sentences/clauses) for IDF calculation."""
    # Split on sentence-ending punctuation
    docs = re.split(r'[.!?؟。،\n]+', text)
    return [d.strip() for d in docs if d.strip()]


def compute_tf(tokens: list[str]) -> dict[str, float]:
    """Compute term frequency for a list of tokens.

    TF(t) = count(t) / total_tokens

    Args:
        tokens: List of word tokens.

    Returns:
        Dictionary mapping each term to its TF score.
    """
    if not tokens:
        return {}
    counter = Counter(tokens)
    total = len(tokens)
    return {term: count / total for term, count in counter.items()}


def compute_idf(documents: list[list[str]]) -> dict[str, float]:
    """Compute inverse document frequency across documents.

    IDF(t) = log(N / (1 + df(t)))

    Args:
        documents: List of tokenized documents.

    Returns:
        Dictionary mapping each term to its IDF score.
    """
    n = len(documents)
    if n == 0:
        return {}

    df: dict[str, int] = {}
    for doc in documents:
        seen = set(doc)
        for term in seen:
            df[term] = df.get(term, 0) + 1

    return {
        term: math.log(n / (1 + freq))
        for term, freq in df.items()
    }


def extract_keywords(text: str, top_n: int = 5) -> list[tuple[str, float]]:
    """Extract the top keywords from Arabic text using TF-IDF.

    Treats punctuation-separated clauses as "documents" for IDF.
    Filters out common Arabic stop-words.

    Args:
        text: The input Arabic text.
        top_n: Number of top keywords to return (default 5).

    Returns:
        Sorted list of (keyword, tfidf_score) tuples, highest first.

    Examples:
        >>> extract_keywords("الذكاء الاصطناعي هو فرع من علوم الحاسوب", top_n=3)
        [('الحاسوب', ...), ('علوم', ...), ('الذكاء', ...)]
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    if top_n < 1:
        raise ValueError("top_n must be >= 1")

    try:
        # Split into pseudo-documents
        raw_docs = _split_documents(text)
        if not raw_docs:
            return []

        # Tokenize each document and filter stop-words
        tokenized_docs: list[list[str]] = []
        all_tokens: list[str] = []

        for doc in raw_docs:
            tokens = _tokenize(doc)
            filtered = [t for t in tokens if t not in STOP_WORDS]
            if filtered:
                tokenized_docs.append(filtered)
                all_tokens.extend(filtered)

        if not all_tokens:
            return []

        # Compute TF over the entire text
        tf = compute_tf(all_tokens)

        # Compute IDF across pseudo-documents
        idf = compute_idf(tokenized_docs)

        # Compute TF-IDF
        tfidf = {
            term: tf[term] * idf.get(term, 0.0)
            for term in tf
            if term in idf
        }

        # Sort by score descending, then alphabetically for ties
        ranked = sorted(tfidf.items(), key=lambda x: (-x[1], x[0]))

        return ranked[:top_n]
    except Exception:
        logger.warning("extract_keywords failed, returning empty list")
        return []


# ---------------------------------------------------------------------------
# Feature 3: Levenshtein Distance Fuzzy Matcher
# ---------------------------------------------------------------------------

def _levenshtein_distance(s1: str, s2: str, use_keyboard: bool = False) -> float:
    """Compute Levenshtein distance between two strings.

    Optionally applies Arabic keyboard proximity penalties for substitutions.

    Args:
        s1: First string.
        s2: Second string.
        use_keyboard: If True, reduce substitution cost for adjacent keyboard keys.

    Returns:
        The edit distance (float when keyboard penalties are used).
    """
    m, n = len(s1), len(s2)

    # DP matrix
    dp: list[list[float]] = [[0.0] * (n + 1) for _ in range(m + 1)]

    # Base cases
    for i in range(m + 1):
        dp[i][0] = float(i)
    for j in range(n + 1):
        dp[0][j] = float(j)

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0.0
            elif use_keyboard and s1[i - 1] in KEYBOARD_NEIGHBORS:
                if s2[j - 1] in KEYBOARD_NEIGHBORS.get(s1[i - 1], frozenset()):
                    cost = 0.3  # Adjacent key: reduced penalty
                else:
                    cost = 1.0
            else:
                cost = 1.0

            dp[i][j] = min(
                dp[i - 1][j] + 1.0,       # deletion
                dp[i][j - 1] + 1.0,       # insertion
                dp[i - 1][j - 1] + cost,  # substitution
            )

    return dp[m][n]


def suggest_correction(
    word: str,
    dictionary: list[str],
    use_keyboard: bool = True,
) -> str:
    """Find the closest matching word from a dictionary using Levenshtein distance.

    Uses dynamic programming edit distance with optional Arabic keyboard
    proximity penalties (adjacent keys get reduced substitution cost).

    Args:
        word: The potentially misspelled word.
        dictionary: A list of candidate words to match against.
        use_keyboard: Apply Arabic keyboard proximity penalties (default True).

    Returns:
        The closest matching word from the dictionary.

    Raises:
        ValueError: If the dictionary is empty.

    Examples:
        >>> suggest_correction("مدرية", ["مدرسة", "مدينة", "مربية"])
        'مدرسة'
    """
    if not isinstance(word, str):
        raise TypeError(f"Expected str for word, got {type(word).__name__}")
    if not isinstance(dictionary, list):
        raise TypeError(f"Expected list for dictionary, got {type(dictionary).__name__}")
    if not dictionary:
        raise ValueError("Dictionary cannot be empty")

    best_word = dictionary[0]
    best_dist = float('inf')

    for candidate in dictionary:
        dist = _levenshtein_distance(word, candidate, use_keyboard=use_keyboard)
        if dist < best_dist:
            best_dist = dist
            best_word = candidate

    return best_word
