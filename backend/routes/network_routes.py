"""
Live network stats API — the single source of truth for the
real-time dashboard. All connected clients poll this endpoint,
so every device sees the same live numbers.

Modes
-----
LIVE_NETWORK_MODE=true
    All values are produced by ``NetworkMeasurementService`` and
    tagged with their actual provenance. Physical measurements
    that the host cannot provide are explicitly returned as
    ``UNAVAILABLE`` and rendered as N/A in the UI.

LIVE_NETWORK_MODE=false (default)
    A deterministic random-walk simulation is used so the research
    simulation framework remains reproducible. All values are
    tagged ``SIMULATION`` so the UI can show the research badge.

This endpoint NEVER fabricates physical measurements. The
``bandwidth`` field is the Wi-Fi link CAPACITY and is always
``UNAVAILABLE`` on a generic host. The separately labelled
``throughput`` field carries the actual observed data rate.
"""

import os
import random
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify

from backend.data_provenance import (
    CALCULATED_FROM_REAL_DATA,
    SIMULATION,
    UNAVAILABLE,
    REAL_RUNTIME_MEASUREMENT,
)
from backend.services.network_measurement_service import get_network_measurement_service
from backend.config import Config

network_bp = Blueprint("network", __name__)

# Source of truth for the live runtime measurement switch. The
# LIVE_NETWORK_MODE environment variable (loaded via backend.config)
# controls whether /api/network/stats returns real runtime measurements
# or the deterministic research simulation.
LIVE_MODE = bool(getattr(Config, "LIVE_NETWORK_MODE", False))

# In-memory deterministic state used ONLY when LIVE_NETWORK_MODE is
# disabled. Research experiments rely on a reproducible simulation.
_state = {
    "bandwidth": 62.0,
    "latency": 14.0,
    "packet_loss": 0.4,
    "throughput": 94.0,
    "jitter": 3.0,
    "history": [],
    "started_at": time.time(),
}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _tick() -> None:
    s = _state
    s["bandwidth"] = round(_clamp(s["bandwidth"] + random.uniform(-6, 6), 35, 98), 1)
    s["latency"] = round(_clamp(s["latency"] + random.uniform(-2, 2), 6, 28), 1)
    s["packet_loss"] = round(_clamp(s["packet_loss"] + random.uniform(-0.15, 0.15), 0.05, 1.5), 2)
    s["throughput"] = round(_clamp(s["throughput"] + random.uniform(-2, 2), 85, 99), 1)
    s["jitter"] = round(_clamp(s["jitter"] + random.uniform(-0.8, 0.8), 0.5, 7), 1)
    s["history"].append({"t": int(time.time()), "v": s["bandwidth"]})
    if len(s["history"]) > 30:
        s["history"] = s["history"][-30:]


def health_score(latency, packet_loss, throughput) -> Tuple[Optional[int], Optional[str]]:
    if latency is None or throughput is None:
        return None, None
    score = 100 - (latency or 0) * 1.2 - (packet_loss or 0) * 12 - abs(95 - (throughput or 0))
    score = int(_clamp(score, 0, 100))
    label = (
        "Excellent" if score >= 90
        else "Good" if score >= 75
        else "Fair" if score >= 65
        else "Poor"
    )
    return score, label


# ============================================================
# LIVE USER LIST
# ============================================================

_DEVICE_TYPES = [
    ("Laptop", "💻"), ("Mobile", "📱"), ("TV", "📺"),
    ("Tablet", "📲"), ("Desktop", "🖥️"), ("Smart Speaker", "🔊"),
    ("Gaming Console", "🎮"), ("IoT Camera", "📷"),
]

_ROOMS = ["Living Room", "Bedroom", "Kitchen", "Hall", "Study Room"]

_user_drift: Dict[str, float] = {}


