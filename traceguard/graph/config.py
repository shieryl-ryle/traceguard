"""Rule parameters (PRD Q7, ADR-003). The test copy of these values must agree (TC-004)."""

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "dataset.json"
DEFAULT_MAX_DEPTH = 3
CURRENCY = "PHP"  # System Design §3: one currency


@dataclass(frozen=True)
class FanInConfig:
    rule_id: str = "RULE-FANIN-01"
    window_seconds: int = 1800
    min_senders: int = 3

    def as_output(self) -> dict[str, Any]:
        return {
            "window_minutes": self.window_seconds // 60,
            "window_seconds": self.window_seconds,
            "min_senders": self.min_senders,
        }


@dataclass(frozen=True)
class ForwardingConfig:
    rule_id: str = "RULE-FWD-01"
    window_seconds: int = 3600
    min_forward_ratio: Decimal = Decimal("0.50")

    def as_output(self) -> dict[str, Any]:
        return {
            "window_minutes": self.window_seconds // 60,
            "window_seconds": self.window_seconds,
            "min_forward_ratio": str(self.min_forward_ratio),
        }


FAN_IN = FanInConfig()
FORWARDING = ForwardingConfig()
