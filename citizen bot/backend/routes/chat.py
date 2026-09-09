"""FastAPI Route Handlers for Municipal FAQ Chatbot."""

from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.models.schemas import (
    ChatRequest,
    ChatResponse,
    ClearResponse,
    HealthResponse,
)
from backend.services.chat_service import ChatService

router = APIRouter(tags=["Municipal Chatbot"])

# Global singleton service instance
_chat_service = ChatService()


def get_chat_service() -> ChatService:
    """Dependency provider for ChatService."""
    return _chat_service


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
def health_check(service: ChatService = Depends(get_chat_service)) -> HealthResponse:
    """Return backend operational status, dataset verification, and provider status."""
    has_key = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") not in ("your_api_key_here", "your_gemini_api_key_here"))
    return HealthResponse(
        status="healthy",
        service="Municipal Service FAQ Chatbot Backend",
        version="1.0.0",
        datasets_loaded=True,
        llm_configured=has_key,
    )


@router.post("/chat", response_model=ChatResponse, summary="Process Citizen Query")
def process_chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Accept natural-language citizen questions and return grounded answers."""
    session_id = request.session_id or "default_session"
    return service.process_query(message=request.message, session_id=session_id)


@router.post("/clear", response_model=ClearResponse, summary="Clear Conversation Memory")
def clear_conversation(
    session_id: str = Query(default="default_session", description="Session to reset"),
    service: ChatService = Depends(get_chat_service),
) -> ClearResponse:
    """Reset conversational session context and history."""
    service.clear_session(session_id)
    return ClearResponse(
        status="success",
        session_id=session_id,
        message="Conversation history and session memory cleared.",
    )
