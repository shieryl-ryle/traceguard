"""TC-013 (BR-002), TC-014 (BR-003), TC-016 (BR-005): every ID and figure shown comes from tool output."""

from traceguard.ai.evidence import EvidenceBundle, ToolCall
from traceguard.ai.schema import ModelBrief, Statement
from traceguard.ai.validate import citation_problems, figure_problems, structure_problems

FAN_IN = ToolCall(
    tool="detect_fan_in",
    inputs={"account_id": "A-07"},
    output={"sender_count": 3, "aggregate_amount": "15000.00", "window_minutes": 30, "rule_id": "RULE-FANIN-01"},
    evidence_ids=frozenset({"TX-0001", "TX-0002", "RULE-FANIN-01"}),
)
TRACE = ToolCall(
    tool="trace_funds",
    inputs={"account_id": "A-07"},
    output={"transaction_ids": ["TX-0004"], "receiver": "A-09", "truncated": True, "reason": "data boundary"},
    evidence_ids=frozenset({"TX-0004"}),
)
EVIDENCE = EvidenceBundle(case_id="C-1", rounds=((FAN_IN, TRACE),))


def brief(observations: list[Statement], counter: list[Statement] | None = None, unknowns: list[str] | None = None) -> ModelBrief:
    return ModelBrief(
        observations=observations,
        counterevidence=counter or [],
        unknowns=unknowns or ["Where funds went after the data boundary."],
        suggested_checks=["Review account opening details manually."],
    )


def test_valid_citations_pass() -> None:
    b = brief([Statement(text="Two transfers reached A-07.", evidence_ids=["TX-0001", "TX-0002"])])
    assert citation_problems(b, EVIDENCE) == []


def test_nonexistent_id_rejected() -> None:
    b = brief([Statement(text="A transfer occurred.", evidence_ids=["TX-0001", "TX-9999"])])
    assert citation_problems(b, EVIDENCE) == ["Cited ID 'TX-9999' is not in the evidence bundle."]


def test_ids_are_matched_exactly() -> None:
    b = brief([Statement(text="A transfer occurred.", evidence_ids=["tx-0001", "TX-0001 "])])
    assert len(citation_problems(b, EVIDENCE)) == 2


def test_observation_without_citation_rejected() -> None:
    b = brief([Statement(text="Something happened.", evidence_ids=[])])
    assert citation_problems(b, EVIDENCE) == ["Observation 1 cites no evidence IDs."]


def test_counterevidence_citations_are_checked() -> None:
    b = brief(
        [Statement(text="Funds converged.", evidence_ids=["RULE-FANIN-01"])],
        counter=[Statement(text="No forwarding.", evidence_ids=["RULE-FWD-99"])],
    )
    assert citation_problems(b, EVIDENCE) == ["Cited ID 'RULE-FWD-99' is not in the evidence bundle."]


def test_counterevidence_may_have_no_citation() -> None:
    b = brief(
        [Statement(text="Funds converged.", evidence_ids=["RULE-FANIN-01"])],
        counter=[Statement(text="Device sharing alone is common in households.", evidence_ids=[])],
    )
    assert citation_problems(b, EVIDENCE) == []


def test_invented_id_in_free_text_rejected() -> None:
    b = brief([Statement(text="Funds then moved to TX-9999.", evidence_ids=["TX-0004"])])
    assert citation_problems(b, EVIDENCE) == ["ID 'TX-9999' in the text does not appear in the tool results."]


def test_account_past_data_boundary_rejected() -> None:
    # TC-016: A-09 is the last known receiver; naming a next recipient (A-12) is invention.
    b = brief(
        [Statement(text="TX-0004 sent funds to A-09.", evidence_ids=["TX-0004"])],
        unknowns=["A-09 probably forwarded funds to A-12."],
    )
    assert citation_problems(b, EVIDENCE) == ["ID 'A-12' in the text does not appear in the tool results."]


def test_figures_from_tool_output_pass() -> None:
    b = brief([Statement(text="3 senders paid PHP 15,000.00 to A-07 within 30 minutes.", evidence_ids=["RULE-FANIN-01"])])
    assert figure_problems(b, EVIDENCE) == []


def test_model_computed_figure_rejected() -> None:
    b = brief([Statement(text="On average each sender paid PHP 5,000.00.", evidence_ids=["RULE-FANIN-01"])])
    assert figure_problems(b, EVIDENCE) == [
        "The figure 5000.00 does not appear in the tool results; quote figures exactly as given."
    ]


def test_unit_conversion_rejected() -> None:
    b = brief([Statement(text="All within half an hour (1800 seconds).", evidence_ids=["RULE-FANIN-01"])])
    assert len(figure_problems(b, EVIDENCE)) == 1


def test_empty_sections_flagged() -> None:
    empty = ModelBrief(observations=[], counterevidence=[], unknowns=[], suggested_checks=[])
    assert len(structure_problems(empty)) == 3
