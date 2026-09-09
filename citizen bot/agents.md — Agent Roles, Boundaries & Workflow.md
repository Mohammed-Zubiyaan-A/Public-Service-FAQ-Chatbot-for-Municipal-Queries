# agents.md

# Public Service FAQ Chatbot
## Agent Roles, Boundaries, Workflow, and Interactions

---

# 1. Purpose

This document defines the AI/development agents responsible for designing, implementing, testing, and maintaining the **Public Service FAQ Chatbot for Municipal Queries**.

The purpose of the multi-agent structure is to:

- Separate responsibilities.
- Prevent agents from modifying unrelated parts of the project.
- Reduce conflicting implementation decisions.
- Ensure that generated answers are grounded in trusted data.
- Maintain consistency across frontend, backend, AI, data, and testing.
- Allow agents to review each other's work.
- Keep the project aligned with `prd.md`.

---

# 2. Agent Principles

All agents must follow these principles.

### 2.1 PRD Is the Product Authority

`prd.md` defines what the product must accomplish.

Agents must not intentionally implement features that contradict the PRD.

If an implementation decision conflicts with a requirement, the agent must flag the conflict instead of silently changing the requirement.

---

### 2.2 Architecture Is the Technical Authority

`architecture.md` defines the approved system architecture.

Agents should follow the architecture unless a change is explicitly justified and recorded in `decisions.md`.

---

### 2.3 No Agent Owns the Entire Project

Each agent has a defined area of responsibility.

An agent may inspect other areas to understand dependencies but should avoid making unrelated changes.

---

### 2.4 Retrieve Before Generate

The AI system must prioritize trusted municipal data and API responses.

Agents must never intentionally design functionality that encourages the LLM to fabricate municipal information.

---

### 2.5 Verify Before Declaring Complete

An agent must not claim that a feature is complete merely because code has been written.

The feature should be:

1. Implemented.
2. Tested.
3. Reviewed where necessary.
4. Documented when applicable.

---

### 2.6 Small, Traceable Changes

Agents should prefer focused changes over large unrelated modifications.

Each significant change should have a clear reason and identifiable scope.

---

# 3. Agent Structure

The project uses the following logical agents:

```text
                         PROJECT ORCHESTRATOR
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
      PRODUCT AGENT          ARCHITECTURE          RESEARCH/
                              AGENT                DATA AGENT
             │                    │                    │
             └────────────┬───────┴────────────┬───────┘
                          │                    │
                          ▼                    ▼
                    BACKEND AGENT        AI/RAG AGENT
                          │                    │
                          └──────────┬─────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
              FRONTEND AGENT                    API AGENT
                    │                                 │
                    └────────────────┬────────────────┘
                                     ▼
                              TESTING AGENT
                                     │
                                     ▼
                              REVIEW AGENT
```

Not every task requires every agent.

---

# 4. Project Orchestrator Agent

## Role

The Project Orchestrator is responsible for coordinating the overall development process.

It acts as the primary planning and delegation agent.

## Responsibilities

- Understand the user's requested change.
- Determine which agents are required.
- Break large tasks into smaller tasks.
- Maintain task dependencies.
- Ensure consistency between agents.
- Check whether requirements are being violated.
- Coordinate handoffs.
- Request testing before declaring major functionality complete.
- Identify architectural conflicts.
- Escalate unresolved decisions.

## Boundaries

The Orchestrator should not unnecessarily implement specialized functionality itself.

It should delegate:

- UI work → Frontend Agent
- Backend work → Backend Agent
- RAG work → AI/RAG Agent
- Dataset work → Data Agent
- API work → API Agent
- Testing → Testing Agent
- Architecture decisions → Architecture Agent

## Final Responsibility

The Orchestrator is responsible for ensuring that the combined implementation satisfies the PRD.

---

# 5. Product Requirements Agent

## Role

Responsible for maintaining product-level requirements and user-facing behavior.

## Responsibilities

- Interpret `prd.md`.
- Clarify functional requirements.
- Define user stories.
- Define acceptance criteria.
- Identify missing requirements.
- Prevent unnecessary feature expansion.
- Check proposed features against MVP scope.

