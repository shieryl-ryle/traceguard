"""Case timeline (F-002): transactions in time order; selected rows feed graph highlighting."""

from typing import Any

import streamlit as st

from traceguard.ui.models import CaseView, Transaction

TIMELINE_KEY = "timeline"


def ordered_transactions(view: CaseView) -> list[Transaction]:
    return sorted(view.transactions, key=lambda t: (t.timestamp, t.transaction_id))


def timeline_rows(view: CaseView, highlight_ids: frozenset[str] = frozenset()) -> list[dict[str, Any]]:
    return [
        {
            "Selected": "●" if t.transaction_id in highlight_ids else "",
            "Time": t.timestamp.isoformat(timespec="minutes"),
            "Transaction": t.transaction_id,
            "From": t.sender_account_id,
            "To": t.receiver_account_id,
            "Amount": f"{t.amount:,.2f}",
            "Currency": t.currency,
        }
        for t in ordered_transactions(view)
    ]


def selected_transaction_ids(view: CaseView, key: str = TIMELINE_KEY) -> frozenset[str]:
    """Reads the row selection from the previous run so the graph can highlight it this run."""
    state = st.session_state.get(key)
    rows: list[int] = list(state["selection"]["rows"]) if state else []
    ordered = ordered_transactions(view)
    return frozenset(ordered[i].transaction_id for i in rows if 0 <= i < len(ordered))


def render_timeline(view: CaseView, highlight_ids: frozenset[str] = frozenset(), key: str = TIMELINE_KEY) -> None:
    st.dataframe(
        timeline_rows(view, highlight_ids),
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        key=key,
        column_config={"Selected": st.column_config.TextColumn(width="small")},
    )
    st.caption("Select rows to highlight those transfers on the graph. Times shown as recorded (with UTC offset).")
