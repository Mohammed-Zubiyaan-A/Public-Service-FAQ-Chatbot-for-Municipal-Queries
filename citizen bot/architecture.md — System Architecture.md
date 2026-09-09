# architecture.md

# Public Service FAQ Chatbot for Municipal Queries
## System Architecture

---

# 1. Purpose

This document defines the technical architecture of the **Public Service FAQ Chatbot for Municipal Queries**.

The architecture is designed to satisfy the requirements defined in `prd.md`, including:

- Natural-language interaction
- GenAI-powered response generation
- Knowledge retrieval
- Conversational context
- Municipal datasets
- Public API integration
- Response time below 20 seconds
- At least 80% answer accuracy
- Simple browser-based chat interface
- Secure API-key handling
- Extensibility for additional municipal services

---

# 2. Architecture Goals

The architecture should prioritize:

1. Accuracy
2. Reliable knowledge retrieval
3. Grounded AI responses
4. Simplicity
5. Maintainability
6. Extensibility
7. Security
8. Demonstrability
9. Reasonable response time

The project is a college-level MVP, so unnecessary complexity should be avoided.

---

# 3. High-Level Architecture

The system follows a layered architecture with a RAG-based AI pipeline.

```text
                         ┌─────────────────────┐
                         │       CITIZEN       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      CHAT UI        │
                         │   Browser Client    │
                         └──────────┬──────────┘
                                    │
                              HTTP / REST
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      BACKEND        │
                         │   API / Controller  │
                         └──────────┬──────────┘
                                    │
                       ┌────────────┼────────────┐
                       │            │            │
                       ▼            ▼            ▼
                ┌────────────┐ ┌──────────┐ ┌─────────────┐
                │ Knowledge  │ │  Public  │ │ Conversation│
                │ Retrieval  │ │   APIs   │ │   Memory    │
                └─────┬──────┘ └────┬─────┘ └──────┬──────┘
                      │              │              │
                      ▼              ▼              │
                ┌────────────┐ ┌──────────┐        │
                │ Municipal  │ │ Weather/ │        │
                │ JSON/CSV   │ │  Alerts  │        │
                └────────────┘ └──────────┘        │
                       │             │              │
                       └─────────────┼──────────────┘
                                     ▼
                            ┌─────────────────┐
                            │  AI/RAG ENGINE  │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ GROQ / GEMINI   │
                            │      API        │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ Generated Answer│
                            └────────┬────────┘
                                     │
                                     ▼
                              ┌─────────────┐
                              │   Citizen   │
                              └─────────────┘
```

---

# 4. Architecture Layers

The system is divided into the following layers.

```text
┌───────────────────────────────┐
│ Presentation Layer            │
│ Chat UI                       │
├───────────────────────────────┤
│ Application Layer             │
│ Backend API                   │
├───────────────────────────────┤
│ Intelligence Layer            │
│ Query Understanding + RAG     │
├───────────────────────────────┤
│ Knowledge/Data Layer          │
│ Municipal JSON/CSV            │
├───────────────────────────────┤
│ Integration Layer             │
│ Public APIs                   │
├───────────────────────────────┤
│ External AI Layer             │
│ Groq API / Gemini API         │
└───────────────────────────────┘
```

---

# 5. Frontend Architecture

The frontend is responsible for interaction with the citizen.

## Responsibilities

- Display chat messages.
- Accept user input.
- Send requests to the backend.
- Display generated responses.
- Show loading status.
- Display errors.
- Maintain the visual conversation history.
- Provide suggested questions.

The frontend must not directly contain:

- LLM API keys
- Weather API keys
- Retrieval credentials
- Internal system prompts

All sensitive operations should occur on the backend.

---

# 6. Backend Architecture

The backend acts as the central application layer.

Its responsibilities include:

- Receiving user queries.
- Managing conversation sessions.
- Determining the appropriate processing path.
- Calling the retrieval system.
- Calling public APIs.
- Preparing context.
- Calling the LLM.
- Returning the generated answer.
- Handling errors.

Conceptual request flow:

```text
POST /chat
     │
     ▼
Validate Request
     │
     ▼
Load Conversation Context
     │
     ▼
Determine Query Type
     │
     ├──────────────┐
     │              │
     ▼              ▼
Municipal       Dynamic
Knowledge       Information
     │              │
     ▼              ▼
Retrieval       Public API
     │              │
     └───────┬──────┘
             ▼
       Build AI Context
             │
             ▼
        Groq/Gemini
             │
             ▼
       Validate Result
             │
             ▼
        Return Answer
```

---

# 7. LLM Provider Requirement

The instructor has specified that the project should use:

- **Groq API**, or
- **Gemini API**

