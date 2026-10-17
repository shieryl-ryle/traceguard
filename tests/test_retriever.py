"""Graph retriever honours the AI module contract (System Design §2, BR-007, BR-010)."""

import json

import pytest

from traceguard.ai.errors import InvestigationError
from traceguard.ai.evidence import MAX_EVIDENCE_CHARS
from traceguard.ai.investigate import MAX_TOOL_ROUNDS
from traceguard.graph.loader import load_dataset
from traceguard.graph.retriever import graph_retriever

TOOLS = {"get_account_context", "detect_fan_in", "detect_rapid_forwarding", "find_shared_devices", "trace_funds"}


@pytest.mark.parametrize("case_id", ["C-1", "C-2", "C-3"])
def test_bundle_shape_and_caps(case_id: str) -> None:
    bundle = graph_retriever(case_id, MAX_TOOL_ROUNDS)
    assert bundle.case_id == case_id
    assert 1 <= len(bundle.rounds) <= MAX_TOOL_ROUNDS
    assert {call.tool for call in bundle.calls} == TOOLS
    for call in bundle.calls:
        json.dumps(call.output)
        json.dumps(call.inputs)
    assert {"RULE-FANIN-01", "RULE-FWD-01"} <= bundle.evidence_ids
    payload = bundle.to_prompt_json()
    assert len(payload) <= MAX_EVIDENCE_CHARS


@pytest.mark.parametrize("case_id", ["C-1", "C-2", "C-3"])
def test_case_text_never_reaches_model_input(case_id: str) -> None:
    case = next(c for c in load_dataset().cases if c["case_id"] == case_id)
    payload = graph_retriever(case_id, MAX_TOOL_ROUNDS).to_prompt_json()
    for field in ("title", "description", "scenario_label"):
        assert case[field] not in payload


def test_rule_flags_match_expected_outcomes() -> None:
    def flags(case_id: str) -> dict[tuple[str, str], bool]:
        bundle = graph_retriever(case_id, MAX_TOOL_ROUNDS)
        return {(c.output["rule_id"], c.inputs["account_id"]): c.output["matched"]
                for c in bundle.calls if "rule_id" in c.output}

    assert flags("C-1") == {("RULE-FANIN-01", "A-07"): True, ("RULE-FWD-01", "A-07"): True}
    assert not any(flags("C-2").values())
    assert flags("C-3") == {("RULE-FANIN-01", "A-19"): False, ("RULE-FWD-01", "A-19"): True}


def test_unknown_case_and_round_cap_raise() -> None:
    with pytest.raises(InvestigationError) as exc:
        graph_retriever("C-9", MAX_TOOL_ROUNDS)
    assert exc.value.kind == "validation"
    with pytest.raises(InvestigationError) as exc:
        graph_retriever("C-1", 1)
    assert exc.value.kind == "too_many_rounds"
