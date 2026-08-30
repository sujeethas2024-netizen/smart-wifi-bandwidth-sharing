"""
Real WiFi Validation Workflow

This module provides a standardized workflow for importing and evaluating
real WiFi network measurements. It allows researchers to validate the
simulation results against actual network data.

Data Sources:
- Real WiFi measurements (imported CSV/JSON)
- Same algorithms are applied to both synthetic and real data
- Provenance labels clearly distinguish real from synthetic data

Supported Metrics:
- Throughput (Mbps)
- Latency / RTT (ms)
- Jitter (ms)
- Packet loss (%)
- Bandwidth utilization (%)

Expected Input Format (CSV):
    user_id, activity, traffic_class, requested_bandwidth, throughput, latency, jitter, packet_loss, qos_min_throughput, qos_max_latency, qos_max_jitter, qos_max_packet_loss

Example:
    1, gaming, real-time, 20.0, 15.5, 12.3, 2.1, 0.05, 10.0, 20.0, 5.0, 0.1
"""

import csv
import json
import os
from datetime import datetime
from typing import Any

from backend.data_provenance import (
    REAL_DATASET,
    REAL_RUNTIME_MEASUREMENT,
    CALCULATED_FROM_REAL_DATA,
)

# Default schema for real WiFi measurement files
REAL_WIFI_SCHEMA = {
    "required_columns": [
        "user_id",
        "activity",
        "traffic_class",
        "requested_bandwidth",
        "throughput",
        "latency",
        "jitter",
        "packet_loss",
    ],
    "optional_columns": [
        "qos_min_throughput",
        "qos_max_latency",
        "qos_max_jitter",
        "qos_max_packet_loss",
        "device_type",
        "location",
        "timestamp",
    ],
    "data_types": {
        "user_id": str,
        "activity": str,
        "traffic_class": str,
        "requested_bandwidth": float,
        "throughput": float,
        "latency": float,
        "jitter": float,
        "packet_loss": float,
        "qos_min_throughput": float,
        "qos_max_latency": float,
        "qos_max_jitter": float,
        "qos_max_packet_loss": float,
    },
}


class RealWiFiValidator:
    """Validates and processes real WiFi measurement data."""

    def __init__(self, schema=None):
        self.schema = schema or REAL_WIFI_SCHEMA
        self.validation_errors = []

    def validate_file(self, filepath: str) -> bool:
        """Validate that a CSV/JSON file matches the expected schema."""
        if not os.path.exists(filepath):
            self.validation_errors.append(f"File not found: {filepath}")
            return False

        ext = os.path.splitext(filepath)[1].lower()
        if ext not in (".csv", ".json"):
            self.validation_errors.append(f"Unsupported file format: {ext}")
            return False

        try:
            if ext == ".csv":
                with open(filepath, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    columns = reader.fieldnames or []
            else:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        columns = list(data[0].keys())
                    elif isinstance(data, dict):
                        columns = list(data.keys())
                    else:
                        self.validation_errors.append("JSON file is empty or malformed")
                        return False

            missing = [
                col for col in self.schema["required_columns"] if col not in columns
            ]
            if missing:
                self.validation_errors.append(f"Missing required columns: {missing}")
                return False

            return True
        except Exception as e:
            self.validation_errors.append(f"Error reading file: {e}")
            return False

    def load_measurements(self, filepath: str) -> list[dict[str, Any]]:
        """Load real WiFi measurements from CSV or JSON."""
        if not self.validate_file(filepath):
            raise ValueError(f"Validation failed: {self.validation_errors}")

        ext = os.path.splitext(filepath)[1].lower()
        measurements = []

        if ext == ".csv":
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    measurement = self._convert_types(row)
                    measurement["_meta"] = {
                        "source": REAL_DATASET,
                        "measurement_type": REAL_RUNTIME_MEASUREMENT,
                        "file": os.path.basename(filepath),
                        "imported_at": datetime.utcnow().isoformat(),
                    }
                    measurements.append(measurement)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    measurement = self._convert_types(item)
                    measurement["_meta"] = {
                        "source": REAL_DATASET,
                        "measurement_type": REAL_RUNTIME_MEASUREMENT,
                        "file": os.path.basename(filepath),
                        "imported_at": datetime.utcnow().isoformat(),
                    }
                    measurements.append(measurement)

        return measurements

    def _convert_types(self, row: dict) -> dict:
        """Convert string values to appropriate Python types."""
        converted = {}
        for key, value in row.items():
            if key in self.schema["data_types"]:
                try:
                    converted[key] = self.schema["data_types"][key](value)
                except (ValueError, TypeError):
                    converted[key] = value
            else:
                converted[key] = value
        return converted

    def compute_qos_violations(self, measurement: dict) -> dict:
        """Compute QoS violations for a single measurement."""
        violations = {
            "throughput_violation": False,
            "latency_violation": False,
            "jitter_violation": False,
            "packet_loss_violation": False,
            "total_violations": 0,
        }

        if "qos_min_throughput" in measurement:
            if measurement.get("throughput", 0) < measurement["qos_min_throughput"]:
                violations["throughput_violation"] = True
                violations["total_violations"] += 1

        if "qos_max_latency" in measurement:
            if measurement.get("latency", 0) > measurement["qos_max_latency"]:
                violations["latency_violation"] = True
                violations["total_violations"] += 1

        if "qos_max_jitter" in measurement:
            if measurement.get("jitter", 0) > measurement["qos_max_jitter"]:
                violations["jitter_violation"] = True
                violations["total_violations"] += 1

        if "qos_max_packet_loss" in measurement:
            if measurement.get("packet_loss", 0) > measurement["qos_max_packet_loss"]:
                violations["packet_loss_violation"] = True
                violations["total_violations"] += 1

        return violations

    def generate_validation_report(self, measurements: list[dict]) -> dict:
        """Generate a summary report of real WiFi measurements."""
        if not measurements:
            return {"status": "error", "message": "No measurements provided"}

        total = len(measurements)
        violations_summary = {
            "throughput_violations": 0,
            "latency_violations": 0,
            "jitter_violations": 0,
            "packet_loss_violations": 0,
        }

        for m in measurements:
            v = self.compute_qos_violations(m)
            violations_summary["throughput_violations"] += int(v["throughput_violation"])
            violations_summary["latency_violations"] += int(v["latency_violation"])
            violations_summary["jitter_violations"] += int(v["jitter_violation"])
            violations_summary["packet_loss_violations"] += int(v["packet_loss_violation"])

        return {
            "status": "success",
            "source": REAL_DATASET,
            "total_measurements": total,
            "traffic_classes": list(set(m.get("traffic_class", "unknown") for m in measurements)),
            "activities": list(set(m.get("activity", "unknown") for m in measurements)),
            "qos_violations": violations_summary,
            "violation_rates": {
                k: f"{(v / total * 100):.1f}%" for k, v in violations_summary.items()
            },
        }


def validate_and_load_real_wifi(filepath: str) -> tuple[list[dict], dict]:
    """Convenience function: validate, load, and report on real WiFi data."""
    validator = RealWiFiValidator()
    measurements = validator.load_measurements(filepath)
    report = validator.generate_validation_report(measurements)
    return measurements, report
