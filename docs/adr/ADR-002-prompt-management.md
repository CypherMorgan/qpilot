# ADR-002: Prompt Management

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-01 |
| **Last Updated** | 2026-07-02 |
| **Author(s)** | CypherPilot Engineering Team |
| **Supersedes** | None |
| **Superseded by** | N/A |

---

## Context

CypherPilot uses AI prompts to drive every analysis feature. These prompts contain:
- **System instructions** — role definition, output format rules, constraints
- **Few-shot examples** — sample inputs and expected outputs
- **Context insertion points** — where user-provided artifacts are injected
- **Output schema definitions** — structured JSON schemas for the response

Without a structured prompt management system, prompts tend to:
1. Become hardcoded strings in Python files
2. Diverge from actual model behavior (no version tracking)
3. Be invisible to non-developers who may need to review them
4. Lack clear ownership and change history
5. Accumulate dead code (prompts for features that no longer exist)

---

## Problem Statement

How should CypherPilot store, version, load, render, and evolve its AI prompt templates to ensure:

1. **Prompts are reviewable** — can be diffed in PRs, reviewed by non-developers
2. **Prompts are versioned** — changes can be tracked, rolled back, and correlated with feature releases
3. **Prompts are separate from code** — changing a prompt should not require changing Python code
4. **Prompts are testable** — prompt rendering can be unit tested with fixture data
5. **Prompts can evolve independently** — different prompts can have different version lifecycles

---

## Decision

We will store prompts as **versioned Markdown files** in a dedicated directory, loaded at runtime by a **Prompt Manager** component.

### Directory Structure

```
prompts/
├── analysis/                          # Analysis type (matches AI Orchestrator analysis_type)
│   ├── requirement-analysis/
│   │   ├── v1/
│   │   │   ├── system.md              # System prompt
│   │   │   └── examples.md            # Few-shot examples (optional)
│   │   └── v2/
│   │       ├── system.md
│   │       └── examples.md
│   ├── api-test-generation/
│   │   └── v1/
│   │       ├── system.md
│   │       └── examples.md
│   └── failure-analysis/
│       └── v1/
│           ├── system.md
│           ├── examples.md
│           └── context_schema.json    # JSON Schema for expected context variables
└── shared/
    └── v1/
        ├── output-format.md           # Shared output format instructions
        └── json-schema.md             # Shared JSON mode instructions
```

### Template File Format

Each template file is a Markdown file with **Jinja2-style variable placeholders**:

```markdown
# system.md (Requirement Analysis v1)

You are a senior QA engineer specializing in software testing.
Analyze the following feature requirement and generate
comprehensive test cases.

## Output Format

Return a JSON object matching this schema:
{{ output_schema }}

## Response Requirements

- Generate exactly {{ num_test_cases }} test cases
- Cover: happy path, negative scenarios, boundary values, edge cases
- Each test case must have: title, description, preconditions, steps,
  expected_result, priority, category

## Quality Rules

{{ quality_rules }}
```

```markdown
# examples.md (Requirement Analysis v1)

## Example 1

**Input Requirement:**
"Users must enter a valid email address to register."

**Expected Output:**
{
  "test_cases": [
    {
      "title": "Valid email format is accepted",
      "category": "happy_path",
      "priority": "high",
      ...
    }
  ]
}
```

### Prompt Manager Component

```python
# app/ai/prompt_manager.py

from pathlib import Path
import jinja2


class PromptTemplate:
    """A loaded and rendered prompt."""

    def __init__(
        self,
        system_prompt: str,
        user_message: str,
        metadata: TemplateMetadata,
    ) -> None:
        self.system_prompt = system_prompt
        self.user_message = user_message
        self.metadata = metadata


class TemplateMetadata:
    """Version and provenance information for a prompt template."""

    def __init__(
        self,
        analysis_type: str,
        version: str,
        template_path: Path,
    ) -> None:
        self.analysis_type = analysis_type
        self.version = version
        self.template_path = template_path


class PromptManager:
    """Loads, caches, and renders prompt templates from the filesystem."""

    def __init__(self, prompts_dir: str | Path) -> None:
        self._prompts_dir = Path(prompts_dir)
        self._env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self._prompts_dir)),
            undefined=jinja2.StrictUndefined,
        )
        self._cache: dict[str, str] = {}

    def load(
        self,
        analysis_type: str,
        context: dict[str, Any],
        version: str = "v1",
    ) -> PromptTemplate:
        """Load and render a prompt template for the given analysis type."""

        template_dir = f"analysis/{analysis_type}/{version}"

        system_prompt = self._render(f"{template_dir}/system.md", context)

        examples_path = f"{template_dir}/examples.md"
        if (self._prompts_dir / examples_path).exists():
            examples = self._render(examples_path, context)
            user_message = f"{context.get('artifact', '')}\n\n{examples}"
        else:
            user_message = context.get("artifact", "")

        return PromptTemplate(
            system_prompt=system_prompt,
            user_message=user_message,
            metadata=TemplateMetadata(
                analysis_type=analysis_type,
                version=version,
                template_path=self._prompts_dir / template_dir,
            ),
        )

    def _render(self, template_path: str, context: dict[str, Any]) -> str:
        cache_key = template_path
        if cache_key not in self._cache:
            template = self._env.get_template(template_path)
            self._cache[cache_key] = template
            return template.render(**context)
        return self._cache[cache_key].render(**context)
```

