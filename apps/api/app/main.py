"""HTTP boundary for the initial RepoPilot vertical slice."""

import httpx
import redis
from fastapi import FastAPI, Header, HTTPException, Request, status

from apps.worker.worker.queue import RedisQueue, RunJob
from packages.agents.planner import Planner
from packages.context.context import build_context
from packages.github.api import GitHubInstallationTokenProvider, GitHubPublisherClient
from packages.github.auth import GitHubAppAuthenticator, GitHubAppConfigurationError

from .config import get_settings
from .github.repositories import RepositoryStore
from .github.webhooks import DeliveryStore, InvalidWebhookSignature, parse_event, verify_signature
from .runs import ApprovalDecision, CreateRunRequest, PlanRunRequest
from .storage.sqlalchemy import SqlAlchemyRunStore
from .storage.sqlite import RunStore

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.delivery_store = DeliveryStore()
app.state.repository_store = RepositoryStore()
app.state.run_store = (
    SqlAlchemyRunStore(settings.database_url)
    if settings.storage_backend == "postgres"
    else RunStore(settings.database_path)
)
app.state.queue = RedisQueue(redis.Redis.from_url(settings.redis_url))


def resolve_branch_sha(owner: str, repository: str, branch: str, installation_id: int) -> str:
    if not settings.github_app_id:
        raise GitHubAppConfigurationError("GitHub App ID is not configured")
    authenticator = GitHubAppAuthenticator(
        settings.github_app_id,
        private_key=settings.github_app_private_key,
        private_key_path=settings.github_app_private_key_path,
    )
    token = GitHubInstallationTokenProvider(authenticator).get_token(installation_id)
    return GitHubPublisherClient(owner, repository, token).get_branch_sha(owner, repository, branch)


app.state.github_sha_resolver = resolve_branch_sha


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def ready() -> dict[str, object]:
    return {
        "status": "ready",
        "environment": settings.app_env,
        "github_app_configured": settings.github_credentials_configured,
    }


@app.get("/api/v1/repositories", tags=["repositories"])
def list_repositories() -> list[dict[str, object]]:
    return [repository.model_dump() for repository in app.state.repository_store.list()]


