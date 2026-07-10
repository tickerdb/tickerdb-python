"""Team types."""

from typing import List, Literal, Optional, TypedDict

__all__ = [
    "TeamRole",
    "TeamMember",
    "TeamInvite",
    "Team",
    "TeamPendingInvite",
    "TeamsResponse",
]

TeamRole = Literal["owner", "admin", "member"]


class TeamMember(TypedDict, total=False):
    """A member of a team."""

    user_id: str
    email: str
    name: Optional[str]
    role: TeamRole
    joined_at: Optional[str]


class TeamInvite(TypedDict, total=False):
    """A pending invite on a team (as seen by owners/admins)."""

    id: str
    email: str
    role: TeamRole
    expires_at: Optional[str]
    created_at: Optional[str]


class Team(TypedDict, total=False):
    """A team the authenticated user belongs to."""

    id: str
    name: str
    max_seats: int
    extra_seats: int
    seats_used: int
    seats_available: int
    your_role: TeamRole
    members: List[TeamMember]
    pending_invites: List[TeamInvite]


class TeamPendingInvite(TypedDict, total=False):
    """A pending invite addressed to the authenticated user."""

    id: str
    team_id: str
    team_name: str
    role: TeamRole
    inviter_email: str
    expires_at: Optional[str]


class TeamsResponse(TypedDict, total=False):
    """Response from the team list endpoint."""

    teams: List[Team]
    my_pending_invites: List[TeamPendingInvite]
