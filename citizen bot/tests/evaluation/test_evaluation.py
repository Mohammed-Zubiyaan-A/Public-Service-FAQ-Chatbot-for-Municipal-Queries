"""Accuracy and Performance Benchmark Evaluation Suite.

Evaluates 65 representative municipal queries across 8 categories:
  1. Waste Collection (10)
  2. Permits (10)
  3. Municipal Services (10)
  4. Events (10)
  5. Weather / API (10)
  6. Follow-up Questions (5)
  7. Ambiguous Queries (5)
  8. Unknown / Out-of-Scope Queries (5)

Measures:
  - Accuracy: (Correct Answers / Total Questions) * 100 (Target: >= 80%)
  - Latency: Average, min, and max response time (Target: < 20s)
"""

from __future__ import annotations
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Ensure project root is in sys.path for direct CLI script execution
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from backend.services.chat_service import ChatService

# 65 Representative Evaluation Test Cases
EVALUATION_DATASET: List[Dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # Category 1: Waste Collection (10 questions)
    # -------------------------------------------------------------------------
    {
        "id": "W01",
        "category": "waste_collection",
        "question": "When is waste collected in Zone A?",
        "expected_keywords": ["Monday", "Thursday", "7:00 AM"],
        "disallowed_keywords": ["Friday"],
    },
    {
        "id": "W02",
        "category": "waste_collection",
        "question": "What time does garbage pickup happen in Zone A?",
        "expected_keywords": ["7:00 AM"],
    },
    {
        "id": "W03",
        "category": "waste_collection",
        "question": "What days do they collect garbage in Zone B?",
        "expected_keywords": ["Tuesday", "Friday"],
    },
    {
        "id": "W04",
        "category": "waste_collection",
        "question": "When is dry recycling collected in Zone A?",
        "expected_keywords": ["Wednesday"],
    },
    {
        "id": "W05",
        "category": "waste_collection",
        "question": "What is the green waste collection schedule for Zone A?",
        "expected_keywords": ["Saturday"],
    },
    {
        "id": "W06",
        "category": "waste_collection",
        "question": "When is recycling picked up in Zone B?",
        "expected_keywords": ["Thursday"],
    },
    {
        "id": "W07",
        "category": "waste_collection",
        "question": "What is the general waste collection schedule for Zone C?",
        "expected_keywords": ["Monday", "Wednesday", "Friday"],
    },
    {
        "id": "W08",
        "category": "waste_collection",
        "question": "When does garbage collection happen in Zone D?",
        "expected_keywords": ["Tuesday", "Saturday", "6:30 AM"],
    },
    {
        "id": "W09",
        "category": "waste_collection",
        "question": "How do I dispose of bulky furniture like an old mattress?",
        "expected_keywords": ["Bulky", "2 free", "appointment"],
    },
    {
        "id": "W10",
        "category": "waste_collection",
        "question": "Where can I drop off hazardous waste and old laptop batteries?",
        "expected_keywords": ["Eco-Center", "Hazardous", "Saturday"],
    },

    # -------------------------------------------------------------------------
    # Category 2: Permits & Licensing (10 questions)
    # -------------------------------------------------------------------------
    {
        "id": "P01",
        "category": "permits",
        "question": "What documents are required for a building permit?",
        "expected_keywords": ["Architectural", "ownership", "stability"],
    },
    {
        "id": "P02",
        "category": "permits",
        "question": "How much does a building permit cost?",
        "expected_keywords": ["$250"],
    },
    {
        "id": "P03",
        "category": "permits",
        "question": "How long does it take to process a building permit?",
        "expected_keywords": ["15 to 20", "working days"],
    },
    {
        "id": "P04",
        "category": "permits",
        "question": "What documents do I need for a commercial trade license?",
        "expected_keywords": ["ID proof", "lease", "Fire"],
    },
    {
        "id": "P05",
        "category": "permits",
        "question": "What is the processing time for a trade license?",
        "expected_keywords": ["7 to 10", "working days"],
    },
    {
        "id": "P06",
        "category": "permits",
        "question": "What are the requirements for an outdoor public event permit?",
        "expected_keywords": ["Police", "insurance", "evacuation"],
    },
    {
        "id": "P07",
        "category": "permits",
        "question": "How much is the fee for a residential renovation permit?",
        "expected_keywords": ["$75"],
    },
    {
        "id": "P08",
        "category": "permits",
        "question": "How long is a residential renovation permit valid for?",
        "expected_keywords": ["6 months"],
    },
    {
        "id": "P09",
        "category": "permits",
        "question": "What is the fee for a street vending permit?",
        "expected_keywords": ["$50"],
    },
    {
        "id": "P10",
        "category": "permits",
        "question": "What types of permits can I apply for in the municipality?",
        "expected_keywords": ["Building", "Trade", "Event"],
    },

    # -------------------------------------------------------------------------
    # Category 3: Municipal Services & Offices (10 questions)
    # -------------------------------------------------------------------------
    {
        "id": "S01",
        "category": "municipal_services",
        "question": "What are the office hours for the Citizen Service Center?",
        "expected_keywords": ["Monday to Friday", "9:00 AM"],
    },
    {
        "id": "S02",
        "category": "municipal_services",
        "question": "Where is the Citizen Service Center located?",
        "expected_keywords": ["1 Civic Boulevard", "Municipal Headquarters"],
    },
    {
        "id": "S03",
        "category": "municipal_services",
        "question": "How do I report an emergency water pipe leakage?",
        "expected_keywords": ["(555) 019-2222", "24/7"],
    },
    {
        "id": "S04",
        "category": "municipal_services",
        "question": "Can I book a drinking water tanker from the municipality?",
        "expected_keywords": ["tanker", "$20"],
    },
    {
        "id": "S05",
        "category": "municipal_services",
        "question": "When is property tax due?",
        "expected_keywords": ["June 30", "December 31"],
    },
    {
        "id": "S06",
        "category": "municipal_services",
        "question": "Is there a discount or rebate for paying property tax early?",
        "expected_keywords": ["5%", "April 30"],
    },
    {
        "id": "S07",
        "category": "municipal_services",
        "question": "How do I lodge a complaint about broken streetlights?",
        "expected_keywords": ["Grievance", "1800-555-CARE"],
    },
    {
        "id": "S08",
        "category": "municipal_services",
        "question": "What is the resolution timeline for pothole complaints?",
        "expected_keywords": ["3 to 7", "working days"],
    },
    {
        "id": "S09",
        "category": "municipal_services",
        "question": "Where can I register a birth or death certificate?",
        "expected_keywords": ["Birth & Death", "55 Hospital Road"],
    },
    {
        "id": "S10",
        "category": "municipal_services",
        "question": "How much does a certified duplicate copy of a birth certificate cost?",
        "expected_keywords": ["$10"],
    },

    # -------------------------------------------------------------------------
    # Category 4: Municipal Events (10 questions)
    # -------------------------------------------------------------------------
    {
        "id": "E01",
        "category": "events",
        "question": "When is the Clean City & Community Recycling Drive?",
        "expected_keywords": ["October 2", "8:00 AM"],
    },
    {
        "id": "E02",
        "category": "events",
        "question": "Where is the Clean City campaign being held?",
        "expected_keywords": ["Central Park Pavilion", "Zone A"],
    },
    {
        "id": "E03",
        "category": "events",
        "question": "What are the dates for the Annual Heritage and Cultural Festival?",
        "expected_keywords": ["October 15", "October 18"],
    },
    {
        "id": "E04",
        "category": "events",
        "question": "How much is admission to the Heritage and Cultural Festival?",
        "expected_keywords": ["Free"],
    },
    {
        "id": "E05",
        "category": "events",
        "question": "When is the Ward 4 Citizen Town Hall meeting?",
        "expected_keywords": ["September 25", "6:00 PM"],
    },
    {
        "id": "E06",
        "category": "events",
        "question": "Where will the Ward 4 Town Hall meeting take place?",
        "expected_keywords": ["Ward 4 Community Center", "Riverdale Road"],
    },
    {
        "id": "E07",
        "category": "events",
        "question": "Tell me about the Green Citizen Tree Plantation drive.",
        "expected_keywords": ["October 10", "Riverside Promenade", "2,000"],
    },
    {
        "id": "E08",
        "category": "events",
        "question": "When is the Free Preventive Health and Vaccination Camp?",
        "expected_keywords": ["September 28", "Dispensary East"],
    },
    {
        "id": "E09",
        "category": "events",
        "question": "When is the Electronics and E-Waste Recycling Mela?",
        "expected_keywords": ["October 24", "Civic Center South"],
    },
    {
        "id": "E10",
        "category": "events",
        "question": "What municipal events are happening upcoming?",
        "expected_keywords": ["Event", "October"],
    },

    # -------------------------------------------------------------------------
    # Category 5: Weather / Public API (10 questions)
    # -------------------------------------------------------------------------
    {
        "id": "WE01",
        "category": "weather",
        "question": "What's the weather today?",
        "expected_keywords": ["Weather", "Temperature", "Condition"],
    },
    {
        "id": "WE02",
        "category": "weather",
        "question": "What is the weather tomorrow?",
        "expected_keywords": ["Weather", "Tomorrow"],
    },
    {
        "id": "WE03",
        "category": "weather",
        "question": "Will it rain today?",
        "expected_keywords": ["Rain", "Probability"],
    },
    {
        "id": "WE04",
        "category": "weather",
        "question": "What is the temperature right now?",
        "expected_keywords": ["°C"],
    },
    {
        "id": "WE05",
        "category": "weather",
        "question": "Is it cloudy or sunny today?",
        "expected_keywords": ["Condition", "Weather"],
    },
    {
        "id": "WE06",
        "category": "weather",
        "question": "Do I need an umbrella today?",
        "expected_keywords": ["rain", "Weather"],
    },
    {
        "id": "WE07",
        "category": "weather",
        "question": "What is the wind speed outside?",
        "expected_keywords": ["km/h"],
    },
    {
        "id": "WE08",
        "category": "weather",
        "question": "Can you give me the forecast for tomorrow?",
        "expected_keywords": ["Weather", "Tomorrow"],
    },
    {
        "id": "WE09",
        "category": "weather",
        "question": "Is there any rain forecast for this weekend or tomorrow?",
        "expected_keywords": ["Rain", "Weather"],
    },
    {
        "id": "WE10",
        "category": "weather",
        "question": "What is today's high and low temperature?",
        "expected_keywords": ["High", "Low"],
    },

    # -------------------------------------------------------------------------
    # Category 6: Follow-Up Questions (5 scenarios)
    # -------------------------------------------------------------------------
    {
        "id": "F01",
        "category": "follow_ups",
        "context_setup": [("When is waste collected in Zone A?", "test_eval_f01")],
        "question": "What time?",
        "session_id": "test_eval_f01",
        "expected_keywords": ["7:00 AM"],
    },
    {
        "id": "F02",
        "category": "follow_ups",
        "context_setup": [("When is garbage collected in Zone A?", "test_eval_f02")],
        "question": "What about Friday?",
        "session_id": "test_eval_f02",
        "expected_keywords": ["no scheduled", "not"],
    },
    {
        "id": "F03",
        "category": "follow_ups",
        "context_setup": [("What permits are available?", "test_eval_f03")],
        "question": "What documents are required for the trade permit?",
        "session_id": "test_eval_f03",
        "expected_keywords": ["Trade", "documents"],
    },
    {
        "id": "F04",
        "category": "follow_ups",
        "context_setup": [("Tell me about waste collection in Zone A.", "test_eval_f04")],
        "question": "Actually, I mean Zone B.",
        "session_id": "test_eval_f04",
        "expected_keywords": ["Zone B", "Tuesday"],
    },
    {
        "id": "F05",
        "category": "follow_ups",
        "context_setup": [("What is the weather today?", "test_eval_f05")],
        "question": "What about tomorrow?",
        "session_id": "test_eval_f05",
        "expected_keywords": ["Tomorrow", "Weather"],
    },

    # -------------------------------------------------------------------------
    # Category 7: Ambiguous Queries Requiring Clarification (5 questions)
    # -------------------------------------------------------------------------
    {
        "id": "A01",
        "category": "ambiguous",
        "question": "When is waste collected?",
        "expected_keywords": ["Which zone", "Zone A"],
    },
    {
        "id": "A02",
        "category": "ambiguous",
        "question": "What time does garbage pickup happen?",
        "expected_keywords": ["Which zone"],
    },
    {
        "id": "A03",
        "category": "ambiguous",
        "question": "When do they collect recycling?",
        "expected_keywords": ["Which zone"],
    },
    {
        "id": "A04",
        "category": "ambiguous",
        "question": "What documents do I need for my permit?",
        "expected_keywords": ["Which type of permit", "Building Permits"],
    },
    {
        "id": "A05",
        "category": "ambiguous",
        "question": "How much is the permit fee?",
        "expected_keywords": ["Which type of permit"],
    },

    # -------------------------------------------------------------------------
    # Category 8: Unknown / Safe Fallback Queries (5 questions)
    # -------------------------------------------------------------------------
    {
        "id": "U01",
        "category": "unknown",
        "question": "What is the municipal tax penalty on commercial space flight pads?",
        "expected_keywords": ["don't currently have reliable information", "available"],
    },
    {
        "id": "U02",
        "category": "unknown",
        "question": "Can you book a flight ticket to Paris for me?",
        "expected_keywords": ["don't currently have reliable information", "available data"],
    },
    {
        "id": "U03",
        "category": "unknown",
        "question": "What is the municipal swimming pool adult membership fee?",
        "expected_keywords": ["don't currently have reliable information", "couldn't find reliable information"],
    },
    {
        "id": "U04",
        "category": "unknown",
        "question": "What is the speed of light in vacuum?",
        "expected_keywords": ["don't currently have reliable information", "available municipal data"],
    },
    {
        "id": "U05",
        "category": "unknown",
        "question": "Who is the mayor of Tokyo?",
        "expected_keywords": ["don't currently have reliable information", "available"],
    },
]


