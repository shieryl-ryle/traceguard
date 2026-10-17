"""Seeded generator for the bundled synthetic dataset (TASK-002, BR-001).

Everything here is synthetic. The three cases are hand-designed from public fraud-typology
patterns (convergence + forwarding, shared device, incomplete trail); background activity is
random but seeded, so every run writes a byte-identical `data/dataset.json`.

Case accounts and background accounts never transact with each other, so each case's
transactions are exactly the weakly connected component around its seed accounts.

Usage:
    python data/generate.py          # write data/dataset.json
    python data/generate.py --check  # exit 1 if the committed file is out of date
"""

import argparse
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

SEED = 20261017
CURRENCY = "PHP"
MANILA = timezone(timedelta(hours=8))
OUT_PATH = Path(__file__).with_name("dataset.json")

# (case_id, title, description, seed_ids, scenario_label). Descriptions read like the alert an
# analyst would open; they never state rule results (those come from the tools, BR-003).
CASES = [
    ("C-1", "Convergence and forwarding to one account",
     "Alert raised on A-07: several inbound transfers in a short period, followed by a large "
     "outbound transfer.", ["A-07"], "Convergence & forwarding"),
    ("C-2", "Three accounts on one shared device",
     "Alert raised on A-13, A-14 and A-15: three accounts are linked to the same device.",
     ["A-13", "A-14", "A-15"], "Benign shared device"),
    ("C-3", "Funds leave the visible trail",
     "Alert raised on A-19: inbound transfers followed by an outbound transfer.", ["A-19"],
     "Incomplete evidence"),
]

# Scenario transfers: (transaction_id, sender, receiver, amount, Manila local time).
SCENARIO_TRANSACTIONS = [
    # C-1: A-07 receives from A-01..A-04 (A-01 twice) then forwards to A-08, which splits onward.
    ("TX-0001", "A-05", "A-07", "1500.00", "2026-09-30 08:20:00"),  # earlier, outside windows
    ("TX-0002", "A-01", "A-07", "4800.00", "2026-09-30 09:01:00"),
    ("TX-0003", "A-02", "A-07", "2500.00", "2026-09-30 09:06:00"),
    ("TX-0004", "A-03", "A-07", "3700.00", "2026-09-30 09:12:00"),
    ("TX-0005", "A-01", "A-07", "4000.00", "2026-09-30 09:20:00"),  # repeat pair A-01 -> A-07
    ("TX-0006", "A-04", "A-07", "2000.00", "2026-09-30 09:31:00"),  # exactly 30 min after TX-0002
    ("TX-0007", "A-07", "A-08", "15500.00", "2026-09-30 10:01:00"),  # exactly 60 min after TX-0002
    ("TX-0008", "A-09", "A-06", "1200.00", "2026-09-30 09:00:00"),  # before A-09 is funded
    ("TX-0009", "A-08", "A-09", "7000.00", "2026-09-30 10:15:00"),
    ("TX-0010", "A-08", "A-10", "8000.00", "2026-09-30 10:40:00"),
    ("TX-0011", "A-10", "A-11", "5000.00", "2026-09-30 11:30:00"),
    ("TX-0012", "A-11", "A-12", "4500.00", "2026-09-30 12:05:00"),  # hop 4 from A-07
    # C-2: payday for a household; spending is small or more than an hour later.
    ("TX-0013", "A-16", "A-13", "25000.00", "2026-09-25 08:00:00"),
    ("TX-0014", "A-13", "A-14", "3000.00", "2026-09-25 08:30:00"),  # in window, below half
    ("TX-0015", "A-13", "A-18", "12000.00", "2026-09-25 09:00:01"),  # 60 min + 1 s after payday
    ("TX-0016", "A-13", "A-15", "2000.00", "2026-09-26 12:00:00"),
    ("TX-0017", "A-14", "A-17", "1200.00", "2026-09-27 18:00:00"),
    ("TX-0018", "A-15", "A-17", "800.00", "2026-09-28 10:00:00"),
    # C-3: A-19 forwards to A-22; A-22 has no later activity in the dataset.
    ("TX-0019", "A-23", "A-20", "9000.00", "2026-09-29 13:00:00"),
    ("TX-0020", "A-20", "A-19", "8000.00", "2026-09-29 14:00:00"),
    ("TX-0021", "A-21", "A-19", "6500.00", "2026-09-29 14:10:00"),
    ("TX-0022", "A-19", "A-22", "14000.00", "2026-09-29 14:35:00"),
]

# Scenario device links: (relationship_id, account, device, Manila local time).
SCENARIO_DEVICE_LINKS = [
    ("DL-0001", "A-01", "D-01", "2026-09-30 08:50:00"),  # A-01 and A-03 share D-01
    ("DL-0002", "A-03", "D-01", "2026-09-30 09:05:00"),
    ("DL-0003", "A-07", "D-02", "2026-09-30 08:10:00"),
    ("DL-0004", "A-08", "D-03", "2026-09-30 09:55:00"),
    ("DL-0005", "A-13", "D-04", "2026-09-24 19:00:00"),  # household tablet
    ("DL-0006", "A-14", "D-04", "2026-09-24 19:20:00"),
    ("DL-0007", "A-15", "D-04", "2026-09-24 20:05:00"),
    ("DL-0008", "A-13", "D-05", "2026-09-24 07:45:00"),
    ("DL-0009", "A-19", "D-06", "2026-09-29 13:40:00"),
    ("DL-0010", "A-22", "D-07", "2026-09-29 14:30:00"),
]

