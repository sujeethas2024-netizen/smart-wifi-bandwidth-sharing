"""
Accounts database (SQLite) — stores registered users with their
declared WiFi usage reason. Zero-config: works on any machine.

The MySQL connection in db.py remains untouched for allocation history;
this module handles authentication & account management only.
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "database", "accounts.db")

USERNAME_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_]{3,15}$"
PASSWORD_PATTERN = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[^\s]{8,32}$"

VALID_ROLES = ("admin", "user")

# Status values for live_sessions.status
LIVE_SESSION_STATUS_ACTIVE = "active"
LIVE_SESSION_STATUS_REVOKED = "revoked"

# Configurable inactivity timeout for live sessions. Heartbeats must arrive
# within this window for a session to be considered active. Centralised
# here so the value lives in exactly one place.
LIVE_SESSION_TIMEOUT_SECONDS = int(
    os.environ.get("LIVE_SESSION_TIMEOUT_SECONDS", "90")
)


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


def _hash_password(password: str, salt: str = None):
    """Salted SHA-256 hash. Returns (salt, hash)."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, digest


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables and seed the default admin account."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT DEFAULT '',
                role TEXT NOT NULL DEFAULT 'user',
                usage_reason TEXT NOT NULL DEFAULT 'General Browsing',
                device_count INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_login TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS live_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                ip_address TEXT DEFAULT '',
                user_agent TEXT DEFAULT ''
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_live_sessions_username "
            "ON live_sessions(username)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_live_sessions_last_seen "
            "ON live_sessions(last_seen)"
        )

        # Seed default admin once
        row = conn.execute(
            "SELECT id FROM accounts WHERE username = ?", ("admin",)
        ).fetchone()
        if not row:
            salt, digest = _hash_password("Admin@123")
            conn.execute(
                """
                INSERT INTO accounts
                    (username, password_hash, salt, full_name, role,
                     usage_reason, device_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "admin",
                    digest,
                    salt,
                    "Administrator",
                    "admin",
                    "Network Administration",
                    0,
                    datetime.utcnow().isoformat(),
                ),
            )
        conn.commit()
    finally:
        conn.close()


# ---------------- Validation ----------------

def validate_username(username: str):
    import re
    if not re.match(USERNAME_PATTERN, username or ""):
        return False, (
            "Username must be 4-16 chars, start with a letter, and contain "
            "only letters, numbers & underscore."
        )
    return True, None


def validate_password(password: str):
    import re
    if not re.match(PASSWORD_PATTERN, password or ""):
        return False, ("Password needs 8+ chars with uppercase, lowercase, "
                       "a number and a special character (@$!%*?&#).")
    return True, None


def validate_usage_reason(reason: str):
    if not reason or len(reason.strip()) < 3:
        return False, "Please provide a valid WiFi usage reason."
    return True, None


# ---------------- CRUD ----------------

def username_exists(username: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM accounts WHERE LOWER(username) = LOWER(?)",
            (username,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def create_account(username, password, full_name, role, usage_reason, device_count=1):
    """Returns (ok, error_or_account_dict)."""
    ok, err = validate_username(username)
    if not ok:
        return False, err
    ok, err = validate_password(password)
    if not ok:
        return False, err
    ok, err = validate_usage_reason(usage_reason)
    if not ok:
        return False, err
    if role not in VALID_ROLES:
        role = "user"

    if username_exists(username):
        return False, f"Username '{username}' is already taken."

    salt, digest = _hash_password(password)
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO accounts
                (username, password_hash, salt, full_name, role,
                 usage_reason, device_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                digest,
                salt,
                (full_name or username).strip()[:40],
                role,
                usage_reason.strip()[:80],
                max(1, int(device_count or 1)),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' is already taken."
    finally:
        conn.close()

    return True, get_account(username)


def get_account(username: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM accounts WHERE LOWER(username) = LOWER(?)",
            (username,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def verify_credentials(username: str, password: str):
    """Returns (account_dict | None, error | None). Updates last_login."""
    account = get_account(username)
    if not account:
        return None, "No account found with this username."

    _, digest = _hash_password(password, account["salt"])
    if digest != account["password_hash"]:
        return None, "Incorrect password. Please try again."

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE accounts SET last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), account["id"]),
        )
        conn.commit()
    finally:
        conn.close()

    return get_account(username), None


def list_accounts():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, username, full_name, role, usage_reason,
                   device_count, created_at, last_login
            FROM accounts
            ORDER BY created_at DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def public_account(account: dict):
    """Strip sensitive fields for API responses."""
    return {
        "id": account["id"],
        "username": account["username"],
        "fullName": account["full_name"],
        "role": account["role"],
        "usageReason": account["usage_reason"],
        "deviceCount": account["device_count"],
        "createdAt": account["created_at"],
        "lastLogin": account.get("last_login"),
    }


# ---------------- Live sessions ----------------

def create_live_session(
    session_id: str,
    username: str,
    ip_address: str = "",
    user_agent: str = "",
):
    """Insert a new live session row. Returns the inserted record dict or None.

    session_id must be unique. If a collision occurs, None is returned so
    the caller can regenerate. The same username may have many live
    sessions simultaneously.
    """
    if not session_id or not username:
        return None
    now = _utcnow_iso()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO live_sessions
                (session_id, username, created_at, last_seen, status,
                 ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                username,
                now,
                now,
                LIVE_SESSION_STATUS_ACTIVE,
                (ip_address or "")[:64],
                (user_agent or "")[:256],
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()
    return get_live_session(session_id)


def get_live_session(session_id: str):
    """Return a session dict by its unique session_id, or None."""
    if not session_id:
        return None
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM live_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def touch_live_session(session_id: str):
    """Update last_seen for an existing session to now.

    Only touches sessions that are still marked active. Returns True if
    a row was updated, False otherwise.
    """
    if not session_id:
        return False
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            UPDATE live_sessions
            SET last_seen = ?
            WHERE session_id = ? AND status = ?
            """,
            (_utcnow_iso(), session_id, LIVE_SESSION_STATUS_ACTIVE),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def revoke_live_session(session_id: str):
    """Mark a session revoked (or remove it if not found). Returns True on
    success. Revoked sessions are excluded from list_active_sessions.
    """
    if not session_id:
        return False
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            UPDATE live_sessions
            SET status = ?
            WHERE session_id = ?
            """,
            (LIVE_SESSION_STATUS_REVOKED, session_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_active_sessions(timeout_seconds: int = None):
    """Return all sessions whose last_seen is within the timeout window
    and whose status is still active. Fully dynamic — no fixed user limit.
    """
    if timeout_seconds is None:
        timeout_seconds = LIVE_SESSION_TIMEOUT_SECONDS
    # We store ISO-8601 strings (UTC, 'T' separator) and compare against
    # a Python-computed cutoff in the same format. Lexicographic string
    # comparison is reliable for this fixed-width format.
    from datetime import datetime as _dt, timedelta as _td

    cutoff = (_dt.utcnow() - _td(seconds=int(timeout_seconds))).isoformat()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM live_sessions
            WHERE status = ?
              AND last_seen >= ?
            ORDER BY last_seen DESC
            """,
            (LIVE_SESSION_STATUS_ACTIVE, cutoff),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def public_live_session(session: dict):
    """Return a sanitised view of a live session for API responses."""
    return {
        "sessionId": session["session_id"],
        "username": session["username"],
        "createdAt": session["created_at"],
        "lastSeen": session["last_seen"],
        "status": session.get("status"),
    }


# Initialize on import
init_db()