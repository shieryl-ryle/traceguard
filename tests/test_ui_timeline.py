"""TC-002 (F-002): timeline lists a case's transactions in time order with all fields."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from traceguard.ui.models import load_sample_case
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
    rows = timeline_rows(VIEW, frozenset({"TX-0003"}))
    assert set(rows[0]) == {"Selected", "Time", "Transaction", "From", "To", "Amount", "Currency"}
    assert [r["Transaction"] for r in rows if r["Selected"]] == ["TX-0003"]
    assert rows[0]["Amount"] == "4,800.00" and rows[0]["Currency"] == "PHP"