@app.get("/api/v1/repositories/{repository_id}", tags=["repositories"])
def get_repository(repository_id: int) -> dict[str, object]:
    repository = app.state.repository_store.get(repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository.model_dump()


@app.post("/api/v1/repositories/{repository_id}/runs", status_code=status.HTTP_201_CREATED, tags=["runs"])
def create_run(repository_id: int, request: CreateRunRequest) -> dict[str, object]:
    if app.state.repository_store.get(repository_id) is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    run = app.state.run_store.create_run(repository_id, request.trigger_type, request.base_sha)
    app.state.queue.enqueue(
        RunJob(
            run_id=run["id"],
            repository_id=repository_id,
            base_sha=request.base_sha,
            issue_title=request.issue_title,
            issue_body=request.issue_body,
            files=request.files,
            repository_url=request.repository_url,
            patch=request.patch,
            branch_name=request.branch_name,
            commit_message=request.commit_message,
        )
    )
    return run


@app.get("/api/v1/runs/{run_id}", tags=["runs"])
def get_run(run_id: str) -> dict[str, object]:
    run = app.state.run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.get("/api/v1/runs/{run_id}/events", tags=["runs"])
def get_run_events(run_id: str) -> list[dict[str, object]]:
    if app.state.run_store.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return app.state.run_store.list_events(run_id)


def _control_run(run_id: str) -> dict[str, object]:
    run = app.state.run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["status"] in {"succeeded", "failed", "cancelled"}:
        raise HTTPException(status_code=409, detail="Run is already terminal")
    return run


@app.post("/api/v1/runs/{run_id}/cancel", tags=["runs"])
def cancel_run(run_id: str, decision: ApprovalDecision | None = None) -> dict[str, object]:
    _control_run(run_id)
    app.state.run_store.update_status(run_id, "cancelled")
    app.state.run_store.append_event(run_id, "run.cancelled", {"rationale": decision.rationale if decision else ""})
    return app.state.run_store.get_run(run_id)


@app.post("/api/v1/runs/{run_id}/approve", tags=["runs"])
def approve_run(run_id: str, decision: ApprovalDecision) -> dict[str, object]:
    run = _control_run(run_id)
    if run["status"] != "waiting_for_approval":
        raise HTTPException(status_code=409, detail="Run is not waiting for approval")
    app.state.run_store.update_status(run_id, "queued")
    app.state.run_store.append_event(run_id, "run.approved", decision.model_dump())
    return app.state.run_store.get_run(run_id)


@app.post("/api/v1/runs/{run_id}/reject", tags=["runs"])
def reject_run(run_id: str, decision: ApprovalDecision) -> dict[str, object]:
    run = _control_run(run_id)
    if run["status"] != "waiting_for_approval":
        raise HTTPException(status_code=409, detail="Run is not waiting for approval")
    app.state.run_store.update_status(run_id, "failed")
    app.state.run_store.append_event(run_id, "run.rejected", decision.model_dump())
    return app.state.run_store.get_run(run_id)


@app.post("/api/v1/runs/{run_id}/plan", tags=["runs"])
def plan_run(run_id: str, request: PlanRunRequest) -> dict[str, object]:
    run = app.state.run_store.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    context = build_context(
        repository_id=run["repository_id"],
        base_sha=run["base_sha"],
        issue_title=request.issue_title,
        issue_body=request.issue_body,
        files=request.files,
    )
    plan = Planner().plan(context)
    plan_payload = {"context": context.model_dump(), "plan": plan.model_dump()}
    app.state.run_store.append_event(run_id, "run.planned", plan_payload)
    return plan.model_dump()


@app.post("/webhooks/github", status_code=status.HTTP_202_ACCEPTED, tags=["github"])
async def github_webhook(
    request: Request,
    x_github_delivery: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    """Verify, deduplicate, and acknowledge a GitHub webhook delivery."""

    if not settings.github_webhook_secret:
        raise HTTPException(status_code=503, detail="GitHub webhook secret is not configured")
    if not x_github_delivery:
        raise HTTPException(status_code=400, detail="Missing GitHub delivery ID")

    payload = await request.body()
    try:
        verify_signature(payload, x_hub_signature_256, settings.github_webhook_secret)
    except InvalidWebhookSignature as exc:
        raise HTTPException(status_code=401, detail="Invalid webhook signature") from exc

    if not app.state.delivery_store.claim(x_github_delivery):
        return {"status": "duplicate", "delivery_id": x_github_delivery}

    if x_github_event == "installation_repositories":
        event = parse_event(payload)
        installation_id = event.installation.get("id") if event.installation else None
        for repository in event.model_dump().get("repositories_added", []):
            app.state.repository_store.upsert_from_github(repository, installation_id)
    elif x_github_event == "issues":
        event = parse_event(payload)
        labels = event.issue.get("labels", [])
        triggered = x_github_event == "issues" and event.action in {"opened", "reopened", "labeled"} and any(
            label.get("name") == "repopilot" for label in labels if isinstance(label, dict)
        )
        if triggered:
            repository = event.repository
            installation_id = event.installation.get("id") if event.installation else None
            full_name = repository.get("full_name", "")
            if not installation_id or not repository.get("id") or "/" not in full_name:
                raise HTTPException(status_code=400, detail="Issue event lacks repository installation context")
            owner, repository_name = full_name.split("/", 1)
            app.state.repository_store.upsert_from_github(repository, installation_id)
            try:
                base_sha = app.state.github_sha_resolver(
                    owner,
                    repository_name,
                    repository.get("default_branch", "main"),
                    installation_id,
                )
            except (GitHubAppConfigurationError, OSError, httpx.HTTPError) as exc:
                raise HTTPException(status_code=503, detail="Unable to resolve repository base revision") from exc
            run = app.state.run_store.create_run(repository["id"], "github_issue", base_sha)
            issue = event.issue
            app.state.queue.enqueue(
                RunJob(
                    run_id=run["id"],
                    repository_id=repository["id"],
                    base_sha=base_sha,
                    issue_title=issue.get("title", ""),
                    issue_body=issue.get("body", "") or "",
                    repository_url=f"https://github.com/{full_name}.git",
                )
            )

    return {"status": "accepted", "delivery_id": x_github_delivery}
