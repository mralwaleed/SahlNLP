"""
Zero-dependency Arabic dialect classification — real machine learning,
implemented entirely in pure Python (no numpy / sklearn / torch).

Two classifiers:
  - **Multinomial Naive Bayes** (closed-form, probabilistic, fast).
  - **Multinomial Logistic Regression** (softmax + gradient descent).

Features: character n-grams (2–4) capture sub-word dialectal patterns —
verb endings, prefixes, pronouns, particles — that distinguish dialects.

The model is trained offline on a bundled corpus (utils/dialect_corpus.py)
and the learned weights are shipped as data, keeping import instant and
the library dependency-free.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

# ─── feature extraction ────────────────────────────────────────────────── #

_NGRAM_SIZES = (2, 3, 4)


def extract_features(text: str) -> Counter:
    """Extract character n-gram features from normalised Arabic text."""
    # strip diacritics + tatweel + normalise whitespace
    t = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    t = re.sub(r"\u0640", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    # pad for boundary n-grams
    t = f" {t} "
    feats: Counter = Counter()
    for n in _NGRAM_SIZES:
        for i in range(len(t) - n + 1):
            feats[t[i : i + n]] += 1
    return feats


# ─── Multinomial Naive Bayes ───────────────────────────────────────────── #

class NaiveBayesClassifier:
    """Multinomial Naive Bayes with Laplace smoothing, log-space, pure Python."""

    def __init__(self, classes: list[str]):
        self.classes = classes
        self.class_doc_counts: dict[str, int] = {c: 0 for c in classes}
        self.class_feature_counts: dict[str, Counter] = {c: Counter() for c in classes}
        self.class_total: dict[str, int] = {c: 0 for c in classes}
        self.vocab: set[str] = set()
        self.total_docs = 0

    def train(self, samples: list[tuple[str, str]]) -> None:
        for text, label in samples:
            feats = extract_features(text)
            self.class_doc_counts[label] += 1
            self.total_docs += 1
            for f, c in feats.items():
                self.class_feature_counts[label][f] += c
                self.class_total[label] += c
                self.vocab.add(f)

    def predict(self, text: str) -> dict[str, float]:
        feats = extract_features(text)
        V = len(self.vocab)
        log_probs: dict[str, float] = {}
        for c in self.classes:
            lp = math.log(self.class_doc_counts[c] / self.total_docs) if self.total_docs else 0.0
            denom = self.class_total[c] + V
            for f, cnt in feats.items():
                fc = self.class_feature_counts[c].get(f, 0)
                lp += cnt * math.log((fc + 1) / denom)
            log_probs[c] = lp
        # softmax normalisation → probabilities summing to 1
        mx = max(log_probs.values())
        exps = {c: math.exp(lp - mx) for c, lp in log_probs.items()}
        s = sum(exps.values())
        return {c: round(v / s, 4) for c, v in exps.items()}

    def save(self, path: str | Path) -> None:
        data = {
            "classes": self.classes,
            "class_doc_counts": self.class_doc_counts,
            "class_feature_counts": {c: dict(self.class_feature_counts[c]) for c in self.classes},
            "class_total": self.class_total,
            "vocab": sorted(self.vocab),
            "total_docs": self.total_docs,
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "NaiveBayesClassifier":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        clf = cls(data["classes"])
        clf.class_doc_counts = data["class_doc_counts"]
        clf.class_feature_counts = {c: Counter(data["class_feature_counts"][c]) for c in data["classes"]}
        clf.class_total = data["class_total"]
        clf.vocab = set(data["vocab"])
        clf.total_docs = data["total_docs"]
        return clf


# ─── Logistic Regression (softmax + gradient descent) ──────────────────── #

class LogisticRegressionClassifier:
    """Softmax regression trained via full-batch gradient descent, pure Python.

    Sparse weight storage — only features that appear in training have weights.
    L2 regularisation prevents overfitting on small corpora.
    """

    def __init__(self, classes: list[str], lr: float = 0.5, iterations: int = 150, l2: float = 0.01):
        self.classes = classes
        self.lr = lr
        self.iterations = iterations
        self.l2 = l2
        self.weights: dict[str, dict[str, float]] = {c: {} for c in classes}
        self.bias: dict[str, float] = {c: 0.0 for c in classes}

    def train(self, samples: list[tuple[str, str]]) -> None:
        feats_list = [(extract_features(t), l) for t, l in samples]
        n = len(feats_list)
        for _it in range(self.iterations):
            grad_w: dict[str, dict[str, float]] = {c: {} for c in self.classes}
            grad_b: dict[str, float] = {c: 0.0 for c in self.classes}
            for feats, label in feats_list:
                # forward
                scores = {c: self.bias[c] for c in self.classes}
                for f, cnt in feats.items():
                    for c in self.classes:
                        w = self.weights[c].get(f)
                        if w:
                            scores[c] += w * cnt
                # softmax
                mx = max(scores.values())
                exps = {c: math.exp(scores[c] - mx) for c in self.classes}
                ssum = sum(exps.values())
                # gradient
                for c in self.classes:
                    err = exps[c] / ssum - (1.0 if c == label else 0.0)
                    grad_b[c] += err
                    gw = grad_w[c]
                    for f, cnt in feats.items():
                        gw[f] = gw.get(f, 0.0) + err * cnt
            # update (full-batch)
            inv_n = 1.0 / n
            for c in self.classes:
                wc = self.weights[c]
                for f, g in grad_w[c].items():
                    wc[f] = wc.get(f, 0.0) - self.lr * (g * inv_n + self.l2 * wc.get(f, 0.0))
                self.bias[c] -= self.lr * grad_b[c] * inv_n

    def predict(self, text: str) -> dict[str, float]:
        feats = extract_features(text)
        scores = {c: self.bias[c] for c in self.classes}
        for f, cnt in feats.items():
            for c in self.classes:
                w = self.weights[c].get(f)
                if w:
                    scores[c] += w * cnt
        mx = max(scores.values())
        exps = {c: math.exp(scores[c] - mx) for c in self.classes}
        s = sum(exps.values())
        return {c: round(v / s, 4) for c, v in exps.items()}

    def save(self, path: str | Path) -> None:
        data = {
            "classes": self.classes,
            "weights": self.weights,
            "bias": self.bias,
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "LogisticRegressionClassifier":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        clf = cls(data["classes"])
        clf.weights = data["weights"]
        clf.bias = data["bias"]
        return clf


# ─── evaluation ────────────────────────────────────────────────────────── #

def evaluate(
    clf, test_samples: list[tuple[str, str]]
) -> dict[str, object]:
    """Compute accuracy + per-class precision / recall / F1."""
    classes = clf.classes
    tp = {c: 0 for c in classes}
    fp = {c: 0 for c in classes}
    fn = {c: 0 for c in classes}
    correct = 0
    for text, gold in test_samples:
        scores = clf.predict(text)
        pred = max(scores, key=scores.get)
        if pred == gold:
            correct += 1
            tp[gold] += 1
        else:
            fp[pred] += 1
            fn[gold] += 1
    n = len(test_samples)
    metrics: dict[str, object] = {"accuracy": round(correct / n, 4) if n else 0.0}
    per_class: dict[str, dict[str, float]] = {}
    for c in classes:
        p = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) else 0.0
        r = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        per_class[c] = {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}
    metrics["per_class"] = per_class
    macro_f1 = sum(v["f1"] for v in per_class.values()) / len(classes)
    metrics["macro_f1"] = round(macro_f1, 4)
    return metrics


# ─── word-level helpers ────────────────────────────────────────────────── #

def _tokenize_words(text: str) -> list[str]:
    t = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)
    return re.findall(r"[^\s\W]+", t, flags=re.UNICODE)


def build_vocab(samples: list[tuple[str, str]], top_k: int = 250) -> dict[str, int]:
    """Build a word→index vocabulary from the top-k most frequent words."""
    counter: Counter = Counter()
    for text, _ in samples:
        counter.update(_tokenize_words(text))
    return {w: i for i, (w, _) in enumerate(counter.most_common(top_k))}


# ─── Neural Network (MLP + backprop, pure Python) ───────────────────────── #

class NeuralNetworkClassifier:
    """A multi-layer perceptron trained via backpropagation.

    Architecture: input (sparse word features) → hidden (sigmoid) → output
    (softmax).  All matrix operations use plain Python lists — no numpy,
    no torch.  Sparse forward pass iterates only over present features,
    keeping training fast even in pure Python.

    This is genuine deep learning from mathematical first principles:
    forward propagation, chain-rule backpropagation, and gradient descent
    — implemented entirely without ML frameworks.
    """

    def __init__(
        self,
        classes: list[str],
        vocab: dict[str, int],
        hidden: int = 24,
        lr: float = 0.3,
        iterations: int = 200,
        l2: float = 0.001,
    ):
        import random as _r
        rng = _r.Random(42)
        self.classes = classes
        self.vocab = vocab
        self.input_size = len(vocab)
        self.hidden = hidden
        self.output_size = len(classes)
        self.lr = lr
        self.iterations = iterations
        self.l2 = l2
        self.W1: list[list[float]] = [
            [rng.gauss(0, 0.1) for _ in range(hidden)] for _ in range(self.input_size)
        ]
        self.b1: list[float] = [0.0] * hidden
        self.W2: list[list[float]] = [
            [rng.gauss(0, 0.1) for _ in range(self.output_size)] for _ in range(hidden)
        ]
        self.b2: list[float] = [0.0] * self.output_size

    # ── forward ── #
    def _featurize(self, text: str) -> dict[int, int]:
        feats: dict[int, int] = {}
        for w in _tokenize_words(text):
            idx = self.vocab.get(w)
            if idx is not None:
                feats[idx] = feats.get(idx, 0) + 1
        return feats

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        return math.exp(x) / (1.0 + math.exp(x))

    def _forward(self, feats: dict[int, int]) -> tuple[list[float], list[float]]:
        hidden = [0.0] * self.hidden
        for j in range(self.hidden):
            s = self.b1[j]
            for i, cnt in feats.items():
                s += cnt * self.W1[i][j]
            hidden[j] = self._sigmoid(s)
        scores = [0.0] * self.output_size
        for c in range(self.output_size):
            s = self.b2[c]
            for j in range(self.hidden):
                s += hidden[j] * self.W2[j][c]
            scores[c] = s
        mx = max(scores)
        exps = [math.exp(s - mx) for s in scores]
        total = sum(exps)
        return hidden, [e / total for e in exps]

    # ── train ── #
    def train(self, samples: list[tuple[str, str]]) -> None:
        n = len(samples)
        feats_list = [(self._featurize(t), self.classes.index(l)) for t, l in samples]
        for _ in range(self.iterations):
            dW2 = [[0.0] * self.output_size for _ in range(self.hidden)]
            db2 = [0.0] * self.output_size
            db1 = [0.0] * self.hidden
            # sparse W1 grads: dict of (i,j) → float
            dW1: dict[tuple[int, int], float] = {}
            for feats, label_idx in feats_list:
                hidden, probs = self._forward(feats)
                dz2 = list(probs)
                dz2[label_idx] -= 1.0
                for j in range(self.hidden):
                    for c in range(self.output_size):
                        dW2[j][c] += dz2[c] * hidden[j]
                db2_c = db2
                for c in range(self.output_size):
                    db2_c[c] += dz2[c]
                for j in range(self.hidden):
                    da1 = 0.0
                    w2j = self.W2[j]
                    for c in range(self.output_size):
                        da1 += dz2[c] * w2j[c]
                    dz1 = da1 * hidden[j] * (1.0 - hidden[j])
                    db1[j] += dz1
                    for i, cnt in feats.items():
                        key = (i, j)
                        dW1[key] = dW1.get(key, 0.0) + dz1 * cnt
            inv_n = 1.0 / n
            for i in range(self.input_size):
                w1i = self.W1[i]
                for j in range(self.hidden):
                    g = dW1.get((i, j), 0.0) * inv_n
                    w1i[j] -= self.lr * (g + self.l2 * w1i[j])
            for j in range(self.hidden):
                self.b1[j] -= self.lr * db1[j] * inv_n
                w2j = self.W2[j]
                dw2j = dW2[j]
                for c in range(self.output_size):
                    w2j[c] -= self.lr * (dw2j[c] * inv_n + self.l2 * w2j[c])
            for c in range(self.output_size):
                self.b2[c] -= self.lr * db2[c] * inv_n

    # ── predict ── #
    def predict(self, text: str) -> dict[str, float]:
        feats = self._featurize(text)
        _, probs = self._forward(feats)
        return {c: round(probs[i], 4) for i, c in enumerate(self.classes)}

    # ── save / load ── #
    def save(self, path: str | Path) -> None:
        data = {
            "classes": self.classes,
            "vocab": self.vocab,
            "hidden": self.hidden,
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "NeuralNetworkClassifier":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        clf = cls(data["classes"], data["vocab"], data["hidden"])
        clf.W1 = data["W1"]
        clf.b1 = data["b1"]
        clf.W2 = data["W2"]
        clf.b2 = data["b2"]
        return clf
