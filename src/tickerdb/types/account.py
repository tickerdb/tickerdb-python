"""Account endpoint types."""

from typing import Optional, TypedDict

__all__ = ["AccountLimits", "AccountUsage", "AccountResponse"]


class AccountLimits(TypedDict, total=False):
    """Plan limits reported by the account endpoint."""

    monthly_requests: int
    overage_enabled: bool
    search_results: int
    history_days: int


class AccountUsage(TypedDict, total=False):
    """Current usage reported by the account endpoint."""

    monthly_requests_used: int
    monthly_requests_remaining: int
    credit_balance: int


class AccountResponse(TypedDict, total=False):
    """Response from the account endpoint."""

    tier: str
    tier_full: str
    email: str
    limits: AccountLimits
    usage: AccountUsage
    scheduled_tier: Optional[str]
    scheduled_change_at: Optional[str]
