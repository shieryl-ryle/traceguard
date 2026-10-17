"""UI view of one case (System Design §3 shapes). The graph layer (TASK-003) will produce this."""

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

SAMPLE_PATH = Path(__file__).with_name("sample_case.json")
DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "dataset.json"


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


def _case_component(data: dict[str, Any], seed_ids: list[str]) -> set[str]:
    """Accounts and devices connected to the seeds through transfers or device links.

    `data/generate.py` guarantees each case is its own weakly connected component, so this is
    exactly the case's records. Display-only; graph analytics belong to `traceguard/graph/`.
    """
    adjacency: dict[str, set[str]] = {}
    edges = [(t["sender_account_id"], t["receiver_account_id"]) for t in data["transactions"]]
    edges += [(d["account_id"], d["device_id"]) for d in data["device_links"]]
    for a, b in edges:
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    seen: set[str] = set()
    stack = list(seed_ids)
    while stack:
        node = stack.pop()
        if node not in seen:
            seen.add(node)
            stack.extend(adjacency.get(node, ()))
    return seen


def load_dataset_cases(path: Path = DATASET_PATH) -> tuple[CaseView, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    views = []
    for case in data["cases"]:
        nodes = _case_component(data, case["seed_ids"])
        views.append(
            case_view_from_dict(
                {
                    "case": case,
                    "accounts": [a for a in data["accounts"] if a["account_id"] in nodes],
                    "device_links": [d for d in data["device_links"] if d["account_id"] in nodes],
                    "transactions": [t for t in data["transactions"] if t["sender_account_id"] in nodes],
                }
            )
        )
    return tuple(views)


def load_cases() -> tuple[CaseView, ...]:
    """Cases for the queue: the bundled dataset (C-1..C-3), plus the hand-made sample S-1 that
    keeps the AI flow demonstrable until the TASK-003 graph tools are wired in."""
    return (*load_dataset_cases(), load_sample_case())
