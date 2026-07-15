# ADR-005: API Design

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | 2026-07-01 |
| **Author(s)** | CypherPilot Engineering Team |
| **Supersedes** | None |
| **Superseded by** | N/A |

---

## Context

CypherPilot exposes a RESTful HTTP API consumed by the React frontend. The API must support three MVP modules (Requirement Analysis, API Test Generation, Failure Analysis), file uploads, history listing, and structured result retrieval.

The API is the contract between frontend and backend — it must be:
- **Consistent** — every endpoint follows the same conventions for naming, status codes, error format, and pagination
- **Discoverable** — FastAPI auto-generates OpenAPI docs that are useful for both the frontend developer and future API consumers
- **Extensible** — new modules and endpoints can be added without breaking existing contracts
- **Self-documenting** — the schema tells you what to send and what you'll receive

---

## Problem Statement

Design the CypherPilot REST API such that:

1. All three MVP modules have endpoints that follow identical patterns
2. File uploads (requirements, OpenAPI specs, logs, screenshots) are handled with standard multipart/form-data
3. Analysis results are returned as structured JSON, with generated Python files available for download
4. History listing supports pagination, filtering by type, and sorting by date
5. Error responses are consistent across all endpoints — the frontend can parse any error predictably
6. The API is versioned from day one (`/api/v1/`) to allow future evolution

---

## Decision

### API Base URL

```
/api/v1/
```

Versioning in the URL path is the simplest approach for MVP. It makes the version explicit in every request and doesn't require content negotiation or custom headers.

**Why not header-based versioning?** (e.g., `Accept: application/vnd.cypherpilot.v1+json`)
- More complex for the frontend client to implement
- Harder to test manually (curl, Postman)
- Less visible in logs and metrics
- Not supported natively by FastAPI's OpenAPI generation

**Why v1 from day one?** Starting with a version number signals that this API is designed for evolution. When we need breaking changes, we create `/api/v2/` and run both versions during migration. Building without a version number and adding it later is harder than starting with one.

### Endpoint Map

#### Module 1: Requirement Analysis

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/requirements/analyze` | Upload a requirement document and generate test cases |
| `GET` | `/api/v1/requirements/sessions` | List requirement analysis history |
| `GET` | `/api/v1/requirements/sessions/{session_id}` | Get a specific analysis session with results |
| `DELETE` | `/api/v1/requirements/sessions/{session_id}` | Delete an analysis session |

#### Module 2: API Test Generation

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/openapi/analyze` | Upload an OpenAPI spec and generate PyTest suite |
| `GET` | `/api/v1/openapi/sessions` | List API test generation history |
| `GET` | `/api/v1/openapi/sessions/{session_id}` | Get a specific analysis session with results |
| `GET` | `/api/v1/openapi/sessions/{session_id}/download` | Download generated test files as a ZIP archive |
| `DELETE` | `/api/v1/openapi/sessions/{session_id}` | Delete an analysis session |

#### Module 3: Failure Analysis

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/failures/analyze` | Upload failure artifacts and get root-cause analysis |
| `GET` | `/api/v1/failures/sessions` | List failure analysis history |
| `GET` | `/api/v1/failures/sessions/{session_id}` | Get a specific analysis session with results |
| `DELETE` | `/api/v1/failures/sessions/{session_id}` | Delete an analysis session |

#### Cross-Module

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/sessions` | List all analysis sessions across all modules |
| `GET` | `/api/v1/health` | Health check (DB connectivity, provider status) |

### Standard Response Envelopes

#### Success Response

```json
{
  "data": { ... },
  "meta": {
    "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "timestamp": "2026-07-01T12:00:00Z"
  }
}
```

#### List Response

```json
{
  "data": [ ... ],
  "meta": {
    "request_id": "...",
    "timestamp": "...",
    "page": 1,
    "page_size": 20,
    "total": 42,
    "has_more": true
  }
}
```

#### Error Response

```json
{
  "error": {
    "code": "PROVIDER_ERROR",
    "message": "AI provider returned an error",
    "detail": {
      "provider": "gemini",
      "status_code": 429,
      "retry_after": 30
    }
  },
  "meta": {
    "request_id": "...",
    "timestamp": "..."
  }
}
```

