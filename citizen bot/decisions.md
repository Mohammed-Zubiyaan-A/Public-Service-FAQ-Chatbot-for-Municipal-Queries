# Architecture and Technical Decisions

## 1. Purpose

This document records the important technical and architectural decisions for the **Public Service FAQ Chatbot for Municipal Queries**.

The purpose is to:

- Prevent unnecessary technology changes.
- Keep all agents aligned.
- Explain why major technologies were selected.
- Provide a reference when implementation decisions are unclear.
- Maintain consistency between the PRD, architecture, design, and implementation.

A decision recorded here should not be changed casually.

If a major decision needs to change, the reason must be documented.

---

# 2. Decision Status

Each decision can have one of the following statuses:

- **Proposed** — Being considered.
- **Accepted** — Approved for implementation.
- **Rejected** — Considered but not selected.
- **Superseded** — Previously accepted but replaced by a newer decision.

Current decisions are marked **Accepted** unless otherwise specified.

---

# 3. Decision Summary

| Area | Decision | Status |
|---|---|---|
| Programming Language | Python | Accepted |
| LLM Provider | Groq or Gemini | Accepted |
| LLM Architecture | Provider abstraction | Accepted |
| Backend | FastAPI preferred | Accepted |
| Frontend | HTML/CSS/JavaScript | Accepted |
| Knowledge Format | JSON initially | Accepted |
| Retrieval | Structured/simple retrieval first | Accepted |
| Vector Database | Not required for initial MVP | Accepted |
| Conversation Memory | Session-based | Accepted |
| Public API | Weather API preferred | Accepted |
| Authentication | Not required for MVP | Accepted |
| Database | Not required initially | Accepted |
| Deployment | Local/demo deployment first | Accepted |
| Secrets | Environment variables | Accepted |
| Testing | Unit + integration + evaluation testing | Accepted |

---

# 4. Programming Language

## Decision

Use **Python** as the primary backend and AI development language.

## Reason

Python is suitable because:

- It has strong AI/LLM support.
- It provides libraries for API development.
- It simplifies data processing.
- It is easy for students to understand.
- It supports both retrieval and API integration.
- It reduces the number of programming languages required for backend development.

## Status

**Accepted**

---

# 5. LLM Provider

## Decision

The project must use either:

- **Google Gemini**, or
- **Groq**

as required by the instructor.

The final primary provider must be selected before implementation of the production LLM integration and recorded here.

## Initial Strategy

The application should be designed around an abstract interface:

```text
LLMProvider
├── GeminiProvider
└── GroqProvider
```

Only one provider needs to be implemented for the MVP.

A second provider can be added later if useful.

## Reason

Provider abstraction prevents the application from becoming tightly coupled to one API.

It also allows the project to switch between Groq and Gemini without rewriting the entire application.

## Status

**Accepted**

---

# 6. Gemini vs Groq

## Decision

Do not implement both providers unnecessarily during the first MVP iteration.

Select one primary provider and make the implementation work reliably first.

## Selection Criteria

The final choice should consider:

- API availability
- Free-tier suitability
- Response speed
- Model availability
- Ease of integration
- Reliability
- Rate limits
- Student/demo requirements

## Final Provider Selection

**Primary LLM Provider:** Google Gemini API  
**Default Model:** `gemini-2.5-flash` (with automatic fallback to `gemini-1.5-flash`)  
**Configuration:** Environment variable `GEMINI_API_KEY`  
**Offline/Test Mode:** Deterministic grounded response generator for 100% reproducible headless CI and unit testing  
**Public API:** Open-Meteo REST API (`https://api.open-meteo.com/v1/forecast`), requiring zero API keys and offering real-time weather and forecast data.

## Status

**Accepted**

---

# 7. Backend Framework

## Decision

Use **FastAPI** as the preferred backend framework.

## Reason

FastAPI provides:

- Simple API development.
- Python compatibility.
- Automatic API documentation.
- Good asynchronous support.
- Clean route structure.
- Easy integration with AI and external APIs.

The backend can expose endpoints such as:

```text
POST /chat
GET  /health
```

## Alternative

Flask may be used if implementation constraints make FastAPI impractical.

However, agents should not switch frameworks without documenting the reason.

## Status

**Accepted — FastAPI preferred**

---

# 8. Frontend Technology

## Decision

Use a lightweight browser frontend based on:

- HTML
- CSS
- JavaScript

## Reason

The chatbot does not require a complex frontend framework for the MVP.

A lightweight frontend:

- Reduces complexity.
- Is easy to demonstrate.
- Is easy to maintain.
- Keeps the focus on the AI/RAG functionality.
- Avoids unnecessary dependencies.

## Status

**Accepted**

---

# 9. Knowledge Base Format

## Decision

Use **JSON files** for the initial municipal knowledge base.

Recommended structure:

```text
data/
├── waste_collection.json
├── permits.json
├── events.json
├── municipal_services.json
└── alerts.json
```

## Reason

JSON is:

- Easy to create.
- Easy to read from Python.
- Human-readable.
- Suitable for structured FAQ data.
- Easy to modify during development.
- Suitable for a small academic project.

CSV can be supported if a dataset is provided in spreadsheet format.

## Status

**Accepted**

---

# 10. Retrieval Strategy

## Decision

Start with simple structured retrieval.

The system should initially use:

- Keyword matching
- Intent/category identification
- Structured field matching
- Basic semantic techniques if necessary

Example:

```text
User query
    ↓
Identify "waste collection"
    ↓
Identify "Zone A"
    ↓
Search waste_collection.json
    ↓
Return matching record
```

## Reason

The expected MVP dataset is relatively small and structured.

A simple retrieval system is:

- Easier to understand.
- Easier to test.
- Easier to explain during viva.
- Faster to implement.
- Less dependent on external infrastructure.

## Status

**Accepted**

---

# 11. Vector Database

## Decision

A vector database is **not required for the initial MVP**.

Do not introduce technologies such as:

- Chroma
- Pinecone
- Weaviate
- Milvus
- Qdrant

unless the existing retrieval approach proves inadequate.

## Reason

The project primarily uses structured municipal FAQ information.

A vector database would introduce additional:

- Dependencies
- Configuration
- Infrastructure
- Debugging complexity

without necessarily improving the MVP sufficiently.

## Future Use

Vector retrieval may be considered if:

- The knowledge base becomes large.
- Documents become mostly unstructured.
- Semantic retrieval accuracy is insufficient.

## Status

**Accepted — Not required for MVP**

---

# 12. RAG Strategy

## Decision

Use a lightweight retrieval-augmented generation approach.

The basic pipeline is:

```text
User Question
      ↓
Query Understanding
      ↓
Knowledge Retrieval
      ↓
Context Construction
      ↓
LLM
      ↓
Grounded Response
```

## Reason

The chatbot needs to answer questions based on municipal information rather than relying entirely on the LLM's pretrained knowledge.

## Core Rule

> **Retrieve first, generate second.**

## Status

**Accepted**

---

# 13. Conversation Memory

## Decision

Use **session-based conversation memory**.

The MVP does not require permanent user memory.

Memory should contain:

- Recent conversation messages.
- Relevant entities.
- Current service.
- Zone.
- Permit type.
- Date.
- Previous intent.
- Relevant retrieved context.

## Reason

This is sufficient to support follow-up questions without introducing unnecessary databases or user accounts.

## Status

**Accepted**

---

# 14. Database

## Decision

A traditional database is not required for the first MVP.

The application can initially use:

- JSON files.
- In-memory session state.
- External API responses.

## Reason

The expected dataset size is small and primarily read-oriented.

Introducing PostgreSQL, MySQL, or another database at the beginning would increase complexity.

## Future Use

A database may be introduced if the project later requires:

- Large datasets.
- Admin updates.
- Persistent conversations.
- User accounts.
- Analytics.
- Dynamic municipal records.

## Status

**Accepted — No database for initial MVP**

---

# 15. Public API

## Decision

Integrate at least one public API.

A **weather API** is the preferred initial integration.

## Reason

Weather provides information that:

- Changes dynamically.
- Cannot reliably be stored permanently in the FAQ dataset.
- Demonstrates real-time API integration.
- Is easy to demonstrate.

Example:

```text
User:
What is the weather today?

        ↓

Backend

        ↓

Weather API

        ↓

Current weather data

        ↓

LLM / Response formatter

        ↓

User
```

## Status

**Accepted**

---

# 16. API Abstraction

External APIs should be isolated from the main application logic.

Conceptually:

```text
api/
├── weather.py
└── other_services.py
```

The rest of the application should interact with clean functions rather than directly constructing external API requests throughout the codebase.

## Reason

This makes APIs:

- Easier to replace.
- Easier to test.
- Easier to mock.
- Easier to debug.

## Status

**Accepted**

---

# 17. Authentication

## Decision

No user authentication is required for the MVP.

## Reason