def evaluate_single_test(chat_service: ChatService, item: Dict[str, Any]) -> Dict[str, Any]:
    """Execute single test item and score accuracy and response latency."""
    session_id = item.get("session_id", f"eval_{item['id']}")

    # Context setup for follow-ups
    if "context_setup" in item:
        chat_service.clear_session(session_id)
        for setup_query, s_id in item["context_setup"]:
            chat_service.process_query(setup_query, s_id)

    start_time = time.time()
    response = chat_service.process_query(item["question"], session_id)
    latency = time.time() - start_time

    answer_text = response.response
    lower_answer = answer_text.lower()

    # Accuracy verification
    expected_kws = item.get("expected_keywords", [])
    disallowed_kws = item.get("disallowed_keywords", [])

    has_expected = False
    # Check if at least one expected keyword is present (or all if strict)
    matches = sum(1 for kw in expected_kws if kw.lower() in lower_answer)
    if matches >= 1:
        has_expected = True

    has_disallowed = False
    if disallowed_kws:
        has_disallowed = any(kw.lower() in lower_answer for kw in disallowed_kws)

    is_correct = has_expected and not has_disallowed

    return {
        "id": item["id"],
        "category": item["category"],
        "question": item["question"],
        "answer": answer_text,
        "is_correct": is_correct,
        "latency_seconds": round(latency, 3),
        "status": response.status,
    }


