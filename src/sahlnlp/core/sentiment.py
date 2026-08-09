"""
Arabic sentiment analysis — lexicon-based scorer with negation handling.

Scores text by matching tokens against a curated positive/negative lexicon
with 3-tier weights (1 mild · 2 moderate · 3 strong). Negation particles
within a 2-token window flip polarity (e.g. "مو زين" → negative).

Zero-dependency, O(n), instant prediction — no models to load.

>>> analyze_sentiment("المنتج رائع والخدمة ممتازة")
{'label': 'positive', 'positive': 0.95, 'negative': 0.0, 'neutral': 0.05}
>>> analyze_sentiment("جودة سيئة وتأخر التوصيل")
{'label': 'negative', ...}
>>> analyze_sentiment("الطلب وصل اليوم")
{'label': 'neutral', ...}
"""

from __future__ import annotations

import re

from sahlnlp.utils.sentiment_lexicon import NEGATIVE_WORDS, POSITIVE_WORDS

_NEGATION: frozenset[str] = frozenset({
    "لا", "ما", "مش", "مو", "غير", "ليس", "ليست", "ليسوا",
    "بدون", "مستحيل", "أبداً", "ابدا", "ممنوع", "حرام",
})


def _tokenize(text: str) -> list[str]:
    t = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)
    return re.findall(r"[^\s\W]+", t, flags=re.UNICODE)


def analyze_sentiment(text: str) -> dict[str, object]:
    """Analyse the sentiment of Arabic text.

    Returns a dict with ``label`` (``"positive"`` | ``"negative"`` |
    ``"neutral"``) and probability scores that sum to 1.0.

    Uses a curated lexicon with 3-tier weights and a 2-token negation
    window. A Laplace-style neutral pseudo-count ensures neutral > 0
    even when strong sentiment is present.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    tokens = _tokenize(text)
    pos_score = 0.0
    neg_score = 0.0

    for i, tok in enumerate(tokens):
        w_pos = POSITIVE_WORDS.get(tok, 0)
        w_neg = NEGATIVE_WORDS.get(tok, 0)

        # check negation in the previous 2 tokens
        negated = any(tokens[j] in _NEGATION for j in range(max(0, i - 2), i))

        if negated:
            pos_score += w_neg
            neg_score += w_pos
        else:
            pos_score += w_pos
            neg_score += w_neg

    # Laplace-style neutral pseudo-count: +1 ensures neutral > 0
    total = pos_score + neg_score + 1.0
    positive = pos_score / total
    negative = neg_score / total
    neutral = 1.0 / total

    probs = {"positive": positive, "negative": negative, "neutral": neutral}
    label = max(probs, key=probs.get)

    return {
        "label": label,
        "positive": round(positive, 4),
        "negative": round(negative, 4),
        "neutral": round(neutral, 4),
        "score": round(pos_score - neg_score, 4),
    }
