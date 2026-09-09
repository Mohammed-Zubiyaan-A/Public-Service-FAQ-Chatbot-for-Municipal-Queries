"""Unit tests for Intent Classification Subsystem."""

import pytest
from ai.retrieval.retriever import KnowledgeRetriever


@pytest.fixture
def retriever():
    return KnowledgeRetriever()


def test_intent_waste(retriever):
    queries = [
        "When is waste collected in Zone A?",
        "When does garbage get picked up?",
        "Where can I recycle glass bottles?",
        "How do I schedule bulky trash collection?",
    ]
    for q in queries:
        intent, conf = retriever.detect_intent(q)
        assert intent == "waste_collection"
        assert conf >= 0.7


def test_intent_permit(retriever):
    intent, conf = retriever.detect_intent("What documents are needed for a building permit?")
    assert intent in ("permit_requirements", "permit_information")
    assert conf >= 0.7

    intent, conf = retriever.detect_intent("What permits are available in the city?")
    assert intent == "permit_information"


def test_intent_event(retriever):
    queries = [
        "What events are happening this month?",
        "Tell me about the annual cultural festival",
        "When is the tree plantation drive?",
    ]
    for q in queries:
        intent, conf = retriever.detect_intent(q)
        assert intent == "event_lookup"
        assert conf >= 0.7


def test_intent_weather(retriever):
    queries = [
        "What is the weather today?",
        "Will it rain today?",
        "What is the temperature outside?",
        "Do I need an umbrella tomorrow?",
    ]
    for q in queries:
        intent, conf = retriever.detect_intent(q)
        assert intent == "weather"
        assert conf >= 0.8


def test_intent_office_and_services(retriever):
    intent, _ = retriever.detect_intent("What are the municipal office timings?")
    assert intent == "office_information"

    intent, _ = retriever.detect_intent("How do I report a pothole or water leak?")
    assert intent == "municipal_service"


def test_intent_unknown(retriever):
    queries = [
        "Who was the Roman Emperor in 117 AD?",
        "Can you write me a poem about quantum computers?",
        "Tell me stock market investment tips",
    ]
    for q in queries:
        intent, _ = retriever.detect_intent(q)
        assert intent == "unknown"