def run_full_evaluation() -> Dict[str, Any]:
    """Run all 65 evaluation tests and produce aggregated accuracy and performance metrics."""
    chat_service = ChatService()
    results = []

    total_count = len(EVALUATION_DATASET)
    category_scores: Dict[str, Dict[str, int]] = {}

    for item in EVALUATION_DATASET:
        cat = item["category"]
        if cat not in category_scores:
            category_scores[cat] = {"correct": 0, "total": 0}

        res = evaluate_single_test(chat_service, item)
        results.append(res)

        category_scores[cat]["total"] += 1
        if res["is_correct"]:
            category_scores[cat]["correct"] += 1

    correct_count = sum(1 for r in results if r["is_correct"])
    accuracy_percentage = (correct_count / total_count) * 100.0

    latencies = [r["latency_seconds"] for r in results]
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)

    return {
        "total_questions": total_count,
        "correct_answers": correct_count,
        "accuracy_percentage": round(accuracy_percentage, 2),
        "target_accuracy_met": accuracy_percentage >= 80.0,
        "avg_latency_sec": round(avg_latency, 3),
        "max_latency_sec": round(max_latency, 3),
        "min_latency_sec": round(min_latency, 3),
        "target_latency_met": max_latency < 20.0,
        "category_breakdown": category_scores,
        "results": results,
    }


