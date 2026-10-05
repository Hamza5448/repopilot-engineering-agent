"""HTTP boundary for the initial RepoPilot vertical slice."""

from fastapi import FastAPI, Header, HTTPException, Request, status

from .config import get_settings
from .github.webhooks import DeliveryStore, InvalidWebhookSignature, parse_event, verify_signature

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.delivery_store = DeliveryStore()


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["operations"])
def ready() -> dict[str, str]:
    return {"status": "ready", "environment": settings.app_env}


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

    if x_github_event == "issues":
        parse_event(payload)

    return {"status": "accepted", "delivery_id": x_github_delivery}
