import os

from dotenv import load_dotenv


load_dotenv()


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on")


class Config:

    # ---- Live network measurement mode ----------------------------------
    # When True, /api/network/stats uses the runtime measurement service
    # (local ICMP/TCP latency, host interface counters, derived throughput).
    # When False, the legacy deterministic simulation is used so the
    # research experiments remain reproducible. Set via the
    # LIVE_NETWORK_MODE environment variable (e.g. in .env).
    LIVE_NETWORK_MODE: bool = _truthy(os.getenv("LIVE_NETWORK_MODE"))

    MYSQL_HOST = os.getenv(
        "MYSQL_HOST",
        "localhost"
    )

    MYSQL_USER = os.getenv(
        "MYSQL_USER",
        "root"
    )

    MYSQL_PASSWORD = os.getenv(
        "MYSQL_PASSWORD",
        ""
    )

    MYSQL_DATABASE = os.getenv(
        "MYSQL_DATABASE",
        "smart_wifi"
    )

    MYSQL_PORT = int(
        os.getenv(
            "MYSQL_PORT",
            "3306"
        )
    )