"""Knowledge Retrieval Subsystem for Municipal Public Service FAQ Chatbot.

Follows the architectural principle:
    Retrieve first, generate second.
Responsible for query normalization, intent detection, entity extraction,
dataset querying, ambiguity detection, and safe fallback handling.
"""

from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class KnowledgeRetriever:
    """Structured knowledge retriever for municipal FAQ queries."""

    def __init__(self, data_dir: Optional[str] = None) -> None:
        if data_dir is None:
            # Default to data/ directory in project root
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            self.data_dir = project_root / "data"
        else:
            self.data_dir = Path(data_dir)

        self._waste_data: Dict[str, Any] = {}
        self._permits_data: Dict[str, Any] = {}
        self._events_data: Dict[str, Any] = {}
        self._services_data: Dict[str, Any] = {}

        self.load_datasets()

    def load_datasets(self) -> None:
        """Load and cache municipal JSON datasets."""
        self._waste_data = self._read_json_file(self.data_dir / "waste_collection.json")
        self._permits_data = self._read_json_file(self.data_dir / "permits.json")
        self._events_data = self._read_json_file(self.data_dir / "events.json")
        self._services_data = self._read_json_file(self.data_dir / "municipal_services.json")

    def _read_json_file(self, filepath: Path) -> Dict[str, Any]:
        """Safely read a JSON file, returning empty structure on failure."""
        if not filepath.exists():
            return {"metadata": {}, "records": []}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"metadata": {}, "records": []}

    # -------------------------------------------------------------------------
    # Intent Detection
    # -------------------------------------------------------------------------
    def detect_intent(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float]:
        """Detect the intent of the user query with confidence score.

        Returns:
            Tuple of (intent_name, confidence_score)
        """
        q = query.lower().strip()
        ctx = context or {}
        previous_intent = ctx.get("previous_intent")

        # 0. Check for explicit out-of-scope / unsupported domains first
        unsupported_terms = [
            "interstellar", "spaceship", "spaceships", "space flight", "flight ticket",
            "quantum", "alien", "swimming pool", "tokyo", "rome", "roman emperor",
            "speed of light", "stock market", "investment tips", "poem"
        ]
        if any(term in q for term in unsupported_terms):
            return "unknown", 0.99

        # 1. Weather intent
        weather_keywords = [
            "weather", "forecast", "rain", "raining", "rainy", "temperature",
            "sunny", "cloudy", "umbrella", "snow", "degrees", "windy", "wind", "humidity"
        ]
        if any(w in q for w in weather_keywords):
            return "weather", 0.95

        # 2. Specific Event Titles / Indicators (prioritize over generic keywords)
        specific_event_cues = [
            "clean city", "mela", "festival", "cultural fest", "tree plantation",
            "health camp", "town hall", "hearing", "exhibition", "campaign",
            "bengaluru habba", "hasiru bengaluru", "janata darbar", "swachh bengaluru",
            "nirmal mela", "habba"
        ]
        if any(cue in q for cue in specific_event_cues):
            return "event_lookup", 0.95

        # 3. Check for explicit follow-up phrases that rely on previous context
        is_follow_up = bool(
            re.search(r"^(what|how) about\b", q)
            or re.search(r"^(actually|i mean)\b", q)
            or re.search(r"^what (time|days|documents|fee|cost)\b", q)
            or re.search(r"^(is there|are there|can i|do i need|where is|what are)\b", q)
            or len(q.split()) <= 3
        )

        # 4. Waste collection intent
        waste_keywords = [
            "waste", "garbage", "trash", "rubbish", "refuse", "bin", "bins",
            "recycle", "recycling", "recyclable", "organic waste", "green waste",
            "yard waste", "bulky", "e-waste", "curbside", "pickup", "collection"
        ]
        waste_matches = sum(1 for kw in waste_keywords if kw in q)
        if waste_matches > 0:
            return "waste_collection", min(0.95, 0.7 + waste_matches * 0.1)

        # 5. Permit requirements vs general permit information
        permit_keywords = [
            "permit", "permits", "license", "licence", "licensing",
            "renovation", "building plan", "trade license", "vendor permit"
        ]
        permit_matches = sum(1 for kw in permit_keywords if kw in q)
        if permit_matches > 0:
            if any(doc_word in q for doc_word in ["document", "documents", "need", "require", "required", "apply", "papers"]):
                return "permit_requirements", 0.95
            return "permit_information", 0.90

        # 6. Event lookup (general)
        event_keywords = [
            "event", "events", "festival", "fest", "exhibition", "mela",
            "town hall", "hearing", "happening", "activity", "activities",
            "cultural", "plantation", "cleanliness drive", "health camp",
            "clean city", "campaign", "drive",
            "habba", "hasiru", "swachh", "janata darbar", "nirmal"
        ]
        if any(kw in q for kw in event_keywords):
            return "event_lookup", 0.92

        # 7. Municipal services & office information
        office_keywords = [
            "office", "timing", "timings", "hours", "open", "close", "closed",
            "address", "location", "headquarters", "suvidha kendra", "counter"
        ]
        service_keywords = [
            "service", "services", "water", "sewage", "leak", "tanker",
            "property tax", "tax", "rebate", "complaint", "complaints", "grievance",
            "pothole", "potholes", "streetlight", "street light", "birth certificate",
            "death certificate", "helpline", "toll free", "contact", "bbmp"
        ]
        if any(kw in q for kw in office_keywords):
            return "office_information", 0.90
        if any(kw in q for kw in service_keywords):
            return "municipal_service", 0.90

        # 8. Follow-up fallback using prior session intent
        if is_follow_up and previous_intent and previous_intent != "unknown":
            if previous_intent == "weather":
                return "weather", 0.90
            if previous_intent == "waste_collection":
                return "waste_collection", 0.90
            if previous_intent in ("permit_information", "permit_requirements"):
                if any(w in q for w in ["document", "documents", "fee", "cost", "time", "take"]):
                    return "permit_requirements", 0.85
                return "permit_information", 0.80
            if previous_intent == "event_lookup":
                return "event_lookup", 0.80
            if previous_intent in ("municipal_service", "office_information"):
                return previous_intent, 0.80

        # 8. Check for greetings or system queries
        if q in ["hello", "hi", "hey", "good morning", "good evening", "help"]:
            return "greeting", 0.90

        # 9. Default to unknown
        return "unknown", 0.50

    # -------------------------------------------------------------------------
    # Entity Extraction
    # -------------------------------------------------------------------------
    def extract_entities(
        self, query: str, intent: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract municipal entities (zone, permit_type, days, service) from query and context."""
        q = query.lower()
        ctx = context or {}
        entities: Dict[str, Any] = {}

        # 1. Zone extraction
        # Zone A, Zone B, Zone C, Zone D, or by name / area
        zone_match = re.search(r"\bzone\s*([a-d])\b", q)
        if zone_match:
            entities["zone"] = f"Zone {zone_match.group(1).upper()}"
        elif "area a" in q or "malleshwaram" in q or "north bengaluru" in q or "downtown" in q:
            entities["zone"] = "Zone A"
        elif "area b" in q or "indiranagar" in q or "east bengaluru" in q or "riverdale" in q:
            entities["zone"] = "Zone B"
        elif "area c" in q or "jayanagar" in q or "koramangala" in q or "south bengaluru" in q or "hillview" in q:
            entities["zone"] = "Zone C"
        elif "area d" in q or "peenya" in q or "rajajinagar" in q or "west bengaluru" in q or "industrial zone" in q:
            entities["zone"] = "Zone D"
        elif "all zones" in q or "citywide" in q or "city-wide" in q:
            entities["zone"] = "All Zones"
        elif ctx.get("zone") and intent in ("waste_collection", "unknown"):
            # Preserve zone from session context for follow-ups
            entities["zone"] = ctx["zone"]

        # 2. Days of week extraction
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        found_days = [d.capitalize() for d in days if re.search(rf"\b{d}\b", q)]
        if found_days:
            entities["days"] = found_days

        # 3. Waste type extraction
        if "recycl" in q:
            entities["waste_type"] = "Recycling Collection"
        elif "green" in q or "yard" in q or "organic" in q or "leaves" in q or "branch" in q:
            entities["waste_type"] = "Green Waste Collection"
        elif "bulky" in q or "furniture" in q or "mattress" in q or "appliance" in q:
            entities["waste_type"] = "Bulky Item Collection"
        elif "hazard" in q or "e-waste" in q or "electronic" in q or "battery" in q or "paint" in q:
            entities["waste_type"] = "Hazardous & E-Waste Depot"
        elif "garbage" in q or "trash" in q or "general" in q or "household" in q:
            entities["waste_type"] = "Waste Collection"

        # 4. Permit type extraction
        if "build" in q or "construct" in q or "structural" in q:
            entities["permit_type"] = "Building Permit"
        elif "trade" in q or "business" in q or "shop" in q or "commercial" in q or "store" in q:
            entities["permit_type"] = "Commercial Trade License"
        elif "event" in q or "gathering" in q or "festival" in q or "concert" in q or "rally" in q:
            entities["permit_type"] = "Public Event Permit"
        elif "renovat" in q or "remodel" in q or "interior" in q:
            entities["permit_type"] = "Residential Renovation Permit"
        elif "vending" in q or "vendor" in q or "hawker" in q or "food cart" in q:
            entities["permit_type"] = "Street Vending Permit"
        elif ctx.get("permit_type") and intent in ("permit_information", "permit_requirements"):
            entities["permit_type"] = ctx["permit_type"]

        # 5. Service / Department extraction
        if "water" in q or "sewage" in q or "leak" in q or "tanker" in q:
            entities["service"] = "Water Supply & Sewage Department"
        elif "tax" in q or "property tax" in q or "house tax" in q:
            entities["service"] = "Property Tax Assessment & Collection"
        elif "grievance" in q or "complaint" in q or "pothole" in q or "streetlight" in q or "report" in q:
            entities["service"] = "Public Grievance & Citizen Complaint Redressal Cell"
        elif "birth" in q or "death" in q or "vital" in q:
            entities["service"] = "Vital Statistics: Birth & Death Registration Office"
        elif "road" in q or "pavement" in q or "footpath" in q:
            entities["service"] = "Road Maintenance & Streetlight Division"
        elif "suvidha" in q or "citizen service" in q or "center" in q or "office hours" in q or "timings" in q:
            entities["service"] = "Citizen Service Center (Single Window)"
        elif ctx.get("service") and intent in ("municipal_service", "office_information"):
            entities["service"] = ctx["service"]

        # 6. Event keyword / date
        if "this month" in q or "upcoming" in q:
            entities["event_timeframe"] = "upcoming"
        for month in ["september", "october", "november"]:
            if month in q:
                entities["event_month"] = month.capitalize()

        return entities

    # -------------------------------------------------------------------------
    # Core Retrieval Dispatcher
    # -------------------------------------------------------------------------
    def retrieve(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Main retrieval method executing grounded search across datasets.

        Returns structured retrieval packet:
            {
                "status": "found" | "not_found" | "clarification_required",
                "intent": str,
                "entities": dict,
                "records": list[dict],
                "clarification_prompt": Optional[str],
                "source": str,
                "last_updated": str,
                "data_type": str
            }
        """
        ctx = context or {}
        intent, confidence = self.detect_intent(query, ctx)
        entities = self.extract_entities(query, intent, ctx)

        # Base response template
        result: Dict[str, Any] = {
            "status": "not_found",
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "records": [],
            "clarification_prompt": None,
            "source": "Municipal Demonstration Dataset",
            "last_updated": "2026-09-01",
            "data_type": "synthetic_demo"
        }

        # Route by intent
        if intent == "waste_collection":
            return self._retrieve_waste(query, entities, result)
        elif intent in ("permit_information", "permit_requirements"):
            return self._retrieve_permits(query, entities, result)
        elif intent == "event_lookup":
            return self._retrieve_events(query, entities, result)
        elif intent in ("municipal_service", "office_information"):
            return self._retrieve_services(query, entities, result)
        elif intent == "weather":
            result["status"] = "found"
            result["source"] = "Weather API"
            result["records"] = []
            return result
        elif intent == "greeting":
            result["status"] = "found"
            result["records"] = [{"message": "Welcome! How can I assist you with municipal services today?"}]
            return result

        # Unknown query fallback
        result["status"] = "not_found"
        return result

    # -------------------------------------------------------------------------
    # Specific Dataset Retrievers
    # -------------------------------------------------------------------------
    def _retrieve_waste(
        self, query: str, entities: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        records = self._waste_data.get("records", [])
        result["source"] = "Municipal Waste Management Dataset"

        zone = entities.get("zone")
        waste_type = entities.get("waste_type")
        query_lower = query.lower()

        # Check for special collections (Bulky or Hazardous)
        if waste_type == "Bulky Item Collection" or "bulky" in query_lower:
            matched = [r for r in records if r.get("service") == "Bulky Item Collection"]
            result["status"] = "found"
            result["records"] = matched
            return result

        if waste_type == "Hazardous & E-Waste Depot" or "e-waste" in query_lower or "hazard" in query_lower:
            matched = [r for r in records if r.get("service") == "Hazardous & E-Waste Depot"]
            result["status"] = "found"
            result["records"] = matched
            return result

        # If zone is missing, check if this is an ambiguous query requiring clarification
        if not zone:
            # Check if user is asking for all zones or asking general questions
            if any(w in query_lower for w in ["all zones", "every zone", "what zones"]):
                result["status"] = "found"
                result["records"] = records
                return result

            # Clarification trigger as mandated by PRD Section 14 and rules.md
            result["status"] = "clarification_required"
            result["clarification_prompt"] = (
                "Which zone are you asking about? Bengaluru is divided into: "
                "Zone A (Malleshwaram, Central & North Bengaluru), "
                "Zone B (Indiranagar & East Bengaluru), "
                "Zone C (Jayanagar, Koramangala & South Bengaluru), "
                "and Zone D (Peenya, Rajajinagar & West Industrial Zone)."
            )
            return result

        # Filter by zone
        zone_records = [r for r in records if r.get("zone") == zone]
        if not zone_records:
            result["status"] = "not_found"
            return result

        # If specific waste type requested (e.g. recycling or green waste), filter further
        if waste_type:
            matched = [r for r in zone_records if r.get("service") == waste_type]
            if matched:
                zone_records = matched

        result["status"] = "found"
        result["records"] = zone_records
        return result

    def _retrieve_permits(
        self, query: str, entities: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        records = self._permits_data.get("records", [])
        result["source"] = "Municipal Licensing & Permits Dataset"

        permit_type = entities.get("permit_type")

        # If no specific permit type is identified:
        if not permit_type:
            # Check if asking general permit list
            if any(w in query.lower() for w in ["what permits", "list", "types of permit", "available permits", "which permits"]):
                result["status"] = "found"
                result["records"] = records
                return result

            # If asking requirements or documents without specifying permit type
            result["status"] = "clarification_required"
            result["clarification_prompt"] = (
                "Which type of permit do you need information on? We handle: "
                "Building Permits, Commercial Trade Licenses, Public Event Permits, "
                "Residential Renovation Permits, and Street Vending Permits."
            )
            return result

        # Match specific permit
        matched = [r for r in records if r.get("permit_type") == permit_type]
        if matched:
            result["status"] = "found"
            result["records"] = matched
        else:
            result["status"] = "not_found"

        return result

    def _retrieve_events(
        self, query: str, entities: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        records = self._events_data.get("records", [])
        result["source"] = "Municipal Public Events Dataset"
        q_lower = query.lower()

        # 1. Match by specific event title or alias (normalize & to and)
        matched = []
        q_norm = q_lower.replace("&", "and")
        for r in records:
            title = r.get("title", "").lower().replace("&", "and")
            aliases = [a.lower().replace("&", "and") for a in r.get("aliases", [])]
            if any(term in q_norm for term in [title] + aliases):
                matched.append(r)
            elif "mela" in q_norm and "mela" in title:
                matched.append(r)
            elif "tree plantation" in q_norm and "tree" in title:
                matched.append(r)
            elif "clean city" in q_norm and "clean" in title:
                matched.append(r)
            elif "swachh" in q_norm and "swachh" in title:
                matched.append(r)
            elif "town hall" in q_norm and "town hall" in title:
                matched.append(r)
            elif "janata darbar" in q_norm and "janata" in title:
                matched.append(r)
            elif "vaccination" in q_norm and "vaccination" in title:
                matched.append(r)
            elif "heritage" in q_norm and "heritage" in title:
                matched.append(r)
            elif "habba" in q_norm and "habba" in title:
                matched.append(r)
            elif "hasiru" in q_norm and "hasiru" in title:
                matched.append(r)
            elif "nirmal" in q_norm and "nirmal" in title:
                matched.append(r)

        if matched:
            result["status"] = "found"
            result["records"] = matched
            return result

        # 2. Check for month or timeframe filter
        month = entities.get("event_month")
        if month:
            month_records = [r for r in records if month.lower() in r.get("date_display", "").lower()]
            if month_records:
                result["status"] = "found"
                result["records"] = month_records
                return result

        # 3. Return all upcoming events if asking broadly ("what events are happening?")
        result["status"] = "found"
        result["records"] = records
        return result

    def _retrieve_services(
        self, query: str, entities: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        records = self._services_data.get("records", [])
        result["source"] = "Municipal Services & Citizen Facilities Dataset"
        q_lower = query.lower()

        service_name = entities.get("service")

        # 1. Direct match by extracted service name
        if service_name:
            matched = [r for r in records if r.get("service_name") == service_name]
            if matched:
                result["status"] = "found"
                result["records"] = matched
                return result

        # 2. Match by keyword / alias search
        matched = []
        for r in records:
            name = r.get("service_name", "").lower()
            aliases = [a.lower() for a in r.get("aliases", [])]
            dept = r.get("department", "").lower()
            if any(term in q_lower for term in [name, dept] + aliases):
                matched.append(r)

        if matched:
            result["status"] = "found"
            result["records"] = matched
            return result

        # 3. Broad query asking what services exist
        if any(w in q_lower for w in ["what services", "available services", "municipal services", "bbmp services", "departments"]):
            result["status"] = "found"
            result["records"] = records
            return result

        result["status"] = "not_found"
        return result