### Version Selection Strategy

For MVP, the version is **explicitly configured** in the prompt manager or hardcoded per analysis type:

```python
# app/ai/orchestrator.py (during orchestration)

prompt = await self._prompt_manager.load(
    analysis_type="requirement-analysis",
    context=context,
    version="v1",  # Explicit version — changes when we ship new prompts
)
```

**Future versions** may add:
- Version ranges (e.g., `"v1"` = latest compatible v1.x)
- A/B testing between versions
- Database-backed version override per workspace
- Prompt effectiveness analytics

---

## Alternatives Considered

### Alternative A: Hardcoded Prompts in Python Strings (Rejected)

```python
# app/modules/requirement_analysis/prompts.py

SYSTEM_PROMPT = """You are a senior QA engineer...
Generate test cases...
"""
```

| Dimension | Hardcoded | Markdown Files (Chosen) |
|---|---|---|
| **Reviewability** | Python files — non-devs can't easily review | Markdown files — anyone can review on GitHub |
| **Diff quality** | Python string diffs are noisy | Clean line-by-line diffs |
| **Iteration speed** | Redeploy to change a prompt | Edit file, container picks up (volume mount) |
| **Versioning** | Manual — copy-paste old versions into comments | Git-native — branches, tags, reverts |
| **Dead prompt detection** | Hidden in code — hard to find | File-based — orphaned files are visible |

**Decision:** Rejected. Hardcoded prompts are the primary source of "AI feature rot" in production systems. The Markdown approach costs ~50 lines of Prompt Manager code and pays massive dividends in maintainability.

### Alternative B: Prompts in Database (Deferred)

| Dimension | Database | Filesystem (Chosen) |
|---|---|---|
| **Runtime editing** | Yes — can build a prompt editor UI | Requires filesystem access or container restart |
| **Versioning** | Must build version tables manually | Git handles this natively |
| **Migration complexity** | Alembic migrations for prompt changes | File copy / rename in git |
| **MVP complexity** | High — DB schema, API endpoints, admin UI | Low — filesystem loader |
| **Payload size** | Unbounded — prompts can be very large | Limited only by disk |

**Decision:** Deferred. Filesystem-based prompts are simpler, git-versioned natively, and sufficient for single-user self-hosted MVP. A database-backed prompt store can be added when we need runtime editing or per-workspace prompt overrides.

### Alternative C: No Template Engine (String.format)

```python
prompt = SYSTEM_PROMPT.format(
    output_schema=...,
    num_test_cases=...,
)
```

| Dimension | str.format | Jinja2 (Chosen) |
|---|---|---|
| **Template syntax** | Simple `{variable}` | Full control flow — `{% if %}`, `{% for %}` |
| **Error messages** | KeyError at runtime | `jinja2.StrictUndefined` — clear error on missing var |
| **Template complexity** | Limited — can't conditionally include sections | Rich — extend, include, conditionals |
| **Dependency** | None (stdlib) | `jinja2` library |

**Decision:** Jinja2 over `str.format`. The added dependency is minimal (Jinja2 is mature and stable), and the benefits — strict undefined checking, template inheritance, conditional rendering — become essential as prompts grow in complexity.

---

## Trade-offs

| Trade-off | Assessment |
|---|---|
| **File I/O on every request** vs **In-memory caching** | We cache parsed templates in memory. File I/O happens once per template at first load. After that, rendering is in-memory and fast. |
| **Template complexity** vs **Maintainability** | Jinja2 enables complex prompts with conditionals and loops. But complex templates are harder to test. Rule: keep templates declarative (variable insertion) rather than procedural (conditionals, loops) where possible. |
| **Fixed version** vs **Latest alias** | MVP uses explicit versions. A "latest" alias would simplify config but risks accidental breaking changes. Explicit versions are safer for a platform that may archive results referencing specific prompt versions. |
| **Filesystem dependency** vs **Database** | Filesystem works perfectly for single-user Docker deployment. If we add multi-tenant prompt customization, we'll add database fallback/override. |

---

## Consequences

### Positive