### Status Codes

| Scenario | HTTP Status | When |
|---|---|---|
| **Success — resource created** | `201 Created` | POST that creates a new analysis session |
| **Success — resource returned** | `200 OK` | GET, POST that returns immediately |
| **Accepted — async processing** | `202 Accepted` | Future: when analysis runs asynchronously |
| **No content** | `204 No Content` | DELETE success |
| **Bad request** | `400 Bad Request` | Validation failure, missing required fields |
| **Not found** | `404 Not Found` | Session ID doesn't exist |
| **Provider error** | `502 Bad Gateway` | AI provider returns an error |
| **Configuration error** | `503 Service Unavailable` | Missing API key, provider not configured |
| **Rate limit** | `429 Too Many Requests` | Future: rate limiting |

### Detailed Endpoint Contracts

#### POST /api/v1/requirements/analyze

**Request (multipart/form-data):**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File (upload) | No | Requirement document (.md, .txt, .docx) |
| `text` | String | No | Raw requirement text (alternative to file) |
| `title` | String | No | Optional session title |
| `options` | JSON string | No | Optional parameters: `{ "num_test_cases": 15, "include_edge_cases": true }` |

*At least one of `file` or `text` must be provided.*

**Response (201 Created):**

```json
{
  "data": {
    "session_id": "uuid",
    "status": "completed",
    "analysis_type": "requirement-analysis",
    "title": "User Registration Feature",
    "test_suite": {
      "summary": {
        "total_test_cases": 12,
        "categories": {
          "happy_path": 3,
          "negative": 4,
          "boundary": 2,
          "edge_case": 3
        }
      },
      "test_cases": [
        {
          "id": "TC-001",
          "title": "Valid email format is accepted during registration",
          "description": "Verify that a user can register with a properly formatted email address",
          "category": "happy_path",
          "priority": "high",
          "preconditions": ["User is on the registration page"],
          "steps": [
            "Enter 'user@example.com' in the email field",
            "Enter a valid password",
            "Click 'Register'"
          ],
          "expected_result": "User account is created successfully and confirmation message is displayed"
        }
      ]
    },
    "artifacts": [
      {
        "id": "uuid",
        "filename": "requirements.md",
        "type": "requirement"
      }
    ],
    "provider": {
      "name": "gemini",
      "model": "gemini-2.0-flash",
      "prompt_tokens": 450,
      "completion_tokens": 1200,
      "latency_ms": 3400
    },
    "created_at": "2026-07-01T12:00:00Z"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-07-01T12:00:00Z"
  }
}
```

#### GET /api/v1/requirements/sessions

**Query Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | Integer | 1 | Page number (1-indexed) |
| `page_size` | Integer | 20 | Items per page (max 100) |
| `sort` | String | `-created_at` | Sort field; prefix `-` for descending |
| `status` | String | — | Filter by status: `completed`, `failed`, `processing` |

**Response (200 OK):**

```json
{
  "data": [
    {
      "session_id": "uuid",
      "analysis_type": "requirement-analysis",
      "title": "User Registration Feature",
      "status": "completed",
      "summary": {
        "total_test_cases": 12,
        "categories": {
          "happy_path": 3,
          "negative": 4,
          "boundary": 2,
          "edge_case": 3
        }
      },
      "provider": "gemini",
      "total_tokens": 1650,
      "latency_ms": 3400,
      "created_at": "2026-07-01T12:00:00Z",
      "completed_at": "2026-07-01T12:00:04Z"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 5,
    "has_more": false,
    "request_id": "uuid",
    "timestamp": "2026-07-01T12:00:00Z"
  }
}
```

#### POST /api/v1/openapi/analyze

**Request (multipart/form-data):**

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File (upload) | Yes | OpenAPI specification (YAML or JSON) |
| `title` | String | No | Optional session title |
| `options` | JSON string | No | Optional parameters: `{ "framework": "pytest", "include_schema_tests": true }` |

**Response (201 Created):**

