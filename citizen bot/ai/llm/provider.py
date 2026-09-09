"""LLM Provider Interface.

Abstract base class isolating LLM operations from backend orchestration,
allowing seamless switching between LLM providers (Gemini, Groq, or Mock/Offline)
without architectural redesign.
"""

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Abstract interface for LLM text generation."""

    @abstractmethod
    def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate conversational completion from prompt and system prompt.

        Args:
            prompt: Formatted user prompt containing retrieved context & conversation history.
            system_prompt: System-level instructions governing tone, grounding, and security.

        Returns:
            Grounded natural-language string response.
        """
        pass