The chatbot provides public FAQ information and does not require citizen accounts.

Avoiding authentication reduces:

- Development time.
- Security complexity.
- Privacy concerns.

## Status

**Accepted**

---

# 18. Deployment

## Decision

Develop and demonstrate the MVP locally first.

The application should be able to run on a standard student computer.

Typical architecture:

```text
Browser
   ↓
Local Frontend
   ↓
Python Backend
   ↓
Gemini/Groq
   ↓
Public API
```

Cloud deployment may be considered later if required for demonstration.

## Status

**Accepted**

---

# 19. Secrets Management

## Decision

All API keys must be stored using environment variables.

Example:

```text
GEMINI_API_KEY=...
```

or:

```text
GROQ_API_KEY=...
```

The project must contain:

```text
.env.example
```

but must not commit the actual:

```text
.env
```

## Reason

API credentials must never be exposed in source code or frontend files.

## Status

**Accepted**

---

# 20. API Error Handling

## Decision

External API failures must be handled gracefully.

For example:

```text
Weather API unavailable
        ↓
Catch error
        ↓
Inform user
        ↓
Do not fabricate weather information
```

The application should not crash simply because an external API is unavailable.

## Status

**Accepted**

---

# 21. LLM Error Handling

If the LLM provider fails:

- Return a user-friendly error.
- Log appropriate debugging information.
- Do not expose internal credentials or technical secrets.
- Do not fabricate an answer as a replacement.

Example response:

> “I'm temporarily unable to generate a response. Please try again shortly.”

## Status

**Accepted**

---

# 22. Unknown Questions

## Decision

The chatbot should explicitly handle unsupported questions.

If no relevant information can be retrieved, the system should not invent an answer.

Example:

> “I don't currently have reliable information about that municipal service.”

If appropriate, the chatbot can suggest supported categories.

## Status

**Accepted**

---

# 23. Clarification Questions

## Decision

The chatbot should ask clarification questions when required information is missing.

Example:

```text
User:
When is waste collected?

System:
Which zone are you asking about?
```

The chatbot must not randomly select a zone.

## Status

**Accepted**

---

# 24. Response Generation

## Decision

The LLM is responsible primarily for:

- Understanding natural language.
- Using retrieved context.
- Generating conversational responses.
- Handling follow-up questions.
- Formatting information clearly.

The LLM is not the authoritative source of municipal facts.

## Principle

> **The knowledge base provides facts; the LLM communicates them.**

## Status

**Accepted**

---

# 25. Response Validation

Before returning a response, the system should verify where practical that:

- Relevant context was available.
- The response does not contradict retrieved data.
- Unsupported facts are not unnecessarily introduced.
- API-dependent information came from the API.
- Errors are not presented as facts.

More advanced validation can be added later.

## Status

**Accepted**

---

# 26. Accuracy Target

## Decision

The project should achieve at least:

> **80% correct answers**

during evaluation.

The evaluation dataset should contain representative questions covering:

- Waste collection
- Permits
- Events
- Municipal services
- Weather/API queries
- Follow-up questions
- Unknown questions

## Status

**Accepted**

---

# 27. Performance Target

## Decision

The target response time is:

> **Less than 20 seconds**

The team should measure response time during testing.

Performance should be improved by avoiding unnecessary:

- LLM calls
- API calls
- Retrieval operations
- Repeated processing

## Status

**Accepted**

---

# 28. UI Decision

## Decision

Use a single-page chat interface.

The primary screen should contain:

```text
------------------------------------------------
| Municipal Service Assistant                  |
| Your digital assistant for public services   |
------------------------------------------------
|                                              |
| Assistant: Hello! How can I help?            |
|                                              |
| User: When is waste collected in Zone A?     |
|                                              |
| Assistant: ...                               |
|                                              |
------------------------------------------------
| Type your question...                  [Send]|
------------------------------------------------
```

## Reason

The application is fundamentally conversational, so the UI should focus on the chat experience.

## Status

**Accepted**

---

# 29. Accessibility

## Decision

The interface should follow basic accessibility principles.

It should provide:

- Readable text.
- Sufficient contrast.
- Keyboard usability.
- Clear buttons.
- Meaningful labels.
- Responsive layout.

Accessibility has priority over decorative visual effects.

## Status

**Accepted**

---

# 30. Data Privacy

## Decision

No unnecessary personal data should be collected.

The application does not require:

- Aadhaar
- Passwords
- Bank information
- Payment information
- Government identification numbers
- Permanent citizen profiles