```json
{
  "data": {
    "session_id": "uuid",
    "status": "completed",
    "analysis_type": "api-test-generation",
    "title": "Petstore API v3",
    "test_suite": {
      "summary": {
        "endpoints_covered": 12,
        "total_tests": 48,
        "files_generated": 5
      },
      "files": [
        {
          "filename": "conftest.py",
          "description": "Shared fixtures and configuration"
        },
        {
          "filename": "test_pets.py",
          "description": "Tests for /pets endpoint (8 tests)"
        },
        {
          "filename": "test_store.py",
          "description": "Tests for /store endpoint (6 tests)"
        }
      ]
    },
    "download_url": "/api/v1/openapi/sessions/{uuid}/download",
    "provider": {
      "name": "gemini",
      "model": "gemini-2.0-flash",
      "prompt_tokens": 2800,
      "completion_tokens": 4500,
      "latency_ms": 12000
    },
    "created_at": "2026-07-01T12:00:00Z"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-07-01T12:00:00Z"
  }
}
```

#### GET /api/v1/openapi/sessions/{session_id}/download

**Response (200 OK):**

Returns a ZIP archive containing all generated Python test files (`conftest.py`, `test_*.py`, `requirements.txt`).

Content-Type: `application/zip`
Content-Disposition: `attachment; filename="cypherpilot-api-tests-{session_id[:8]}.zip"`

#### POST /api/v1/failures/analyze

**Request (multipart/form-data):**

| Field | Type | Required | Description |
|---|---|---|---|
| `log_file` | File (upload) | No | Test failure log file (.txt, .log) |
| `log_text` | String | No | Raw failure log text (alternative to file) |
| `page_source` | File (upload) | No | HTML page source at time of failure (.html) |
| `screenshot` | File (upload) | No | Screenshot at time of failure (.png, .jpg) |
| `framework` | String | No | Test framework: `playwright`, `selenium`, `pytest` |
| `title` | String | No | Optional session title |

*At least one of `log_file` or `log_text` must be provided.*

**Response (201 Created):**

