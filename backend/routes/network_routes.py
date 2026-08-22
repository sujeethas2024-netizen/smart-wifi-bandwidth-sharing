"""
Live network stats API — the single source of truth for the
real-time dashboard. All connected clients poll this endpoint,
so every device sees the same live numbers.
"""

import random
import time
from datetime import datetime

from flask import Blueprint, jsonify

from backend.database.accounts_db import list_accounts

network_bp = Blueprint("network", __name__)

# In-memory live state shared by ALL clients (server-side simulation).
# Replace with real router/ONVIF/SNMP polling in production.
_state = {
    "bandwidth": 62.0,
    "latency": 14.0,
    "packet_loss": 0.4,
    "throughput": 94.0,
    "jitter": 3.0,
    "history": [],          # last 30 bandwidth samples
    "started_at": time.time(),
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _tick():
    """Advance the simulated network one step."""
    s = _state
    s["bandwidth"] = round(_clamp(s["bandwidth"] + random.uniform(-6, 6), 35, 98), 1)
    s["latency"] = round(_clamp(s["latency"] + random.uniform(-2, 2), 6, 28), 1)
    s["packet_loss"] = round(_clamp(s["packet_loss"] + random.uniform(-0.15, 0.15), 0.05, 1.5), 2)
    s["throughput"] = round(_clamp(s["throughput"] + random.uniform(-2, 2), 85, 99), 1)
    s["jitter"] = round(_clamp(s["jitter"] + random.uniform(-0.8, 0.8), 0.5, 7), 1)

    s["history"].append({"t": int(time.time()), "v": s["bandwidth"]})
    if len(s["history"]) > 30:
        s["history"] = s["history"][-30:]


def health_score():
    s = _state
    score = 100 - s["latency"] * 1.2 - s["packet_loss"] * 12 - abs(95 - s["throughput"])
    return int(_clamp(score, 55, 99))


# ============================================================
# LIVE USER LIST — real registered accounts + live usage
# ============================================================

_DEVICE_TYPES = [
    ("Laptop", "💻"), ("Mobile", "📱"), ("TV", "📺"),
    ("Tablet", "📲"), ("Desktop", "🖥️"), ("Smart Speaker", "🔊"),
    ("Gaming Console", "🎮"), ("IoT Camera", "📷"),
]

_ROOMS = ["Living Room", "Bedroom", "Kitchen", "Hall", "Study Room"]

_user_drift = {}   # username -> current live usage (drifts each poll)


def _seed(text):
    """Deterministic 32-bit hash so each user gets stable traits."""
    h = 2166136261
    for ch in text or "":
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _presence(last_login_iso):
    """Map last_login recency -> online / idle / offline."""
    if not last_login_iso:
        return "offline"
    try:
        dt = datetime.fromisoformat(last_login_iso)
        minutes = (datetime.utcnow() - dt).total_seconds() / 60
    except (ValueError, TypeError):
        return "offline"
    if minutes <= 15:
        return "online"
    if minutes <= 120:
        return "idle"
    return "offline"


@network_bp.route("/network/users", methods=["GET"])
def live_users():
    """
    Real registered accounts rendered as live network users.
    Usage values drift slightly on every poll so every connected
    client sees the same evolving numbers (true shared live state).
    """
    accounts = list_accounts()
    now_iso = int(time.time())
    users_out = []

    for acc in accounts:
        uname = acc.get("username", "user")
        seed = _seed(uname)
        rnd = random.Random(seed)

        device, icon = _DEVICE_TYPES[seed % len(_DEVICE_TYPES)]
        base = rnd.uniform(4, 24)

        # Live drift around the user's baseline
        current = _user_drift.get(uname, base)
        current = _clamp(current + random.uniform(-1.2, 1.2), 0.4, base + 8)
        _user_drift[uname] = round(current, 1)

        allocated = round(base + rnd.uniform(3, 10), 1)
        usage = min(current, allocated)
        priority = "High" if usage >= 16 else "Medium" if usage >= 8 else "Low"

        users_out.append({
            "id": acc.get("id", seed % 100000),
            "name": (acc.get("fullName") or uname).strip(),
            "username": uname,
            "role": acc.get("role", "user"),
            "device": device,
            "deviceIcon": icon,
            "ip": f"192.168.0.{10 + (seed % 240)}",
            "mac": "A4:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(
                (seed >> 3) & 0xFF, (seed >> 7) & 0xFF, (seed >> 11) & 0xFF,
                (seed >> 15) & 0xFF, (seed >> 19) & 0xFF,
            ),
            "priority": priority,
            "usage": round(usage, 1),
            "allocated": allocated,
            "status": _presence(acc.get("lastLogin")),
            "signal": ["excellent", "good", "fair", "weak"][(seed >> 5) % 4],
            "room": _ROOMS[(seed >> 9) % len(_ROOMS)],
            "connectedSince": "{}h {}m".format((seed >> 13) % 12 + 1, (seed >> 17) % 60),
            "dataUsed": round(((seed >> 21) % 3800) / 100 + usage * 0.25, 1),
            "usageReason": acc.get("usageReason", ""),
        })

    return jsonify({"ok": True, "timestamp": now_iso, "users": users_out})


@network_bp.route("/network/stats", methods=["GET"])
def stats():
    """One tick per request — every client sees identical live values."""
    _tick()
    s = _state
    health = health_score()
    label = (
        "Excellent" if health >= 90
        else "Good" if health >= 75
        else "Fair" if health >= 65
        else "Poor"
    )
    return jsonify(
        {
            "ok": True,
            "timestamp": int(time.time()),
            "stats": {
                "bandwidth": s["bandwidth"],
                "latency": s["latency"],
                "packetLoss": s["packet_loss"],
                "throughput": s["throughput"],
                "jitter": s["jitter"],
                "health": health,
                "healthLabel": label,
            },
            "history": s["history"],
        }
    )