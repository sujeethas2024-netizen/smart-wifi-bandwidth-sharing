"""
Auth API — registration (with WiFi usage reason), login,
username availability and admin account listing.
Data is persisted in SQLite (database/accounts.db).
"""

from flask import Blueprint, jsonify, request

from backend.database.accounts_db import (
    create_account,
    verify_credentials,
    get_account,
    list_accounts,
    public_account,
    username_exists,
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

    return jsonify({"ok": True, "user": public_account(account)})


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