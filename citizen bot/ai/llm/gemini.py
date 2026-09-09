"""Google Gemini LLM Provider Implementation.

Connects to Google's Generative Language REST API using GEMINI_API_KEY.
Provides grounded natural-language response generation, strict prompt-injection
defense, timeout handling, and deterministic fallback for offline test environments.
"""

from __future__ import annotations
import json
import logging
import os
import re
from typing import Optional
import httpx
from ai.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini API Provider with resilient offline fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        # Clean placeholder values
        if self.api_key in ("your_api_key_here", "your_gemini_api_key_here", ""):
            self.api_key = ""

        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout = timeout
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def generate_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate grounded natural-language completion using Gemini API."""
        # 1. Security check: detect prompt injection attempting key/prompt leakage
        lower_prompt = prompt.lower()
        if any(leak_kw in lower_prompt for leak_kw in ["reveal the api key", "tell me the api key", "what is your api key", "print the api key", "give me the gemini api key"]):
            return "I cannot disclose internal credentials or API keys. I am here to assist with municipal service inquiries."

        # 2. If API key is available, call Gemini API
        if self.api_key:
            try:
                response = self._call_gemini_api(prompt, system_prompt)
                if response:
                    return response
            except Exception as e:
                logger.warning("Gemini API call failed, falling back to local generator: %s", e)

        # 3. Offline / fallback generator: generate grounded response from provided context
        return self._offline_grounded_generator(prompt, system_prompt)

    def _call_gemini_api(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Invoke Gemini generateContent endpoint via HTTP."""
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        payload: dict = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 800,
            },
        }

        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        headers = {"Content-Type": "application/json"}

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text = parts[0].get("text", "").strip()
                        return text
            elif response.status_code == 404 and "gemini-2.5-flash" in self.model:
                # Fallback to gemini-1.5-flash if 2.5 is not accessible in this region/key
                fallback_url = f"{self.base_url}/gemini-1.5-flash:generateContent?key={self.api_key}"
                fallback_res = client.post(fallback_url, json=payload, headers=headers)
                if fallback_res.status_code == 200:
                    data = fallback_res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                logger.warning("Gemini API returned status %s: %s", response.status_code, response.text)
            else:
                logger.warning("Gemini API returned status %s: %s", response.status_code, response.text)

        return None

    def _offline_grounded_generator(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Deterministic grounded generator parsing structured context in the prompt.

        Used when operating offline, in unit tests, or as a graceful fallback during API outages.
        Guarantees that all factual claims match retrieved data and prevents hallucinations.
        """
        # Extract sections from the constructed prompt
        query_match = re.search(r"CURRENT USER QUESTION:\s*(.*?)(?=\n\n|\Z)", prompt, re.DOTALL | re.IGNORECASE)
        user_query = query_match.group(1).strip() if query_match else prompt

        # Check for unavailable / fallback indicator in prompt
        if "No relevant municipal records or public API data were found" in prompt:
            return (
                "I don't currently have reliable information about that municipal service. "
                "For official assistance, please consult the Municipal Citizen Service Center "
                "or visit the official municipal portal."
            )

        # Check for clarification request in prompt
        clarification_match = re.search(r"CLARIFICATION REQUIRED:\s*(.*?)(?=\n\n|\Z)", prompt, re.DOTALL)
        if clarification_match:
            return clarification_match.group(1).strip()

        # Check for Public API Weather context
        if "PUBLIC API INFORMATION" in prompt:
            weather_match = re.search(r"PUBLIC API INFORMATION:\s*(.*?)(?=\n\nCURRENT USER QUESTION|\Z)", prompt, re.DOTALL)
            if weather_match:
                weather_text = weather_match.group(1).strip()
                return f"Here is the latest weather report:\n\n{weather_text}\n\nPlease check back for dynamic updates."

        # Check for Municipal Information context
        if "RETRIEVED MUNICIPAL INFORMATION" in prompt:
            context_match = re.search(r"RETRIEVED MUNICIPAL INFORMATION:\s*(.*?)(?=\n\nPUBLIC API|\n\nCURRENT USER QUESTION|\Z)", prompt, re.DOTALL)
            if context_match:
                context_str = context_match.group(1).strip()
                try:
                    records = json.loads(context_str)
                    if isinstance(records, list) and records:
                        return self._format_records_to_text(records, user_query)
                    elif isinstance(records, dict):
                        return self._format_records_to_text([records], user_query)
                except Exception:
                    # Fallback to presenting the context text cleanly
                    return f"According to municipal records:\n\n{context_str}"

        return "I couldn't find reliable information about that in the available municipal data."

    def _format_records_to_text(self, records: list, query: str) -> str:
        """Format retrieved structured JSON records into a concise, scannable civic response."""
        q_lower = query.lower()

        # 1. Waste collection records
        if "zone" in records[0] and "days" in records[0]:
            r = records[0]
            zone = r.get("zone", "Your Zone")
            service = r.get("service", "Waste Collection")
            days = ", ".join(r.get("days", []))
            time_str = r.get("time", "")

            # Check if user asked specifically about a day (e.g. "What about Thursday?", "Is there a collection on Friday?")
            for d in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                if d in q_lower:
                    if d.capitalize() in r.get("days", []):
                        return f"Yes, {service} is scheduled for {zone} on **{d.capitalize()}** at **{time_str}**."
                    else:
                        return f"There is no scheduled {service.lower()} for {zone} on **{d.capitalize()}**. Scheduled collection days are: **{days}** at **{time_str}**."

            # Check if user asked specifically for time ("what time?")
            if "what time" in q_lower or "when time" in q_lower:
                return f"{service} in **{zone}** begins at **{time_str}** ({r.get('collection_window', '')})."

            lines = [f"**{service} Schedule for {zone}** ({r.get('zone_name', '')}):", ""]
            lines.append(f"• **Collection Days:** {days}")
            lines.append(f"• **Pickup Time:** {time_str} ({r.get('collection_window', '')})")
            if r.get("guidelines"):
                lines.append(f"• **Guidelines:** {r['guidelines']}")
            if r.get("accepted_items"):
                lines.append(f"• **Accepted Items:** {', '.join(r['accepted_items'])}")
            return "\n".join(lines)

        # 2. Permit records
        if "permit_type" in records[0]:
            r = records[0]
            lines = [f"**{r.get('permit_type')}**", ""]
            if r.get("description"):
                lines.append(f"{r['description']}\n")

            # Check if asked specifically for documents
            if "document" in q_lower or "paper" in q_lower:
                docs = r.get("required_documents", [])
                lines = [f"Required documents for a **{r.get('permit_type')}**:\n"]
                for doc in docs:
                    lines.append(f"• {doc}")
                lines.append(f"\n**Processing Time:** {r.get('processing_time', 'N/A')}")
                lines.append(f"**Fee:** {r.get('fee', 'N/A')}")
                return "\n".join(lines)

            # Check if asked specifically for fee
            if "fee" in q_lower or "cost" in q_lower or "how much" in q_lower:
                return f"The application fee for a **{r.get('permit_type')}** is: **{r.get('fee')}**. Processing takes {r.get('processing_time')}."

            lines.append(f"• **Department:** {r.get('department', 'Municipal Licensing')}")
            lines.append(f"• **Fee:** {r.get('fee', 'N/A')}")
            lines.append(f"• **Processing Time:** {r.get('processing_time', 'N/A')}")
            lines.append(f"• **Validity:** {r.get('validity_period', 'N/A')}")

            if r.get("required_documents"):
                lines.append("\n**Key Required Documents:**")
                for doc in r["required_documents"][:4]:
                    lines.append(f"• {doc}")

            return "\n".join(lines)

        # 3. Event records
        if "date" in records[0] and "location" in records[0]:
            if len(records) == 1:
                r = records[0]
                lines = [f"**{r.get('title')}**", ""]
                lines.append(f"• **Date:** {r.get('date_display', r.get('date'))}")
                lines.append(f"• **Time:** {r.get('time')}")
                lines.append(f"• **Location:** {r.get('location')}")
                lines.append(f"• **Admission:** {r.get('admission')}")
                lines.append(f"• **Description:** {r.get('description')}")
                return "\n".join(lines)
            else:
                lines = ["**Upcoming Municipal Events:**", ""]
                for r in records[:4]:
                    lines.append(f"• **{r.get('title')}** — {r.get('date_display', r.get('date'))} at {r.get('location')} ({r.get('time')})")
                return "\n".join(lines)

        # 4. Municipal service records
        if "service_name" in records[0] or "office_location" in records[0]:
            r = records[0]
            lines = [f"**{r.get('service_name')}**", ""]
            if r.get("office_location"):
                lines.append(f"• **Location:** {r['office_location']}")
            if r.get("working_hours"):
                lines.append(f"• **Office Hours:** {r['working_hours']}")
            if r.get("phone"):
                lines.append(f"• **Phone:** {r['phone']}")
            if r.get("toll_free_helpline"):
                lines.append(f"• **Toll-Free Helpline:** {r['toll_free_helpline']}")
            if r.get("toll_free_grievance_number"):
                lines.append(f"• **Grievance Hotline:** {r['toll_free_grievance_number']}")
            if r.get("emergency_pipeline_hotline"):
                lines.append(f"• **24/7 Hotline:** {r['emergency_pipeline_hotline']}")
            if r.get("payment_deadlines"):
                lines.append(f"• **Payment Deadlines & Rebate:** {r['payment_deadlines']}")
            if r.get("penalty_rate"):
                lines.append(f"• **Penalty Rate:** {r['penalty_rate']}")
            if r.get("resolution_sla"):
                lines.append(f"• **Resolution Timeline (SLA):** {r['resolution_sla']}")
            if r.get("complaint_turnaround"):
                lines.append(f"• **Turnaround SLA:** {r['complaint_turnaround']}")
            if r.get("services_offered"):
                lines.append("\n**Services Offered:**")
                for s in r["services_offered"][:4]:
                    lines.append(f"• {s}")
            return "\n".join(lines)

        return json.dumps(records, indent=2)
