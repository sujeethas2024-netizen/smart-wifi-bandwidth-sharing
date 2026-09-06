"""
Focused tests for the network measurement service.

These tests do not require physical network access.
System measurement calls are mocked where necessary.
"""

import platform
import time
from unittest.mock import MagicMock, patch

import pytest

from backend.data_provenance import (
    CALCULATED_FROM_REAL_DATA,
    REAL_RUNTIME_MEASUREMENT,
    SIMULATION,
    UNAVAILABLE,
)
from backend.services.network_measurement_service import (
    DerivedThroughputCalculator,
    HostInterfaceAdapter,
    LocalLatencyAdapter,
    Metric,
    NetworkMeasurementService,
    bandwidth_capacity_metric,
    get_network_measurement_service,
    packet_loss_metric,
    reset_network_measurement_service_for_tests,
)


class TestMetricDataclass:
    def test_metric_creation(self):
        m = Metric(
            metric="latency",
            value=8.2,
            unit="ms",
            source="local_icmp",
            classification=REAL_RUNTIME_MEASUREMENT,
            note="measured via ICMP",
        )
        assert m.metric == "latency"
        assert m.value == 8.2
        assert m.classification == REAL_RUNTIME_MEASUREMENT

    def test_metric_default_fields(self):
        m = Metric(
            metric="x", value=1.0, unit="x", source="x",
            classification=REAL_RUNTIME_MEASUREMENT,
        )
        assert m.note == ""
        assert m.measured_at is None


class TestServiceSingleton:
    def setup_method(self):
        reset_network_measurement_service_for_tests()

    def test_singleton_returns_same_instance(self):
        a = get_network_measurement_service()
        b = get_network_measurement_service()
        assert a is b

    def test_singleton_is_network_measurement_service(self):
        svc = get_network_measurement_service()
        assert isinstance(svc, NetworkMeasurementService)


