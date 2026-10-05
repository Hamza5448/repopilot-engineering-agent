# Contributing to RepoPilot

RepoPilot is built as a professional, review-driven engineering project. Every change should be small enough to understand, tested at the appropriate level, and documented when it changes a contract or architectural decision.

## Git workflow

1. Start from an up-to-date `main` branch.
2. Create a short-lived branch: `feat/<issue>-<name>`, `fix/<issue>-<name>`, `docs/<issue>-<name>`, or `chore/<issue>-<name>`.
3. Make one coherent change at a time. Do not manufacture commits.
4. Use Conventional Commit style where useful, for example `feat(api): persist webhook deliveries`.
5. Open a pull request with the problem, approach, tests/evidence, risk, and screenshots for UI changes.
6. Merge only after required CI and review checks pass.

`main` is intended to be protected: no direct pushes, no force pushes, and required CI checks.

## Definition of done

- Acceptance criteria are covered.
- Tests, linting, typing, and security checks relevant to the change pass.
- New behavior has structured logs and correlation IDs where appropriate.
- API, data model, policy, or architecture changes are documented.
- The pull request explains validation evidence and known limitations.

## Commit and issue discipline

Use GitHub Issues for work. Include acceptance criteria and test expectations. Add an ADR for decisions about the agent runtime, queue, sandbox, authorization, deployment, or other cross-cutting concerns.
