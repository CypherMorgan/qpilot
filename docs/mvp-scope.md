# CypherPilot — MVP Scope

## Release: CypherPilot v0.1.0 — "Foundation" (Phase 2)

**Goal:** Establish the platform skeleton — backend, frontend, database, AI pipeline, and developer infrastructure — with zero business features.

**Deliverables:**

- [ ] FastAPI application with modular router structure
- [ ] React + TypeScript + Vite frontend shell (placeholder pages)
- [ ] PostgreSQL database with SQLAlchemy 2.0 + Alembic migrations
- [ ] Docker + Docker Compose for local development
- [ ] AI Provider abstraction layer with OpenRouter adapter (default) and Ollama adapter
- [ ] Prompt Manager with versioned Markdown prompt templates
- [ ] CI/CD pipeline (GitHub Actions: lint, type-check, test, build)
- [ ] Development tooling: Ruff, MyPy, PyTest, pre-commit hooks
- [ ] Logging and exception handling infrastructure
- [ ] Configuration management (environment-based, `.env` support)
- [ ] Dependency injection container
- [ ] Pydantic models for common request/response schemas
- [ ] API documentation auto-generation
- [ ] This release contains **no business logic** for test generation or analysis

---

## Release: CypherPilot v0.2.0 — "Requirement Analysis" (MVP Module 1)

**Goal:** QA engineers can paste or upload a feature requirement and receive structured test case suggestions.

**User Story:**

> As a QA engineer, I want to upload a requirements document (Markdown or plain text) so that CypherPilot generates a comprehensive set of test cases including functional, negative, boundary, and edge cases with acceptance criteria.

**Deliverables:**

- [ ] Requirements upload page (text input + file upload)
- [ ] AI-powered requirement parsing and test case generation
- [ ] Structured output: test suite with categorized test cases
- [ ] Ability to copy/export generated test cases
- [ ] History of past analyses
- [ ] Unit and integration tests

**Acceptance Criteria:**

- Uploading "User must enter a valid email address" generates ≥8 test cases
- Output includes: happy path, negative cases, boundary values, edge cases
- Each test case has: ID, title, description, preconditions, steps, expected result, priority, category
- All outputs pass Pydantic validation
- Generation completes within 30 seconds for typical requirements (<500 words)

---

## Release: CypherPilot v0.3.0 — "API Test Generation" (MVP Module 2)

**Goal:** QA engineers can upload an OpenAPI 3.x specification and receive a downloadable PyTest test suite.

**User Story:**

> As a QA engineer, I want to upload an OpenAPI specification so that CypherPilot generates a complete PyTest API test suite covering all endpoints, status codes, request/response schemas, and error scenarios.

**Deliverables:**

- [ ] OpenAPI spec upload page (YAML/JSON file upload)
- [ ] Spec parsing and validation
- [ ] AI-powered test generation for each endpoint
- [ ] Downloadable PyTest files (one per endpoint or resource)
- [ ] Generated tests include: status code validation, schema validation, error handling, edge cases
- [ ] Generated config file (conftest.py) with fixtures
- [ ] History of generated suites
- [ ] Unit and integration tests

**Acceptance Criteria:**

- Uploading a Petstore-level OpenAPI spec (≥10 endpoints) generates tests for every endpoint
- Generated tests are syntactically valid Python (can be imported without errors)
- Each test function includes: proper fixtures, assertions, docstrings
- Output includes: `conftest.py`, `test_<resource>.py` files
- Generation completes within 60 seconds for standard specs (<50 endpoints)

---

## Release: CypherPilot v0.4.0 — "Automation Failure Analysis" (MVP Module 3)

**Goal:** QA engineers can upload automation failure artifacts and receive structured root-cause analysis.

**User Story:**

> As a QA engineer, I want to upload test failure logs, screenshots, and page source so that CypherPilot analyzes the failure and provides a root cause, confidence score, suggested fix, and prevention recommendation.

**Deliverables:**

- [ ] Failure analysis upload page (logs + screenshot + page source)
- [ ] AI-powered failure analysis (text-based analysis first; screenshot analysis as enhancement)
- [ ] Structured output: root cause, confidence, suggested fix, prevention
- [ ] History of past analyses with status tracking
- [ ] Unit and integration tests

**Acceptance Criteria:**

- Uploading a Playwright failure log + page source produces a plausible root cause
- Output includes: root cause description, confidence level, suggested code fix, prevention tip
- Analysis handles: assertion failures, timeout errors, element-not-found errors, network errors
- Generation completes within 45 seconds for standard inputs

---

## MVP Definition of Done

Phase 3 (v0.2.0–v0.4.0) is complete when:

- [ ] All three modules are functional end-to-end
- [ ] AI provider abstraction works with OpenRouter (primary) and Ollama (local/offline) and is wired for extensibility
- [ ] All prompts are in versioned Markdown files, not hardcoded in Python
- [ ] All responses pass Pydantic validation before being returned
- [ ] Test coverage ≥80% for business logic modules
- [ ] Type-checking passes with MyPy (strict mode)
- [ ] Linting passes with Ruff
- [ ] Docker Compose starts the full stack with a single command
- [ ] CI passes on every PR
- [ ] ADRs written for all major architectural decisions
