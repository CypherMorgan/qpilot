# ADR-007: API Test Generation Module

| Field | Value |
|---|---|
| **Status** | Proposed |
| **Date** | 2026-07-02 |
| **Author(s)** | CypherPilot Engineering Team |
| **Supersedes** | None |
| **Superseded by** | N/A |

---

## Context

CypherPilot's second business module (Phase 4) generates executable PyTest API test suites from OpenAPI 3.1 specifications. This transforms a static API document into a runnable test suite that validates endpoint behavior, response schemas, error handling, and edge cases.

### Problem

Manually writing API tests is tedious, error-prone, and rarely keeps pace with specification changes. Engineers need a way to:

1. **Bootstrap test suites** from an OpenAPI spec in seconds, not days
2. **Cover all endpoints** — not just the happy path, but error codes, validation rules, and edge cases
3. **Generate maintainable tests** — well-structured Python code with fixtures, assertions, and documentation
4. **Regenerate when specs change** — diff the old and new test suite, not rewrite from scratch

### What makes this different from Requirement Analysis (Phase 3)

| Dimension | Phase 3: Requirement Analysis | Phase 4: API Test Generation |
|---|---|---|
| **Input format** | Free-text (Markdown, plain text) | Structured (OpenAPI 3.1 JSON/YAML) |
| **Output format** | Structured report (JSON + Markdown) | Executable Python code (.py files) |
| **AI role** | Analyze and categorize | Analyze and generate code |
| **Pre-processing** | None | Parse OpenAPI spec, extract endpoints/schemas |
| **Post-processing** | Render to Markdown/JSON | Zip multiple .py files, syntax validation |
| **User interaction** | Paste text → get report | Upload spec → select endpoints → get test files |
| **Token consumption** | Moderate (input = requirements text) | Potentially large (input = full spec) |
| **Output structure** | Single JSON document | Multiple files (conftest.py, test_*.py) |

---

## Problem Statement

Design the API Test Generation module such that:

1. **Supports OpenAPI 3.0 and 3.1** — the two most common versions; 2.0 is not a priority for MVP
2. **Handles large specs efficiently** — specs with 50+ endpoints can exceed context windows; we must extract and structure before AI processing
3. **Generates production-quality tests** — pytest fixtures, httpx.AsyncClient, proper assertions, type hints, docstrings
4. **Allows endpoint selection** — users can generate tests for a subset of endpoints, not the entire spec
5. **Output is immediately runnable** — tests can be dropped into a project and executed with `pytest`
6. **Supports auth schemes** — API key, Bearer token, Basic auth, OAuth2 from the spec's `securitySchemes`
7. **Supports regeneration** — generate again when the spec changes, minimizing manual rework
8. **Follows the same module pattern** as Phase 3 — `models.py`, `service.py`, `repository.py`, `router.py`, `prompts/v1/`, `exporters/`, `tests/`

---

## Decision

### Technology Choices

| Decision | Choice | Rationale |
|---|---|---|
| **Spec parsing** | `openapi-schema-pydantic` + custom extraction | Parse OpenAPI spec into Pydantic models, then extract structured endpoint info. Avoids heavy frameworks like `openapi-core`. |
| **Test framework output** | PyTest + httpx | Matches our backend stack; `httpx.AsyncClient` is the standard for async HTTP testing in Python |
| **Multi-file packaging** | `io.BytesIO` + `zipfile` | Bundle all generated .py files into a single downloadable ZIP archive |
| **Token optimization** | Programmatic spec summarization | Extract endpoint paths, methods, parameters, request/response schemas — feed structured data to AI, not raw YAML |
| **Endpoint selection** | Optional `paths` field in request | User specifies which paths to generate tests for; empty = all paths |

### Spec Parser Strategy

Rather than feeding raw OpenAPI YAML/JSON to the AI (which wastes tokens on verbose schema definitions), we parse the spec programmatically first:

