"""TC-003 (F-003) and TC-007 (F-007): graph elements built from a case view."""

from traceguard.ui.graph_view import HIGHLIGHT_COLOR, SEED_COLOR, build_elements
from traceguard.ui.models import load_sample_case

VIEW = load_sample_case()


def test_one_edge_per_transaction_and_device_link() -> None:
    edges = build_elements(VIEW).edges
    ids = [e.id for e in edges]
    assert len(ids) == len(set(ids)) == len(VIEW.transactions) + len(VIEW.device_links)


def test_repeated_transfers_are_separate_and_curved_apart() -> None:
    edges = {e.id: e for e in build_elements(VIEW).edges}
    first, second = edges["TX-0002"], edges["TX-0003"]
    assert (first.source, first.to) == (second.source, second.to) == ("A-02", "A-07")
    assert first.smooth["roundness"] != second.smooth["roundness"]


def test_transfers_are_directed_and_device_links_are_not() -> None:
    edges = {e.id: e for e in build_elements(VIEW).edges}
    assert edges["TX-0001"].arrows == "to"
    assert edges["DL-0001"].arrows == "" and edges["DL-0001"].dashes is True


def test_account_and_device_nodes_are_distinct() -> None:
    nodes = {n.id: n for n in build_elements(VIEW).nodes}
    assert nodes["A-01"].shape == "dot"
    assert nodes["D-01"].shape == "square"
    assert nodes["A-07"].color == SEED_COLOR


def test_nodes_have_no_title_so_double_click_is_inert() -> None:
    assert all(n.title is None for n in build_elements(VIEW).nodes)


def test_highlight_marks_only_the_cited_elements() -> None:
    elements = build_elements(VIEW, frozenset({"TX-0003", "D-01"}))
    highlighted_edges = [e.id for e in elements.edges if e.color == HIGHLIGHT_COLOR]
    highlighted_nodes = [n.id for n in elements.nodes if n.color == HIGHLIGHT_COLOR]
    assert highlighted_edges == ["TX-0003"]
    assert highlighted_nodes == ["D-01"]


def test_node_evidence_lists_transfers_and_device_links() -> None:
    assert VIEW.evidence_for("A-01") == ("TX-0001", "DL-0001")
    assert VIEW.evidence_for("D-01") == ("DL-0001", "DL-0002")