Therefore, the application must use one of these providers for the GenAI component.

The architecture should isolate the LLM provider behind an internal interface.

Conceptually:

```text
                 AI Application
                      │
                      ▼
              ┌───────────────┐
              │ LLM Interface │
              └───────┬───────┘
                      │
              ┌───────┴────────┐
              ▼                ▼
          Gemini Adapter    Groq Adapter
              │                │
              ▼                ▼
         Gemini API         Groq API
```

This allows the provider to be changed without redesigning the complete chatbot.

---

# 8. Recommended LLM Strategy

The application should initially implement **one provider**, rather than unnecessarily integrating both.

Recommended development approach:

```text
Phase 1
   ↓
Choose one provider
   ↓
Implement and test
   ↓
Complete MVP
   ↓
Optionally add second provider
```

The final provider/model selection should be recorded in `decisions.md`.

---

# 9. RAG Architecture

The chatbot should use Retrieval-Augmented Generation.

The basic pipeline is:

```text
User Question
      │
      ▼
Query Processing
      │
      ▼
Retriever
      │
      ▼
Relevant Municipal Data
      │
      ▼
Context Construction
      │
      ▼
LLM
      │
      ▼
Grounded Response
```

The LLM should generate its response using the retrieved context.

---

# 10. Retrieval Strategy

The system should support retrieval from structured municipal data.

For the MVP, retrieval can begin with a **simple structured/semantic retrieval approach** rather than introducing unnecessary infrastructure.

Example:

```text
User:
"When is garbage collected in Zone A?"

          ↓

Retriever

          ↓

waste_collection.json

          ↓

Zone A
Monday
Wednesday
Friday
7:00 AM

          ↓

LLM

          ↓

"Garbage collection in Zone A occurs
on Monday, Wednesday and Friday at 7 AM."
```

A vector database can be introduced if semantic retrieval becomes necessary.

---

# 11. Knowledge Base Architecture

The municipal knowledge base should be organized into logical datasets.

Recommended structure:

```text
data/
│
├── waste_collection.json
├── permits.json
├── events.json
├── municipal_services.json
└── alerts.json
```

Each dataset should have a consistent structure.

Example:

```json
{
  "id": "WC001",
  "service": "Waste Collection",
  "zone": "Zone A",
  "days": [
    "Monday",
    "Wednesday",
    "Friday"
  ],
  "time": "07:00",
  "last_updated": "2026-09-01"
}
```

---

# 12. Knowledge Retrieval Components

The retrieval subsystem should contain:

```text
Query
  ↓
Query Normalization
  ↓
Intent / Category Detection
  ↓
Relevant Dataset Selection
  ↓
Record Retrieval
  ↓
Context Formatting
```

Example:

```text
"What documents do I need for a building permit?"

        ↓

Category:
Permit

        ↓

Dataset:
permits.json

        ↓

Relevant Record:
Building Permit

        ↓

Retrieved Context
```

---

# 13. Conversation Memory Architecture

The chatbot must support context retention.

For the MVP, conversation history can be maintained at the application/session level.

Example:

```text
Session
│
├── User message 1
├── Assistant response 1
├── User message 2
├── Assistant response 2
└── Current user message
```

The relevant conversation history is supplied to the AI model when processing a follow-up question.

---

# 14. Conversation Processing

Example:

```text
User:
"When is garbage collection in Zone A?"

        ↓

Context:
Zone A + Waste Collection

        ↓

Bot:
"Monday, Wednesday and Friday at 7 AM."

        ↓

User:
"What about Thursday?"

        ↓

Previous Context:
Waste Collection
Zone A

        ↓

Interpretation:
"Is waste collection available Thursday
in Zone A?"

        ↓

Retrieve Data

        ↓

Answer
```

---

# 15. Public API Architecture

The system must integrate with at least one public API.

The recommended MVP API category is:

**Weather**

Architecture:

```text
User
 │
 ▼
Backend
 │
 ▼
API Service
 │
 ▼
Weather API
 │
 ▼
Validate Response
 │
 ▼
Normalize Data
 │
 ▼
AI/RAG Layer
 │
 ▼
User-Friendly Answer
```

The API service should be isolated from the rest of the application.

---

# 16. Query Routing

The backend should determine whether a query requires:

### Static municipal data

Example:

> "What documents are required for a building permit?"

### Dynamic API data

Example:

> "What's the weather today?"

### Both

Example:

> "Is garbage collection scheduled today, and will it rain?"

Conceptually:

```text
                    User Query
                         │
                         ▼
                  Query Router
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
        Municipal       API           Both
        Knowledge     Request         Sources
           │             │             │
           └─────────────┼─────────────┘
                         ▼
                   Context Builder
                         │
                         ▼
                    LLM Provider
```

