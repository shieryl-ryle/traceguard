"""Interactive relationship graph (F-003) with evidence highlighting (F-007).

streamlit-agraph 0.0.45 returns the clicked *node* ID to Python; edge clicks return nothing,
so transactions are highlighted by restyling edges from Python instead.
"""

from collections import defaultdict
from dataclasses import dataclass

from streamlit_agraph import Config, Edge, Node, agraph

from traceguard.ui.models import CaseView

ACCOUNT_COLOR = "#4C78A8"
SEED_COLOR = "#E45756"
DEVICE_COLOR = "#9D755D"
TRANSFER_COLOR = "#8C8C8C"
DEVICE_LINK_COLOR = "#BAB0AC"
HIGHLIGHT_COLOR = "#F2A900"


@dataclass(frozen=True)
class GraphElements:
    nodes: list[Node]
    edges: list[Edge]


def _node(node_id: str, label: str, color: str, shape: str, highlighted: bool) -> Node:
    node = Node(
        id=node_id,
        label=label,
        color=HIGHLIGHT_COLOR if highlighted else color,
        shape=shape,
        size=30 if highlighted else 22,
        borderWidth=4 if highlighted else 1,
        font={"size": 16, "strokeWidth": 3, "strokeColor": "#ffffff"},
    )
    # agraph's double-click handler calls window.open(<title>); no title keeps it inert.
    node.title = None
    return node


def build_elements(view: CaseView, highlight_ids: frozenset[str] = frozenset()) -> GraphElements:
    seeds = set(view.case.seed_ids)
    nodes = [
        _node(
            a.account_id,
            a.account_id,
            SEED_COLOR if a.account_id in seeds else ACCOUNT_COLOR,
            "dot",
            a.account_id in highlight_ids,
        )
        for a in view.accounts
    ]
    nodes += [_node(d, d, DEVICE_COLOR, "square", d in highlight_ids) for d in view.device_ids]

    # One edge per transaction (never collapse repeats). Parallel transfers between the same
    # pair get increasing curvature so each stays visible and selectable for highlighting.
    pair_count: dict[tuple[str, str], int] = defaultdict(int)
    edges: list[Edge] = []
    for t in sorted(view.transactions, key=lambda t: t.timestamp):
        pair = (t.sender_account_id, t.receiver_account_id)
        index = pair_count[pair]
        pair_count[pair] += 1
        highlighted = t.transaction_id in highlight_ids
        edges.append(
            Edge(
                source=t.sender_account_id,
                target=t.receiver_account_id,
                id=t.transaction_id,
                label=f"{t.transaction_id}\n{t.currency} {t.amount:,.2f}",
                color=HIGHLIGHT_COLOR if highlighted else TRANSFER_COLOR,
                width=5 if highlighted else 1.5,
                arrows="to",
                smooth={"enabled": True, "type": "curvedCW", "roundness": 0.2 + 0.3 * index},
                font={"size": 12, "align": "middle", "strokeWidth": 4, "strokeColor": "#ffffff"},
            )
        )
    for link in view.device_links:
        highlighted = link.relationship_id in highlight_ids
        edges.append(
            Edge(
                source=link.account_id,
                target=link.device_id,
                id=link.relationship_id,
                color=HIGHLIGHT_COLOR if highlighted else DEVICE_LINK_COLOR,
                width=4 if highlighted else 1,
                dashes=True,
                arrows="",
            )
        )
    return GraphElements(nodes=nodes, edges=edges)


def graph_height(node_count: int) -> int:
    """Bigger cases get a taller canvas so labels stay readable."""
    return max(480, min(640, 360 + 20 * node_count))


def render_graph(
    view: CaseView, highlight_ids: frozenset[str] = frozenset(), height: int | None = None, width: int = 680
) -> str | None:
    """Draws the graph and returns the ID of the node the analyst clicked, if any."""
    elements = build_elements(view, highlight_ids)
    height = height or graph_height(len(elements.nodes))
    config = Config(
        height=height,
        width=width,
        directed=True,
        physics=True,
        hierarchical=False,
        interaction={"hover": True, "navigationButtons": False},
    )
    compact = len(elements.nodes) > 9
    config.physics["barnesHut"] = {
        "springLength": 110 if compact else 220,
        "avoidOverlap": 0.6,
        "gravitationalConstant": -3000 if compact else -6000,
    }
    selected = agraph(nodes=elements.nodes, edges=elements.edges, config=config)
    return selected if isinstance(selected, str) else None
