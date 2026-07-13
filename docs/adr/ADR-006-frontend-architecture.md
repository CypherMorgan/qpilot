# ADR-006: Frontend Architecture

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-07-02 |
| **Author(s)** | QPilot Engineering Team |
| **Supersedes** | None |
| **Superseded by** | N/A |

---

## Context

QPilot needs a single-page application (SPA) frontend that consumes the RESTful API defined in ADR-005. The frontend must support three MVP feature modules (Requirement Analysis, API Test Generation, Failure Analysis) with a consistent shell, navigation, and design system.

The frontend is the user's primary interface — it must feel like an internal engineering platform (inspired by GitHub, Linear, Stripe Dashboard, Railway, Atlassian), not a chat-style interface.

---

## Problem Statement

Design the QPilot frontend architecture such that:

1. **Feature-first organization** — modules are self-contained directories that mirror the backend module architecture (ADR-003)
2. **No global state library** — prefer local state + TanStack Query; avoid Redux/Zustand/MobX unless a genuine need emerges
3. **Production-quality shell** — sidebar navigation, top bar, responsive layout, theme support, error boundaries, loading/empty/error states
4. **Reusable API layer** — typed Axios client with interceptors that feature modules consume, not raw HTTP calls
5. **Testing infrastructure** — Vitest + React Testing Library from day one
6. **Docker integration** — frontend builds into the Docker Compose stack

---

## Decision

### Tech Stack

| Technology | Version | Role |
|---|---|---|
| React | 18.x | UI library |
| TypeScript | 5.x | Type safety |
| Vite | 5.x | Build tool & dev server |
| Tailwind CSS | 3.x | Utility-first CSS |
| shadcn/ui | latest | Radix UI primitives + design system |
| React Router | 6.x | Client-side routing |
| TanStack Query | 5.x | Server state management |
| Axios | 1.x | HTTP client |
| React Hook Form | 7.x | Form state management (future use) |
| Zod | 3.x | Schema validation (future use) |
| Lucide React | latest | Icon library |
| Vitest | latest | Unit testing |
| React Testing Library | latest | Component testing |

**Why these choices:**

| Choice | Rationale |
|---|---|
| **Vite over CRA** | Faster dev server, native ESM, better TypeScript support. CRA is effectively deprecated. |
| **Tailwind over CSS-in-JS** | Zero runtime, consistent design tokens, excellent dev experience. shadcn/ui is built on Tailwind. |
| **shadcn/ui over MUI/Chakra** | Copy-paste components (no npm dependency on design system), full control over styling, Radix UI primitives for accessibility. Aligns with "production-quality, not production-dependent" philosophy. |
| **TanStack Query over Redux** | 90% of state is server state (API responses). TanStack Query handles caching, refetching, loading/error states, and pagination without boilerplate. Client-only state (form inputs, UI toggles) stays in local React state. |
| **Axios over fetch** | Interceptors for auth/error normalization, request cancellation, progress events, broader browser support. Wrapped behind typed service functions so modules don't call Axios directly. |
| **React Hook Form + Zod** | Not used in this milestone but included in dependencies so future modules don't need to add new packages. Aligns with shadcn/ui's form integration pattern. |

### Folder Structure

