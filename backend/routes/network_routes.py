"""
Live network stats API — the single source of truth for the
real-time dashboard. All connected clients poll this endpoint,
so every device sees the same live numbers.
"""

import random
import time

from flask import Blueprint, jsonify

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