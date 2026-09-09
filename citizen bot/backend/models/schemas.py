"""Pydantic schemas for the Municipal FAQ Chatbot API."""

from __future__ import annotations
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Citizen query payload."""
    message: str = Field(..., min_length=1, max_length=2000, description="Citizen query text")
    session_id: Optional[str] = Field(default="default_session", description="Unique session identifier")


class SourceMetadata(BaseModel):
    """Transparency provenance metadata."""
    source: str = Field(..., description="Source dataset or external service name")
    last_updated: Optional[str] = Field(default=None, description="Date or timeframe of data currency")
    data_type: Optional[str] = Field(default="synthetic_demo", description="Synthetic demo or live API label")


class ChatResponse(BaseModel):
    """Chatbot output response payload."""
    response: str = Field(..., description="Conversational, grounded response text")
    session_id: str = Field(..., description="Session identifier")
    intent: str = Field(..., description="Detected intent category")
    status: str = Field(..., description="'success', 'clarification_required', 'not_found', or 'error'")
    source_metadata: Optional[SourceMetadata] = Field(default=None, description="Source provenance details")


class HealthResponse(BaseModel):
    """Service health response."""
    status: str = "healthy"
    service: str = "Municipal FAQ Chatbot Backend"
    version: str = "1.0.0"
    datasets_loaded: bool = True
    llm_configured: bool = False


class ClearResponse(BaseModel):
    """Session reset response."""
    status: str = "success"
    session_id: str
    message: str = "Conversation history and session memory cleared."
