# RepoPilot Delivery Roadmap

The roadmap is the execution contract. Work should be delivered in small vertical slices, with each phase leaving the system more runnable and more observable.

## Phase 0 — Engineering foundation

Monorepo, domain model, ADRs, CI, local Compose stack, configuration, logging, health endpoints, testing conventions, and quality gates.

## Phase 1 — GitHub App core

Installation/authentication, scoped permissions, webhook signature verification, delivery idempotency, repository onboarding, and event persistence.

## Phase 2 — Context and planning

Repository map, language/framework detection, targeted retrieval, issue analysis, structured planner output, risk assessment, and validation strategy.

## Phase 3 — Sandbox execution

Ephemeral workspace, exact-SHA clone, typed filesystem tools, command authorization, resource limits, patch creation, validation adapters, and artifact retention.

## Phase 4 — Pull request delivery

Branch/commit/PR publishing, GitHub Checks, annotations, approval gates, cancellation, retry/backoff, and failure recovery.

## Phase 5 — Independent review agent

Diff review, scope and security checks, risk scoring, high-confidence PR review findings, and bounded repair orchestration.

## Phase 6 — Productization

Dashboard, run timeline, live updates, metrics, traces, structured logs, deployment, secrets handling, runbooks, and operational hardening.

## Phase 7 — Evaluation and release

Curated benchmark, seeded demo repository, regression suite, threat-model review, architecture diagrams, release notes, and v1.0 readiness review.

## Working rules

- Build one end-to-end thin slice before broadening abstractions.
- Keep provider, GitHub, queue, sandbox, and validation integrations behind explicit interfaces.
- Treat every external mutation as policy-gated and auditable.
- Do not add autonomous merge to the v1 critical path.
- Revalidate external GitHub and model-provider assumptions during implementation.
