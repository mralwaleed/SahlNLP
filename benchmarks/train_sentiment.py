#!/usr/bin/env python3
"""
Train + evaluate Arabic sentiment classifiers (NB + LR + Neural Network).
"""
import json
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from sahlnlp.utils.sentiment_corpus import SENTIMENT_CORPUS
from sahlnlp.core.ml import (
    NaiveBayesClassifier,
    LogisticRegressionClassifier,
    NeuralNetworkClassifier,
    build_vocab,
    evaluate,
)


def main() -> None:
    random.seed(42)

    # ── stratified 80/20 split ──
    train: list[tuple[str, str]] = []
    test: list[tuple[str, str]] = []
    for label, sentences in SENTIMENT_CORPUS.items():
        shuffled = list(sentences)
        random.shuffle(shuffled)
        k = int(len(shuffled) * 0.8)
        train.extend((s, label) for s in shuffled[:k])
        test.extend((s, label) for s in shuffled[k:])

    random.shuffle(train)
    random.shuffle(test)
    classes = sorted(SENTIMENT_CORPUS.keys())
    print(f"Sentiment corpus: {len(train)} train, {len(test)} test, {len(classes)} classes\n")

    # ── Naive Bayes (char n-grams) ──
    nb = NaiveBayesClassifier(classes)
    nb.train(train)
    nb_m = evaluate(nb, test)

    # ── Logistic Regression (char n-grams) ──
    lr = LogisticRegressionClassifier(classes, lr=0.5, iterations=150, l2=0.01)
    lr.train(train)
    lr_m = evaluate(lr, test)

    # ── Neural Network (word features, from scratch) ──
    vocab = build_vocab(train, top_k=250)
    nn = NeuralNetworkClassifier(classes, vocab, hidden=24, lr=0.3, iterations=200, l2=0.001)
    nn.train(train)
    nn_m = evaluate(nn, test)

    # ── report ──
    print(f"Naive Bayes          accuracy={nb_m['accuracy']:.2%}  F1={nb_m['macro_f1']:.4f}")
    print(f"Logistic Regr.       accuracy={lr_m['accuracy']:.2%}  F1={lr_m['macro_f1']:.4f}")
    print(f"Neural Network       accuracy={nn_m['accuracy']:.2%}  F1={nn_m['macro_f1']:.4f}")

    models = [("NaiveBayes", nb, nb_m), ("LogisticRegression", lr, lr_m), ("NeuralNetwork", nn, nn_m)]
    best_name, best_model, best_m = max(models, key=lambda x: x[2]["accuracy"])

    print(f"\n▶ Best: {best_name}  ({best_m['accuracy']:.2%} accuracy)\n")
    print(f"{'Class':<12} {'Precision':>10} {'Recall':>8} {'F1':>8}")
    print("-" * 42)
    for c, m in best_m["per_class"].items():
        print(f"{c:<12} {m['precision']:>10.4f} {m['recall']:>8.4f} {m['f1']:>8.4f}")

    # ── save all models ──
    utils_dir = os.path.join(_SRC, "sahlnlp", "utils")
    nb.save(os.path.join(utils_dir, "sentiment_nb_model.json"))
    lr.save(os.path.join(utils_dir, "sentiment_lr_model.json"))
    nn.save(os.path.join(utils_dir, "sentiment_nn_model.json"))

    meta = {
        "best": best_name,
        "nb": {"accuracy": nb_m["accuracy"], "f1": nb_m["macro_f1"]},
        "lr": {"accuracy": lr_m["accuracy"], "f1": lr_m["macro_f1"]},
        "nn": {"accuracy": nn_m["accuracy"], "f1": nn_m["macro_f1"]},
        "train_size": len(train),
        "test_size": len(test),
        "vocab_size": len(vocab),
    }
    with open(os.path.join(utils_dir, "sentiment_model_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n✓ Models saved to src/sahlnlp/utils/")
    print(f"✓ Best: {best_name} shipped as default for analyze_sentiment()")


if __name__ == "__main__":
    main()