SCENARIO_ACCOUNT_COUNT = 23  # A-01 .. A-23
BACKGROUND_ACCOUNT_COUNT = 12  # A-24 .. A-35
BACKGROUND_TRANSACTION_COUNT = 80
BACKGROUND_START = datetime(2026, 9, 24, 7, 0, tzinfo=MANILA)
BACKGROUND_SPAN_MINUTES = 7 * 24 * 60


def _account_id(n: int) -> str:
    return f"A-{n:02d}"


def _iso(local: str) -> str:
    return datetime.strptime(local, "%Y-%m-%d %H:%M:%S").replace(tzinfo=MANILA).isoformat()


def build() -> dict[str, Any]:
    rng = random.Random(SEED)
    total_accounts = SCENARIO_ACCOUNT_COUNT + BACKGROUND_ACCOUNT_COUNT
    accounts = [
        {"account_id": _account_id(n), "label": f"Wallet {_account_id(n)}"}
        for n in range(1, total_accounts + 1)
    ]
    transactions = [
        {"transaction_id": tx, "sender_account_id": s, "receiver_account_id": r,
         "amount": amount, "currency": CURRENCY, "timestamp": _iso(ts)}
        for tx, s, r, amount, ts in SCENARIO_TRANSACTIONS
    ]
    device_links = [
        {"relationship_id": rel, "account_id": acct, "device_id": dev, "observed_at": _iso(ts)}
        for rel, acct, dev, ts in SCENARIO_DEVICE_LINKS
    ]

    background = [_account_id(n) for n in range(SCENARIO_ACCOUNT_COUNT + 1, total_accounts + 1)]
    for i, acct in enumerate(background):
        observed = BACKGROUND_START + timedelta(minutes=rng.randrange(0, 24 * 60))
        device_links.append({
            "relationship_id": f"DL-{len(device_links) + 1:04d}",
            "account_id": acct,
            "device_id": f"D-{8 + i:02d}",
            "observed_at": observed.isoformat(),
        })

    for _ in range(BACKGROUND_TRANSACTION_COUNT):
        sender, receiver = rng.sample(background, 2)
        amount = Decimal(rng.randrange(100, 5001)).quantize(Decimal("0.01"))
        when = BACKGROUND_START + timedelta(minutes=rng.randrange(0, BACKGROUND_SPAN_MINUTES))
        transactions.append({
            "transaction_id": f"TX-{len(transactions) + 1:04d}",
            "sender_account_id": sender,
            "receiver_account_id": receiver,
            "amount": str(amount),
            "currency": CURRENCY,
            "timestamp": when.isoformat(),
        })

    dataset = {
        "_note": "SYNTHETIC DATA generated by data/generate.py (seeded). No real people, "
                 "institutions, or employer data (BR-001). Do not edit by hand.",
        "seed": SEED,
        "currency": CURRENCY,
        "cases": [
            {"case_id": cid, "title": title, "description": desc, "seed_ids": seeds,
             "scenario_label": label}
            for cid, title, desc, seeds, label in CASES
        ],
        "accounts": accounts,
        "device_links": device_links,
        "transactions": transactions,
    }
    _check_invariants(dataset)
    return dataset


def _check_invariants(dataset: dict[str, Any]) -> None:
    account_ids = {a["account_id"] for a in dataset["accounts"]}
    txs = dataset["transactions"]
    links = dataset["device_links"]
    assert len({t["transaction_id"] for t in txs}) == len(txs), "duplicate transaction_id"
    assert len({d["relationship_id"] for d in links}) == len(links), "duplicate relationship_id"
    assert 20 <= len(account_ids) <= 40 and 80 <= len(txs) <= 150, "size outside System Design §3"
    scenario = {_account_id(n) for n in range(1, SCENARIO_ACCOUNT_COUNT + 1)}
    for t in txs:
        ends = {t["sender_account_id"], t["receiver_account_id"]}
        assert ends <= account_ids and len(ends) == 2, t["transaction_id"]
        assert ends <= scenario or not ends & scenario, f"{t['transaction_id']} crosses into a case"
        assert datetime.fromisoformat(t["timestamp"]).utcoffset() is not None
        assert Decimal(t["amount"]) > 0 and Decimal(t["amount"]).as_tuple().exponent == -2
    for d in links:
        assert d["account_id"] in account_ids, d["relationship_id"]
    for case in dataset["cases"]:
        assert set(case["seed_ids"]) <= scenario, case["case_id"]


def render(dataset: dict[str, Any]) -> str:
    return json.dumps(dataset, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if dataset.json is stale")
    args = parser.parse_args()
    text = render(build())
    if args.check:
        if not OUT_PATH.exists() or OUT_PATH.read_text(encoding="utf-8") != text:
            print(f"{OUT_PATH} is out of date; run python data/generate.py", file=sys.stderr)
            return 1
        print(f"{OUT_PATH} is up to date")
        return 0
    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