def test_evaluation_benchmark():
    """Pytest test asserting that Accuracy >= 80% and Max Response Time < 20 seconds."""
    metrics = run_full_evaluation()

    print(f"\n{'='*60}")
    print(f"EVALUATION RESULTS:")
    print(f"Total Questions Evaluated: {metrics['total_questions']}")
    print(f"Correct Answers: {metrics['correct_answers']}")
    print(f"Overall Accuracy: {metrics['accuracy_percentage']}% (Target: >= 80%)")
    print(f"Avg Response Latency: {metrics['avg_latency_sec']}s (Target: < 20s)")
    print(f"Max Response Latency: {metrics['max_latency_sec']}s")
    print(f"{'='*60}")

    for cat, data in metrics["category_breakdown"].items():
        cat_acc = (data["correct"] / data["total"]) * 100.0
        print(f" - {cat:20}: {data['correct']}/{data['total']} ({cat_acc:.1f}%)")

    assert metrics["target_accuracy_met"], f"Accuracy target not met: {metrics['accuracy_percentage']}% < 80%"
    assert metrics["target_latency_met"], f"Latency target not met: {metrics['max_latency_sec']}s >= 20s"


if __name__ == "__main__":
    report = run_full_evaluation()
    print(f"Accuracy: {report['accuracy_percentage']}% ({report['correct_answers']}/{report['total_questions']})")
    print(f"Avg Latency: {report['avg_latency_sec']}s")
    print(f"Max Latency: {report['max_latency_sec']}s")
    for c, d in report["category_breakdown"].items():
        print(f"  {c:18}: {d['correct']}/{d['total']}")
