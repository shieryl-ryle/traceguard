"""TC-003 (graph part): MultiDiGraph structure, plus case membership from the fixtures."""

import json
from pathlib import Path

import pytest

from traceguard.graph.loader import case_account_ids, case_dict, load_dataset

FIXTURES = Path(__file__).with_name("fixtures")


def test_node_kinds_and_edge_counts() -> None:
    dataset = load_dataset()
    graph, raw = dataset.graph, dataset.raw
    kinds = [d["kind"] for _, d in graph.nodes(data=True)]
    assert kinds.count("account") == len(raw["accounts"])
    assert kinds.count("device") == len({d["device_id"] for d in raw["device_links"]})
    edge_kinds = [d["kind"] for _, _, d in graph.edges(data=True)]
    assert edge_kinds.count("transfer") == len(raw["transactions"])
    assert edge_kinds.count("device_link") == len(raw["device_links"])


def test_repeated_transfers_are_separate_edges() -> None:
    graph = load_dataset().graph
    expected = json.loads((FIXTURES / "expected_C-1.json").read_text(encoding="utf-8"))
    for pair in expected["graph"]["transfer_edges_between"]:
        keys = sorted(graph.get_edge_data(pair["sender"], pair["receiver"]))
        assert keys == pair["transaction_ids"]


def test_device_links_point_account_to_device() -> None:
    graph = load_dataset().graph
    for u, v, d in graph.edges(data=True):
        if d["kind"] == "device_link":
            assert graph.nodes[u]["kind"] == "account" and graph.nodes[v]["kind"] == "device"


@pytest.mark.parametrize("case_id", ["C-1", "C-2", "C-3"])
def test_case_membership(case_id: str) -> None:
    expected = json.loads((FIXTURES / f"expected_{case_id}.json").read_text(encoding="utf-8"))["case"]
    dataset = load_dataset()
    assert case_account_ids(dataset, case_id) == expected["account_ids"]
    view = case_dict(dataset, case_id)
    assert sorted(t["transaction_id"] for t in view["transactions"]) == expected["transaction_ids"]
    assert {d["account_id"] for d in view["device_links"]} <= set(expected["account_ids"])
