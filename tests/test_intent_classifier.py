import pytest
from ai.retrieval.intent_classifier import IntentClassifier, QueryIntent


def test_intent_classification_product_standard():
    res = IntentClassifier.classify_intent("Which BIS standard covers ceiling fans?")
    assert res["intent"] == QueryIntent.PRODUCT_STANDARD.value


def test_intent_classification_technical_value():
    res = IntentClassifier.classify_intent("What is the minimum yield strength of Fe 500D grade rebar?")
    assert res["intent"] == QueryIntent.TECHNICAL_VALUE.value


def test_intent_classification_certification_qco():
    res = IntentClassifier.classify_intent("Is BIS certification mandatory under QCO for steel products?")
    assert res["intent"] == QueryIntent.CERTIFICATION_QCO.value


def test_intent_classification_laboratory():
    res = IntentClassifier.classify_intent("Which recognized laboratories can test cement samples?")
    assert res["intent"] == QueryIntent.LABORATORY.value


def test_intent_classification_clause():
    res = IntentClassifier.classify_intent("Explain clause 7.2.1 of IS 1786")
    assert res["intent"] == QueryIntent.CLAUSE_LOOKUP.value
