"""Provider health endpoint.

Returns real-time health statistics for all AI providers:
- Success/failure counts
- Average latency
- Last error messages
- Provider availability status

This endpoint is used by the Settings UI to display provider health.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Request

from app.ai.registry import ProviderRegistry
from app.ai.resilience import HealthTracker, ResilientProvider
from app.domain.models import ResponseMeta

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


@router.get("/providers/health", response_model=dict)
async def get_providers_health(request: Request) -> dict[str, Any]:
    """Return health statistics for all configured AI providers.

    Includes per-provider success/failure counts, average latency,
    consecutive failures, and whether each provider is considered healthy.
    """
    registry: ProviderRegistry | None = getattr(
        request.app.state, "provider_registry", None
    )
    health_tracker: HealthTracker | None = getattr(
        request.app.state, "health_tracker", None
    )

    providers: list[dict[str, Any]] = []

    if registry and health_tracker:
        # Get stats from the health tracker
        all_stats = health_tracker.all_stats()

        # Also include registered providers that haven't been called yet
        registered_names = set(registry.available)
        seen_names = {s["name"] for s in all_stats}

        for name in registered_names - seen_names:
            all_stats.append({
                "name": name,
                "success_count": 0,
                "failure_count": 0,
                "avg_latency_ms": 0,
                "success_rate": 0.0,
                "is_healthy": True,
                "consecutive_failures": 0,
                "last_error": "",
                "last_error_time": 0,
                "last_success_time": 0,
            })

        providers = sorted(all_stats, key=lambda s: s["name"])

    return {
        "data": {
            "providers": providers,
            "total_providers": len(providers),
        },
        "meta": ResponseMeta(
            request_id=getattr(request.state, "request_id", ""),
            timestamp=datetime.utcnow(),
        ).model_dump(),
    }
