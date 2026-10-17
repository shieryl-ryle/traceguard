"""TC-004: the 5 graph tools match the hand-derived expected outcomes (F-004, BR-003, ADR-003)."""

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from traceguard.graph import tools
from traceguard.graph.config import DEFAULT_MAX_DEPTH, FAN_IN, FORWARDING
from traceguard.graph.loader import dataset_from_dict, load_dataset

FIXTURES = Path(__file__).with_name("fixtures")
CASE_IDS = ["C-1", "C-2", "C-3"]


def _expected(case_id: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / f"expected_{case_id}.json").read_text(encoding="utf-8"))
    return data


def assert_subset(expected: Any, actual: Any, where: str = "") -> None:
    """Every key in `expected` must match `actual`; extra keys in `actual` are allowed."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict), where
        for key, value in expected.items():
            if key.startswith("_"):
                continue
            assert key in actual, f"{where}.{key} missing"
            assert_subset(value, actual[key], f"{where}.{key}")
    elif isinstance(expected, list) and expected and isinstance(expected[0], dict):
        assert isinstance(actual, list) and len(actual) == len(expected), f"{where}: {actual}"
        for i, (e, a) in enumerate(zip(expected, actual, strict=True)):
            assert_subset(e, a, f"{where}[{i}]")
    else:
        assert actual == expected, f"{where}: expected {expected!r}, got {actual!r}"


def _run(graph: Any, tool: str, inputs: dict[str, Any]) -> tools.ToolResult:
    if tool == "get_account_context":
        return tools.get_account_context(graph, inputs["account_id"])
    if tool == "detect_fan_in":
        return tools.detect_fan_in(graph, inputs["account_id"])
    if tool == "detect_rapid_forwarding":
        return tools.detect_rapid_forwarding(graph, inputs["account_id"])
    if tool == "find_shared_devices":
        return tools.find_shared_devices(graph, inputs["account_ids"])
    if tool == "trace_funds":
        return tools.trace_funds(graph, inputs["account_id"], inputs.get("direction", "out"),
                                 inputs.get("max_depth", DEFAULT_MAX_DEPTH), inputs.get("start_time"))
    raise AssertionError(tool)


def test_config_matches_fixture_copy() -> None:
    cfg = json.loads((FIXTURES / "rule_config.json").read_text(encoding="utf-8"))
    assert cfg["fan_in"] == {"rule_id": FAN_IN.rule_id, **FAN_IN.as_output()}
    assert cfg["rapid_forwarding"] == {"rule_id": FORWARDING.rule_id, **FORWARDING.as_output()}
    assert cfg["trace_funds"]["default_max_depth"] == DEFAULT_MAX_DEPTH


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_account_context(case_id: str) -> None:
    graph = load_dataset().graph
    for account, expected in _expected(case_id)["account_context"].items():
        assert_subset(expected, tools.get_account_context(graph, account).output, f"{case_id}.{account}")


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_fan_in(case_id: str) -> None:
    graph = load_dataset().graph
    for account, expected in _expected(case_id)["fan_in"].items():
        assert_subset(expected, tools.detect_fan_in(graph, account).output, f"{case_id}.{account}")


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_rapid_forwarding(case_id: str) -> None:
    graph = load_dataset().graph
    for account, expected in _expected(case_id)["rapid_forwarding"].items():
        assert_subset(expected, tools.detect_rapid_forwarding(graph, account).output, f"{case_id}.{account}")


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_shared_devices(case_id: str) -> None:
    graph = load_dataset().graph
    for item in _expected(case_id)["shared_devices"]:
        actual = tools.find_shared_devices(graph, item["account_ids"]).output["shared_devices"]
        assert actual == item["expected"]


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_trace_funds(case_id: str) -> None:
    graph = load_dataset().graph
    for item in _expected(case_id)["trace_funds"]:
        actual = _run(graph, "trace_funds", item["inputs"]).output
        assert_subset({"truncated": item["truncated"], "paths": item["paths"]}, actual, str(item["inputs"]))


def test_c2_has_no_forwarding_match_and_c3_is_truncated_at_boundary() -> None:
    graph = load_dataset().graph
    for account in ("A-13", "A-14", "A-15"):
        assert tools.detect_rapid_forwarding(graph, account).output["matched"] is False
    trace = tools.trace_funds(graph, "A-19").output
    assert trace["truncated"] is True and trace["truncation_reasons"] == ["data_boundary"]
    assert "unknown" in trace["notice"]


def test_trace_paths_are_time_ordered() -> None:
    graph = load_dataset().graph
    for account in ("A-07", "A-13", "A-19"):
        for path in tools.trace_funds(graph, account, max_depth=5).output["paths"]:
            stamps = [step["timestamp"] for step in path["steps"]]
            assert stamps == sorted(stamps)


_BOUNDARY = json.loads((FIXTURES / "boundary_cases.json").read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", _BOUNDARY, ids=[c["name"] for c in _BOUNDARY])
def test_boundary_cases(case: dict[str, Any]) -> None:
    graph = dataset_from_dict(case["data"]).graph
    result = _run(graph, case["call"]["tool"], case["call"]["inputs"])
    assert_subset(case["expected"], result.output, case["name"])


@pytest.mark.parametrize("account", ["A-99", "D-01"])
def test_unknown_or_non_account_returns_empty(account: str) -> None:
    graph = load_dataset().graph
    assert tools.get_account_context(graph, account).evidence_ids == frozenset()
    assert tools.detect_fan_in(graph, account).output["sender_count"] == 0
    assert tools.detect_rapid_forwarding(graph, account).output["evaluated"] == []
    assert tools.trace_funds(graph, account).output["paths"] == []
    assert tools.find_shared_devices(graph, [account]).output["shared_devices"] == []


def test_invalid_trace_inputs_raise() -> None:
    graph = load_dataset().graph
    with pytest.raises(ValueError):
        tools.trace_funds(graph, "A-07", "sideways")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        tools.trace_funds(graph, "A-07", max_depth=0)
    with pytest.raises(ValueError):
        tools.trace_funds(graph, "A-07", start_time="2026-09-30T10:00:00")


def _numbers(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set().union(*(_numbers(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(_numbers(v) for v in value)) if value else set()
    if isinstance(value, bool) or value is None:
        return set()
    return {str(value)}


@pytest.mark.parametrize("account", ["A-07", "A-13", "A-19"])
def test_outputs_are_json_ready_and_cite_only_their_records(account: str) -> None:
    graph = load_dataset().graph
    for result in (tools.get_account_context(graph, account), tools.detect_fan_in(graph, account),
                   tools.detect_rapid_forwarding(graph, account), tools.trace_funds(graph, account)):
        json.dumps(result.output)  # JSON-serialisable without default=
        text = json.dumps(result.output)
        assert "%" not in text  # BR-004: ratios are decimals, never percentages
        for evidence_id in result.evidence_ids:
            assert evidence_id in text


def test_explanation_figures_appear_as_output_fields() -> None:
    """BR-003: every figure in an explanation is a field value the validator can match."""
    graph = load_dataset().graph
    for account in ("A-07", "A-13", "A-19"):
        for result in (tools.detect_fan_in(graph, account), tools.detect_rapid_forwarding(graph, account)):
            output = dict(result.output)
            explanation = output.pop("explanation")
            values = {Decimal(v) for v in _numbers(output) if v.replace(".", "", 1).isdigit()}
            for token in re.findall(r"(?<![\w.-])\d+(?:\.\d+)?", explanation):
                assert Decimal(token) in values, f"{account}: {token} in {explanation!r}"


def _mini(transactions: list[tuple[str, str, str, str, str]]) -> Any:
    accounts = sorted({a for _, s, r, _, _ in transactions for a in (s, r)})
    return dataset_from_dict({
        "accounts": [{"account_id": a, "label": f"Wallet {a}"} for a in accounts],
        "device_links": [],
        "transactions": [
            {"transaction_id": tx, "sender_account_id": s, "receiver_account_id": r, "amount": amt,
             "currency": "PHP", "timestamp": ts}
            for tx, s, r, amt, ts in transactions
        ],
    }).graph


def test_trace_never_reuses_a_transaction_in_one_path() -> None:
    graph = _mini([
        ("TX-9001", "A-91", "A-92", "100.00", "2026-10-01T10:00:00+08:00"),
        ("TX-9002", "A-92", "A-91", "100.00", "2026-10-01T10:00:00+08:00"),
    ])
    for path in tools.trace_funds(graph, "A-91", max_depth=5).output["paths"]:
        assert len(path["transaction_ids"]) == len(set(path["transaction_ids"]))


def test_inbound_notice_wording_and_start_time_bound() -> None:
    graph = load_dataset().graph
    assert tools.trace_funds(graph, "A-01", "in").output["notice"] == (
        "No incoming transfers to A-01 in the dataset."
    )
    notice = tools.trace_funds(graph, "A-12", "out", start_time="2026-09-30T13:00:00+08:00").output["notice"]
    assert notice == "No outgoing transfers from A-12 at or after 2026-09-30T13:00:00+08:00 in the dataset."


def test_mixed_currency_is_rejected() -> None:
    data = {"accounts": [{"account_id": "A-91", "label": "x"}, {"account_id": "A-92", "label": "y"}],
            "device_links": [],
            "transactions": [{"transaction_id": "TX-9001", "sender_account_id": "A-91",
                              "receiver_account_id": "A-92", "amount": "1.00", "currency": "USD",
                              "timestamp": "2026-10-01T10:00:00+08:00"}]}
    with pytest.raises(ValueError):
        dataset_from_dict(data)


def _rule_results(account: str) -> tuple[tools.ToolResult, tools.ToolResult]:
    graph = load_dataset().graph
    return tools.detect_fan_in(graph, account), tools.detect_rapid_forwarding(graph, account)


@pytest.mark.parametrize("account", ["A-07", "A-13", "A-14", "A-15", "A-19"])
def test_contrasts_are_quotable_and_cite_tool_evidence(account: str) -> None:
    """Contrasts become counterevidence verbatim: figures and IDs must be in the same output (BR-002, BR-003)."""
    for result in _rule_results(account):
        output = dict(result.output)
        contrasts = output.pop("contrasts")
        output.pop("explanation")
        values = {Decimal(v) for v in _numbers(output) if v.replace(".", "", 1).isdigit()}
        text_of_output = json.dumps(output)
        for contrast in contrasts:
            assert contrast["evidence_ids"] and set(contrast["evidence_ids"]) <= result.evidence_ids
            for token in re.findall(r"(?<![\w.-])\d+(?:\.\d+)?", contrast["text"]):
                assert Decimal(token) in values, f"{account}: {token} in {contrast['text']!r}"
            for id_token in re.findall(r"\b[A-Z]+-\d+\b", contrast["text"]):
                assert id_token in text_of_output, f"{account}: {id_token} not in output"
            assert "%" not in contrast["text"] and "same money" not in contrast["text"].lower()


def test_c2_has_no_contrasts() -> None:
    for account in ("A-13", "A-14", "A-15"):
        for result in _rule_results(account):
            assert result.output["contrasts"] == []


def test_no_fan_in_contrast_when_every_sender_shares_a_device() -> None:
    graph = dataset_from_dict({
        "accounts": [{"account_id": a, "label": a} for a in ("A-90", "A-91", "A-92", "A-93")],
        "device_links": [
            {"relationship_id": f"DL-990{i}", "account_id": a, "device_id": "D-99",
             "observed_at": "2026-10-01T09:00:00+08:00"}
            for i, a in enumerate(("A-91", "A-92", "A-93"), 1)
        ],
        "transactions": [
            {"transaction_id": f"TX-900{i}", "sender_account_id": a, "receiver_account_id": "A-90",
             "amount": "100.00", "currency": "PHP", "timestamp": f"2026-10-01T10:0{i}:00+08:00"}
            for i, a in enumerate(("A-91", "A-92", "A-93"), 1)
        ],
    }).graph
    output = tools.detect_fan_in(graph, "A-90").output
    assert output["senders_on_shared_device"] == ["A-91", "A-92", "A-93"]
    assert output["senders_not_on_shared_device"] == [] and output["contrasts"] == []


def test_no_fan_in_contrast_when_rule_not_matched() -> None:
    graph = dataset_from_dict({
        "accounts": [{"account_id": a, "label": a} for a in ("A-90", "A-91", "A-92")],
        "device_links": [
            {"relationship_id": "DL-9901", "account_id": "A-91", "device_id": "D-99", "observed_at": "2026-10-01T09:00:00+08:00"},
            {"relationship_id": "DL-9902", "account_id": "A-92", "device_id": "D-99", "observed_at": "2026-10-01T09:00:00+08:00"},
        ],
        "transactions": [
            {"transaction_id": f"TX-900{i}", "sender_account_id": a, "receiver_account_id": "A-90",
             "amount": "100.00", "currency": "PHP", "timestamp": f"2026-10-01T10:0{i}:00+08:00"}
            for i, a in enumerate(("A-91", "A-92"), 1)
        ],
    }).graph
    output = tools.detect_fan_in(graph, "A-90").output
    assert output["matched"] is False and output["contrasts"] == []