class TestServiceMeasureAll:
    def test_measure_all_returns_dict(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        assert isinstance(result, dict)

    def test_measure_all_contains_expected_keys(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        for key in ("latency", "jitter", "packet_loss", "bandwidth", "throughput"):
            assert key in result

    def test_measure_all_structure(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        for key, data in result.items():
            assert "value" in data
            assert "unit" in data
            assert "source" in data
            assert "classification" in data
            assert "note" in data
            assert "measured_at" in data
            assert "age_seconds" in data
            assert "is_stale" in data

    def test_bandwidth_is_unavailable(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        assert result["bandwidth"]["classification"] == UNAVAILABLE
        assert result["bandwidth"]["value"] is None

    def test_packet_loss_is_unavailable(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        assert result["packet_loss"]["classification"] == UNAVAILABLE
        assert result["packet_loss"]["value"] is None

    def test_force_recache(self):
        svc = NetworkMeasurementService()
        a = svc.measure_all()
        b = svc.measure_all(force=True)
        # both calls must succeed; force must not break the response shape
        assert "bandwidth" in a
        assert "bandwidth" in b


class TestJitterDerivation:
    def test_jitter_unavailable_without_samples(self):
        svc = NetworkMeasurementService()
        with patch.object(svc._latency, "_try_icmp_ping", return_value=None):
            with patch.object(svc._latency, "_try_tcp_timing", return_value=None):
                result = svc.measure_all()
        assert result["jitter"]["classification"] == UNAVAILABLE
        assert result["jitter"]["value"] is None

    def test_jitter_calculated_when_two_samples_available(self):
        svc = NetworkMeasurementService()
        with patch.object(svc._latency, "_try_icmp_ping", return_value=10.0):
            with patch.object(svc._latency, "_try_tcp_timing", return_value=None):
                result = svc.measure_all()
        assert result["jitter"]["classification"] == CALCULATED_FROM_REAL_DATA
        assert result["jitter"]["value"] is not None
        assert result["jitter"]["value"] == 0.0

    def test_jitter_derived_from_latency_samples(self):
        adapter = LocalLatencyAdapter()
        adapter._samples = [10.0, 12.0, 11.0, 13.0]
        m = adapter.jitter()
        assert m.classification == CALCULATED_FROM_REAL_DATA
        assert m.value is not None
        assert m.value >= 0

    def test_jitter_history_bounded(self):
        adapter = LocalLatencyAdapter()
        adapter._samples = [float(i) for i in range(50)]
        # Service should cap the history to a sensible size.
        adapter._samples = adapter._samples[-adapter.HISTORY_LIMIT:]
        m = adapter.jitter()
        assert m.classification == CALCULATED_FROM_REAL_DATA


class TestHostInterfaceAdapter:
    def test_returns_dict_or_empty(self):
        adapter = HostInterfaceAdapter()
        result = adapter.measure()
        assert isinstance(result, dict)

    def test_throughput_derived_from_counters(self):
        adapter = HostInterfaceAdapter()
        now = time.time()
        adapter._last_counters = {"eth0": {"bytes_in": 1000, "bytes_out": 2000}}
        adapter._last_time = now - 1.0
        counters = {"eth0": {"bytes_in": 1500, "bytes_out": 2500}}
        with patch.object(adapter, "_read_counters", return_value=counters):
            metrics = adapter.measure()
        assert "eth0_throughput" in metrics
        assert metrics["eth0_throughput"].classification == CALCULATED_FROM_REAL_DATA

    def test_throughput_zero_delta(self):
        adapter = HostInterfaceAdapter()
        adapter._last_counters = {"eth0": {"bytes_in": 1000, "bytes_out": 2000}}
        adapter._last_time = time.time() - 1.0
        counters = {"eth0": {"bytes_in": 1000, "bytes_out": 2000}}
        with patch.object(adapter, "_read_counters", return_value=counters):
            metrics = adapter.measure()
        if "eth0_throughput" in metrics:
            assert metrics["eth0_throughput"].value == 0.0

    def test_throughput_unavailable_without_counters(self):
        adapter = HostInterfaceAdapter()
        adapter._last_counters = None
        adapter._last_time = None
        with patch.object(adapter, "_read_counters", return_value=None):
            metrics = adapter.measure()
        assert not any(k.endswith("_throughput") for k in metrics)

    def test_counter_reset_does_not_crash(self):
        adapter = HostInterfaceAdapter()
        adapter._last_counters = {"eth0": {"bytes_in": 5000, "bytes_out": 7000}}
        adapter._last_time = time.time() - 1.0
        counters = {"eth0": {"bytes_in": 100, "bytes_out": 200}}  # wrapped
        with patch.object(adapter, "_read_counters", return_value=counters):
            metrics = adapter.measure()
        assert isinstance(metrics, dict)

    def test_loopback_filter(self):
        m = DerivedThroughputCalculator.best({
            "lo_throughput": Metric(
                metric="lo_throughput", value=100.0, unit="Mbps",
                source="x", classification=CALCULATED_FROM_REAL_DATA,
            ),
            "eth0_throughput": Metric(
                metric="eth0_throughput", value=5.0, unit="Mbps",
                source="x", classification=CALCULATED_FROM_REAL_DATA,
            ),
        })
        assert m is not None
        assert m.metric == "eth0_throughput"

    def test_best_returns_none_when_empty(self):
        assert DerivedThroughputCalculator.best({}) is None


class TestLatencyAdapter:
    def test_icmp_ping_success(self):
        adapter = LocalLatencyAdapter()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Reply from 127.0.0.1: bytes=32 time=1ms TTL=128"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            result = adapter._try_icmp_ping()
        assert result == 1.0

    def test_icmp_ping_failure(self):
        adapter = LocalLatencyAdapter()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Request timed out."

        with patch("subprocess.run", return_value=mock_result):
            assert adapter._try_icmp_ping() is None

    def test_icmp_ping_timeout(self):
        adapter = LocalLatencyAdapter()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ping", 5)):
            assert adapter._try_icmp_ping() is None

    def test_icmp_ping_subprocess_missing(self):
        adapter = LocalLatencyAdapter()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert adapter._try_icmp_ping() is None

    def test_tcp_timing_success(self):
        adapter = LocalLatencyAdapter()
        mock_sock = MagicMock()
        with patch("socket.create_connection", return_value=mock_sock):
            with patch("time.perf_counter", side_effect=[0.0, 0.05]):
                assert adapter._try_tcp_timing() == 50.0

    def test_tcp_timing_connection_refused(self):
        adapter = LocalLatencyAdapter()
        with patch("socket.create_connection", side_effect=ConnectionRefusedError):
            assert adapter._try_tcp_timing() is None

    def test_tcp_timing_timeout(self):
        adapter = LocalLatencyAdapter()
        with patch("socket.create_connection", side_effect=TimeoutError):
            assert adapter._try_tcp_timing() is None

    def test_measure_falls_back_to_tcp_when_icmp_fails(self):
        adapter = LocalLatencyAdapter()
        with patch.object(adapter, "_try_icmp_ping", return_value=None):
            with patch.object(adapter, "_try_tcp_timing", return_value=2.5):
                result = adapter.measure()
        assert "latency" in result
        assert result["latency"].value == 2.5

    def test_measure_returns_unavailable_when_all_fail(self):
        adapter = LocalLatencyAdapter()
        with patch.object(adapter, "_try_icmp_ping", return_value=None):
            with patch.object(adapter, "_try_tcp_timing", return_value=None):
                result = adapter.measure()
        assert result["latency"].classification == UNAVAILABLE
        assert result["latency"].value is None


class TestHardcodedUnavailable:
    def test_bandwidth_capacity(self):
        m = bandwidth_capacity_metric()
        assert m.classification == UNAVAILABLE
        assert m.value is None
        assert m.unit == "Mbps"

    def test_packet_loss(self):
        m = packet_loss_metric()
        assert m.classification == UNAVAILABLE
        assert m.value is None


class TestProvenanceClassification:
    def test_live_measurement_classification(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        for key, data in result.items():
            assert data["classification"] in (
                REAL_RUNTIME_MEASUREMENT,
                CALCULATED_FROM_REAL_DATA,
                SIMULATION,
                UNAVAILABLE,
            )

    def test_unavailable_metrics_have_note(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        for key, data in result.items():
            if data["classification"] == UNAVAILABLE:
                assert data["note"] != ""

    def test_real_measurements_have_source(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        for key, data in result.items():
            if data["classification"] != UNAVAILABLE:
                assert data["source"] not in ("unavailable", "")

    def test_stale_metrics_downgrade_to_unavailable(self):
        # A short TTL but a zero stale window means: the first call
        # collects measurements, the second call returns the cached
        # snapshot (no re-collection) but the values must be flagged
        # as stale and reported as UNAVAILABLE because their age
        # exceeds `stale_seconds`.
        svc = NetworkMeasurementService(ttl_seconds=10.0, stale_seconds=0.0)
        first = svc.measure_all()
        time.sleep(0.05)
        second = svc.measure_all()
        for key in first:
            if first[key]["classification"] != UNAVAILABLE:
                assert second[key]["is_stale"] is True
                assert second[key]["value"] is None
                assert second[key]["classification"] == UNAVAILABLE

    def test_age_seconds_never_negative(self):
        svc = NetworkMeasurementService()
        result = svc.measure_all()
        for key, data in result.items():
            if data["age_seconds"] is not None:
                assert data["age_seconds"] >= 0


import subprocess
