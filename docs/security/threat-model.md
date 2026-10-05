# RepoPilot Threat Model

## Assets

Source code, GitHub credentials, repository metadata, issue and PR content, generated patches, validation artifacts, model prompts and outputs, audit history, and deployment secrets.

## Trust boundaries

1. GitHub and webhook payloads to the API gateway.
2. API gateway to durable storage and queue.
3. Agent runtime to repository context and model provider.
4. Worker to sandbox execution environment.
5. Sandbox and publisher to GitHub external mutations.

## Primary threats and controls

- Forged webhook: verify HMAC signature and deduplicate delivery IDs.
- Prompt injection in repository content: treat all repository/issue/PR text as untrusted data; keep policy and tool authorization outside model-controlled context.
- Secret exfiltration: scoped installation tokens, secret redaction, no credentials in prompts/logs/artifacts, encrypted storage.
- Dangerous command or path: typed tools, allowlists, protected paths, resource limits, and explicit denials.
- Duplicate or replayed mutation: idempotency keys, exact base SHA, provenance checks, and durable publication state.
- Model self-approval: independent reviewer role and human approval gates.
- Sandbox escape or resource exhaustion: ephemeral isolation, CPU/memory/disk/time limits, controlled network egress, and cleanup.
- Provider/API outage: bounded retries, backoff, durable events, dead-letter handling, and replay procedures.

## Security test cases

Invalid signature, duplicate delivery, prompt injection, protected-path write, forbidden command, secret-like output, sandbox timeout, retry replay, unauthorized approval, and attempted direct default-branch push.
