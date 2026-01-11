"""Confidence Score Configuration.

Per Confidence Score Spec T2 (REQ-CONF-005, REQ-CONF-011)


- Real implementation (no stubs)
- Environment variable loading
- Singleton pattern via get_confidence_config()

Features:
- Configurable aggregation modes
- Threshold enforcement settings
- Per-tenant override support
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

# Singleton instance
_config_instance: Optional["ConfidenceConfig"] = None


@dataclass(frozen=True)
class ConfidenceConfig:
    """
    Configuration for confidence score calculation and enforcement.

    Attributes:
        enabled: Whether confidence calculation is active
        aggregation: How to aggregate token logprobs (average, min, percentile_90)
        min_acceptance: Minimum confidence threshold (0.0-1.0)
        on_low: Action when confidence is below threshold
        treat_null_as_low: Whether to treat null confidence as low
        precision_decimals: Decimal places for rounding confidence
    """

    enabled: bool = False
    aggregation: Literal["average", "min", "percentile_90"] = "average"
    min_acceptance: float = 0.40
    on_low: Literal["allow", "flag", "reject"] = "flag"
    treat_null_as_low: bool = False
    precision_decimals: int = 3

    @classmethod
    def from_env(cls) -> "ConfidenceConfig":
        """
        Create config from environment variables.

        Env vars:
        - CONFIDENCE_ENABLED: true/false
        - CONFIDENCE_AGGREGATION: average/min/percentile_90
        - CONFIDENCE_MIN_ACCEPTANCE: 0.0-1.0 float
        - CONFIDENCE_ON_LOW: allow/flag/reject
        - CONFIDENCE_TREAT_NULL_AS_LOW: true/false
        - CONFIDENCE_PRECISION_DECIMALS: integer

        Returns:
            ConfidenceConfig instance
        """

        def parse_bool(val: str, default: bool) -> bool:
            """Execute parse bool.

            Args:
                val: The val.
                default: The default.
            """

            if not val:
                return default
            return val.lower() in ("true", "1", "yes", "on")

        def parse_float(val: str, default: float) -> float:
            """Execute parse float.

            Args:
                val: The val.
                default: The default.
            """

            if not val:
                return default
            try:
                return float(val)
            except ValueError:
                return default

        def parse_int(val: str, default: int) -> int:
            """Execute parse int.

            Args:
                val: The val.
                default: The default.
            """

            if not val:
                return default
            try:
                return int(val)
            except ValueError:
                return default

        def parse_aggregation(val: str) -> Literal["average", "min", "percentile_90"]:
            """Execute parse aggregation.

            Args:
                val: The val.
            """

            if val in ("average", "min", "percentile_90"):
                return val  # type: ignore
            return "average"

        def parse_on_low(val: str) -> Literal["allow", "flag", "reject"]:
            """Execute parse on low.

            Args:
                val: The val.
            """

            if val in ("allow", "flag", "reject"):
                return val  # type: ignore
            return "flag"

        return cls(
            enabled=parse_bool(os.getenv("CONFIDENCE_ENABLED", ""), False),
            aggregation=parse_aggregation(os.getenv("CONFIDENCE_AGGREGATION", "average")),
            min_acceptance=parse_float(os.getenv("CONFIDENCE_MIN_ACCEPTANCE", ""), 0.40),
            on_low=parse_on_low(os.getenv("CONFIDENCE_ON_LOW", "flag")),
            treat_null_as_low=parse_bool(os.getenv("CONFIDENCE_TREAT_NULL_AS_LOW", ""), False),
            precision_decimals=parse_int(os.getenv("CONFIDENCE_PRECISION_DECIMALS", ""), 3),
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceConfig":
        """
        Create config from dictionary (for YAML loading).

        Args:
            data: Configuration dictionary

        Returns:
            ConfidenceConfig instance
        """
        return cls(
            enabled=data.get("enabled", False),
            aggregation=data.get("aggregation", "average"),
            min_acceptance=data.get("min_acceptance", 0.40),
            on_low=data.get("on_low", "flag"),
            treat_null_as_low=data.get("treat_null_as_low", False),
            precision_decimals=data.get("precision_decimals", 3),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "enabled": self.enabled,
            "aggregation": self.aggregation,
            "min_acceptance": self.min_acceptance,
            "on_low": self.on_low,
            "treat_null_as_low": self.treat_null_as_low,
            "precision_decimals": self.precision_decimals,
        }


def get_confidence_config() -> ConfidenceConfig:
    """
    Get singleton confidence config instance.

    Loads from environment on first call, then caches.
    Use reset_confidence_config() to reload.

    Returns:
        ConfidenceConfig singleton
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfidenceConfig.from_env()
    return _config_instance


def reset_confidence_config() -> None:
    """Reset singleton config (for testing)."""
    global _config_instance
    _config_instance = None


def set_confidence_config(config: ConfidenceConfig) -> None:
    """Override singleton config (for testing)."""
    global _config_instance
    _config_instance = config
