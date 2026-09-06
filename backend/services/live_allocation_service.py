"""
Live allocation service.

Translates the server-authoritative active-user list into a request
that the existing Game Theory ``allocate_bandwidth`` engine already
understands:

    { user_id, activity, requested_bandwidth, ... }

No new algorithm is introduced. The existing research engine is reused
as-is. The mapping rules live in ``backend.services.activity_mapping``
so the same logic is unit-testable.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Look up these at call time so tests can monkey-patch them onto the
# module to point at an isolated database.
from backend import database
from backend.data_provenance import REAL_USER_INPUT
from backend.services.activity_mapping import normalise_activity


def _get_account(username: str):
    return database.accounts_db.get_account(username)


def _list_active_sessions(timeout_seconds: Optional[int] = None):
    return database.accounts_db.list_active_sessions(timeout_seconds)


def _timeout_seconds() -> int:
    return database.accounts_db.LIVE_SESSION_TIMEOUT_SECONDS


def _usage_bandwidth_for(username: str, seed_base: float) -> float:
    """Derive a deterministic but unique requested bandwidth per user.

    No hardcoded cap on the number of users — every unique active
    username gets its own value. Values are in the 1-25 Mbps range to
    span typical Wi-Fi client demand without overflowing the
    Game Theory search grid.
    """
    h = 2166136261
    for ch in username:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    h &= 0xFFFFFFFF
    return float(1.0 + (h % 1000) / 1000.0 * 24.0 + (seed_base % 1.0))


def build_live_allocation_request(
    timeout_seconds: Optional[int] = None,
    total_bandwidth: float = 40.0,
    user_requests: Optional[Dict[str, float]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Build an allocation request from the live session table.

    Only active users who have provided a genuine bandwidth request
    are included. Users without a real request are skipped; the
    caller must not fabricate demand.

    Returns
    -------
    (users, meta)
        users  — list of dicts compatible with ``/api/allocate``
        meta   — provenance/observability info
    """
    sessions = _list_active_sessions(timeout_seconds or _timeout_seconds())
    real_requests = user_requests or {}

    users: List[Dict[str, Any]] = []
    seen = set()
    for sess in sessions:
        username = sess.get("username")
        if not username or username in seen:
            continue
        seen.add(username)

        if username not in real_requests:
            continue

        requested = float(real_requests[username])
        account = _get_account(username) or {}
        reason = account.get("usage_reason") or "General Browsing"
        activity = normalise_activity(reason)
        users.append({
            "user_id": username,
            "activity": activity,
            "requested_bandwidth": round(requested, 2),
        })

    meta = {
        "active_session_count": len(sessions),
        "unique_user_count": len(users),
        "timeout_seconds": timeout_seconds or _timeout_seconds(),
        "total_bandwidth": total_bandwidth,
        "user_demand_source": REAL_USER_INPUT,
    }
    return users, meta
