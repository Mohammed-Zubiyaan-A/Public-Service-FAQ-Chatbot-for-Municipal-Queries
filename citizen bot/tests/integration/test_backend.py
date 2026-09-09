"""Integration tests for FastAPI Backend endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["datasets_loaded"] is True
    assert "version" in data


def test_chat_waste_query(client):
    payload = {
        "message": "When is waste collected in Zone A?",
        "session_id": "integration_test_1",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["intent"] == "waste_collection"
    assert "Monday" in data["response"] or "Thursday" in data["response"]
    assert data["source_metadata"] is not None
    assert "Municipal" in data["source_metadata"]["source"]


def test_chat_empty_input(client):
    payload = {
        "message": "   ",
        "session_id": "integration_test_2",
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clarification_required"
    assert "Please enter a question" in data["response"]


def test_clear_endpoint(client):
    # Establish session
    client.post("/chat", json={"message": "When is waste collected in Zone A?", "session_id": "integration_clear_1"})

    # Clear session
    clear_res = client.post("/clear?session_id=integration_clear_1")
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "success"


def test_frontend_root_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Municipal Service Assistant" in response.text
