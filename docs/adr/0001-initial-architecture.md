# ADR 0001 Initial Architecture

## Status

Accepted

## Decision

Use a service-oriented monorepo with a FastAPI API boundary, durable PostgreSQL state, Redis-backed asynchronous work, isolated sandbox workers, adapter-based GitHub and model integrations, and a React/TypeScript dashboard.

## Rationale

RepoPilot needs durable long-running work, clear trust boundaries, replaceable infrastructure integrations, and a local environment that demonstrates production concerns. Keeping related services in one repository supports shared contracts, tests, and coordinated changes while preserving deployment boundaries.

## Consequences

The initial scaffold is broader than a single web application, but it makes safety, recovery, and observability first-class. Implementation must avoid premature distributed complexity and should begin with a runnable vertical slice.