```
frontend/
├── public/                          # Static assets served as-is
├── src/
│   ├── main.tsx                     # Application entry point
│   ├── App.tsx                      # Root component (providers + router)
│   ├── index.css                    # Tailwind imports + base styles
│   │
│   ├── app/                         # Application infrastructure
│   │   ├── providers.tsx            # All providers composed together
│   │   ├── router.tsx               # React Router instance + route tree
│   │   └── pages/                   # App-level pages (not feature modules)
│   │       ├── home.tsx             # Dashboard / home page
│   │       ├── settings.tsx         # Settings page (placeholder)
│   │       └── not-found.tsx        # 404 page
│   │
│   ├── components/                  # Shared/reusable components
│   │   ├── ui/                      # shadcn/ui primitives (Button, Sheet, etc.)
│   │   ├── error-boundary.tsx       # Error boundary wrapper
│   │   ├── loading-state.tsx        # Loading spinner / skeleton
│   │   ├── empty-state.tsx          # Empty state with icon + message + action
│   │   └── theme-toggle.tsx         # Light/dark theme switch
│   │
│   ├── layouts/                     # Application layouts
│   │   ├── root-layout.tsx          # Shell: sidebar + topbar + content area
│   │   ├── sidebar.tsx              # Sidebar navigation
│   │   └── topbar.tsx               # Top navigation bar
│   │
│   ├── modules/                     # Feature modules (feature-first! )
│   │   ├── requirement-analysis/    # Future: Requirement Analysis module
│   │   │   └── (empty — Phase 3)
│   │   ├── api-test-generation/     # Future: API Test Generation module
│   │   │   └── (empty — Phase 3)
│   │   └── failure-analysis/        # Future: Failure Analysis module
│   │       └── (empty — Phase 3)
│   │
│   ├── services/                    # API client layer
│   │   ├── api-client.ts            # Axios instance + interceptors
│   │   ├── health.ts                # Health check service
│   │   └── index.ts                 # Barrel exports
│   │
│   ├── hooks/                       # Shared custom hooks
│   │   ├── use-health.ts            # TanStack Query hook for health
│   │   └── use-theme.ts             # Theme context hook
│   │
│   ├── lib/                         # Pure utility functions
│   │   ├── utils.ts                 # cn() classname merger
│   │   └── constants.ts             # App-wide constants
│   │
│   └── types/                       # Shared TypeScript types
│       ├── api.ts                   # API response envelopes
│       └── index.ts                 # Barrel exports
│
├── tests/                           # Test files (mirrors src/ structure)
│   ├── setup.ts                     # Vitest setup (jsdom, matchers)
│   ├── test-utils.tsx               # Custom render with providers
│   ├── app/
│   │   └── router.test.tsx          # Router tests
│   ├── components/
│   │   ├── error-boundary.test.tsx
│   │   └── loading-state.test.tsx
│   ├── layouts/
│   │   └── root-layout.test.tsx
│   ├── services/
│   │   └── api-client.test.ts       # API client tests
│   └── hooks/
│       └── use-health.test.tsx      # Health query hook tests
│
├── package.json
├── vite.config.ts
├── vitest.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── tsconfig.json
├── tsconfig.node.json
├── components.json                  # shadcn/ui configuration
├── index.html
├── Dockerfile                       # Multi-stage frontend build
└── nginx.conf                       # Nginx config for production serving
```

### Module Development Pattern

When a new feature module is created (Phase 3+), it follows this structure:

```
src/modules/<module-name>/
├── components/          # Module-specific components
├── hooks/               # Module-specific hooks
├── pages/               # Module-specific pages/routes
├── services/            # Module-specific API calls
├── types/               # Module-specific types
└── index.ts             # Public API — exports router, components
```

**Rules:**

1. A module may import from `src/services/`, `src/hooks/`, `src/components/`, `src/lib/`, `src/types/` — shared infrastructure
2. A module must NOT import from another module's directory — prevents accidental coupling
3. A module's `index.ts` exports ONLY what the app router needs (pages, routes)
4. Module-specific API calls use the shared `apiClient` from `src/services/api-client.ts`

### Routing Strategy

```
/                    → Home dashboard
/settings            → Settings page
/*                   → 404 (catch-all)
```

Module routes are added by the module during registration:

```typescript
// Example: when Requirement Analysis is added in Phase 3
// src/app/router.tsx
const router = createBrowserRouter([
  {
    path: "/",
    element: <RootLayout />,
    errorElement: <ErrorBoundary />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "requirements/*", element: <RequirementAnalysisModule /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
```

**Why nested routes under RootLayout?** Every page shares the same shell (sidebar + top bar). React Router's `<Outlet />` renders child routes inside the layout. This prevents layout duplication across pages.

### State Management

**Decision: Local state + TanStack Query. No global state library.**

| State Type | Storage | Example |
|---|---|---|
| Server state (API data) | TanStack Query | Analysis sessions, health status |
| UI state (toggles, modals) | Local `useState` | Sidebar open/closed, theme |
| Form state (future) | React Hook Form | Analysis input forms |
| URL state (navigation) | React Router | Current route, search params |
| Shared UI state (theme) | React Context | Theme (light/dark) — low churn, simple |

**Why not Redux/Zustand?**

TanStack Query handles server state caching, refetching, pagination, and optimistic updates — which is 90% of what a global store would manage. The remaining 10% (UI state) is simpler and more maintainable as local state or context.

This decision is re-evaluated if:
- A state needs to be shared across disconnected parts of the tree with high update frequency
- Complex undo/redo workflows are required
- Cross-module state synchronization becomes necessary

### Theme System

**Approach:** CSS custom properties + Tailwind dark mode (`class` strategy) + React Context.

