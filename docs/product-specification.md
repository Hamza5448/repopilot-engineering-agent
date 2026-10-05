# RepoPilot Product Specification

## Purpose

RepoPilot is a policy-controlled engineering agent, not a repository chatbot. It reacts to GitHub events, builds context for an exact commit, plans changes, works inside isolated execution environments, validates patches, performs independent review, and reports evidence through GitHub Checks.

## v1 scope

The first production release focuses on issue-to-pull-request engineering work and pull-request review for controlled repositories. It must be deployable, observable, testable, recoverable, and safe enough to install on selected repositories.

## Core capabilities

- GitHub App installation and repository onboarding.
- Signed, deduplicated webhook processing.
- Durable run orchestration with retries, cancellation, approvals, events, artifacts, and audit history.
- Repository mapping and targeted context retrieval for an exact target SHA.
- Structured planner, implementer, and independent reviewer roles.
- Isolated sandbox execution with typed tools and allowlisted commands.
- Repository-specific test, lint, formatting, type, and security validation.
- Bounded repair loops after validation or review failures.
- Branch, commit, pull request, GitHub Check, and annotation publishing when policy allows.
- Dashboard for run timelines, evidence, approvals, settings, and repository health.
- Evaluation harness for task success, regression rate, review precision, cost, and latency.

## Safety and authority

The model never receives an unrestricted shell. Every state-changing tool call is policy-authorized. Repository content, issue text, and pull request text are untrusted input and cannot override system policy. Destructive Git operations, secret access, protected-path writes, branch-protection changes, and direct default-branch pushes are denied.

Authority levels are L0 Observe, L1 Propose, L2 Workspace, L3 Branch, L4 Pull Request, and L5 Merge. L5 is outside v1.

## Functional requirements

FR-01 through FR-18 cover onboarding, webhook verification and idempotency, exact-SHA context, structured planning, authorization, isolation, validation evidence, independent review, bounded repair, Checks, PR publication, approvals, dashboard visibility, cancellation, retries, usage metrics, and read-only PR review by default.

## Non-functional requirements

Webhook acknowledgement should remain under two seconds under normal load; long work is queued. Runs must be auditable and recoverable, secrets must not leak, integrations must be replaceable behind interfaces, and the local stack must run through Docker Compose.

## Initial API surface

```text
POST   /webhooks/github
GET    /api/v1/repositories
GET    /api/v1/repositories/{id}
PUT    /api/v1/repositories/{id}/policy
POST   /api/v1/repositories/{id}/runs
GET    /api/v1/runs/{id}
POST   /api/v1/runs/{id}/cancel
POST   /api/v1/runs/{id}/approve
POST   /api/v1/runs/{id}/reject
GET    /api/v1/runs/{id}/events
GET    /api/v1/runs/{id}/artifacts
POST   /api/v1/pull-requests/{id}/review
GET    /health
GET    /ready
GET    /metrics
```

## Explicitly out of scope for v1

Replacing a full IDE, unrestricted execution of arbitrary public repositories, automatic merge to protected branches, every programming language, foundation-model training, large-scale enterprise billing/SSO/RBAC, and a visual no-code agent builder.

## Acceptance bar

The project is portfolio-ready only when a controlled GitHub installation can demonstrate an issue-triggered durable run, context and plan evidence, sandbox changes, real validation, a failure-and-repair cycle, independent review, approval, a generated PR, passing CI, and an explainable threat model and recovery design.