---

# 17. Context Builder

The Context Builder combines relevant information before sending it to the LLM.

Example:

```text
SYSTEM INSTRUCTIONS

+
CONVERSATION HISTORY

+

MUNICIPAL KNOWLEDGE

+

API DATA

+

CURRENT USER QUESTION
```

The LLM then generates the final response.

---

# 18. Grounding Strategy

The system should enforce the following priority:

```text
Trusted Retrieved Data
        ↓
Public API Data
        ↓
Conversation Context
        ↓
LLM Generation
```

The LLM should not override trusted retrieved information with unsupported assumptions.

---

# 19. Hallucination Prevention

The AI layer should include instructions such as:

```text
Answer using the supplied municipal context.

Do not invent municipal policies, schedules,
fees, deadlines, or procedures.

If the required information is unavailable,
clearly state that the information could not
be found.
```

The exact production system prompt should be maintained separately from this architecture document.

---

# 20. Project Structure

The initial project structure should follow a modular organization.

```text
municipal-chatbot/
│
├── frontend/
│   ├── ...
│   └── ...
│
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── utils/
│
├── ai/
│   ├── llm/
│   ├── prompts/
│   ├── retrieval/
│   └── memory/
│
├── data/
│   ├── waste_collection.json
│   ├── permits.json
│   ├── events.json
│   └── municipal_services.json
│
├── api/
│   ├── weather.py
│   └── ...
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
│
├── docs/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The exact folder structure may be adjusted during implementation if justified.

---

# 21. Configuration and Secrets

Sensitive information must never be hard-coded.

The project should use environment variables.

Example:

```text
GEMINI_API_KEY=...
```

or:

```text
GROQ_API_KEY=...
```

Additional API credentials should also be stored using environment variables.

The `.env` file must not be committed to version control.

A `.env.example` file should document required variables without containing real credentials.

---

# 22. API Abstraction

The AI provider should be abstracted.

Conceptual interface:

```text
LLMProvider
│
├── generate_response()
├── generate_with_context()
└── handle_error()
```

Implementations:

```text
GeminiProvider
GroqProvider
```

This allows:

```text
AI Provider
     │
     ├── Gemini
     │
     └── Groq
```

without changing the rest of the application.

---

# 23. Error Handling Architecture

Errors should be handled at the appropriate layer.

```text
Frontend Error
      ↓
User-friendly UI message

Backend Error
      ↓
Structured error response

LLM Error
      ↓
Fallback response

API Error
      ↓
Inform user that live information
is temporarily unavailable

Retrieval Error
      ↓
Knowledge unavailable response
```

Internal stack traces must not be shown to citizens.

---

# 24. Health Monitoring

The backend should provide a basic health endpoint.

Example:

```text
GET /health
```

Possible response:

```json
{
  "status": "healthy"
}
```

This can be used during development and demonstration.

---

# 25. Security Architecture

Security measures include:

### API keys

Stored only in environment variables.

### Client

Never receives private API credentials.

### Input

User input should be validated.

### External API

Responses should be validated before being used.

### LLM

System instructions should prevent unsupported municipal claims.

### Data

No unnecessary personal information should be stored.

---

# 26. Performance Architecture

The target is:

**< 20 seconds per normal request.**

Performance should be improved by:

- Keeping retrieval lightweight.
- Avoiding unnecessary API calls.
- Limiting conversation history to relevant context.
- Using efficient LLM models.
- Avoiding unnecessary processing steps.
- Reusing cached data where appropriate.

Caching may be introduced for frequently requested static or API information.

---

# 27. Scalability

The architecture should allow new services to be added.

Current:

```text
Waste
Permits
Events
General Services
Weather
```

Future:

```text
Parking
Water
Property Tax
Road Maintenance
Public Transport
Emergency Alerts
```

Adding a service should primarily involve:

1. Adding the dataset/API.
2. Defining its schema.
3. Registering its retrieval/routing logic.
4. Adding tests.

The core chatbot should not require major restructuring.

---

# 28. Data Flow — Static Query

Example:

> "What documents are required for a building permit?"

```text
Citizen
  ↓
Chat UI
  ↓
Backend
  ↓
Query Router
  ↓
Municipal Retrieval
  ↓
permits.json
  ↓
Relevant Permit Data
  ↓
Context Builder
  ↓
Gemini/Groq
  ↓
Generated Answer
  ↓
Chat UI
  ↓
Citizen
```

---

# 29. Data Flow — Dynamic Query

Example:

> "What's the weather today?"

```text
Citizen
  ↓
Chat UI
  ↓
