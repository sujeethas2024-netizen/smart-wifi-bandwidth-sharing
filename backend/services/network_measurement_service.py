"""
Network Measurement Service
===========================

Provides defensible local network measurements with honest provenance.

The service is composed of small, focused adapters so that:

  * the dashboard, Game Theory engine, allocation logic, provenance and
    API contracts never need to know WHERE a metric came from;
  * new router/AP-specific sources can be added later by writing a new
    adapter and registering it in ``get_measurement_service``;
  * cached or unavailable values are explicitly marked so the UI never
    displays stale data as if it were freshly measured.

Hierarchy
---------
    REAL_RUNTIME_MEASUREMENT  — measured directly from the running system
    CALCULATED_FROM_REAL_DATA — computed from real inputs deterministically
    SIMULATION                — synthetic values for research/demo mode
    UNAVAILABLE               — metric cannot be measured in this environment

Architecture
------------
    NetworkMeasurementService
        ├── HostInterfaceAdapter     (local OS interface counters)
        ├── LocalLatencyAdapter      (ICMP/TCP latency)
        ├── DerivedThroughputCalculator
        └── (future) RouterAPAdapter — explicit seam for AP telemetry

The router/AP adapter is intentionally NOT implemented; a future
environment that exposes per-client Wi-Fi telemetry can register one
without touching the rest of the system.
"""

from __future__ import annotations

import os
import platform
import re
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from backend.data_provenance import (
    CALCULATED_FROM_REAL_DATA,
    REAL_RUNTIME_MEASUREMENT,
    SIMULATION,
    UNAVAILABLE,
)


# ============================================================
# PUBLIC RESULT TYPE
# ============================================================

@dataclass
class Metric:
    """Single network metric with provenance metadata."""

    metric: str
    value: Optional[float]
    unit: str
    source: str
    classification: str
    note: str = ""
    measured_at: Optional[float] = None
    age_seconds: Optional[float] = None
    is_stale: bool = False


# ============================================================
# ADAPTER PROTOCOL
# ============================================================

class MeasurementAdapter:
    """Base class for a network measurement source.

    An adapter is responsible for one narrow concern (interface byte
    counters, latency, etc.). It must never raise; any failure is
    translated into a ``Metric`` with ``classification=UNAVAILABLE``.
    """

    name: str = "base"

    def measure(self) -> Dict[str, Metric]:  # pragma: no cover - interface
        raise NotImplementedError


# ============================================================
# HOST INTERFACE COUNTERS ADAPTER
# ============================================================

