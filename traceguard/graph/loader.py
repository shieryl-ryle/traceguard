"""Load the bundled synthetic dataset into a NetworkX MultiDiGraph (System Design §2, §3).

Nodes are accounts (`kind="account"`) and devices (`kind="device"`). Every transaction is its
own `kind="transfer"` edge keyed by `transaction_id`, so repeated transfers between one pair stay
separate; device links are `kind="device_link"` edges (account -> device) keyed by
`relationship_id`.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import cache
from pathlib import Path
from typing import Any

import networkx as nx

from traceguard.graph.config import CURRENCY, DATASET_PATH


@dataclass(frozen=True)
class Transfer:
    transaction_id: str
    sender: str
    receiver: str
    amount: Decimal
    currency: str
    timestamp: datetime

    def sort_key(self) -> tuple[datetime, str]:
        return (self.timestamp, self.transaction_id)


@dataclass(frozen=True)
class Dataset:
    raw: dict[str, Any]
    graph: nx.MultiDiGraph

    @property
    def cases(self) -> list[dict[str, Any]]:
        return list(self.raw.get("cases", []))


def _aware(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must be timezone-aware: {value}")
    return parsed


def build_graph(data: dict[str, Any]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for account in data["accounts"]:
        graph.add_node(account["account_id"], kind="account", label=account["label"])
    for link in data["device_links"]:
        graph.add_node(link["device_id"], kind="device")
        graph.add_edge(
            link["account_id"],
            link["device_id"],
            key=link["relationship_id"],
            kind="device_link",
            relationship_id=link["relationship_id"],
            observed_at=_aware(link["observed_at"]),
        )
    for tx in data["transactions"]:
        transfer = Transfer(
            transaction_id=tx["transaction_id"],
            sender=tx["sender_account_id"],
            receiver=tx["receiver_account_id"],
            amount=Decimal(tx["amount"]),
            currency=tx["currency"],
            timestamp=_aware(tx["timestamp"]),
        )
        if transfer.currency != CURRENCY:
            raise ValueError(f"{transfer.transaction_id}: currency {transfer.currency} is not {CURRENCY}")
        graph.add_edge(transfer.sender, transfer.receiver, key=transfer.transaction_id,
                       kind="transfer", transfer=transfer)
    return graph


def dataset_from_dict(data: dict[str, Any]) -> Dataset:
    return Dataset(raw=data, graph=build_graph(data))


@cache
def load_dataset(path: Path = DATASET_PATH) -> Dataset:
    return dataset_from_dict(json.loads(path.read_text(encoding="utf-8")))


def is_account(graph: nx.MultiDiGraph, node_id: str) -> bool:
    return bool(graph.has_node(node_id) and graph.nodes[node_id].get("kind") == "account")


def transfers_out(graph: nx.MultiDiGraph, account_id: str) -> list[Transfer]:
    if not is_account(graph, account_id):
        return []
    found = [d["transfer"] for _, _, d in graph.out_edges(account_id, data=True) if d["kind"] == "transfer"]
    return sorted(found, key=Transfer.sort_key)


def transfers_in(graph: nx.MultiDiGraph, account_id: str) -> list[Transfer]:
    if not is_account(graph, account_id):
        return []
    found = [d["transfer"] for _, _, d in graph.in_edges(account_id, data=True) if d["kind"] == "transfer"]
    return sorted(found, key=Transfer.sort_key)


def device_links(graph: nx.MultiDiGraph, account_id: str) -> list[tuple[str, str]]:
    """(device_id, relationship_id) pairs for an account, sorted by relationship ID."""
    if not is_account(graph, account_id):
        return []
    links = [(v, d["relationship_id"]) for _, v, d in graph.out_edges(account_id, data=True)
             if d["kind"] == "device_link"]
    return sorted(links, key=lambda pair: pair[1])


def case_account_ids(dataset: Dataset, case_id: str) -> list[str]:
    """Accounts connected to the case seeds by transfers (in either direction)."""
    case = get_case(dataset, case_id)
    transfers = nx.Graph((u, v) for u, v, d in dataset.graph.edges(data=True) if d["kind"] == "transfer")
    seen: set[str] = set()
    for seed in case["seed_ids"]:
        seen.add(seed)
        if transfers.has_node(seed):
            seen |= nx.node_connected_component(transfers, seed)
    return sorted(seen)


def get_case(dataset: Dataset, case_id: str) -> dict[str, Any]:
    for case in dataset.cases:
        if case["case_id"] == case_id:
            return case
    raise KeyError(case_id)


def case_dict(dataset: Dataset, case_id: str) -> dict[str, Any]:
    """One case in the `sample_case.json` shape the UI reads (`case_view_from_dict`)."""
    accounts = set(case_account_ids(dataset, case_id))
    raw = dataset.raw
    return {
        "case": get_case(dataset, case_id),
        "accounts": [a for a in raw["accounts"] if a["account_id"] in accounts],
        "device_links": [d for d in raw["device_links"] if d["account_id"] in accounts],
        "transactions": [
            t for t in raw["transactions"]
            if t["sender_account_id"] in accounts and t["receiver_account_id"] in accounts
        ],
    }


def case_dicts(dataset: Dataset | None = None) -> list[dict[str, Any]]:
    ds = dataset or load_dataset()
    return [case_dict(ds, case["case_id"]) for case in ds.cases]
