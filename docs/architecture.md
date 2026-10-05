# RepoPilot Architecture

```text
GitHub App -> FastAPI Gateway -> Run Orchestrator -> PostgreSQL
                                  |              -> Redis queue
                                  v
                         Agent workers -> Sandbox workers -> Validation
                                  |              |              |
                                  +--------------+--------------+-> Artifact store
                                  v
                         GitHub publisher -> Checks / branches / PRs

React dashboard -> API Gateway
All services -> structured logs / traces / metrics
```

## Components

- API gateway: authentication, webhook verification, rate limits, request IDs, and REST boundaries.
- Orchestrator: durable state machine, retries, cancellation, approval gates, and stage sequencing.
- Context engine: repository map, file/symbol retrieval, history, and token budgeting.
- Agent runtime: structured outputs, typed tool calls, role handoffs, provider abstraction, and bounded repair.
- Sandbox: ephemeral clone, filesystem tools, allowlisted commands, controlled network, CPU/memory/disk limits.
- Validation: normalized tests, lint, formatting, type, and security results.
- GitHub adapter: installation tokens, branches, commits, PRs, comments, Checks, and annotations.
- Policy engine: authority level, protected paths, command rules, and approval rules.
- Dashboard: runs, events, evidence, approvals, repository settings, and health.

## State and evidence

The core entities are User, Installation, Repository, Policy, AgentRun, RunEvent, ToolExecution, Approval, Artifact, and Evaluation. Ordered run events and immutable artifacts provide the audit trail needed to reconstruct what the agent attempted and why.

## Reliability boundaries

Webhook requests acknowledge quickly and enqueue durable work. Workers own long-running execution. Retries are bounded and idempotency keys prevent duplicate runs or duplicate PR publication. Health and readiness are distinct. Dead-letter handling and replay runbooks are required before production deployment.
