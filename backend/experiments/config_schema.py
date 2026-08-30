"""
Experiment Configuration Schema

Defines the configuration for reproducible multi-seed experiments.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class ExperimentConfig:
    """Configuration for a reproducible multi-seed experiment."""

    seed: int = 42
    repetitions: int = 30
    user_counts: List[int] = field(default_factory=lambda: [5, 10, 20, 30, 50, 100, 200, 373])
    total_bandwidth: float = 100.0
    scenario: str = "medium"
    algorithms: List[str] = field(default_factory=lambda: [
        "equal", "proportional", "priority", "max_min_fairness", "alpha_fair", "game_theory"
    ])
    utility_weights: Dict[str, float] = field(default_factory=lambda: {
        "w_throughput": 1.0,
        "w_latency": 0.5,
        "w_jitter": 0.3,
        "w_congestion": 0.5,
        "w_qos": 0.4,
    })
    traffic_class_distribution: Dict[str, float] = field(default_factory=lambda: {
        "browsing": 0.2,
        "online_class": 0.2,
        "gaming": 0.2,
        "streaming": 0.2,
        "downloading": 0.2,
    })
    output_directory: str = "data"
    alpha: float = 1.0
    max_iterations: int = 100
    description: str = "Multi-seed reproducible experiment"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if self.repetitions < 1:
            raise ValueError("repetitions must be at least 1")
        if not self.user_counts:
            raise ValueError("user_counts must not be empty")
        if self.total_bandwidth <= 0:
            raise ValueError("total_bandwidth must be greater than 0")
        if not self.scenario:
            raise ValueError("scenario must not be empty")
        if not self.algorithms:
            raise ValueError("algorithms must not be empty")
        if self.output_directory:
            pass  # validated by path creation

    def to_dict(self) -> dict:
        """Convert configuration to a dictionary."""
        return {
            "seed": self.seed,
            "repetitions": self.repetitions,
            "user_counts": self.user_counts,
            "total_bandwidth": self.total_bandwidth,
            "scenario": self.scenario,
            "algorithms": self.algorithms,
            "utility_weights": self.utility_weights,
            "traffic_class_distribution": self.traffic_class_distribution,
            "output_directory": self.output_directory,
            "alpha": self.alpha,
            "max_iterations": self.max_iterations,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExperimentConfig":
        """Create an ExperimentConfig from a dictionary."""
        return cls(
            seed=data.get("seed", 42),
            repetitions=data.get("repetitions", 30),
            user_counts=data.get("user_counts", [5, 10, 20, 30, 50, 100, 200, 373]),
            total_bandwidth=data.get("total_bandwidth", 100.0),
            scenario=data.get("scenario", "medium"),
            algorithms=data.get("algorithms", [
                "equal", "proportional", "priority", "max_min_fairness", "alpha_fair", "game_theory"
            ]),
            utility_weights=data.get("utility_weights", {
                "w_throughput": 1.0,
                "w_latency": 0.5,
                "w_jitter": 0.3,
                "w_congestion": 0.5,
                "w_qos": 0.4,
            }),
            traffic_class_distribution=data.get("traffic_class_distribution", {
                "browsing": 0.2,
                "online_class": 0.2,
                "gaming": 0.2,
                "streaming": 0.2,
                "downloading": 0.2,
            }),
            output_directory=data.get("output_directory", "data"),
            alpha=data.get("alpha", 1.0),
            max_iterations=data.get("max_iterations", 100),
            description=data.get("description", "Multi-seed reproducible experiment"),
        )

    def get_seeds(self) -> List[int]:
        """Return list of seeds to run: [seed, seed+1, ..., seed+repetitions-1]."""
        return list(range(self.seed, self.seed + self.repetitions))