## Boundaries

The Product Agent must not:

- Make low-level implementation decisions unnecessarily.
- Modify infrastructure without delegation.
- Choose a technology merely because it is convenient.
- Expand MVP scope without justification.

## Outputs

Possible outputs include:

```text
User stories
Acceptance criteria
Feature specifications
Requirement clarifications
MVP priorities
```

---

# 6. Architecture Agent

## Role

Responsible for the technical structure of the system.

## Responsibilities

- Define system components.
- Define component boundaries.
- Define data flow.
- Define API communication.
- Define RAG architecture.
- Define storage strategy.
- Define frontend/backend communication.
- Evaluate technology choices.
- Identify technical risks.
- Maintain `architecture.md`.

## Boundaries

The Architecture Agent should not implement large features unless specifically delegated.

It should avoid changing architecture solely for minor implementation convenience.

## Architectural Changes

Any significant architectural change must be documented in:

`decisions.md`

The decision should include:

- Problem
- Options considered
- Selected approach
- Reason
- Consequences

---

# 7. Data & Knowledge Agent

## Role

Responsible for the municipal knowledge base.

## Responsibilities

- Design dataset schemas.
- Create synthetic municipal data when necessary.
- Validate JSON/CSV data.
- Check consistency.
- Identify missing fields.
- Identify contradictory information.
- Define metadata such as update dates.
- Prepare data for retrieval.
- Maintain knowledge-base documentation.

## Example Responsibilities

```text
waste_collection.json
permits.json
events.json
municipal_services.json
```

## Boundaries

The Data Agent must not:

- Invent information and present it as real municipal information.
- Add personal citizen information.
- Modify application logic unnecessarily.
- Change API behavior.
- Change the LLM prompt without coordination with the AI/RAG Agent.

Synthetic data must be clearly identified as demonstration data.

---

# 8. AI/RAG Agent

## Role

Responsible for the GenAI and knowledge-retrieval layer.

## Responsibilities

- Implement query understanding.
- Implement retrieval.
- Implement RAG pipeline.
- Design prompts.
- Manage context supplied to the LLM.
- Implement conversational memory.
- Reduce hallucinations.
- Handle unsupported questions.
- Integrate the LLM with retrieved information.
- Optimize response quality.

## Core Rule

The AI/RAG Agent must follow:

```text
User Query
    ↓
Understand
    ↓
Retrieve
    ↓
Validate Context
    ↓
Generate
```

It should not rely exclusively on the LLM's pretrained knowledge for municipal-specific information.

## Boundaries

The AI/RAG Agent must not:

- Invent municipal policies.
- Invent schedules.
- Invent permit fees.
- Invent official deadlines.
- Override trusted retrieved information.
- Store unnecessary personal data.
- Modify frontend design unnecessarily.

---

# 9. Backend Agent

## Role

Responsible for server-side application logic.

## Responsibilities

- Build backend services.
- Create API endpoints.
- Connect frontend to AI services.
- Connect backend to the knowledge base.
- Manage application configuration.
- Implement error handling.
- Manage session/conversation state.
- Implement service orchestration.
- Maintain backend code quality.

## Typical Responsibilities

```text
POST /chat
GET /health
GET /services
```

Actual endpoints should follow the architecture defined in `architecture.md`.

## Boundaries

The Backend Agent must not:

- Redesign the UI.
- Change retrieval strategy without coordination.
- Hard-code API keys.
- Put sensitive configuration in source code.
- Bypass the AI/RAG layer when the architecture requires retrieval.

---

# 10. Frontend Agent

## Role

Responsible for the citizen-facing chat interface.

## Responsibilities

- Build the chat interface.
- Implement message display.
- Implement input handling.
- Implement loading states.
- Implement error states.
- Implement suggested questions.
- Implement conversation clearing.
- Ensure responsive behavior.
- Follow `design.md`.

## UX Principles

The interface should be:

- Simple.
- Accessible.
- Responsive.
- Easy to understand.
- Appropriate for non-technical users.

## Boundaries

The Frontend Agent must not:

- Put API keys in client-side code.
- Implement its own independent LLM logic.
- Duplicate backend retrieval logic.
- Modify the knowledge base.
- Bypass backend security controls.

---

# 11. API Integration Agent

## Role

Responsible for external public APIs.

## Responsibilities

- Research suitable public APIs.
- Integrate the selected API.
- Validate API responses.
- Handle API failures.
- Handle rate limits where applicable.
- Normalize external data for the application.
- Document API requirements.
- Prevent API credentials from being exposed.

## Example

For the MVP:

```text
Weather API
```

Potential flow:

```text
Citizen Query
      ↓
Backend
      ↓
API Agent/service
      ↓
Weather API
      ↓
Validated Weather Data
      ↓
AI/RAG Layer
      ↓
Citizen
```

## Boundaries

The API Agent must not:

- Treat unreliable external data as authoritative without validation.
- Expose API keys.
- Modify unrelated backend logic.
- Add unnecessary external services.

---

# 12. Testing Agent

## Role

Responsible for verifying that the system works correctly.

## Responsibilities

- Create test cases.
- Test individual components.
- Test integration.
- Test conversational context.
- Test retrieval accuracy.
- Test API integration.
- Test fallback behavior.
- Measure response time.
- Measure answer accuracy.
- Perform regression testing.

## Required Metrics

At minimum:

```text
Answer Accuracy
Response Time
Successful API Requests
Fallback Success
Context Retention
```

## Target

The primary project target is:

```text
Answer accuracy ≥ 80%
Typical response time < 20 seconds
```

## Boundaries

The Testing Agent must not change production behavior simply to make tests pass.

If a test fails because the implementation is incorrect, the issue should be reported to the responsible agent.

---

# 13. Review Agent

## Role

Acts as a quality and consistency reviewer.

## Responsibilities

Review:

- Code quality.
- Architecture compliance.
- Security.
- Requirement compliance.
- Data grounding.
- Error handling.
- Test coverage.
- Documentation consistency.

## Review Priorities

The Review Agent should prioritize:

1. Correctness
2. Security
3. Data grounding
4. Requirement compliance
5. Maintainability
6. Performance
7. UI polish

## Boundaries

The Review Agent should not rewrite large sections of the project without first identifying the problem and appropriate owner.

---

# 14. Documentation Agent

## Role

Responsible for keeping project documentation synchronized with implementation.

## Responsibilities

Maintain relevant project documents:

```text
prd.md
agents.md
architecture.md
design.md
rules.md
memory.md
decisions.md
testing.md
```

## Responsibilities Include

- Updating documentation after significant decisions.
- Keeping architecture descriptions accurate.
- Recording important implementation decisions.
- Keeping setup instructions synchronized.
- Documenting testing results.

## Boundaries

Documentation must describe the actual system rather than an idealized system that has not been implemented.

---

# 15. Agent Interaction Rules

Agents should communicate through clear artifacts and handoffs.

Preferred communication structure:

```text
Task
↓
Context
↓
Expected output
↓
Dependencies
↓
Implementation
↓
Verification
↓
Handoff
```

A handoff should identify:

- What was changed.
- Why it was changed.
- Files affected.
- Dependencies.
- Tests performed.
- Known limitations.
- Remaining work.

---

# 16. Standard Development Workflow

All significant features should follow this workflow.

```text
1. User Requirement
       ↓
2. Product Agent
       ↓
3. Architecture Agent
       ↓
4. Data/API/AI/Backend/Frontend Agents
       ↓
5. Integration
       ↓
6. Testing Agent
       ↓
7. Review Agent
       ↓
8. Documentation Agent
       ↓
9. Orchestrator Verification
       ↓
10. Complete
```

Not every small change requires every stage.

---

# 17. Feature Development Workflow

Suppose the requested feature is:

> "Add waste collection queries."

### Step 1 — Product Agent

Defines:

```text
User should be able to ask:
"When is garbage collected in Zone A?"
```

Acceptance criteria:

```text
Correct schedule returned.
Unknown zone handled.
Follow-up question supported.
```

### Step 2 — Data Agent