```python
# app/modules/api_test_generation/spec_parser.py

@dataclass
class ExtractedEndpoint:
    path: str
    method: str                          # get, post, put, delete, patch
    summary: str | None
    description: str | None
    operation_id: str | None
    tags: list[str]
    parameters: list[ExtractedParameter]  # path, query, header, cookie
    request_body: ExtractedRequestBody | None
    responses: dict[str, ExtractedResponse]
    security: list[dict[str, list[str]]] | None

@dataclass
class ExtractedSchema:
    name: str
    type: str                            # object, array, string, integer, etc.
    properties: dict[str, ExtractedProperty]
    required: list[str]

@dataclass
class ParsedSpec:
    title: str
    version: str
    description: str | None
    servers: list[str]
    endpoints: list[ExtractedEndpoint]
    schemas: list[ExtractedSchema]
    security_schemes: dict[str, SecurityScheme]
```

**Why extract instead of passing raw YAML?** A 50-endpoint OpenAPI spec can be 50,000+ characters of YAML — most of which is verbose JSON Schema definitions. The extracted summary is typically 5-15% of the original size (depending on schema complexity), preserving all semantically relevant information.

### Prompt Strategy

The prompt instructs the AI to generate Python test code for each endpoint. The system prompt includes:

1. The structured endpoint information (path, method, parameters, request body, responses)
2. The schema definitions (referenced by the endpoint)
3. Instructions for generating pytest tests with httpx
4. Code generation guidelines (type hints, docstrings, assertions, error handling)
5. A few-shot example showing the expected test file structure

```
prompts/analysis/api-test-generation/v1/
├── system.md       # System prompt with code generation instructions
└── examples.md     # Example: generating tests for a Pet Store API endpoint
```

**Important**: The AI generates test *content* (assertions, expected status codes, test data) but the structural scaffolding (fixtures, client setup, conftest.py) is programmatically generated. This hybrid approach ensures structural correctness while leveraging AI for intelligent test logic.

### Output Structure

```
generated-tests/
├── conftest.py              # Shared fixtures: client, auth, base URL
├── test_pets.py             # Tests for /pets endpoints
├── test_users.py            # Tests for /users endpoints
├── test_orders.py           # Tests for /orders endpoints
└── README.md                # How to run the tests
```

Each `test_*.py` file contains:
- One test function per endpoint-method combination
- Happy path tests (200/201 responses)
- Error handling tests (400, 401, 403, 404, 422, 500)
- Schema validation tests (required fields, type checking)
- Edge case tests (empty bodies, boundary values)

### Module Structure

```
app/modules/api_test_generation/
├── __init__.py
├── router.py                         # POST /analyze, GET /sessions, GET /sessions/{id}
├── service.py                        # Orchestration: parse → select → generate → persist
├── models.py                         # Pydantic schemas: GenRequest, GenResponse, etc.
├── spec_parser.py                    # Programmatic OpenAPI parsing & extraction
├── repository.py                     # ApiTestGenerationRepository
├── exporters/
│   ├── __init__.py
│   ├── base.py                       # Abstract test file generator
│   └── pytest_generator.py            # Generates conftest.py + test_*.py files + ZIP
├── prompts/
│   └── v1/
│       ├── system.md                 # Code generation prompt with endpoint schema
│       └── examples.md               # Few-shot example
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_spec_parser.py
    ├── test_service.py
    ├── test_router.py
    └── fixtures/
        ├── petstore.yaml             # Small OpenAPI spec (Pet Store)
        └── complex_spec.yaml         # Larger spec for edge case testing
```

### Service Workflow

```
┌────────────────────────────────────────────────────────────────────┐
│                    API Test Generation Service                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Parse: Load & validate OpenAPI spec (JSON/YAML)                 │
│  2. Extract: Build structured endpoint list (programmatic)          │
│  3. Filter: Apply user's path filters if provided                   │
│  4. Pre-structure: Generate conftest.py (programmatic)              │
│  5. AI Generate: For each endpoint group (by tag/resource):         │
│     a. Render prompt with endpoint info + schemas                   │
│     b. Call AI provider                                             │
│     c. Parse AI response -> test function code                      │
│  6. Assemble: Combine conftest.py + generated test files            │
│  7. Package: Bundle into ZIP archive                                │
│  8. Persist: Store spec + generated tests in session                │
│  9. Return: Session ID + file listing + download URL                │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### API Endpoints

```
POST /api/v1/openapi/analyze
  Accept: multipart/form-data (file upload) OR application/json (paste spec)
  Body: { spec: string (JSON/YAML), format: "json"|"yaml",
          paths?: string[] (optional filter), title?: string }
  Response: { data: { session_id, files: [{name, path, size}],
                      download_url }, meta: { request_id } }

