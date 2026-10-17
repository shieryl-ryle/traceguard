"""TC-001 (F-001, BR-001): the queue loads C-1..C-3 via the graph loader, each as its own case."""

from traceguard.ui.models import load_cases

CASES = load_cases()


def test_queue_has_exactly_the_three_dataset_cases() -> None:
    assert [c.case.case_id for c in CASES] == ["C-1", "C-2", "C-3"]


def test_every_case_contains_its_seeds_and_only_its_own_records() -> None:
    for view in CASES:
        account_ids = {a.account_id for a in view.accounts}
        assert set(view.case.seed_ids) <= account_ids
        assert view.transactions, view.case.case_id
        for t in view.transactions:
            assert {t.sender_account_id, t.receiver_account_id} <= account_ids
        for link in view.device_links:
            assert link.account_id in account_ids


def test_cases_do_not_share_records() -> None:
    seen: set[str] = set()
    for view in CASES:
        ids = {t.transaction_id for t in view.transactions} | {d.relationship_id for d in view.device_links}
        assert not ids & seen
        seen |= ids


def test_repeated_transfers_between_one_pair_are_kept() -> None:
    c1 = next(v for v in CASES if v.case.case_id == "C-1")
    pairs = [(t.sender_account_id, t.receiver_account_id) for t in c1.transactions]
    assert len(pairs) > len(set(pairs))


def test_shared_device_case_shows_one_device_on_several_accounts() -> None:
    c2 = next(v for v in CASES if v.case.case_id == "C-2")
    accounts_per_device: dict[str, set[str]] = {}
    for link in c2.device_links:
        accounts_per_device.setdefault(link.device_id, set()).add(link.account_id)
    assert max(len(a) for a in accounts_per_device.values()) >= 3


def test_timestamps_are_timezone_aware_and_currency_is_php() -> None:
    for view in CASES:
        assert all(t.timestamp.utcoffset() is not None for t in view.transactions)
        assert {t.currency for t in view.transactions} == {"PHP"}
