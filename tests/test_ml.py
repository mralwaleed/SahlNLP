"""Tests for the generic, dependency-free text classifiers."""

import math

from sahlnlp.core.ml import (
    LogisticRegressionClassifier,
    NaiveBayesClassifier,
    NeuralNetworkClassifier,
    build_vocab,
    evaluate,
    extract_features,
)

SAMPLES = [
    ("الخدمة ممتازة وسريعة", "positive"),
    ("المنتج رائع", "positive"),
    ("الخدمة سيئة وبطيئة", "negative"),
    ("المنتج رديء", "negative"),
]
CLASSES = ["positive", "negative"]


def assert_probability_scores(scores):
    assert set(scores) == set(CLASSES)
    assert all(0 <= value <= 1 for value in scores.values())
    assert math.isclose(sum(scores.values()), 1.0, abs_tol=1e-3)


def test_extract_features_normalizes_arabic_text():
    features = extract_features("خِدْمَةٌ   ممتــــازة")
    assert features
    assert all(isinstance(feature, str) for feature in features)


def test_naive_bayes_train_predict_and_round_trip(tmp_path):
    model = NaiveBayesClassifier(CLASSES)
    model.train(SAMPLES)
    scores = model.predict("الخدمة ممتازة")
    assert_probability_scores(scores)
    assert scores["positive"] > scores["negative"]

    path = tmp_path / "naive-bayes.json"
    model.save(path)
    loaded = NaiveBayesClassifier.load(path)
    assert loaded.predict("الخدمة ممتازة") == scores


def test_logistic_regression_train_predict_and_round_trip(tmp_path):
    model = LogisticRegressionClassifier(CLASSES, iterations=5)
    model.train(SAMPLES)
    scores = model.predict("الخدمة ممتازة")
    assert_probability_scores(scores)

    path = tmp_path / "logistic-regression.json"
    model.save(path)
    loaded = LogisticRegressionClassifier.load(path)
    assert loaded.predict("الخدمة ممتازة") == scores


def test_evaluate_reports_accuracy_and_class_scores():
    model = NaiveBayesClassifier(CLASSES)
    model.train(SAMPLES)
    metrics = evaluate(model, SAMPLES)
    assert metrics["accuracy"] == 1.0
    assert set(metrics["per_class"]) == set(CLASSES)
    assert 0 <= metrics["macro_f1"] <= 1


def test_neural_network_train_predict_and_round_trip(tmp_path):
    vocab = build_vocab(SAMPLES)
    assert vocab
    model = NeuralNetworkClassifier(CLASSES, vocab, hidden=3, iterations=2)
    model.train(SAMPLES)
    scores = model.predict("الخدمة ممتازة")
    assert_probability_scores(scores)

    path = tmp_path / "neural-network.json"
    model.save(path)
    loaded = NeuralNetworkClassifier.load(path)
    assert loaded.predict("الخدمة ممتازة") == scores