```json
{
  "data": {
    "session_id": "uuid",
    "status": "completed",
    "analysis_type": "failure-analysis",
    "title": "Login test failure — 2026-07-01",
    "failure_analysis": {
      "root_cause": "Element #login-button was not visible because the previous step (enter_password) timed out waiting for the password field to be enabled. The password field is only enabled after a 2-second animation completes, but the test did not wait for the animation.",
      "confidence": 0.87,
      "confidence_factors": [
        "Timeout error in log at line 42: 'Timed out after 5000ms waiting for element #password'",
        "Screenshot shows the password field is present but disabled",
        "Page source confirms the password field has attribute 'disabled'"
      ],
      "suggested_fix": "Add an explicit wait for the password field to be enabled before typing:\n\n```python\nawait page.locator('#password').wait_for(state='enabled')\nawait page.locator('#password').fill('mypassword')\n```",
      "prevention": "Consider adding a custom wait strategy for elements that depend on CSS transitions or animations. A general rule: prefer `wait_for_*` over fixed `time.sleep()`.",
      "failure_type": "element_not_found",
      "severity": "medium"
    },
    "artifacts": [
      {
        "id": "uuid",
        "filename": "test_output.log",
        "type": "test_log"
      },
      {
        "id": "uuid",
        "filename": "page_source.html",
        "type": "page_source"
      }
    ],
    "provider": {
      "name": "gemini",
      "model": "gemini-2.0-flash",
      "prompt_tokens": 3200,
      "completion_tokens": 800,
      "latency_ms": 5200
    },
    "created_at": "2026-07-01T12:00:00Z"
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-07-01T12:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `NOT_FOUND` | 404 | Resource not found |
| `PROVIDER_ERROR` | 502 | AI provider returned an error |
| `PROVIDER_TIMEOUT` | 502 | AI provider request timed out |
| `CONFIGURATION_ERROR` | 503 | Missing or invalid configuration (e.g., no API key) |
| `RATE_LIMITED` | 429 | Too many requests (future) |
| `FILE_TOO_LARGE` | 413 | Uploaded file exceeds size limit |
| `INVALID_FILE_TYPE` | 400 | Uploaded file has an unsupported format |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### File Upload Conventions

| Convention | Rule |
|---|---|
| **Format** | All uploads use `multipart/form-data` |
| **Size limit** | 10MB per file (configurable) |
| **Accepted types** | `.md`, `.txt`, `.yaml`, `.yml`, `.json`, `.html`, `.png`, `.jpg`, `.jpeg`, `.log`, `.py` |
| **Storage** | Files stored in Docker volume, referenced by `storage_key` in the database |
| **Multiple files** | Each file type has its own form field name (`log_file`, `screenshot`, `page_source`) |

### Pagination Conventions

| Rule | Value |
|---|---|
| **Default page size** | 20 |
| **Max page size** | 100 |
| **Page numbering** | 1-indexed (page=1 is the first page) |
| **Sort syntax** | `field_name` for ascending, `-field_name` for descending |
| **Default sort** | `-created_at` (newest first) |
| **Pagination metadata** | Returned in `meta` object: `page`, `page_size`, `total`, `has_more` |

---

## Alternatives Considered

### Alternative A: GraphQL (Rejected)

Let the frontend query exactly the data it needs:

```graphql
query {
  session(id: "uuid") {
    title
    analysisType
    outputs {
      content
    }
  }
}
```

| Dimension | GraphQL | REST (Chosen) |
|---|---|---|
| **Over-fetching** | Eliminated — client requests only needed fields | Sometimes over-fetches — but schema is small enough |
| **Under-fetching** | Eliminated — nested queries resolve in one request | Multiple requests for deeply nested data |
| **Learning curve** | Significant — schema, resolvers, N+1, caching | Familiar — every developer knows REST |
| **Tooling** | Requires Apollo/Relay, GraphQL IDE | FastAPI-native, OpenAPI, curl, Postman |
| **File uploads** | Complex — multipart requests in GraphQL are non-standard | Simple — standard multipart/form-data |
| **Caching** | Complex — POST-based, varies by query | Simple — GET endpoints are cacheable by URL |
| **Portfolio signal** | "Knows GraphQL" — positive but not core | "Knows REST API design" — universal expectation |

**Decision:** Rejected. GraphQL solves problems we don't have yet (multiple clients with different data needs, mobile bandwidth optimization) and introduces problems we don't want (file upload complexity, caching difficulty, N+1 query resolution). REST with FastAPI auto-docs is simpler, more standard, and perfectly adequate for a single-client SPA.

### Alternative B: Single Endpoint with Action Parameter (Rejected)

```http
POST /api/v1/analyze
Body: { "type": "requirement", "input": "...", "module": "requirements" }
```

| Dimension | Single Endpoint | Per-Module Endpoints (Chosen) |
|---|---|---|
| **Number of endpoints** | 1 | ~15 |
| **Discoverability** | Poor — everything goes to one URL | Clear — module and action are in the URL |
| **API docs clarity** | Single endpoint with complex request variations | Each endpoint documents its specific inputs/outputs |
| **Extensibility** | New module = new parameter case | New module = new router, new prefix |
| **File upload handling** | Ambiguous — how to differentiate file types? | Per-endpoint form fields with clear names |

**Decision:** Rejected. A single endpoint would require a dispatch mechanism in the router and make the API harder to discover, document, and extend. Per-module endpoints are more RESTful and align with the module architecture.

### Alternative C: No Pagination, Return All (Rejected)

Return all sessions in one response, let the client filter.

| Dimension | No Pagination | Paginated (Chosen) |
|---|---|---|
| **Frontend simplicity** | Simpler — no pagination state | More complex — page tracking, load-more |
| **Backend simplicity** | Simpler — no page/sort parameters | Slightly more complex — pagination logic |
| **Data volume** | Works for <100 sessions | Essential for 1000+ sessions |
| **Response time** | Degrades as data grows | Consistent regardless of dataset size |
| **API contract stability** | Breaks when data exceeds response limits | Stable regardless of data volume |

**Decision:** Paginated from day one. The pagination logic is simple (SQL LIMIT/OFFSET), the API contract is stable, and retrofitting pagination later is a breaking change.

---

## Trade-offs

| Trade-off | Assessment |
|---|---|
| **URL-based versioning** vs **Header-based** | URL is simpler, more visible, easier to test. Header-based is cleaner but less usable. URL versioning wins for MVP. |
| **Per-module prefixes** vs **Unified prefix** | `/requirements/`, `/openapi/`, `/failures/` vs `/sessions/`. Per-module is clearer for endpoint discoverability. Unified is simpler for cross-module queries. Both exist — module-specific endpoints for specific actions, `/sessions/` for cross-module listing. |
| **Full response vs Summary in list** | List endpoints return summaries (no full output content). Detail endpoints return the full output. This keeps list responses fast and lightweight. |
| **Synchronous vs Asynchronous** | MVP is synchronous — the client waits for the analysis to complete. This is simpler but means requests can take 30-60 seconds. Async (202 Accepted + polling) can be added later for long-running analyses. |

---

## Consequences

### Positive

1. **Consistent patterns across all modules** — every analyze endpoint returns a session + output, every list endpoint supports pagination, every error has the same format
2. **Frontend can build generic components** — session list, session detail, and error display components work across all modules
3. **API is self-documenting** — FastAPI generates OpenAPI 3.1 docs at `/docs`
4. **File download is standard** — ZIP download for generated code, standard content-disposition headers
5. **Future-proofed** — URL versioning, pagination, consistent error codes

### Negative

1. **Synchronous design** — endpoints block for 5-60 seconds while AI analysis runs. The frontend must handle long request timeouts and show loading states. Mitigated by FastAPI's async support (doesn't block the event loop for other requests).
2. **File upload complexity** — multipart forms with multiple file fields require careful frontend handling
3. **More endpoints than strictly necessary** — ~15 endpoints vs ~5 for a "single endpoint + type" approach

### Neutral

1. **API surface will grow** — as we add modules, the number of endpoints grows linearly. This is fine — each module's endpoints are isolated.

---

## Implementation Impact

### New Files

```
app/
├── api/
│   ├── __init__.py
│   ├── deps.py                 # Shared dependencies (get_db, get_orchestrator, etc.)
│   ├── errors.py               # Error response models and handlers
│   └── v1/
│       ├── __init__.py
│       ├── api.py              # Include all v1 routers
│       └── ...                 # Routers live in each module; API layer imports them
├── modules/
│   ├── requirement_analysis/
│   │   ├── router.py           # POST /api/v1/requirements/analyze, etc.
│   │   ├── models.py           # Request/response Pydantic models
│   │   └── ...
│   ├── api_test_generation/
│   │   └── ... (same structure)
│   └── failure_analysis/
│       └── ... (same structure)
└── main.py                     # Mounts app.api.v1.api
```

### FastAPI Implementation Sketch

```python
# app/api/v1/api.py