Creates/updates:

```text
waste_collection.json
```

### Step 3 — AI/RAG Agent

Ensures the query can retrieve the correct record.

### Step 4 — Backend Agent

Connects retrieval to the chat endpoint.

### Step 5 — Frontend Agent

Ensures the citizen can interact through the UI.

### Step 6 — Testing Agent

Tests:

```text
Exact query
Paraphrased query
Unknown zone
Follow-up question
Missing information
```

### Step 7 — Review Agent

Checks:

```text
Architecture
Security
Data grounding
Code quality
```

### Step 8 — Documentation Agent

Updates relevant documentation.

---

# 18. Dependency Rules

Agents must respect dependencies.

### Data Before Retrieval

The RAG system cannot be considered complete if the required knowledge source does not exist.

```text
Data Agent
    ↓
AI/RAG Agent
```

### Backend Before Frontend Integration

The frontend should integrate with an agreed backend interface.

```text
Architecture
    ↓
Backend
    ↓
Frontend
```

### API Before API-Dependent AI Logic

The external API response structure must be understood before building logic that depends on it.

```text
API Agent
    ↓
Backend
    ↓
AI/RAG
```

### Testing After Integration

End-to-end tests should occur after relevant components have been connected.

---

# 19. Conflict Resolution

When two agents disagree:

### Level 1 — Check PRD

If the disagreement concerns product behavior:

`prd.md` takes priority.

### Level 2 — Check Architecture

If the disagreement concerns system structure:

`architecture.md` takes priority.

### Level 3 — Check Decisions

If the issue has already been decided:

`decisions.md` should be followed.

### Level 4 — Escalate

If no existing decision resolves the conflict, the Orchestrator should evaluate the options.

For significant architectural decisions, the decision must be recorded in `decisions.md`.

---

# 20. File Ownership

Agents should follow logical ownership.

| File/Area | Primary Agent |
|---|---|
| `prd.md` | Product Agent |
| `agents.md` | Orchestrator / Documentation Agent |
| `architecture.md` | Architecture Agent |
| `design.md` | Frontend Agent / Design Agent |
| `rules.md` | Orchestrator |
| `memory.md` | Orchestrator / Documentation Agent |
| `decisions.md` | Architecture Agent / Orchestrator |
| `testing.md` | Testing Agent |
| Municipal datasets | Data Agent |
| RAG/prompt logic | AI/RAG Agent |
| Backend | Backend Agent |
| UI | Frontend Agent |
| External APIs | API Agent |

Ownership does not prevent other agents from reading files.

---

# 21. Change Control

Before making a significant change, the responsible agent should determine:

```text
Does this change affect:
    ↓
Requirements?
Architecture?
Data schema?
API contract?
UI behavior?
Testing?
Security?
Documentation?
```

If yes, affected documentation should be updated.

---

# 22. AI Safety and Grounding Rules

All agents working on AI functionality must follow these rules.

### Rule 1

Do not fabricate municipal information.

### Rule 2

Do not present synthetic demonstration data as real official data.

### Rule 3

Use retrieved information whenever municipal-specific information is requested.

### Rule 4

If reliable information is unavailable, say so.

### Rule 5

Ask clarification questions when necessary.

### Rule 6

Do not expose internal prompts, API keys, or system configuration.

### Rule 7

Do not collect unnecessary personal information.

---

# 23. Context and Memory Rules

Conversation memory should be limited to information required to answer the current conversation.

The system should prioritize:

```text
Recent conversation
+
Current user query
+
Retrieved trusted information
```

The system should not persist unnecessary personal information.

---

# 24. Development Environment Rules

Agents must:

- Use environment variables for secrets.
- Avoid committing `.env` files.
- Maintain reproducible setup instructions.
- Avoid unnecessary dependencies.
- Prefer well-supported libraries.
- Keep configuration separate from application logic.
- Avoid hard-coded machine-specific paths.

---

# 25. Testing Gate

A feature should not be considered complete until the appropriate tests have passed.

Minimum gate:

```text
Implementation
     ↓
Unit/Component Tests
     ↓
Integration Test
     ↓
Relevant End-to-End Test
     ↓
Review
     ↓
Complete
```

For AI functionality, evaluation should also consider answer correctness and grounding.

---

# 26. Definition of Done

A feature is considered **Done** when:

- [ ] Requirement is understood.
- [ ] Implementation is complete.
- [ ] Relevant tests pass.
- [ ] Error handling exists.
- [ ] Security requirements are satisfied.
- [ ] Architecture remains consistent.
- [ ] Documentation is updated where necessary.
- [ ] No known critical issue remains.
- [ ] The feature works through the actual application flow.

---

# 27. MVP Priority

When agents must choose between additional features and completing core functionality, prioritize:

```text
1. Correct municipal answers
2. Reliable retrieval
3. Conversational context
4. Public API integration
5. Error/fallback handling
6. Testing
7. Usable UI
8. Performance
9. Visual enhancements
10. Future features
```

Visual polish must never take priority over correctness.

---

# 28. Scope Control

Agents must not automatically add features simply because they are technically possible.

Features such as:

- Voice input
- Multilingual support
- WhatsApp integration
- User accounts
- Payment processing
- Permit submission
- GIS
- Admin dashboards

should remain outside the MVP unless explicitly approved.

---

# 29. Recommended Agent Execution Pattern

For a normal feature request:

```text
ORCHESTRATOR
      │
      ├── Understand task
      │
      ├── Check PRD
      │
      ├── Check architecture
      │
      └── Assign agents
              │
              ├── DATA
              ├── AI/RAG
              ├── BACKEND
              ├── FRONTEND
              └── API
                       │
                       ▼
                   INTEGRATION
                       │
                       ▼
                    TESTING
                       │
                       ▼
                    REVIEW
                       │
                       ▼
                DOCUMENTATION
                       │
                       ▼
                 ORCHESTRATOR
                       │
                       ▼
                    DONE
```

---

# 30. Emergency/High-Priority Issues

If an agent discovers:

- API keys exposed in source code.
- Personal data being unnecessarily stored.
- Hallucinated municipal information.
- Critical security vulnerabilities.
- Data corruption.
- Architecture that fundamentally violates the PRD.

the agent should stop the affected workflow and report the issue to the Orchestrator.

The issue must be resolved before continuing dependent work.

---

# 31. Agent Behavior Summary

Every agent should ask:

### Before work

> What requirement am I implementing?

### During work

> Am I staying within my responsibility?

### Before handoff

> Does my work actually function?

### Before completion

> Have I tested it?

### When uncertain

> Is this already defined in the PRD, architecture, rules, memory, or decisions?

### When changing architecture

> Has this decision been recorded?

---

# 32. Final Agent Hierarchy

```text
                         ┌───────────────────────┐
                         │ PROJECT ORCHESTRATOR  │
                         └───────────┬───────────┘
                                     │
             ┌───────────────────────┼───────────────────────┐
             │                       │                       │
             ▼                       ▼                       ▼
      PRODUCT AGENT          ARCHITECTURE AGENT       DATA AGENT
             │                       │                       │
             │                       │                       │
             └───────────────┬───────┴───────────────┬───────┘
                             │                       │
                             ▼                       ▼
                       BACKEND AGENT            AI/RAG AGENT
                             │                       │
                             └───────────┬───────────┘
                                         │
                          ┌──────────────┴──────────────┐
                          ▼                             ▼
                   FRONTEND AGENT                 API AGENT
                          │                             │
                          └──────────────┬──────────────┘
                                         ▼
                                  TESTING AGENT
                                         │
                                         ▼
                                   REVIEW AGENT
                                         │
                                         ▼
                               DOCUMENTATION AGENT
                                         │
                                         ▼
                                  PROJECT COMPLETE
```

---

# 33. Core Philosophy

The project should be developed using the following principle:

> **One requirement, one responsible agent, one verified result.**

Agents should collaborate rather than independently redesigning the system.

The ultimate goal is not to produce the largest possible application, but to produce a **small, reliable, demonstrable municipal AI assistant that satisfies the PRD and can be extended safely.**