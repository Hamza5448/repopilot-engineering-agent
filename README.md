# RepoPilot

RepoPilot is a policy-controlled AI software engineering agent that reacts to GitHub events, builds repository context, works in isolated execution environments, validates its own patches, and reports evidence through GitHub Checks. When authorized, it can open review-ready pull requests without bypassing human governance.

This repository is the implementation workspace for the RepoPilot product specification. The project is intentionally organized as a production-oriented monorepo so the backend, worker runtime, frontend, database, integrations, testing, and operations can evolve together.

## Product context

- Primary workflow: GitHub issue -> analysis -> plan -> patch -> validation -> review -> pull request.
- Secondary workflow: pull request -> risk-aware AI review -> GitHub Check annotations.
- Initial language support: Python repositories, with adapter boundaries for future languages.
- Safety posture: no unrestricted shell, isolated sandbox execution, least-privilege GitHub App access, explicit policy gates, durable audit events, and bounded repair loops.
- v1 does not automatically merge protected branches.
- Target: a deployable, observable, testable, recoverable, job-ready flagship project.

## Documentation

- [Product specification](docs/product-specification.md)
- [Delivery roadmap](docs/roadmap.md)
- [Architecture](docs/architecture.md)
- [Security and threat model](docs/security/threat-model.md)
- [Development guide](CONTRIBUTING.md)
- [Architecture decision records](docs/adr/)
- [Runbooks](docs/runbooks/)

## Planned stack

Python 3.12+, FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic, Redis, a queue worker, React/TypeScript, Docker, OpenTelemetry, structured logging, Prometheus-compatible metrics, and GitHub Actions.

## Current status

Phase 0 — Engineering foundation. The repository skeleton and product documentation are established; implementation proceeds in roadmap order.

## Quick start

The local development commands will be finalized with the first backend and frontend implementation slices. Until then, use the roadmap and contributing guide as the source of truth for work sequencing and Git practice.

## License

License to be decided before the first public release.
