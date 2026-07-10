"""Webhook types."""

from typing import Dict, List, Optional

from .common import TypedDict

__all__ = ["WebhookEvents", "WebhookDelivery", "WebhookDeliveriesResponse"]

WebhookEvents = Dict[str, bool]


class WebhookDelivery(TypedDict, total=False):
    """A single webhook delivery attempt record."""

    id: str
    webhook_id: str
    event_type: str
    timeframe: str
    run_date: str
    status: str
    attempt_count: Optional[int]
    http_status: Optional[int]
    error: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class WebhookDeliveriesResponse(TypedDict, total=False):
    """Response from the webhook deliveries endpoint."""

    deliveries: List[WebhookDelivery]
    count: int
    limit: int
