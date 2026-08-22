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


# Initialize on import
init_db()