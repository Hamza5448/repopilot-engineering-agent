# GitHub App Live Setup

RepoPilot uses a GitHub App rather than a broad personal access token for normal repository operations. Configure the App only for a controlled test repository until the live workflow has been reviewed.

## Create the App

In GitHub, create a new GitHub App under the account or organization that owns the test repository.

Use these initial settings:

- Webhook URL: the publicly reachable HTTPS URL for `POST /webhooks/github`.
- Webhook secret: generate a long random value and keep it in the local secret store.
- Repository permissions: Contents read/write, Issues read, Pull requests read/write, Checks read/write, and Metadata read.
- Subscribe to events: Installation repositories, Issues, Pull request, and Workflow run if needed later.
- Install the App only on the controlled repository.

Download the private key once and store it outside Git. Do not paste it into chat, commit it, or put it in an issue or log.

## Local configuration

Copy `.env.example` to `.env` and set:

```text
STORAGE_BACKEND=postgres
GITHUB_APP_ID=<numeric app id>
GITHUB_APP_PRIVATE_KEY_PATH=C:\\secure\\repopilot\\github-app.pem
GITHUB_WEBHOOK_SECRET=<webhook secret>
GITHUB_OWNER=<owner or organization>
GITHUB_REPOSITORY=<repository name>
```

When using Docker Compose, pass the same values through the shell environment or a local Compose override. Keep `.env` untracked.

## Verify configuration

Start the local stack and inspect readiness:

```powershell
docker compose up -d
Invoke-RestMethod http://localhost:8000/ready
```

The response must show `github_app_configured: true`. This flag confirms only that required configuration fields exist; it does not print or validate the private key contents.

## First live workflow checklist

1. Install the App on one disposable or controlled repository.
2. Confirm the webhook delivery reaches `/webhooks/github` with a valid signature.
3. Confirm the repository appears in the onboarding store.
4. Open a small issue with the agreed RepoPilot trigger label.
5. Watch the run timeline and verify approval before any branch or PR mutation.
6. Confirm the generated branch, commit, PR, and Check contain evidence.
7. Revoke the installation and rotate the webhook secret after the test if the environment was temporary.