The `ThemeProvider`:
1. Stores the current theme in React Context
2. Persists the choice to `localStorage`
3. Toggles the `dark` class on `<html>` element
4. Tailwind's `dark:` variants apply dark-mode styles
5. shadcn/ui CSS variables define the color palette per theme

This is intentionally simple — no CSS-in-JS, no runtime theming engine. Tailwind's `class` strategy means dark mode is activation-based (not OS-preference-based by default, though we respect `prefers-color-scheme` for the initial value).

### Design System (shadcn/ui)

shadcn/ui provides copy-paste components built on Radix UI primitives. We adopt the following components for the shell:

| Component | Usage |
|---|---|
| Button | All clickable actions |
| Separator | Visual dividers |
| ScrollArea | Scrollable content regions |
| Sheet | Mobile sidebar drawer |
| DropdownMenu | User menu, settings |
| Tooltip | Icon descriptions |
| Switch | Theme toggle |

Additional components are added per-module as needed — never installed preemptively ("you are not going to need it").

### API Client Architecture

```
┌─────────────────────────────────────────┐
│            Feature Module                │
│  calls typed service function            │
│  e.g., healthService.getStatus()         │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         services/health.ts              │
│  Typed function using apiClient         │
│  Returns Promise<HealthResponse>        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         services/api-client.ts          │
│  Axios instance with interceptors       │
│  - Request: inject headers              │
│  - Response: normalize errors           │
│  - Base URL from env/config             │
└──────────────────┬──────────────────────┘
                   │
            ┌──────▼──────┐
            │   Backend   │
            │  /api/v1/*  │
            └─────────────┘
```

**Error normalization** — all API errors are transformed into a standard shape:

```typescript
interface ApiError {
  code: string;
  message: string;
  detail: Record<string, unknown> | null;
  requestId: string;
  status: number;
}
```

### Testing Strategy

| Layer | Tool | Scope |
|---|---|---|
| Unit tests | Vitest | Pure functions, hooks, utilities |
| Component tests | Vitest + React Testing Library | Components render correctly, handle states |
| Integration tests | Vitest + RTL + MSW (future) | Feature workflows |
| E2E tests | Playwright (future) | Critical user paths |

**For Phase 2.5:** Unit + component tests for all shell components, layouts, API client, and hooks. No integration or E2E tests yet.

### Docker Integration

The frontend is served in production via Nginx (static file server with SPA fallback).

```
docker-compose.yml
├── postgres    (PostgreSQL 16)
├── backend     (FastAPI / Uvicorn)
└── frontend    (Nginx serving built SPA)
```

**Development flow:**
- `cd frontend && npm run dev` — Vite dev server on `:3000`
- Backend CORS already allows `http://localhost:3000`
- `docker compose up --build` — full production-like stack

**Production flow:**
- Multi-stage Dockerfile: `node:20-alpine` for build, `nginx:alpine` for runtime
- Static files served by Nginx, all routes fall back to `index.html`

---

## Alternatives Considered

### Alternative A: Pages-First Organization (Rejected)

Organize by pages: `src/pages/Home.tsx`, `src/pages/Settings.tsx`, etc.

| Dimension | Pages-First | Feature-First (Chosen) |
|---|---|---|
| **Module isolation** | Poor — all pages in one directory | Excellent — modules self-contained |
| **Scaling** | Directory grows linearly with pages | Directory grows by feature |
| **Code proximity** | Related code scattered across directories | Related code in one module |
| **Module extraction** | Hard — must extract from flat structure | Trivial — copy the module directory |

### Alternative B: Redux/Zustand for State Management (Rejected)

| Dimension | Global Store | TanStack Query + Local State (Chosen) |
|---|---|---|
| **Boilerplate** | Actions, reducers, selectors | Minimal — query key + fetcher function |
| **Server state** | Manual caching, refetch logic | Automatic — caching, refetching, pagination |
| **Learning curve** | Significant | Standard React patterns |
| **Bundle size** | ~10KB (Zustand) to ~30KB (Redux Toolkit) | ~15KB (TanStack Query) |
| **Need** | Not yet justified | Not yet justified |

### Alternative C: CSS-in-JS (styled-components, Emotion) (Rejected)

| Dimension | CSS-in-JS | Tailwind CSS (Chosen) |
|---|---|---|
| **Runtime** | ~15KB runtime | Zero runtime |
| **Design consistency** | Depends on discipline | Built-in design tokens |
| **Bundle size** | Each style adds runtime JS | Styles purged at build |
| **Learning curve** | Familiar to React developers | Utility-first requires adjustment |
| **shadcn/ui compatibility** | Not compatible | Native |

