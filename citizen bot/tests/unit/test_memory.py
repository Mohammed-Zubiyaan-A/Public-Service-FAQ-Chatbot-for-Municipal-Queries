"""Unit tests for Conversation Memory Subsystem."""

import pytest
from ai.memory.session_memory import SessionMemoryManager
from backend.services.chat_service import ChatService


@pytest.fixture
def memory():
    return SessionMemoryManager()


@pytest.fixture
def chat_service():
    return ChatService()


def test_basic_follow_up(chat_service):
    session_id = "test_memory_session_1"
    chat_service.clear_session(session_id)

    # First turn: establish zone and waste service
    res1 = chat_service.process_query("What are the waste collection days in Zone A?", session_id)
    assert res1.status == "success"
    assert "Zone A" in res1.response or "Monday" in res1.response

    # Second turn: follow-up asking for time without re-mentioning Zone A
    res2 = chat_service.process_query("What time?", session_id)
    assert res2.status == "success"
    assert "7:00 AM" in res2.response


def test_follow_up_day_query(chat_service):
    session_id = "test_memory_session_2"
    chat_service.clear_session(session_id)

    # Establish Zone A
    chat_service.process_query("When is garbage collected in Zone A?", session_id)

    # Ask about Friday (Zone A has Monday & Thursday, no Friday)
    res = chat_service.process_query("What about Friday?", session_id)
    assert res.status == "success"
    # Should clarify there is no Friday collection for Zone A
    assert "no scheduled" in res.response.lower() or "not" in res.response.lower()


def test_context_switching_zones(chat_service):
    session_id = "test_memory_session_3"
    chat_service.clear_session(session_id)

    # Start with Zone A
    chat_service.process_query("Tell me about waste collection in Zone A.", session_id)

    # Explicitly switch to Zone B
    res = chat_service.process_query("Actually, I mean Zone B.", session_id)
    assert res.status == "success"
    assert "Zone B" in res.response
    assert "Tuesday" in res.response or "Friday" in res.response

    # Verify context is now Zone B
    ctx = chat_service.memory.get_context(session_id)
    assert ctx["zone"] == "Zone B"


def test_topic_switching(chat_service):
    session_id = "test_memory_session_4"
    chat_service.clear_session(session_id)

    # Turn 1: Waste collection
    chat_service.process_query("When is waste collected in Zone A?", session_id)

    # Turn 2: Switch to Permits
    res = chat_service.process_query("What documents are needed for a building permit?", session_id)
    assert res.status == "success"
    assert "Building Permit" in res.response or "document" in res.response.lower()

    # Context should reflect permit type and not conflate with waste
    ctx = chat_service.memory.get_context(session_id)
    assert ctx["permit_type"] == "Building Permit"


def test_clear_conversation(chat_service):
    session_id = "test_memory_session_5"

    # Establish context
    chat_service.process_query("When is waste collected in Zone A?", session_id)
    assert chat_service.memory.get_context(session_id)["zone"] == "Zone A"

    # Clear conversation
    chat_service.clear_session(session_id)
    assert chat_service.memory.get_context(session_id)["zone"] is None
    assert len(chat_service.memory.get_history(session_id)) == 0

    # Asking follow-up now should prompt for zone rather than assuming Zone A
    res = chat_service.process_query("When is waste collected?", session_id)
    assert res.status == "clarification_required"