from fastapi import APIRouter
from app.modules.requirement_analysis.router import router as req_router
from app.modules.api_test_generation.router import router as api_router
from app.modules.failure_analysis.router import router as fail_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.health import router as health_router

router = APIRouter(prefix="/api/v1")

router.include_router(health_router, tags=["Health"])
router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
router.include_router(req_router, prefix="/requirements", tags=["Requirements"])
router.include_router(api_router, prefix="/openapi", tags=["API Tests"])
router.include_router(fail_router, prefix="/failures", tags=["Failure Analysis"])
```

### Error Handler Registration

```python
# app/api/errors.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.infrastructure.exceptions import ProviderError, ConfigurationError


async def provider_error_handler(request: Request, exc: ProviderError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": {
                "code": "PROVIDER_ERROR",
                "message": str(exc),
                "detail": exc.detail,
            },
            "meta": {"request_id": request.state.request_id, "timestamp": ...},
        },
    )


async def configuration_error_handler(request: Request, exc: ConfigurationError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": "CONFIGURATION_ERROR",
                "message": str(exc),
                "detail": None,
            },
            "meta": {"request_id": request.state.request_id, "timestamp": ...},
        },
    )
```

---

## Testing Impact

### API Tests

Each module's router tests:

| Test | What it validates |
|---|---|
| `POST analyze — valid input` | Returns 201 with expected response structure |
| `POST analyze — missing input` | Returns 400 with validation error |
| `POST analyze — provider error` | Returns 502 with provider error envelope |
| `GET sessions — list` | Returns 200 with paginated response |
| `GET sessions — pagination` | Respects page, page_size parameters |
| `GET sessions — filter by status` | Filters correctly |
| `GET session detail` | Returns 200 with full session data |
| `GET session detail — not found` | Returns 404 |
| `DELETE session` | Returns 204, session no longer exists |
| `GET download (openapi)` | Returns 200 with ZIP content-type |

### API Test Approach

```python
# tests/api/v1/test_requirements_api.py