## Status

**Accepted**

---

# 31. Synthetic Data

## Decision

Synthetic municipal data may be used if appropriate public datasets are unavailable.

However, it must be explicitly labeled as demonstration data.

Example:

```text
Dataset Type: Synthetic
Purpose: Academic Demonstration
```

The chatbot must not falsely claim that synthetic information is official municipal policy.

## Status

**Accepted**

---

# 32. Technology Stability Rule

Once the MVP stack is selected, agents should not repeatedly change technologies.

For example, do not move:

```text
FastAPI → Flask → Django → Node.js
```

without a documented reason.

Likewise, do not repeatedly change:

```text
Gemini → Groq → another provider
```

unless required.

Technology changes should happen only when there is a clear technical, project, or instructor-related reason.

---

# 33. Simplicity Rule

When two technologies can solve the same problem, prefer the simpler one.

Example:

```text
Small JSON dataset
        ↓
Simple retrieval
```

is preferable to:

```text
Small JSON dataset
        ↓
Embedding pipeline
        ↓
Vector database
        ↓
Retriever
        ↓
Complex infrastructure
```

unless testing demonstrates that the simple approach is insufficient.

---

# 34. Decision Change Process

If an agent believes an existing decision should change:

### Step 1

Identify the current decision.

### Step 2

Explain why it is insufficient.

### Step 3

Propose an alternative.

### Step 4

Evaluate:

- Complexity
- Reliability
- Performance
- Security
- Cost
- Maintainability
- Academic usefulness

### Step 5

Obtain approval through the project decision process.

### Step 6

Update this document.

### Step 7

Update affected documentation.

### Step 8

Only then modify the implementation.

---

# 35. Decision Record Format

Future decisions should use this structure:

```text
## Decision X: <Title>

Date:
Status:
Decision:

Reason:

Alternatives considered:

Consequences:

Affected files:
```

This ensures that future agents understand not only what was selected, but why it was selected.

---

# 36. Initial Architecture Decision

The accepted initial architecture is:

```text
                 ┌──────────────────────┐
                 │      Web Browser     │
                 │    Chat Interface    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │    Python Backend    │
                 │       FastAPI        │
                 └──────────┬───────────┘
                            │
               ┌────────────┼─────────────┐
               ▼            ▼             ▼
        ┌────────────┐ ┌──────────┐ ┌─────────────┐
        │ Knowledge  │ │ Session  │ │ Public API  │
        │ Retrieval  │ │ Memory   │ │  Weather    │
        └──────┬─────┘ └────┬─────┘ └──────┬──────┘
               │            │              │
               └────────────┼──────────────┘
                            ▼
                 ┌──────────────────────┐
                 │    Context Builder   │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │    Groq / Gemini     │
                 │         LLM          │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │ Response Processing  │
                 └──────────┬───────────┘
                            ▼
                 ┌──────────────────────┐
                 │      Chat UI         │
                 └──────────────────────┘
```

## Status

**Accepted**

---

# 37. Initial Project Structure Decision

The preferred project structure is:

```text
municipal-chatbot/
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
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
├── api/
│   └── weather.py
│
├── data/
│   ├── waste_collection.json
│   ├── permits.json
│   ├── events.json
│   └── municipal_services.json
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

This structure may be simplified if the actual MVP implementation does not require every directory.

---

# 38. Final Technology Stack

The intended MVP stack is:

```text
Language:
Python

Backend:
FastAPI

Frontend:
HTML + CSS + JavaScript

LLM:
Groq OR Gemini

Knowledge:
JSON / CSV

Retrieval:
Simple structured retrieval

Memory:
Session-based

Public API:
Weather API

Database:
None initially

Authentication:
None

Testing:
Python testing tools + evaluation dataset

Version Control:
Git
```

---

# 39. Final Decision Principle

Technical decisions must serve the project requirements.

The team should prioritize:

```text
Accuracy
   ↓
Reliability
   ↓
Security
   ↓
Simplicity
   ↓
Performance
   ↓
Maintainability
   ↓
Visual polish
```

The project should not become unnecessarily complicated simply to demonstrate more technologies.

---

# 40. Final Statement

The chatbot is an **information assistant**, not an official municipal decision-making system.

Its architecture is intentionally designed so that:

> **The knowledge base and public APIs provide the facts, the retrieval system finds the relevant facts, conversation memory provides context, and Groq/Gemini generates a natural-language response.**

All future technical decisions should preserve this architecture unless a documented decision explicitly changes it.