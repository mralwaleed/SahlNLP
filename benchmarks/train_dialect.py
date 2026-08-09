#!/usr/bin/env python3
"""
Train + evaluate the zero-dependency ML dialect classifier.

Trains both Naive Bayes and Logistic Regression on the bundled corpus,
evaluates on a held-out 20% split, and saves the learned weights so the
library can predict at runtime without re-training.

Run:  python benchmarks/train_dialect.py
"""
import json
import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_HERE, "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from sahlnlp.utils.dialect_corpus import DIALECT_CORPUS
from sahlnlp.core.ml import NaiveBayesClassifier, LogisticRegressionClassifier, evaluate


def main() -> None:
    random.seed(42)

    # ── stratified train/test split (80/20) ──
    train: list[tuple[str, str]] = []
    test: list[tuple[str, str]] = []
    for dialect, sentences in DIALECT_CORPUS.items():
        shuffled = list(sentences)
        random.shuffle(shuffled)
        k = int(len(shuffled) * 0.8)
        train.extend((s, dialect) for s in shuffled[:k])
        test.extend((s, dialect) for s in shuffled[k:])

    random.shuffle(train)
    random.shuffle(test)
    classes = sorted(DIALECT_CORPUS.keys())
    print(f"Corpus: {len(train)} train, {len(test)} test, {len(classes)} dialects\n")

    # ── train Naive Bayes ──
    nb = NaiveBayesClassifier(classes)
    nb.train(train)
    nb_m = evaluate(nb, test)

    # ── train Logistic Regression ──
    lr = LogisticRegressionClassifier(classes, lr=0.5, iterations=150, l2=0.01)
    lr.train(train)
    lr_m = evaluate(lr, test)

    # ── report ──
    print(f"Naive Bayes        accuracy={nb_m['accuracy']:.2%}  macro-F1={nb_m['macro_f1']:.4f}")
    print(f"Logistic Regr.     accuracy={lr_m['accuracy']:.2%}  macro-F1={lr_m['macro_f1']:.4f}")

    best_model, best_m, best_name = (
        (lr, lr_m, "LogisticRegression")
        if lr_m["accuracy"] >= nb_m["accuracy"]
        else (nb, nb_m, "NaiveBayes")
    )

    print(f"\n▶ Best: {best_name}  ({best_m['accuracy']:.2%} accuracy)\n")
    print(f"{'Dialect':<12} {'Precision':>10} {'Recall':>8} {'F1':>8}")
    print("-" * 42)
    for c, m in best_m["per_class"].items():
        print(f"{c:<12} {m['precision']:>10.4f} {m['recall']:>8.4f} {m['f1']:>8.4f}")

    # ── save models ──
    utils_dir = os.path.join(_SRC, "sahlnlp", "utils")
    nb_path = os.path.join(utils_dir, "dialect_nb_model.json")
    lr_path = os.path.join(utils_dir, "dialect_lr_model.json")
    nb.save(nb_path)
    lr.save(lr_path)

    meta = {
        "best": best_name,
        "nb_accuracy": nb_m["accuracy"],
        "nb_macro_f1": nb_m["macro_f1"],
        "lr_accuracy": lr_m["accuracy"],
        "lr_macro_f1": lr_m["macro_f1"],
        "test_size": len(test),
        "train_size": len(train),
    }
    meta_path = os.path.join(utils_dir, "dialect_model_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"\n✓ Saved: {os.path.relpath(nb_path)}")
    print(f"✓ Saved: {os.path.relpath(lr_path)}")
    print(f"✓ Saved: {os.path.relpath(meta_path)}")
    print(f"\nThe library now uses {best_name} for dialect detection —")
    print(f"shipped pre-trained, zero-dependency, no runtime training.")


if __name__ == "__main__":
    main()