from fastapi.testclient import TestClient


def test_analyze_requirements_returns_201(client, mock_analyze):
    response = client.post(
        "/api/v1/requirements/analyze",
        data={"text": "Users must enter a valid email address"},
    )
    assert response.status_code == 201
    body = response.json()
    assert "data" in body
    assert "test_suite" in body["data"]
    assert "meta" in body
    assert "request_id" in body["meta"]


def test_analyze_requirements_missing_input_returns_400(client):
    response = client.post("/api/v1/requirements/analyze", data={})
    assert response.status_code == 400
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "VALIDATION_ERROR"
```

---

## Future Evolution

| Phase | Change | Impact |
|---|---|---|
| **Async processing** | Add `202 Accepted` + polling endpoint | New status: `processing`. Frontend polls `GET /session/{id}` until status is `completed` or `failed` |
| **API v2** | Breaking changes use `/api/v2/` | Old clients continue working with v1 |
| **Rate limiting** | Add `429 Too Many Requests` | New error code, rate limit headers |
| **Bulk operations** | Batch analysis endpoints | New endpoints, same patterns |
| **Webhooks** | POST to configured URL on completion | New infrastructure, async processing required |
| **Export endpoints** | PDF, CSV, JIRA XML export | New endpoints with content-type negotiation |

---

## Implementation Notes (2026-07-02)

The following deviations from the original ADR design exist in the current implementation:

1. **POST returns 200 instead of 201** — All MVP create endpoints return `200 OK` instead of `201 Created`. The response body is identical. Reason: simplicity — the frontend handles 200 and 201 identically, and returning 201 would require a separate response model. If a future endpoint needs to distinguish "created" from "returned existing", 201 should be used.

2. **DELETE endpoints not implemented** — No module has DELETE endpoints yet. The frontend has no delete requirement for MVP. Will be added when needed.

3. **No cross-module `/api/v1/sessions` endpoint** — Not implemented. All session listing is done per-module (`/requirements/sessions`, `/openapi/sessions`). Cross-module listing would be useful for a unified history page.

4. **No `sort` or `status` filter on list endpoints** — List endpoints only support `page` and `page_size`. Sorting defaults to `-created_at` via the repository. Filtering by status and custom sort parameters are future enhancements.

5. **No multipart file uploads** — Input is sent as JSON body, not multipart/form-data. All current inputs are text-based (requirements text, OpenAPI spec string, log content). File upload support will be added when binary inputs (screenshots, uploaded documents) are needed.

6. **Endpoint naming** — The API test generation module uses `POST /openapi/analyze` (not `POST /openapi/generate` as originally planned in ADR-007). This aligns with the `POST /requirements/analyze` convention. The service method is also renamed to `analyze()` for consistency.

---

## Decision Rationale Summary

The API Design is **justified** because:

1. **It solves a real problem** — without a contract, frontend and backend development proceed independently and conflict at integration time
2. **The cost is minimal** — FastAPI generates most of the boilerplate (validation, serialization, docs)
3. **The value is immediate** — every endpoint has a clear contract before implementation starts
4. **It demonstrates engineering maturity** — versioned, consistent, documented REST APIs are the industry standard

**Abstraction question answers (per engineering rule):**

| Question | Answer |
|---|---|
| **What problem does this solve?** | Defines the contract between frontend and backend before either is implemented |
| **Why is this necessary today?** | Frontend development depends on knowing what the API returns; backend development depends on knowing what the API receives |
| **What simpler alternative exists?** | Ad-hoc endpoints, no documentation, no consistent error format |
| **Why was that rejected?** | Leads to integration conflicts, undocumented behavior, and frontend rewrites when the backend changes |
| **How does this help evolution?** | Versioned endpoints, consistent patterns, and OpenAPI docs mean the API can evolve without breaking existing consumers |
