"""UI view of one case (System Design §3 shapes). The graph layer (TASK-003) will produce this."""

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

SAMPLE_PATH = Path(__file__).with_name("sample_case.json")


@dataclass(frozen=True)
class Case:
    case_id: str
    title: str
    description: str
    seed_ids: tuple[str, ...]
    scenario_label: str


@dataclass(frozen=True)
class Account:
    account_id: str
    label: str


@dataclass(frozen=True)
class DeviceLink:
    relationship_id: str
    account_id: str
    device_id: str
    observed_at: datetime


@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    sender_account_id: str
    receiver_account_id: str
    amount: Decimal
    currency: str
    timestamp: datetime


@dataclass(frozen=True)
class CaseView:
    case: Case
    accounts: tuple[Account, ...]
    device_links: tuple[DeviceLink, ...]
    transactions: tuple[Transaction, ...]

    @property
    def device_ids(self) -> tuple[str, ...]:
        return tuple(sorted({link.device_id for link in self.device_links}))

    def evidence_for(self, node_id: str) -> tuple[str, ...]:
        """Evidence IDs touching an account or device node, for the selection panel."""
        ids = [
            t.transaction_id
            for t in self.transactions
            if node_id in (t.sender_account_id, t.receiver_account_id)
        ]
        ids += [
            link.relationship_id
            for link in self.device_links
            if node_id in (link.account_id, link.device_id)
        ]
        return tuple(ids)


def _aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must be timezone-aware: {value}")
    return parsed


def case_view_from_dict(data: dict[str, Any]) -> CaseView:
    case = data["case"]
    return CaseView(
        case=Case(
            case_id=case["case_id"],
            title=case["title"],
            description=case["description"],
            seed_ids=tuple(case["seed_ids"]),
            scenario_label=case["scenario_label"],
        ),
        accounts=tuple(Account(a["account_id"], a["label"]) for a in data["accounts"]),
        device_links=tuple(
            DeviceLink(d["relationship_id"], d["account_id"], d["device_id"], _aware(d["observed_at"]))
            for d in data["device_links"]
        ),
        transactions=tuple(
            Transaction(
                t["transaction_id"],
                t["sender_account_id"],
                t["receiver_account_id"],
                Decimal(t["amount"]),
                t["currency"],
                _aware(t["timestamp"]),
            )
            for t in data["transactions"]
        ),
    )


def load_sample_case() -> CaseView:
    return case_view_from_dict(json.loads(SAMPLE_PATH.read_text(encoding="utf-8")))


def load_cases() -> tuple[CaseView, ...]:
    """Cases for the queue. Sample only until the TASK-002 dataset and TASK-003 loader land."""
    return (load_sample_case(),)
