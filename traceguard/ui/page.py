"""Investigation page: case queue, case header, graph + selection panel, timeline (F-001–F-003)."""

import streamlit as st

from traceguard.ui.graph_view import render_graph
from traceguard.ui.models import CaseView
from traceguard.ui.timeline import TIMELINE_KEY, render_timeline, selected_transaction_ids

SELECTED_NODE_KEY = "selected_node"
ACTIVE_CASE_KEY = "active_case"


def render_case_queue(cases: tuple[CaseView, ...]) -> CaseView:
    st.sidebar.header("Case queue")
    st.sidebar.badge("Synthetic data", icon=":material/science:", color="orange")
    labels = {c.case.case_id: f"{c.case.case_id} · {c.case.scenario_label}" for c in cases}
    case_id = st.sidebar.radio("Open a case", options=list(labels), format_func=labels.__getitem__)
    view = next(c for c in cases if c.case.case_id == case_id)
    if st.session_state.get(ACTIVE_CASE_KEY) != case_id:
        st.session_state[ACTIVE_CASE_KEY] = case_id
        st.session_state.pop(SELECTED_NODE_KEY, None)
        st.session_state.pop(TIMELINE_KEY, None)
    return view


def _node_kind(view: CaseView, node_id: str) -> str:
    return "Device" if node_id in view.device_ids else "Account"


def render_selection_panel(view: CaseView, node_id: str | None) -> None:
    st.subheader("Selection")
    if node_id is None:
        st.caption("Click an account or device in the graph to see its evidence.")
        return
    st.markdown(f"**{_node_kind(view, node_id)}** `{node_id}`")
    evidence = view.evidence_for(node_id)
    if evidence:
        st.markdown("Evidence IDs: " + ", ".join(f"`{e}`" for e in evidence))
    else:
        st.caption("No evidence records reference this node.")


def render_case_page(view: CaseView) -> None:
    case = view.case
    st.header(f"{case.case_id} — {case.title}")
    st.badge(case.scenario_label, color="blue")
    st.write(case.description)

    highlight = selected_transaction_ids(view)
    graph_col, panel_col = st.columns([3, 1])
    with graph_col:
        clicked = render_graph(view, highlight)
    if clicked is not None:
        st.session_state[SELECTED_NODE_KEY] = clicked
    with panel_col:
        render_selection_panel(view, st.session_state.get(SELECTED_NODE_KEY))

    st.subheader("Timeline")
    render_timeline(view, highlight)