GET /api/v1/openapi/sessions/{session_id}
  Response: { data: { session_id, status, spec_title, spec_version,
                      files, download_url, ... }, meta: { ... } }

GET /api/v1/openapi/sessions
  Query: page, page_size
  Response: { data: [session list], meta: { pagination, ... } }

GET /api/v1/openapi/sessions/{session_id}/download
  Response: application/zip (the generated test files)
```

### Backend Models (Pydantic)

```python
class OpenApiGenerateRequest(BaseModel):
    """Request to generate API tests from an OpenAPI spec."""
    spec: str                                              # Raw YAML or JSON string
    format: Literal["json", "yaml"] = "yaml"
    title: str | None = None
    paths: list[str] | None = None                        # Optional filter: ["/pets", "/users"]
    context: str | None = None                             # Optional tech stack context

class GeneratedFile(BaseModel):
    """A single generated test file."""
    filename: str                                          # e.g., "test_pets.py"
    path: str                                              # e.g., "generated-tests/test_pets.py"
    size: int                                              # File size in bytes

class OpenApiGenerateResponse(BaseModel):
    """Response after successful test generation."""
    session_id: UUID
    status: str
    spec_title: str
    spec_version: str
    endpoint_count: int
    files: list[GeneratedFile]
    download_url: str
    provider: str | None = None
    model: str | None = None
    total_tokens: int = 0
    latency_ms: int = 0

class OpenApiSessionListItem(BaseModel):
    """Lightweight session summary for listing."""
    session_id: UUID
    title: str | None
    spec_title: str | None
    spec_version: str | None
    endpoint_count: int
    status: str
    provider: str | None
    total_tokens: int
    created_at: datetime
    updated_at: datetime
```

### Database Schema

Reuses the existing `AnalysisSession` table with `analysis_type = AnalysisType.API_TEST_GENERATION`.

`output_data` JSONB structure:
```json
{
  "spec_title": "Pet Store API",
  "spec_version": "1.0.0",
  "endpoint_count": 12,
  "files": [
    {"filename": "conftest.py", "path": "generated-tests/conftest.py", "size": 2048},
    {"filename": "test_pets.py", "path": "generated-tests/test_pets.py", "size": 5120}
  ],
  "endpoints": [
    {"path": "/pets/{petId}", "method": "GET", "tests_generated": 4},
    {"path": "/pets", "method": "POST", "tests_generated": 5}
  ]
}
```

The actual generated file content is stored in `output_data.files` as base64-encoded content (for quick retrieval without file system dependency). The download endpoint decodes and serves as a ZIP.

### Pytest Generator Output

**conftest.py** (programmatically generated):
```python
"""Shared test fixtures for API tests."""
import pytest
import httpx

BASE_URL = "https://api.example.com/v1"

@pytest.fixture
async def client():
    """Provide an async HTTP client for API testing."""
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        yield client

@pytest.fixture
def auth_headers():
    """Provide authentication headers as defined in the OpenAPI spec."""
    return {"Authorization": "Bearer <your-token>"}
```

**test_pets.py** (AI-generated):
```python
"""Tests for /pets endpoints."""
import pytest
import httpx


