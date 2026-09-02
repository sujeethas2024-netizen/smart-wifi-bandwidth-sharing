"""
Auth API — registration (with WiFi usage reason), login,
username availability and admin account listing.
Data is persisted in SQLite (database/accounts.db).
"""

from flask import Blueprint, jsonify, request

import secrets

from backend.database.accounts_db import (
    create_account,
    verify_credentials,
    get_account,
    list_accounts,
    public_account,
    username_exists,
    create_live_session,
    get_live_session,
    touch_live_session,
    revoke_live_session,
    list_active_sessions,
    public_live_session,
    LIVE_SESSION_STATUS_ACTIVE,
    LIVE_SESSION_STATUS_REVOKED,
    LIVE_SESSION_TIMEOUT_SECONDS,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    full_name = (data.get("fullName") or "").strip()
    usage_reason = (data.get("usageReason") or "").strip()
    device_count = data.get("deviceCount", 1)

    if not username:
        return jsonify({"ok": False, "error": "Username is required."}), 400
    if not password:
        return jsonify({"ok": False, "error": "Password is required."}), 400
    if not usage_reason:
        return jsonify({"ok": False, "error": "Please provide your WiFi usage reason."}), 400

    ok, result = create_account(
        username=username,
        password=password,
        full_name=full_name,
        role="user",  # public signups are always regular users
        usage_reason=usage_reason,
        device_count=device_count,
    )

    if not ok:
        return jsonify({"ok": False, "error": result}), 409 if "taken" in str(result) else 400

    return jsonify({"ok": True, "user": public_account(result)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password are required."}), 400

    account, error = verify_credentials(username, password)
    if error:
        status = 404 if "No account" in error else 401
        return jsonify({"ok": False, "error": error}), status

    session_id = secrets.token_urlsafe(32)
    session_row = create_live_session(
        session_id=session_id,
        username=account["username"],
        ip_address=(request.remote_addr or ""),
        user_agent=(request.headers.get("User-Agent") or ""),
    )
    if not session_row:
        return jsonify({
            "ok": False,
            "error": "Could not establish session. Please try again.",
        }), 500

    return jsonify({
        "ok": True,
        "user": public_account(account),
        "sessionId": session_row["session_id"],
    })


@auth_bp.route("/check-username", methods=["GET"])
def check_username():
    username = (request.args.get("username") or "").strip()
    if not username:
        return jsonify({"available": False, "error": "Username required."})
    return jsonify({"available": not username_exists(username)})


@auth_bp.route("/accounts", methods=["GET"])
def accounts():
    """Registered accounts incl. their declared WiFi usage reason
    (used by the admin console)."""
    return jsonify({"ok": True, "accounts": list_accounts()})


@auth_bp.route("/me", methods=["GET"])
def me():
    username = (request.args.get("username") or "").strip()
    account = get_account(username) if username else None
    if not account:
        return jsonify({"ok": False, "error": "Not found."}), 404
    return jsonify({"ok": True, "user": public_account(account)})


def _extract_bearer_token():
    """Extract a session ID from the Authorization header.

    Returns the token string or None when the header is missing or
    malformed. Never accepts ?token= query strings.
    """
    header = request.headers.get("Authorization", "")
    if not header:
        return None
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def _parse_iso(ts: str):
    """Parse an ISO-8601 string written by datetime.utcnow().isoformat().
    Returns None on malformed input."""
    from datetime import datetime
    if not ts:
        return None
    try:
        # Python's fromisoformat handles the 'T' separator and fractional seconds.
        return datetime.fromisoformat(ts)
    except (TypeError, ValueError):
        return None


def live_session_status(session_row):
    """Classify a session row as 'active', 'expired' or 'revoked'.

    Pure helper that consults ONLY the row + the configured timeout.
    Does not touch the database layer.
    """
    if not session_row:
        return None
    if session_row.get("status") == LIVE_SESSION_STATUS_REVOKED:
        return LIVE_SESSION_STATUS_REVOKED
    if session_row.get("status") != LIVE_SESSION_STATUS_ACTIVE:
        return LIVE_SESSION_STATUS_REVOKED
    last_seen = _parse_iso(session_row.get("last_seen"))
    if last_seen is None:
        return "expired"
    from datetime import datetime, timedelta
    age = (datetime.utcnow() - last_seen).total_seconds()
    if age > LIVE_SESSION_TIMEOUT_SECONDS:
        return "expired"
    return LIVE_SESSION_STATUS_ACTIVE


@auth_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    """Authenticated heartbeat.

    Requires `Authorization: Bearer <sessionId>`. Looks up the session
    in `live_sessions`, refuses if missing, revoked, or expired, then
    updates `last_seen` via `touch_live_session`.

    Never echoes the session ID. Never accepts ?token=. Server-authoritative:
    the username/role/etc. are derived from the live_sessions row only.
    """
    session_id = _extract_bearer_token()
    if not session_id:
        return jsonify({
            "ok": False,
            "error": "Missing or malformed Authorization header.",
        }), 401

    session_row = get_live_session(session_id)
    if not session_row:
        return jsonify({
            "ok": False,
            "error": "Invalid session.",
        }), 401

    classification = live_session_status(session_row)
    if classification == LIVE_SESSION_STATUS_REVOKED:
        return jsonify({
            "ok": False,
            "error": "Session is no longer active.",
        }), 401
    if classification == "expired":
        # An expired session must not be silently refreshed back to active.
        # Mark it revoked so list_active_sessions and future lookups agree.
        revoke_live_session(session_id)
        return jsonify({
            "ok": False,
            "error": "Session has expired.",
        }), 401

    if not touch_live_session(session_id):
        return jsonify({
            "ok": False,
            "error": "Session could not be refreshed.",
        }), 500

    refreshed = get_live_session(session_id) or session_row
    return jsonify({
        "ok": True,
        "status": "online",
        "lastSeen": refreshed["last_seen"],
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Authenticated logout.

    Requires `Authorization: Bearer <sessionId>`. Revokes ONLY the
    session identified by the bearer token. Other sessions belonging
    to the same user remain untouched. Never accepts ?token= or
    ?username=.
    """
    session_id = _extract_bearer_token()
    if not session_id:
        return jsonify({
            "ok": False,
            "error": "Missing or malformed Authorization header.",
        }), 401

    session_row = get_live_session(session_id)
    if not session_row:
        return jsonify({
            "ok": False,
            "error": "Invalid session.",
        }), 401

    if session_row.get("status") == LIVE_SESSION_STATUS_REVOKED:
        return jsonify({
            "ok": True,
            "status": "already_signed_out",
        })

    if not revoke_live_session(session_id):
        return jsonify({
            "ok": False,
            "error": "Session could not be revoked.",
        }), 500

    return jsonify({
        "ok": True,
        "status": "signed_out",
    })


@auth_bp.route("/active", methods=["GET"])
def active_sessions():
    """List currently active live sessions.

    Source of truth: the `live_sessions` table filtered through the
    existing `list_active_sessions()` helper. A session is considered
    active only when:
        * status == 'active'  (from the DB layer)
        * last_seen is within LIVE_SESSION_TIMEOUT_SECONDS
    (enforced by the same helper).

    Authentication: requires a valid `Authorization: Bearer <sid>`
    header identifying an active, non-revoked, non-expired session.
    The bearer identity is used purely to confirm the caller is a
    currently-authenticated user; the response never echoes the
    bearer's session ID and the response list never includes
    bearer tokens / passwords / hashes / salts.

    Authorization model: the project currently has no server-side
    admin role gate (see Subtask 1A audit). To avoid inventing a new
    framework within this small task, access is restricted to any
    valid active session. The Admin Dashboard can call this endpoint
    using the admin's own live session token. Tightening this to a
    dedicated admin role check is a separate follow-up.
    """
    session_id = _extract_bearer_token()
    if not session_id:
        return jsonify({
            "ok": False,
            "error": "Missing or malformed Authorization header.",
        }), 401

    caller = get_live_session(session_id)
    if not caller:
        return jsonify({
            "ok": False,
            "error": "Invalid session.",
        }), 401

    if live_session_status(caller) != LIVE_SESSION_STATUS_ACTIVE:
        return jsonify({
            "ok": False,
            "error": "Session is not active.",
        }), 401

    # Reuse the existing DB helper — no SQL duplicated in this route.
    rows = list_active_sessions()
    # Strip the sessionId from the public projection: the session_id IS
    # the bearer token and must never be exposed. We still include a
    # non-secret ordinal id so the admin UI can disambiguate sessions.
    sessions = []
    for idx, r in enumerate(rows):
        view = public_live_session(r)
        view.pop("sessionId", None)
        view["id"] = idx + 1
        sessions.append(view)
    unique_usernames = {r["username"] for r in rows}

    return jsonify({
        "ok": True,
        "activeSessionCount": len(sessions),
        "activeUserCount": len(unique_usernames),
        "timeoutSeconds": LIVE_SESSION_TIMEOUT_SECONDS,
        "sessions": sessions,
    })


@auth_bp.route("/active-users", methods=["GET"])
def active_users():
    """List currently active logged-in users (server-authoritative).

    Source of truth: the ``live_sessions`` table, filtered through the
    existing ``list_active_sessions()`` helper which enforces both:
      * status == 'active'
      * last_seen within ``LIVE_SESSION_TIMEOUT_SECONDS``

    Authentication: requires a valid ``Authorization: Bearer <sid>``
    header identifying an active, non-revoked, non-expired session.
    The bearer identity confirms the caller is authenticated; it is
    never echoed back and ``?username=`` is never accepted.

    Response:
        {
          "ok": true,
          "count": <unique-active-user-count>,
          "users": [
            {"username": ..., "fullName": ..., "role": ..., "lastSeen": ...},
            ...
          ]
        }

    Sensitive fields (session_id, password hashes, salts, IP addresses,
    user-agent strings) are never included.
    """
    session_id = _extract_bearer_token()
    if not session_id:
        return jsonify({
            "ok": False,
            "error": "Missing or malformed Authorization header.",
        }), 401

    caller = get_live_session(session_id)
    if not caller:
        return jsonify({
            "ok": False,
            "error": "Invalid session.",
        }), 401

    if live_session_status(caller) != LIVE_SESSION_STATUS_ACTIVE:
        return jsonify({
            "ok": False,
            "error": "Session is not active.",
        }), 401

    rows = list_active_sessions()

    # Merge sessions by username so each unique user appears once.
    # list_active_sessions() orders by last_seen DESC, so the first
    # occurrence of each username has the most recent last_seen.
    seen = {}
    for r in rows:
        username = r["username"]
        if username in seen:
            continue
        account = get_account(username)
        seen[username] = {
            "username": username,
            "fullName": account["full_name"] if account else username,
            "role": account["role"] if account else "user",
            "lastSeen": r["last_seen"],
        }

    users = list(seen.values())
    return jsonify({
        "ok": True,
        "count": len(users),
        "users": users,
    })