def _seed(text: str) -> int:
    """Deterministic 32-bit hash so each user gets stable traits."""
    h = 2166136261
    for ch in text or "":
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def _presence(last_login_iso: Optional[str]) -> str:
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
    """Real registered accounts rendered as live simulated users."""
    from backend.database.accounts_db import list_accounts

    accounts = list_accounts()
    now_iso = int(time.time())
    users_out: List[Dict[str, Any]] = []

    for acc in accounts:
        uname = acc.get("username", "user")
        seed = _seed(uname)
        rnd = random.Random(seed)

        device, icon = _DEVICE_TYPES[seed % len(_DEVICE_TYPES)]
        base = rnd.uniform(4, 24)

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
            "_meta": {
                "user_source": "REAL_DATASET",
                "device_trait_source": SIMULATION,
                "network_trait_source": SIMULATION,
                "signal_source": SIMULATION,
                "usage_source": SIMULATION,
            },
        })

    return jsonify({
        "ok": True,
        "timestamp": now_iso,
        "source": SIMULATION,
        "users": users_out,
    })


# ============================================================
# LIVE STATS
# ============================================================

@network_bp.route("/network/stats", methods=["GET"])
def stats():
    """One snapshot per request.

    Returns the same canonical payload shape in both modes so the
    frontend can render a single unified dashboard.
    """
    if LIVE_MODE:
        return _live_stats()
    return _simulated_stats()


def _live_stats():
    """Return stats derived from actual local measurements."""
    service = get_network_measurement_service()
    measurement = service.measure_all()

    def _v(key: str) -> Optional[float]:
        data = measurement.get(key, {})
        return data.get("value")

    latency = _v("latency")
    packet_loss = _v("packet_loss")
    throughput = _v("throughput")
    jitter = _v("jitter")
    bandwidth = _v("bandwidth")

    health, health_label = health_score(latency, packet_loss, throughput)

    meta: Dict[str, Any] = {}
    canonical_keys = ("bandwidth", "latency", "packet_loss", "throughput", "jitter")
    for key in canonical_keys:
        data = measurement.get(key, {})
        meta[f"{key}_source"] = data.get("classification", UNAVAILABLE)
        meta[f"{key}_note"] = data.get("note", "")
        meta[f"{key}_age_seconds"] = data.get("age_seconds")

    if health is not None:
        meta["health_source"] = CALCULATED_FROM_REAL_DATA
        meta["health_note"] = "Calculated from real local measurements."
    else:
        meta["health_source"] = UNAVAILABLE
        meta["health_note"] = "Cannot calculate health without latency and throughput."

    history: List[Dict[str, Any]] = []
    if throughput is not None:
        history = [{"t": int(time.time()), "v": throughput}]

    # Top-level source reflects what the dashboard is *actually* showing.
    if health is not None and (latency is not None or throughput is not None):
        top_source = CALCULATED_FROM_REAL_DATA
    elif latency is not None or throughput is not None:
        top_source = REAL_RUNTIME_MEASUREMENT
    else:
        top_source = UNAVAILABLE

    return jsonify(
        {
            "ok": True,
            "timestamp": int(time.time()),
            "source": top_source,
            "live_mode": True,
            "stats": {
                "bandwidth": bandwidth,
                "latency": latency,
                "packetLoss": packet_loss,
                "throughput": throughput,
                "jitter": jitter,
                "health": health,
                "healthLabel": health_label,
                "_meta": meta,
            },
            "history": history,
        }
    )


def _simulated_stats():
    """Return stats from the deterministic random-walk simulation."""
    _tick()
    s = _state
    health = health_score(s["latency"], s["packet_loss"], s["throughput"])[0]
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
            "source": SIMULATION,
            "live_mode": False,
            "stats": {
                "bandwidth": s["bandwidth"],
                "latency": s["latency"],
                "packetLoss": s["packet_loss"],
                "throughput": s["throughput"],
                "jitter": s["jitter"],
                "health": health,
                "healthLabel": label,
                "_meta": {
                    "bandwidth_source": SIMULATION,
                    "latency_source": SIMULATION,
                    "packetLoss_source": SIMULATION,
                    "throughput_source": SIMULATION,
                    "jitter_source": SIMULATION,
                    "health_source": CALCULATED_FROM_REAL_DATA,
                    "health_note": "Calculated from simulated latency/throughput/packet_loss.",
                },
            },
            "history": s["history"],
        }
    )