---

## Trade-offs

| Trade-off | Assessment |
|---|---|
| **No global state** vs **Convenience** | TanStack Query + Context covers current needs. Adding Redux later is possible but should be resisted until a clear pain point emerges. |
| **shadcn/ui copy-paste** vs **npm package** | No locked-in version, full control, but manual updates. Acceptable for a platform that controls its dependencies. |
| **Feature modules** vs **Pages** | Modules add directory nesting but provide clear boundaries. Worth the overhead for 3+ modules. |
| **Nginx SPA serving** vs **Vite dev proxy** | Nginx is production-standard. For development, Vite's dev server with HMR is superior — we support both. |

---

## Consequences

### Positive

1. **Feature modules are independent** — a new module is a directory with clear boundaries
2. **API layer is reusable** — typed services prevent raw Axios calls in components
3. **Shell is established** — every future module gets sidebar, top bar, theme, error boundaries for free
4. **Test infrastructure exists** — no excuses to skip tests on new modules
5. **Docker integration** — full-stack development with one command

### Negative

1. **Initial setup overhead** — configuring Vite, Tailwind, shadcn/ui, Vitest, Docker before any business logic
2. **No global state** — if a cross-cutting concern emerges (e.g., active workspace ID), we'll need to add context or a lightweight store
3. **Module pattern requires discipline** — teams must follow conventions (no cross-module imports)

### Neutral

1. **Frontend grows with modules** — each module adds ~5-10 files; the architecture scales linearly
2. **CDN/deployment flexibility** — static files can be served from any CDN or from the Nginx container

---

## Implementation Impact

### New Files

```
frontend/                          (entire directory — 30+ files)
├── Dockerfile
├── nginx.conf
├── package.json
├── vite.config.ts
├── vitest.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── components.json
├── tsconfig.json
├── tsconfig.node.json
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── app/
    │   ├── providers.tsx
    │   ├── router.tsx
    │   └── pages/
    │       ├── home.tsx
    │       ├── settings.tsx
    │       └── not-found.tsx
    ├── components/
    │   ├── ui/
    │   │   ├── button.tsx
    │   │   ├── separator.tsx
    │   │   ├── scroll-area.tsx
    │   │   ├── sheet.tsx
    │   │   ├── dropdown-menu.tsx
    │   │   └── tooltip.tsx
    │   ├── error-boundary.tsx
    │   ├── loading-state.tsx
    │   ├── empty-state.tsx
    │   └── theme-toggle.tsx
    ├── layouts/
    │   ├── root-layout.tsx
    │   ├── sidebar.tsx
    │   └── topbar.tsx
    ├── modules/
    │   ├── requirement-analysis/
    │   ├── api-test-generation/
    │   └── failure-analysis/
    ├── services/
    │   ├── api-client.ts
    │   ├── health.ts
    │   └── index.ts
    ├── hooks/
    │   ├── use-health.ts
    │   └── use-theme.ts
    ├── lib/
    │   ├── utils.ts
    │   └── constants.ts
    └── types/
        ├── api.ts
        └── index.ts
```

### Modified Files

- `docker-compose.yml` — add `frontend` service
- `docker-compose.override.yml` — add frontend dev overrides
- `docs/development.md` — update project structure, add frontend section
- `docs/adr/README.md` — add ADR-006 reference

---

## Decision Rationale Summary

The Frontend Architecture is **justified** because:

1. **Feature-first organization mirrors the backend** — consistent mental model across the stack
2. **shadcn/ui + Tailwind** provides a professional design system without framework lock-in
3. **TanStack Query + local state** avoids premature global state complexity
4. **Typed API layer** prevents coupling between HTTP concerns and business logic
5. **Docker Compose integration** ensures one-command full-stack development

**Abstraction question answers:**

| Question | Answer |
|---|---|
| **What problem does this solve?** | Provides a scalable frontend architecture that supports multiple feature modules without structural refactoring |
| **Why is this necessary today?** | Frontend must exist before business features; the shell and infrastructure must be established first |
| **What simpler alternative exists?** | Create React App with pages-first organization, no design system, global state from day one |
| **Why was that rejected?** | CRA is deprecated; pages-first doesn't scale with modules; premature global state adds complexity without value |
| **How does this help evolution?** | Adding a module is creating a directory with known structure; removing one is deleting that directory |
