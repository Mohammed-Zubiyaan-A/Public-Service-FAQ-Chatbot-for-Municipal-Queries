"""Chat Service Orchestration Subsystem.

Connects:
    Citizen Query -> Session Memory -> Knowledge Retrieval -> Public Weather API -> Context Builder -> Gemini LLM -> Grounded Output.
Implements the core architectural pipeline:
    Retrieve first, generate second.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ai.llm.gemini import GeminiProvider
from ai.llm.provider import LLMProvider
from ai.memory.session_memory import SessionMemoryManager
from ai.retrieval.retriever import KnowledgeRetriever
from api.weather import WeatherService
from backend.models.schemas import ChatResponse, SourceMetadata

logger = logging.getLogger(__name__)


class ChatService:
    """Coordinates multi-turn dialogue, retrieval, external APIs, and LLM responses."""

    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        memory: Optional[SessionMemoryManager] = None,
        llm: Optional[LLMProvider] = None,
        weather: Optional[WeatherService] = None,
        prompt_path: Optional[str] = None,
    ) -> None:
        self.retriever = retriever or KnowledgeRetriever()
        self.memory = memory or SessionMemoryManager()
        self.llm = llm or GeminiProvider()
        self.weather = weather or WeatherService()

        # Load system prompt
        if prompt_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self.prompt_path = project_root / "ai" / "prompts" / "system_prompt.txt"
        else:
            self.prompt_path = Path(prompt_path)

        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Safely load system prompt template from disk."""
        if self.prompt_path.exists():
            try:
                with open(self.prompt_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                logger.warning("Could not load system prompt file: %s", e)
        return (
            "You are the Municipal Service Assistant. Ground all answers in the "
            "provided municipal or API context. Do not invent municipal policies or facts."
        )

    def process_query(self, message: str, session_id: str = "default_session") -> ChatResponse:
        """Process a citizen query end-to-end and return a validated response."""
        clean_query = message.strip()
        if not clean_query:
            return ChatResponse(
                response="Please enter a question about municipal services, waste collection, permits, events, or weather.",
                session_id=session_id,
                intent="unknown",
                status="clarification_required",
            )

        try:
            # 1. Retrieve session context & previous conversation history
            session_context = self.memory.get_context(session_id)
            conversation_history = self.memory.format_history_for_prompt(session_id)

            # 2. Check for explicit topic change in query
            # If user says "Actually, Zone B" or "Actually, permits"
            if clean_query.lower().startswith("actually") or "switch to" in clean_query.lower():
                # Let retrieval treat this fresh with updated entity
                pass

            # 3. Execute knowledge retrieval
            retrieval_res = self.retriever.retrieve(clean_query, context=session_context)
            intent = retrieval_res.get("intent", "unknown")
            entities = retrieval_res.get("entities", {})
            status = retrieval_res.get("status", "not_found")
            records = retrieval_res.get("records", [])

            # 4. Handle Weather queries (Dynamic Public API)
            if intent == "weather":
                timeframe = "tomorrow" if "tomorrow" in clean_query.lower() else "today"
                weather_res = self.weather.get_weather(timeframe=timeframe)

                if weather_res.get("status") == "success":
                    weather_summary = weather_res.get("summary_text", "")
                    prompt = self._build_prompt(
                        user_query=clean_query,
                        history=conversation_history,
                        api_data=weather_summary,
                    )
                    response_text = self.llm.generate_response(prompt, self.system_prompt)
                    source_meta = SourceMetadata(
                        source="Open-Meteo Public Weather API",
                        last_updated="Live data",
                        data_type="live_api",
                    )
                else:
                    response_text = (
                        "I couldn't retrieve the latest weather information right now. "
                        "Please try again in a few moments."
                    )
                    source_meta = SourceMetadata(
                        source="Open-Meteo Public Weather API",
                        last_updated="Unavailable",
                        data_type="live_api",
                    )

                self.memory.add_message(session_id, "user", clean_query)
                self.memory.add_message(session_id, "assistant", response_text)
                self.memory.update_context(session_id, intent="weather")

                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    intent=intent,
                    status="success" if weather_res.get("status") == "success" else "error",
                    source_metadata=source_meta,
                )

            # 5. Handle Clarification Required
            if status == "clarification_required":
                clarification_msg = retrieval_res.get("clarification_prompt", "Could you please specify more details for your request?")
                self.memory.add_message(session_id, "user", clean_query)
                self.memory.add_message(session_id, "assistant", clarification_msg)
                self.memory.update_context(session_id, intent=intent, entities=entities)

                return ChatResponse(
                    response=clarification_msg,
                    session_id=session_id,
                    intent=intent,
                    status="clarification_required",
                    source_metadata=SourceMetadata(
                        source=retrieval_res.get("source", "Municipal Demonstration Dataset"),
                        last_updated=retrieval_res.get("last_updated", "2026-09-01"),
                        data_type="synthetic_demo",
                    ),
                )

            # 6. Handle Information Not Found (Unsupported / Unknown Query)
            if status == "not_found" or not records:
                prompt = self._build_prompt(
                    user_query=clean_query,
                    history=conversation_history,
                    retrieved_data="No relevant municipal records or public API data were found.",
                )
                response_text = self.llm.generate_response(prompt, self.system_prompt)
                self.memory.add_message(session_id, "user", clean_query)
                self.memory.add_message(session_id, "assistant", response_text)
                self.memory.update_context(session_id, intent="unknown")

                return ChatResponse(
                    response=response_text,
                    session_id=session_id,
                    intent="unknown",
                    status="not_found",
                    source_metadata=SourceMetadata(
                        source="Municipal Knowledge Base",
                        last_updated="2026-09-01",
                        data_type="synthetic_demo",
                    ),
                )

            # 7. Grounded Generation from Retrieved Municipal Records
            records_json_str = json.dumps(records, indent=2)
            prompt = self._build_prompt(
                user_query=clean_query,
                history=conversation_history,
                retrieved_data=records_json_str,
            )
            response_text = self.llm.generate_response(prompt, self.system_prompt)

            # 8. Update Memory with verified turn details
            self.memory.add_message(session_id, "user", clean_query)
            self.memory.add_message(session_id, "assistant", response_text)
            self.memory.update_context(
                session_id,
                intent=intent,
                entities=entities,
                retrieved_records=records,
            )

            source_meta = SourceMetadata(
                source=retrieval_res.get("source", "Municipal Demonstration Dataset"),
                last_updated=retrieval_res.get("last_updated", "2026-09-01"),
                data_type="synthetic_demo",
            )

            return ChatResponse(
                response=response_text,
                session_id=session_id,
                intent=intent,
                status="success",
                source_metadata=source_meta,
            )

        except Exception as e:
            logger.exception("Unexpected error in chat orchestration: %s", e)
            return ChatResponse(
                response="Sorry, I encountered an unexpected error processing your request. Please try again.",
                session_id=session_id,
                intent="unknown",
                status="error",
            )

    def _build_prompt(
        self,
        user_query: str,
        history: str = "No previous conversation.",
        retrieved_data: Optional[str] = None,
        api_data: Optional[str] = None,
    ) -> str:
        """Construct structured prompt adhering to architecture.md Section 17."""
        sections = []

        # Conversation History
        sections.append(f"CONVERSATION CONTEXT:\n{history}")

        # Retrieved Municipal Data
        if retrieved_data:
            sections.append(f"RETRIEVED MUNICIPAL INFORMATION:\n{retrieved_data}")

        # Public API Data
        if api_data:
            sections.append(f"PUBLIC API INFORMATION:\n{api_data}")

        # Current User Question
        sections.append(f"CURRENT USER QUESTION:\n{user_query}")

        return "\n\n".join(sections)

    def clear_session(self, session_id: str) -> bool:
        """Clear memory and reset context for a given session."""
        self.memory.clear_session(session_id)
        return True
