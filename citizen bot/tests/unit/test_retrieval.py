"""Unit tests for Knowledge Retrieval Subsystem."""

import pytest
from ai.retrieval.retriever import KnowledgeRetriever


@pytest.fixture
def retriever():
    return KnowledgeRetriever()


def test_retrieve_waste_zone_a(retriever):
    result = retriever.retrieve("When is waste collected in Zone A?")
    assert result["status"] == "found"
    assert result["intent"] == "waste_collection"
    assert len(result["records"]) > 0
    record = result["records"][0]
    assert record["zone"] == "Zone A"
    assert "Monday" in record["days"]
    assert "Thursday" in record["days"]
    assert record["time"] == "7:00 AM"


def test_retrieve_waste_synonyms(retriever):
    queries = [
        "When does garbage get picked up in Zone A?",
        "What days do they collect rubbish in Zone A?",
        "Tell me about trash pickup in Zone A",
    ]
    for q in queries:
        result = retriever.retrieve(q)
        assert result["status"] == "found", f"Failed for query: {q}"
        assert result["records"][0]["zone"] == "Zone A"


def test_retrieve_waste_zone_b(retriever):
    result = retriever.retrieve("What is the garbage schedule for Zone B?")
    assert result["status"] == "found"
    record = result["records"][0]
    assert record["zone"] == "Zone B"
    assert "Tuesday" in record["days"]
    assert "Friday" in record["days"]


def test_retrieve_waste_ambiguity_no_zone(retriever):
    result = retriever.retrieve("When is waste collected?")
    assert result["status"] == "clarification_required"
    assert result["clarification_prompt"] is not None
    assert "Which zone" in result["clarification_prompt"]


def test_retrieve_permit_trade(retriever):
    result = retriever.retrieve("What documents are required for a commercial trade license?")
    assert result["status"] == "found"
    assert result["intent"] == "permit_requirements"
    record = result["records"][0]
    assert record["permit_type"] == "Commercial Trade License"
    assert len(record["required_documents"]) >= 3


def test_retrieve_permit_building(retriever):
    result = retriever.retrieve("How much does a building permit cost?")
    assert result["status"] == "found"
    record = result["records"][0]
    assert record["permit_type"] == "Building Permit"
    assert "fee" in record


def test_retrieve_event_clean_city(retriever):
    result = retriever.retrieve("Tell me about the Clean City campaign")
    assert result["status"] == "found"
    assert result["intent"] == "event_lookup"
    record = result["records"][0]
    assert "Swachh Bengaluru" in record["title"] or "Clean" in record["title"]
    assert "October 2" in record["date_display"]


def test_retrieve_service_suvidha_center(retriever):
    result = retriever.retrieve("What are the office hours for the Citizen Service Center?")
    assert result["status"] == "found"
    record = result["records"][0]
    assert "Citizen Service Center" in record["service_name"]
    assert "Monday to" in record["working_hours"]


def test_retrieve_unknown_query(retriever):
    result = retriever.retrieve("What is the municipal tax penalty on interstellar spaceships?")
    assert result["status"] == "not_found"
    assert len(result["records"]) == 0
