"""TC-002 (F-002): timeline lists a case's transactions in time order with all fields."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from tests.ui_sample import load_sample_case
from traceguard.ui.timeline import ordered_transactions, timeline_rows

VIEW = load_sample_case()


def test_rows_are_in_ascending_time_order() -> None:
    shuffled = replace(VIEW, transactions=tuple(reversed(VIEW.transactions)))
    times = [t.timestamp for t in ordered_transactions(shuffled)]
    assert times == sorted(times)


def test_ordering_uses_instants_not_local_clock_text() -> None:
    manila, utc = timezone(timedelta(hours=8)), timezone.utc
    early = replace(VIEW.transactions[0], transaction_id="TX-E", timestamp=datetime(2026, 9, 30, 9, 0, tzinfo=manila))
    late = replace(VIEW.transactions[0], transaction_id="TX-L", timestamp=datetime(2026, 9, 30, 2, 0, tzinfo=utc))
    view = replace(VIEW, transactions=(late, early))
    assert [t.transaction_id for t in ordered_transactions(view)] == ["TX-E", "TX-L"]


def test_rows_have_every_field_and_mark_selected() -> None:
    rows = timeline_rows(VIEW, selected_ids=frozenset({"TX-0003"}))
    assert set(rows[0]) == {"Selected", "Cited", "Time", "Transaction", "From", "To", "Amount", "Currency"}
    assert [r["Transaction"] for r in rows if r["Selected"]] == ["TX-0003"]
    assert rows[0]["Amount"] == "4,800.00" and rows[0]["Currency"] == "PHP"


def test_citations_are_marked_separately_from_selection() -> None:
    rows = timeline_rows(VIEW, selected_ids=frozenset({"TX-0001"}), cited_ids=frozenset({"TX-0005"}))
    assert [r["Transaction"] for r in rows if r["Selected"]] == ["TX-0001"]
    assert [r["Transaction"] for r in rows if r["Cited"]] == ["TX-0005"]