@pytest.mark.asyncio
async def test_list_pets_happy_path(client: httpx.AsyncClient, auth_headers: dict) -> None:
    """GET /pets should return a list of pets with 200 status."""
    response = await client.get("/pets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Each item should conform to the Pet schema
    for pet in data:
        assert "id" in pet
        assert "name" in pet
        assert isinstance(pet["id"], int)


@pytest.mark.asyncio
async def test_list_pets_with_pagination(client: httpx.AsyncClient, auth_headers: dict) -> None:
    """GET /pets with limit and offset should return paginated results."""
    response = await client.get("/pets", headers=auth_headers, params={"limit": 10, "offset": 0})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 10


@pytest.mark.asyncio
async def test_get_pet_by_id(client: httpx.AsyncClient, auth_headers: dict) -> None:
    """GET /pets/{petId} should return a single pet."""
    response = await client.get("/pets/1", headers=auth_headers)
    assert response.status_code == 200
    pet = response.json()
    assert pet["id"] == 1
    assert "name" in pet


@pytest.mark.asyncio
async def test_get_pet_not_found(client: httpx.AsyncClient, auth_headers: dict) -> None:
    """GET /pets/{petId} with non-existent ID should return 404."""
    response = await client.get("/pets/999999", headers=auth_headers)
    assert response.status_code == 404
```

### Token Optimization Strategy

Large OpenAPI specs (50+ endpoints, 500+ lines of YAML) can exhaust token budgets. Our strategy:

1. **Programmatic extraction** — Parse the spec into a compact structured format. A 300KB YAML spec becomes ~10KB of structured endpoint data.
2. **Per-endpoint-group generation** — Group endpoints by tag, generate tests one group at a time. Each AI call handles 3-8 endpoints, keeping token usage manageable.
3. **Schema reference resolution** — Resolve `$ref` references during parsing, so the AI sees resolved schemas, not `$ref` pointers.
4. **Parallel generation** — Endpoint groups with no shared dependencies are generated in parallel using `asyncio.gather`.
5. **Progressive context** — The conftest.py structure and auth setup are included once; each AI call only needs the endpoint-specific context.

---

## Alternatives Considered

### Alternative A: Pass Raw Spec to AI (Rejected)

Feed the entire raw OpenAPI YAML/JSON to the AI and have it generate all tests in one call.

| Dimension | Raw Spec (Rejected) | Structured Extraction (Chosen) |
|---|---|---|
| **Token cost** | Very high — full schema definitions waste tokens | Low — only semantically relevant info is preserved |
| **Spec size limit** | ~15-20 endpoints before hitting context limits | 100+ endpoints with paginated generation |
| **Reliability** | AI may misinterpret complex nested schemas | AI receives pre-resolved, clearly structured input |
| **Response size** | Single massive response with all tests | Multiple focused responses, one per endpoint group |
| **Error recovery** | One bad endpoint pollutes the entire output | Failed groups can be retried independently |

**Decision:** Rejected. Raw spec passing wastes tokens, limits spec size, and reduces reliability. Structured extraction is strictly superior for this use case.

### Alternative B: Generate Tests Without AI (Rejected)

Use a template engine (Jinja2) to generate tests programmatically from parsed OpenAPI data.

| Dimension | Template-Only (Rejected) | AI-Assisted (Chosen) |
|---|---|---|
| **Test intelligence** | Mechanical — generates the same assertion pattern for every endpoint | Intelligent — understands semantics, generates meaningful test data and edge cases |
| **Schema validation** | Can check status codes and required fields | Can validate response semantics, business rules, and data relationships |
| **Test data generation** | Static placeholder values | Contextually appropriate test data |
| **Edge case detection** | None — only what's explicitly in the spec | Can infer implicit edge cases |
| **Maintenance** | Template changes affect all outputs globally | Each test is independently generated |

**Decision:** Rejected. Template-only generation produces brittle, low-value tests. The AI's ability to infer intent and generate meaningful scenarios is the core value proposition.

### Alternative C: File System Storage for Generated Files (Deferred)

Store generated .py files on the filesystem and reference them from the database.

| Dimension | File System (Deferred) | Database JSONB (Chosen) |
|---|---|---|
| **Portability** | Requires shared volume or blob storage | Fully self-contained in the database |
| **Backup** | Separate backup for files | Single database backup |
| **Scalability** | Better for large files (10MB+) | Good for test files (typically <500KB) |
| **MVP simplicity** | Requires file storage abstraction | Zero additional infrastructure |

**Decision:** Chose JSONB for MVP. The generated test files are typically small (<500KB total). We add blob/file storage only if file sizes become problematic. The download endpoint reads from the database and serves as a ZIP, so the user experience is identical.

---

## Trade-offs

| Trade-off | Assessment |
|---|---|
| **AI generation accuracy vs. token cost** | Generating per-endpoint-group reduces token cost per call but may miss cross-endpoint integration tests. Acceptable for MVP — the focus is on per-endpoint correctness, not integration scenarios. |
| **Parallel generation vs. consistency** | Parallel `asyncio.gather` calls for independent endpoint groups speed up generation but may produce inconsistent fixture naming. Mitigated by generating conftest.py programmatically (not by AI), providing a stable base. |
| **Spec format support** | JSON + YAML for MVP; OpenAPI 2.0 (Swagger) is not supported. We add it if demand emerges. YAML is the most common format for OpenAPI specs. |
| **File size vs. database storage** | Storing generated files as base64 in JSONB is not ideal for large payloads but works for MVP. A 500KB test suite becomes ~670KB base64 + JSON overhead — acceptable. |

---

## Consequences

### Positive

1. **Efficient token usage** — programmatic extraction reduces input by 85-95% compared to raw YAML
2. **Parallel generation** — independent endpoint groups are generated concurrently, reducing wall-clock time
3. **Production-quality output** — tests include proper async fixtures, assertions, type hints, and docstrings
4. **Familiar pattern** — module structure and API design mirror Phase 3 exactly
5. **Self-contained** — no file system, blob storage, or external dependencies for MVP
6. **Automatic endpoint discovery** — all endpoints are parsed and available; no manual registration

### Negative

1. **OpenAPI 2.0 not supported** — users with Swagger 2.0 specs need to convert (many tools exist for this)
2. **Generated tests may need manual adjustments** — AI-generated test data may not match production data shapes
3. **No cross-endpoint integration tests** — each endpoint is tested in isolation; sequential workflows (create → read → update → delete) are not generated
4. **Spec parsing complexity** — OpenAPI 3.1 has many edge cases (webhooks, callbacks, discriminators) that the parser must handle gracefully

### Neutral

1. **Generated test quality improves with prompt iteration** — as we refine prompts across versions, test quality improves without code changes
2. **Zip download is the primary delivery mechanism** — users download, extract, and run; CI integration is a future enhancement

---

## Implementation Impact

### New Files

```
app/modules/api_test_generation/
├── __init__.py
├── router.py
├── service.py
├── models.py
├── spec_parser.py
├── repository.py
├── exporters/
│   ├── __init__.py
│   ├── base.py
│   └── pytest_generator.py
├── prompts/
│   └── v1/
│       ├── system.md
│       └── examples.md
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_spec_parser.py
    ├── test_service.py
    ├── test_router.py
    └── fixtures/
        ├── petstore.yaml
        └── complex_spec.yaml

frontend/src/modules/api-test-generation/
├── types/index.ts
├── services/api-test-generation.ts
├── hooks/use-api-test-generation.ts
├── components/
│   ├── spec-editor.tsx              # Paste/upload OpenAPI spec
│   ├── endpoint-selector.tsx         # Select which endpoints to generate tests for
│   ├── generated-files-viewer.tsx    # Syntax-highlighted file preview
│   └── download-actions.tsx          # Download ZIP, copy file content
├── pages/
│   ├── generate-page.tsx             # Main workflow page
│   └── session-detail-page.tsx       # View past generation session
└── index.ts
```

### Modified Files

| File | Change |
|---|---|
| `app/domain/models.py` | `AnalysisType.API_TEST_GENERATION` already exists (added in Phase 1) — no change |
| `app/api/v1/api.py` | Add `include_router(api_test_gen_router)` |
| `app/infrastructure/models/analysis_session.py` | No change — existing columns handle API test sessions |
| `frontend/src/lib/constants.ts` | Add `ROUTES.API_TEST_GENERATION`, `ROUTES.API_TEST_SESSION`, add nav item |
| `frontend/src/app/router.tsx` | Add routes for `/api-tests/analyze` and `/api-tests/sessions/:sessionId` |
| `frontend/src/app/pages/home.tsx` | Update API Test Generation card from "Coming soon" to navigable "Live" |

### Test Plan

| Test Suite | Scope | Expected Count |
|---|---|---|
| `test_models.py` | Pydantic schema validation, serialization, defaults | 8-12 tests |
| `test_spec_parser.py` | Parse petstore.yaml, extract endpoints, schemas, handle edge cases | 10-15 tests |
| `test_service.py` | Full pipeline: parse → generate → persist → return | 10-12 tests |
| `test_router.py` | HTTP success/error codes, validation, 404 handling, file upload | 8-10 tests |
| **Backend total** | | **36-49 new tests** |
| Frontend types | TypeScript interface validation | 4-6 tests |
| Frontend components | Render spec editor, file viewer, download actions | 6-8 tests |
| Frontend services | API call mocking | 3-4 tests |
| **Frontend total** | | **13-18 new tests** |

---

## Future Evolution

| Phase | Enhancement | Impact |
|---|---|---|
| **v0.6.0** | Cross-endpoint workflow tests | Generate tests that follow a sequence (create → read → update → delete) |
| **v0.6.0** | CI integration | Output tests as PR comments or commit directly to a test repository |
| **v0.7.0** | OpenAPI 2.0 (Swagger) support | Add a converter or parser extension |
| **v0.7.0** | Webhook/callback testing | Generate tests for webhook receivers defined in OpenAPI 3.1 |
| **v0.8.0** | GraphQL support | Extend to support GraphQL schema → pytest generation |
| **v0.9.0** | Interactive endpoint diff | Compare generated tests against a previous generation, show diff |
| **v1.0.0** | Plugin framework | Users can provide custom assertion templates |

---

## Decision Rationale Summary

The API Test Generation module design is **justified** because:

1. **It solves a real pain point** — manually writing API tests is tedious and doesn't scale with spec evolution
2. **The structured extraction approach** handles large specs efficiently without burning tokens on verbose YAML/JSON
3. **The AI generates intelligent test scenarios** — not just status code checks, but meaningful assertions, edge cases, and error handling
4. **The module pattern is proven** — Phase 3 established the structure; Phase 4 follows it exactly, reducing design risk
5. **The output is immediately useful** — download a ZIP, run `pytest`, and get actionable feedback on API behavior

**Abstraction question answers:**

| Question | Answer |
|---|---|
| **What problem does this solve?** | Manual API test writing is slow and doesn't keep pace with spec changes; this generates comprehensive, maintainable test suites from an OpenAPI spec |
| **Why is this necessary today?** | It's the second MVP module and the core value proposition of CypherPilot — generating tests from artifacts |
| **What simpler alternative exists?** | Template-only generation (no AI) — produces mechanical tests without intelligent assertions or edge cases |
| **Why was that rejected?** | Template-only tests are low-value; users can write those themselves. The AI's ability to infer intent is the differentiator |
| **How does this help evolution?** | The module follows the proven Phase 3 pattern; the spec parser and pytest generator are reusable for future API-related features |

---

## Appendix A: Sample OpenAPI Spec (Pet Store)

Used as test fixture and prompt example:

```yaml
openapi: "3.1.0"
info:
  title: Pet Store API
  version: "1.0.0"
paths:
  /pets:
    get:
      summary: List all pets
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
        - name: offset
          in: query
          schema:
            type: integer
      responses:
        "200":
          description: A list of pets
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Pet"
    post:
      summary: Create a pet
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/NewPet"
      responses:
        "201":
          description: Created
        "400":
          description: Invalid input
  /pets/{petId}:
    get:
      summary: Get a pet by ID
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: A single pet
        "404":
          description: Not found
    delete:
      summary: Delete a pet
      parameters:
        - name: petId
          in: path
          required: true
          schema:
            type: integer
      responses:
        "204":
          description: Deleted
        "404":
          description: Not found
components:
  schemas:
    Pet:
      type: object
      required: [id, name]
      properties:
        id:
          type: integer
        name:
          type: string
        tag:
          type: string
    NewPet:
      type: object
      required: [name]
      properties:
        name:
          type: string
        tag:
          type: string
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
```

This 50-line spec produces ~15 endpoints + schemas in the extracted format (vs. ~50 lines raw). For larger specs, the savings are proportionally greater.

---

## Appendix B: Endpoint Grouping Strategy

Endpoints are grouped by their `tags` list in the OpenAPI spec:

```python
def group_endpoints(endpoints: list[ExtractedEndpoint]) -> dict[str, list[ExtractedEndpoint]]:
    """Group endpoints by their OpenAPI tags.
    
    An endpoint with multiple tags appears in each group.
    Endpoints without tags are grouped under 'default'.
    """
    groups: dict[str, list[ExtractedEndpoint]] = {}
    for ep in endpoints:
        for tag in (ep.tags or ["default"]):
            groups.setdefault(tag, []).append(ep)
    return groups
```

Each group is generated in parallel (one AI call per group). Grouping by tag produces meaningful file boundaries — each `test_<tag>.py` file corresponds to a logical API domain.