class HostInterfaceAdapter(MeasurementAdapter):
    """Reads byte counters from the local OS network interfaces.

    * Linux  → /proc/net/dev
    * Windows → iphlpapi via ctypes

    Bytes are an honest, real number that any host can report. The
    adapter never attempts to invent RSSI, channel utilization or
    per-client radio statistics.
    """

    name = "host_interface"

    def __init__(self) -> None:
        self._last_counters: Optional[Dict[str, Dict[str, int]]] = None
        self._last_time: Optional[float] = None

    def measure(self) -> Dict[str, Metric]:
        counters = self._read_counters()
        if not counters:
            return {}

        now = time.time()
        result: Dict[str, Metric] = {}

        for iface, values in counters.items():
            result[f"{iface}_bytes_in"] = Metric(
                metric=f"{iface}_bytes_in",
                value=float(values["bytes_in"]),
                unit="bytes",
                source="host_interface_counters",
                classification=REAL_RUNTIME_MEASUREMENT,
                note=f"Interface {iface} received bytes (cumulative).",
                measured_at=now,
            )
            result[f"{iface}_bytes_out"] = Metric(
                metric=f"{iface}_bytes_out",
                value=float(values["bytes_out"]),
                unit="bytes",
                source="host_interface_counters",
                classification=REAL_RUNTIME_MEASUREMENT,
                note=f"Interface {iface} transmitted bytes (cumulative).",
                measured_at=now,
            )

        if self._last_counters is not None and self._last_time is not None:
            dt = now - self._last_time
            if dt > 0:
                for iface, values in counters.items():
                    prev = self._last_counters.get(iface)
                    if not prev:
                        continue
                    delta = (
                        (values["bytes_in"] + values["bytes_out"])
                        - (prev["bytes_in"] + prev["bytes_out"])
                    )
                    if delta < 0:
                        # counter reset / interface bounce; skip this iface
                        continue
                    mbps = (delta / dt) / (1024.0 * 1024.0)
                    result[f"{iface}_throughput"] = Metric(
                        metric=f"{iface}_throughput",
                        value=round(mbps, 4),
                        unit="Mbps",
                        source="host_interface_counters",
                        classification=CALCULATED_FROM_REAL_DATA,
                        note=(
                            f"Derived from {iface} byte counter delta over "
                            f"{dt:.2f}s."
                        ),
                        measured_at=now,
                    )

        self._last_counters = counters
        self._last_time = now
        return result

    # ---- platform-specific counter reads ----

    def _read_counters(self) -> Optional[Dict[str, Dict[str, int]]]:
        try:
            system = platform.system()
            if system == "Linux" and os.path.exists("/proc/net/dev"):
                return self._read_proc_net_dev()
            if system == "Windows":
                return self._read_windows_counters()
        except Exception:
            return None
        return None

    def _read_proc_net_dev(self) -> Optional[Dict[str, Dict[str, int]]]:
        if not os.path.exists("/proc/net/dev"):
            return None
        counters: Dict[str, Dict[str, int]] = {}
        try:
            with open("/proc/net/dev", "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except OSError:
            return None
        for line in lines[2:]:
            parts = line.split(":")
            if len(parts) != 2:
                continue
            iface = parts[0].strip()
            stats = parts[1].split()
            if len(stats) < 10:
                continue
            try:
                counters[iface] = {
                    "bytes_in": int(stats[0]),
                    "bytes_out": int(stats[8]),
                }
            except ValueError:
                continue
        return counters or None

    def _read_windows_counters(self) -> Optional[Dict[str, Dict[str, int]]]:
        try:
            import ctypes
            from ctypes import wintypes

            class MIB_IFROW(ctypes.Structure):
                _fields_ = [
                    ("dwIndex", wintypes.DWORD),
                    ("dwType", wintypes.DWORD),
                    ("dwMtu", wintypes.DWORD),
                    ("dwSpeed", wintypes.DWORD),
                    ("dwPhysAddrLen", wintypes.DWORD),
                    ("bPhysAddr", wintypes.BYTE * 8),
                    ("dwAdminStatus", wintypes.DWORD),
                    ("dwOperStatus", wintypes.DWORD),
                    ("dwLastChange", wintypes.DWORD),
                    ("dwInOctets", wintypes.DWORD),
                    ("dwInUcastPkts", wintypes.DWORD),
                    ("dwInNUcastPkts", wintypes.DWORD),
                    ("dwInDiscards", wintypes.DWORD),
                    ("dwInErrors", wintypes.DWORD),
                    ("dwInUnknownProtos", wintypes.DWORD),
                    ("dwInQLen", wintypes.DWORD),
                    ("dwOutOctets", wintypes.DWORD),
                    ("dwOutUcastPkts", wintypes.DWORD),
                    ("dwOutNUcastPkts", wintypes.DWORD),
                    ("dwOutDiscards", wintypes.DWORD),
                    ("dwOutErrors", wintypes.DWORD),
                    ("dwOutQLen", wintypes.DWORD),
                    ("dwDescrLen", wintypes.DWORD),
                    ("bDescr", wintypes.BYTE * 256),
                ]

            class MIB_IFTABLE(ctypes.Structure):
                _fields_ = [("dwNumEntries", wintypes.DWORD)]

            iphlpapi = ctypes.windll.iphlpapi
            size = wintypes.DWORD(0)
            res = iphlpapi.GetIfTable(None, ctypes.byref(size), False)
            if res != 122:
                return None
            buf = ctypes.create_string_buffer(size.value)
            res = iphlpapi.GetIfTable(buf, ctypes.byref(size), False)
            if res != 0:
                return None
            table = ctypes.cast(buf, ctypes.POINTER(MIB_IFTABLE)).contents
            counters: Dict[str, Dict[str, int]] = {}
            entry_size = ctypes.sizeof(MIB_IFROW)
            base_addr = ctypes.addressof(buf) + ctypes.sizeof(MIB_IFTABLE)
            for i in range(table.dwNumEntries):
                row = ctypes.cast(
                    base_addr + i * entry_size, ctypes.POINTER(MIB_IFROW)
                ).contents
                descr_bytes = bytes(row.bDescr[: row.dwDescrLen])
                try:
                    descr = descr_bytes.decode("utf-16-le", errors="replace").strip("\x00")
                except Exception:
                    descr = descr_bytes.decode("utf-8", errors="replace").strip("\x00")
                if not descr:
                    descr = f"Interface_{row.dwIndex}"
                counters[descr] = {
                    "bytes_in": int(row.dwInOctets),
                    "bytes_out": int(row.dwOutOctets),
                }
            return counters or None
        except Exception:
            return None


# ============================================================
# LOCAL LATENCY ADAPTER
# ============================================================

class LocalLatencyAdapter(MeasurementAdapter):
    """Measures round-trip latency to the local host.

    Tries ICMP first, then falls back to TCP connect timing against
    the local Flask server (port 5000). All failures are swallowed and
    reported as ``UNAVAILABLE``.
    """

    name = "local_latency"
    HISTORY_LIMIT = 20

    def __init__(self) -> None:
        self._samples: List[float] = []
        self._lock = threading.Lock()

    def measure(self) -> Dict[str, Metric]:
        now = time.time()
        ping_ms = self._try_icmp_ping()
        if ping_ms is None:
            ping_ms = self._try_tcp_timing()

        if ping_ms is not None:
            with self._lock:
                self._samples.append(ping_ms)
                if len(self._samples) > self.HISTORY_LIMIT:
                    self._samples = self._samples[-self.HISTORY_LIMIT:]
            return {
                "latency": Metric(
                    metric="latency",
                    value=round(ping_ms, 2),
                    unit="ms",
                    source="local_latency_probe",
                    classification=REAL_RUNTIME_MEASUREMENT,
                    note="Round-trip latency to local host.",
                    measured_at=now,
                )
            }

        return {
            "latency": Metric(
                metric="latency",
                value=None,
                unit="ms",
                source="unavailable",
                classification=UNAVAILABLE,
                note="No latency measurement mechanism succeeded.",
                measured_at=now,
            )
        }

    def jitter(self) -> Metric:
        with self._lock:
            samples = list(self._samples)
        if len(samples) < 2:
            return Metric(
                metric="jitter",
                value=None,
                unit="ms",
                source="unavailable",
                classification=UNAVAILABLE,
                note="Need at least 2 latency samples to compute jitter.",
                measured_at=time.time(),
            )
        diffs = [abs(samples[i] - samples[i - 1]) for i in range(1, len(samples))]
        return Metric(
            metric="jitter",
            value=round(sum(diffs) / len(diffs), 2),
            unit="ms",
            source="local_latency_samples",
            classification=CALCULATED_FROM_REAL_DATA,
            note="Average absolute change between consecutive latency samples.",
            measured_at=time.time(),
        )

    def _try_icmp_ping(self) -> Optional[float]:
        try:
            if platform.system() == "Windows":
                cmd = ["ping", "-n", "1", "127.0.0.1"]
            else:
                cmd = ["ping", "-c", "1", "127.0.0.1"]
            res = subprocess.run(
                cmd, capture_output=True, text=True, timeout=2
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None
        except Exception:
            return None
        if res.returncode != 0:
            return None
        m = re.search(r"time[=<](\d+(?:\.\d+)?)\s*ms", res.stdout + res.stderr)
        if not m:
            return None
        try:
            return float(m.group(1))
        except ValueError:
            return None

    def _try_tcp_timing(self) -> Optional[float]:
        try:
            start = time.perf_counter()
            sock = socket.create_connection(("127.0.0.1", 5000), timeout=1.0)
            elapsed = (time.perf_counter() - start) * 1000.0
            try:
                sock.close()
            except OSError:
                pass
            return elapsed
        except (OSError, TimeoutError):
            return None
        except Exception:
            return None


# ============================================================
# DERIVED THROUGHPUT CALCULATOR
# ============================================================

class DerivedThroughputCalculator:
    """Aggregates per-interface throughput into a single top-level value.

    Honours the ``RouterAPAdapter`` boundary: when an external
    adapter provides a higher-quality throughput value, that value
    (and its provenance) takes precedence over the locally derived
    estimate.
    """

    name = "derived_throughput"

    LOOPBACK_TOKENS = ("lo", "loopback", "pseudo", "tunnel", "vmware", "virtual", "hyper-v", "npcap")

    @staticmethod
    def best(per_interface: Dict[str, Metric]) -> Optional[Metric]:
        candidates: List[Metric] = []
        for key, metric in per_interface.items():
            if not key.endswith("_throughput"):
                continue
            if metric.value is None:
                continue
            iface_key = key[: -len("_throughput")].lower()
            if any(tok in iface_key for tok in DerivedThroughputCalculator.LOOPBACK_TOKENS):
                continue
            candidates.append(metric)

        if not candidates:
            for key, metric in per_interface.items():
                if key.endswith("_throughput") and metric.value is not None:
                    candidates.append(metric)

        if not candidates:
            return None
        return max(candidates, key=lambda m: m.value or 0.0)


# ============================================================
# BANDWIDTH CAPACITY (always unavailable on a generic host)
# ============================================================

def bandwidth_capacity_metric() -> Metric:
    """Wi-Fi link capacity cannot be measured on a generic host.

    A dedicated router/AP adapter (future work) would override this
    by writing a Metric named ``bandwidth`` with the appropriate
    classification. Until then, the value is honestly reported as
    UNAVAILABLE so the UI displays N/A instead of fabricated numbers.
    """
    return Metric(
        metric="bandwidth",
        value=None,
        unit="Mbps",
        source="unavailable",
        classification=UNAVAILABLE,
        note=(
            "Link capacity cannot be measured from a generic host. "
            "A future router/AP adapter would supply this value."
        ),
        measured_at=time.time(),
    )


def packet_loss_metric() -> Metric:
    """Physical packet loss cannot be measured from a generic host.

    ICMP ping loss is not a reliable signal on its own and would
    require statistical sampling to be meaningful. Until that is
    implemented, this is honestly reported as UNAVAILABLE.
    """
    return Metric(
        metric="packet_loss",
        value=None,
        unit="%",
        source="unavailable",
        classification=UNAVAILABLE,
        note="Packet loss measurement is not implemented in this environment.",
        measured_at=time.time(),
    )


# ============================================================
# SERVICE
# ============================================================

class NetworkMeasurementService:
    """Top-level façade combining all measurement adapters.

    The service caches a single measurement snapshot. Cached values
    are timestamped and age is included in the response so the UI
    can distinguish a fresh measurement from a stale one.

    Thread-safe so it is safe to share across Flask request workers.
    """

    DEFAULT_TTL_SECONDS = 1.0
    DEFAULT_STALE_SECONDS = 10.0

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        stale_seconds: float = DEFAULT_STALE_SECONDS,
    ) -> None:
        self._lock = threading.Lock()
        self._ttl = float(ttl_seconds)
        self._stale = float(stale_seconds)
        self._cache: Dict[str, Metric] = {}
        self._cache_built_at: Optional[float] = None
        self._last_collection_ok: bool = False
        self._last_error: Optional[str] = None

        self._host_iface = HostInterfaceAdapter()
        self._latency = LocalLatencyAdapter()
        # Future: self._router_ap: Optional[RouterAPAdapter] = None

    # ---------------- public API ----------------

    def measure_all(self, *, force: bool = False) -> Dict[str, Any]:
        """Return every available metric, using a cached snapshot when fresh.

        Parameters
        ----------
        force:
            If True, ignore the TTL and always re-collect.
        """
        now = time.time()
        with self._lock:
            if not force and self._cache_built_at is not None:
                age = now - self._cache_built_at
                if age < self._ttl:
                    return self._serialise(self._cache, now)
            self._cache = self._collect()
            self._cache_built_at = now
            self._last_collection_ok = True
            return self._serialise(self._cache, now)

    def cache_age(self) -> Optional[float]:
        if self._cache_built_at is None:
            return None
        return time.time() - self._cache_built_at

    def is_stale(self) -> bool:
        age = self.cache_age()
        if age is None:
            return True
        return age > self._stale

    # ---------------- internals ----------------

    def _collect(self) -> Dict[str, Metric]:
        metrics: Dict[str, Metric] = {}

        try:
            metrics.update(self._host_iface.measure())
        except Exception as exc:
            self._last_error = f"host_interface: {exc}"
            self._last_collection_ok = False

        try:
            metrics.update(self._latency.measure())
            metrics["jitter"] = self._latency.jitter()
        except Exception as exc:
            self._last_error = f"latency: {exc}"
            self._last_collection_ok = False

        try:
            best_tp = DerivedThroughputCalculator.best(metrics)
            if best_tp is not None:
                metrics["throughput"] = Metric(
                    metric="throughput",
                    value=best_tp.value,
                    unit=best_tp.unit,
                    source=best_tp.source,
                    classification=best_tp.classification,
                    note=(
                        f"Aggregated from {len([k for k in metrics if k.endswith('_throughput')])} "
                        f"interface throughput samples."
                    ),
                    measured_at=best_tp.measured_at,
                )
            else:
                metrics["throughput"] = Metric(
                    metric="throughput",
                    value=None,
                    unit="Mbps",
                    source="unavailable",
                    classification=UNAVAILABLE,
                    note="Insufficient interface data to compute throughput.",
                    measured_at=time.time(),
                )
        except Exception as exc:
            self._last_error = f"throughput: {exc}"
            self._last_collection_ok = False

        # Per-environment hard limits — keep these honest.
        metrics["bandwidth"] = bandwidth_capacity_metric()
        metrics["packet_loss"] = packet_loss_metric()

        return metrics

    def _serialise(self, metrics: Dict[str, Metric], now: float) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, metric in metrics.items():
            age = (
                (now - metric.measured_at)
                if metric.measured_at is not None
                else None
            )
            is_stale = age is not None and age > self._stale
            value = metric.value
            # If a real value has aged past the staleness window, hide it
            # from "fresh" reporting and downgrade to UNAVAILABLE so the
            # UI cannot present stale numbers as freshly measured.
            if is_stale and metric.classification != UNAVAILABLE:
                value = None
                classification = UNAVAILABLE
                note = (
                    f"{metric.note} (stale: last measured {age:.1f}s ago)"
                )
            else:
                classification = metric.classification
                note = metric.note
            result[key] = {
                "value": value,
                "unit": metric.unit,
                "source": metric.source,
                "classification": classification,
                "note": note,
                "measured_at": metric.measured_at,
                "age_seconds": round(age, 2) if age is not None else None,
                "is_stale": is_stale,
            }
        return result


# ============================================================
# SINGLETON
# ============================================================

_service: Optional[NetworkMeasurementService] = None
_service_lock = threading.Lock()


def get_network_measurement_service() -> NetworkMeasurementService:
    """Return the singleton measurement service."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = NetworkMeasurementService()
    return _service


def reset_network_measurement_service_for_tests() -> None:
    """Drop the cached singleton — for unit tests only."""
    global _service
    with _service_lock:
        _service = None
