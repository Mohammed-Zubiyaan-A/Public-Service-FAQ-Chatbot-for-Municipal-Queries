"""Session-Based Conversation Memory Subsystem.

Maintains session-level conversation history and structured context variables
(zone, service, permit_type, previous_intent) across user turns.
Supports context resolution for follow-ups, explicit context switching,
topic transitions, and session clearing.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SessionContext:
    """Structured context variables for a single conversation session."""
    session_id: str
    service: Optional[str] = None
    zone: Optional[str] = None
    permit_type: Optional[str] = None
    event_name: Optional[str] = None
    date: Optional[str] = None
    previous_intent: Optional[str] = None
    last_retrieved_records: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "service": self.service,
            "zone": self.zone,
            "permit_type": self.permit_type,
            "event_name": self.event_name,
            "date": self.date,
            "previous_intent": self.previous_intent,
        }


class SessionMemoryManager:
    """In-memory session store managing multi-turn conversation states."""

    def __init__(self, max_history_turns: int = 5) -> None:
        self.max_history_messages = max_history_turns * 2
        self._contexts: Dict[str, SessionContext] = {}
        self._histories: Dict[str, List[Dict[str, str]]] = {}

    def get_or_create_session(self, session_id: str) -> SessionContext:
        """Retrieve existing session context or create a new one."""
        if session_id not in self._contexts:
            self._contexts[session_id] = SessionContext(session_id=session_id)
            self._histories[session_id] = []
        return self._contexts[session_id]

    def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get structured context dictionary for a session."""
        ctx = self.get_or_create_session(session_id)
        return ctx.to_dict()

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get recent message history for a session."""
        if session_id not in self._histories:
            self._histories[session_id] = []
        return list(self._histories[session_id])

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Append user or assistant message to session history with sliding window limit."""
        if session_id not in self._histories:
            self._histories[session_id] = []

        self._histories[session_id].append({"role": role, "content": content})

        # Trim history to sliding window size
        if len(self._histories[session_id]) > self.max_history_messages:
            self._histories[session_id] = self._histories[session_id][-self.max_history_messages:]

        if session_id in self._contexts:
            self._contexts[session_id].updated_at = time.time()

    def update_context(
        self,
        session_id: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        retrieved_records: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update session variables with context switching and topic transition rules."""
        ctx = self.get_or_create_session(session_id)
        entities = entities or {}

        # Topic transition logic: If switching between major domains, clear conflicting entities
        if intent and intent != ctx.previous_intent:
            if intent in ("permit_information", "permit_requirements") and ctx.previous_intent == "waste_collection":
                ctx.zone = None
                ctx.service = None
            elif intent == "waste_collection" and ctx.previous_intent in ("permit_information", "permit_requirements"):
                ctx.permit_type = None

        # Update intent
        if intent and intent not in ("unknown", "greeting"):
            ctx.previous_intent = intent

        # Context switching: new explicit entities override previous values
        if "zone" in entities and entities["zone"]:
            ctx.zone = entities["zone"]

        if "permit_type" in entities and entities["permit_type"]:
            ctx.permit_type = entities["permit_type"]

        if "service" in entities and entities["service"]:
            ctx.service = entities["service"]

        if retrieved_records is not None:
            ctx.last_retrieved_records = retrieved_records

        ctx.updated_at = time.time()

    def clear_session(self, session_id: str) -> None:
        """Reset conversation history and session context completely."""
        if session_id in self._contexts:
            del self._contexts[session_id]
        if session_id in self._histories:
            del self._histories[session_id]

    def format_history_for_prompt(self, session_id: str) -> str:
        """Format recent conversation history as readable text for LLM context."""
        history = self.get_history(session_id)
        if not history:
            return "No previous conversation."

        lines = []
        for msg in history:
            speaker = "Citizen" if msg["role"] == "user" else "Assistant"
            lines.append(f"{speaker}: {msg['content']}")
        return "\n".join(lines)
