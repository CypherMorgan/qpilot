# CypherPilot — Success Criteria

## How we determine if CypherPilot is well-built and ready for public showcase

---

## 1. Technical Quality Metrics

These are objective, measurable criteria that a senior engineer would evaluate when reviewing the repository.

### Code Quality

| Criterion | Target | Measurement |
|---|---|---|
| Test coverage (backend business logic) | ≥80% | `pytest --cov --cov-fail-under=80` |
| Type coverage | 100% strict | `mypy --strict` passes |
| Lint score | Zero warnings | `ruff check` passes |
| Import cycle count | Zero | `ruff check --select=I` |
| Cyclomatic complexity per function | ≤10 | `ruff check --select=C901` |
| Public API surface documented | 100% | All endpoints have OpenAPI descriptions |

### Architecture Quality

| Criterion | Target | Measurement |
|---|---|---|
| Provider abstraction | New provider in 1 file, zero changes to business logic | Verification by code review |
| Prompt-framework separation | Zero prompt strings in Python code | `grep -r "system.*You are" app/` returns empty |
| Dependency injection | No `from x import y` for infrastructure in business logic | Verified by import graph |
| Database migrations | All changes forward+backward compatible | Alembic `downgrade` tested |

### Performance

| Criterion | Target |
|---|---|
| Requirement Analysis generation | <30s for <500 words |
| API Test Generation (10 endpoints) | <60s |
| Failure Analysis (text only) | <45s |
| Page load (cold start) | <3s |
| Docker Compose startup | <30s |

---

## 2. Portfolio / Showcase Criteria

These are subjective criteria that determine whether the repository meets the goal of being a "flagship GitHub project."

### Repository Presentation

- [ ] Professional README with: project description, architecture diagram, tech stack badges, quick start, screenshots, contribution guide
- [ ] Screenshots of each module's UI
- [ ] Clear project structure navigable in under 30 seconds
- [ ] ADRs that demonstrate architectural decision-making
- [ ] Meaningful commit history (conventional commits or similar)
- [ ] CI badge (GitHub Actions) passing
- [ ] Code coverage badge ≥80%
- [ ] Python versions supported badge
- [ ] License badge

### Interview-Ready Artifacts

An engineer reviewing this repo should be able to understand and discuss:

- [ ] The problem CypherPilot solves and why it exists
- [ ] The architectural decisions and their trade-offs (from ADRs)
- [ ] How the AI provider abstraction works
- [ ] How prompt management is handled
- [ ] The modular feature design
- [ ] The testing strategy
- [ ] The CI/CD pipeline
- [ ] How to extend the platform with a new feature module
- [ ] How to add a new AI provider
- [ ] The database schema and why it's designed that way

---

## 3. User Experience Criteria

- [ ] `docker compose up` starts the full application
- [ ] First-time user can upload a requirement and receive test cases within 2 minutes of starting the app
- [ ] Error messages are human-readable and actionable
- [ ] All generated outputs are valid (valid Python, valid test case structure, valid JSON)
- [ ] No data is lost on page refresh (history is persisted)

---

## 4. Project Health Indicators

| Indicator | Green | Yellow | Red |
|---|---|---|---|
| CI status | Passing | Flaky (<10% failure) | Broken |
| Open issues | <5 | 5–15 | >15 |
| Test coverage | ≥80% | 60–79% | <60% |
| MyPy strict | Passing | 1–10 errors | >10 errors |
| Ruff | Clean | 1–5 warnings | >5 warnings |

---

## 5. Definition of "Ready for Public Showcase"

The MVP (Phase 3) is considered complete and ready for public GitHub when:

1. All **Technical Quality Metrics** meet their targets
2. All **Repository Presentation** items are complete
3. A new developer can go from `git clone` to working app in under 5 minutes
4. A new developer can add a new AI provider by reading one ADR and implementing one class
5. All three MVP modules produce correct, useful outputs for realistic inputs
6. The repository has been reviewed by the mentor (me) and any issues resolved

---

## 6. What Success Looks Like in an Interview

If a senior engineer at Microsoft/Stripe/GitHub opens this repo, they should:

1. **In the first 30 seconds:** Understand what the project does from the README
2. **In 5 minutes:** Navigate the codebase, understand the module structure, find the AI provider abstraction
3. **In 15 minutes:** Understand the architecture decisions from the ADRs
4. **In 30 minutes:** Be able to describe the trade-offs in the design and suggest meaningful improvements

If they can do those four things, this project has succeeded as a portfolio piece.