1. **Prompts are first-class artifacts** — tracked in git, reviewed in PRs, diffed like code
2. **Zero code changes for prompt tuning** — edit a Markdown file, restart the container (or use volume mount for hot-reload)
3. **Prompt rendering is testable** — unit tests load fixture templates, render with test context, assert output structure
4. **Clear provenance** — every `ProviderResponse` can be traced back to the exact template version that produced it
5. **Non-developer review** — QA engineers can review prompts without reading Python

### Negative

1. **File I/O at first load** — mitigated by caching
2. **Template errors surface at runtime** — mitigated by startup validation that compiles all templates
3. **Prompt drift risk** — if someone edits a template file without a PR review, there's no guard. Mitigated by git + CI.
4. **Volume mount complexity** — for hot-reload, the prompts directory must be mounted as a Docker volume

### Neutral

1. **Template format may evolve** — moving from Markdown to a structured format (YAML frontmatter + body) is a natural evolution path

---

## Implementation Impact

### New Files

```
prompts/
├── analysis/
│   ├── requirement-analysis/
│   │   └── v1/
│   │       ├── system.md
│   │       └── examples.md
│   ├── api-test-generation/
│   │   └── v1/
│   │       ├── system.md
│   │       └── examples.md
│   └── failure-analysis/
│       └── v1/
│           ├── system.md
│           └── examples.md
└── shared/
    └── v1/
        ├── output-format.md
        └── json-schema.md

app/
└── ai/
    └── prompt_manager.py          # PromptManager, PromptTemplate, TemplateMetadata
```

### Modified Files

- `app/ai/orchestrator.py` — consumes `PromptManager` instead of hardcoded strings
- `app/main.py` — instantiate `PromptManager` with `prompts/` path
- `Dockerfile` — copy `prompts/` into container
- `docker-compose.yml` — mount `./prompts:/app/prompts` for hot-reload

### Configuration

| Variable | Purpose | Default |
|---|---|---|
| `PROMPTS_DIR` | Path to prompt templates directory | `./prompts` |
| `PROMPT_VERSION` | Default prompt version per analysis type | `v1` |

---

## Testing Impact

### Unit Tests

| Test | What it validates |
|---|---|
| `test_load_renders_system_prompt` | Template renders variables correctly |
| `test_load_missing_variable_errors` | StrictUndefined catches missing variables |
| `test_load_defaults_to_v1` | Version fallback works |
| `test_load_with_examples` | Examples file is included when present |
| `test_load_missing_template_errors` | Clear error for non-existent analysis type |
| `test_cache_hits` | Repeated loads don't re-read filesystem |

### Test Fixtures

```python
# tests/ai/test_prompt_manager.py

@pytest.fixture
def prompts_dir(tmp_path):
    """Create a temporary prompts directory with test templates."""
    base = tmp_path / "prompts"
    template_dir = base / "analysis" / "test-analysis" / "v1"
    template_dir.mkdir(parents=True)

    (template_dir / "system.md").write_text(
        "You are a {{ role }}.\n\nInput: {{ artifact }}"
    )
    return base


@pytest.fixture
def prompt_manager(prompts_dir):
    return PromptManager(prompts_dir)
```

---

## Future Evolution

| Phase | Change | Impact |
|---|---|---|
| **Post-MVP: Prompt validation at startup** | Load all templates at startup, report errors | Better developer experience |
| **Post-MVP: A/B testing** | Select template version per request | PromptManager supports version override |
| **Post-MVP: Prompt playground** | UI for editing and testing prompts | DB-backed prompt store + version history |
| **Post-MVP: Per-workspace prompts** | Workspace can override global templates | DB fallback in PromptManager |
| **Post-MVP: Prompt analytics** | Track which templates produce best results | Template ID in ProviderResponse metadata |
| **Post-MVP: Multi-language prompts** | Locale-specific template directories | `prompts/{locale}/analysis/...` |

---

## Decision Rationale Summary

The Prompt Management approach is **justified** because:

1. **It solves a real problem** — hardcoded prompts are untestable, unreviewable, and invisible
2. **The cost is minimal** — one PromptManager class, one dependency (Jinja2)
3. **The value is immediate** — MVP modules need at least 3 prompt templates; managing them as files from day one prevents technical debt
4. **It demonstrates engineering maturity** — separating prompts from code is a hallmark of production AI systems

**Abstraction question answers (per engineering rule):**

| Question | Answer |
|---|---|
| **What problem does this solve?** | Prompt-code coupling, unreviewable prompts, untestable templates |
| **Why is this necessary today?** | Every feature module needs a prompt; starting with files prevents hardcoded-prompt debt |
| **What simpler alternative exists?** | Python string constants in each module |
| **Why was that rejected?** | Not reviewable by non-devs, no versioning, no diff quality, requires redeploy for prompt changes |
| **How does this help evolution?** | Prompts can be iterated independently of code; versioning supports rollback and A/B testing |