Backend
  ↓
Query Router
  ↓
Weather Service
  ↓
Weather API
  ↓
Validated Weather Data
  ↓
Context Builder
  ↓
Gemini/Groq
  ↓
Generated Answer
  ↓
Citizen
```

---

# 30. Data Flow — Contextual Query

Example:

```text
User:
When is garbage collection in Zone A?

        ↓

Retrieve Zone A schedule

        ↓

Bot:
Monday, Wednesday and Friday.

        ↓

User:
What about Thursday?

        ↓

Conversation Memory

        ↓

Understand:
Thursday + Zone A + Waste Collection

        ↓

Retrieve

        ↓

Generate Answer
```

---

# 31. Data Flow — Unknown Query

Example:

> "What is the tax penalty for my specific property?"

```text
User Query
    ↓
Query Processing
    ↓
Knowledge Retrieval
    ↓
No reliable information
    ↓
Fallback Policy
    ↓
LLM
    ↓
"I couldn't find reliable information
about this in the available data."
```

The system must not fabricate an answer.

---

# 32. Component Responsibilities

| Component | Responsibility |
|---|---|
| Chat UI | Citizen interaction |
| Backend | Application orchestration |
| Query Router | Determine required processing path |
| Retrieval Engine | Find relevant municipal information |
| Knowledge Base | Store municipal information |
| API Service | Fetch dynamic external information |
| Context Builder | Combine relevant context |
| Conversation Memory | Maintain session context |
| LLM Adapter | Communicate with Gemini/Groq |
| Response Handler | Format final response |
| Testing Layer | Verify system behavior |

---

# 33. Technology Direction

The initial implementation should use:

### Language

**Python**

### Backend

A lightweight Python web framework such as:

- FastAPI, or
- Flask

### Frontend

A lightweight browser-based interface.

Possible implementation:

- HTML
- CSS
- JavaScript

or a rapid Python UI framework if appropriate.

### GenAI

One of:

- Gemini API
- Groq API

### Data

- JSON
- CSV

### Public API

Weather API or another appropriate public data API.

### Version Control

Git.

The exact technology selections should be recorded in `decisions.md`.

---

# 34. MVP Architecture

The simplest recommended MVP is:

```text
                 ┌──────────────┐
                 │   Browser    │
                 │   Chat UI    │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │ Python       │
                 │ Backend      │
                 └──────┬───────┘
                        │
             ┌──────────┼──────────┐
             │          │          │
             ▼          ▼          ▼
          JSON/CSV   Weather     Memory
             │          API         │
             └──────────┼──────────┘
                        ▼
                 ┌──────────────┐
                 │ RAG / AI     │
                 │ Processing   │
                 └──────┬───────┘
                        │
                   ┌────┴─────┐
                   ▼          ▼
                Gemini       Groq
                   │          │
                   └────┬─────┘
                        ▼
                     Answer
```

Only one LLM provider needs to be active in the MVP.

---

# 35. Architectural Constraints

The following are mandatory constraints:

1. The application must use either **Groq API or Gemini API**.
2. The LLM API key must remain server-side.
3. Municipal-specific answers must be grounded in retrieved data.
4. The system must support conversational context.
5. At least one public API must be integrated.
6. The chatbot must provide fallback behavior.
7. The system must target ≥80% answer accuracy.
8. Normal responses should target <20 seconds.
9. No unnecessary personal information should be collected.
10. Synthetic data must not be represented as actual official data.

---

# 36. Architecture Evolution

The architecture should evolve incrementally.

### Phase 1 — MVP

```text
JSON/CSV
+
Simple Retrieval
+
Gemini/Groq
+
Weather API
+
Basic Memory
+
Chat UI
```

### Phase 2

Potential additions:

```text
Vector Database
+
Better Semantic Search
+
More APIs
+
Admin Knowledge Management
```

### Phase 3

Potential production-oriented additions:

```text
Authentication
+
Database
+
Monitoring
+
Analytics
+
Scalable Deployment
+
Multilingual/Voice Support
```

These phases should not be implemented unless required.

---

# 37. Architecture Decision Principle

When choosing between two technically valid solutions:

> Prefer the simplest solution that satisfies the PRD.

The project should not introduce infrastructure merely because it is popular or technically impressive.

Every major architectural addition should have a demonstrable benefit.

---

# 38. Final Architecture Principle

The core architecture can be summarized as:

```text
             ASK
              ↓
          UNDERSTAND
              ↓
           RETRIEVE
              ↓
          VALIDATE
              ↓
           GENERATE
              ↓
           RESPOND
```

The fundamental design rule is:

> **The LLM generates the response; the knowledge base and APIs provide the facts.**