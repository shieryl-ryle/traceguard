"""TC-006, TC-007, TC-008, TC-009: brief rendering, citation navigation, export, error states."""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from traceguard.ai import InvestigationError
from traceguard.ai.investigate import MAX_TOOL_ROUNDS
from traceguard.ui import investigation
from traceguard.ui.citations import highlight_for, rule_flags
from traceguard.ui.export import brief_to_markdown
from tests.ui_sample import load_sample_case, sample_retriever

APP = str(Path(__file__).resolve().parents[1] / "app.py")
VIEW = load_sample_case()
EVIDENCE = sample_retriever("S-1", MAX_TOOL_ROUNDS)

GOOD_BRIEF = json.dumps(
    {
        "observations": [
            {"text": "3 senders paid A-07 PHP 15000.00 within the window; this pattern warrants review.",
             "evidence_ids": ["RULE-FANIN-01", "TX-0001"]},
            {"text": "A-07 sent TX-0005 to A-09 13 minutes after TX-0004.", "evidence_ids": ["TX-0005", "RULE-FWD-01"]},
        ],
        "counterevidence": [{"text": "A-02 shares no device with the other senders.", "evidence_ids": ["DL-0001"]}],
        "unknowns": ["Where funds went after A-09 (data boundary)."],
        "suggested_checks": ["Review onboarding records for A-01 and A-03."],
    }
)


# A brief that is valid for the REAL C-1 evidence from the graph tools (figures and IDs quoted).
C1_BRIEF = json.dumps(
    {
        "observations": [
            {"text": "4 senders (A-01, A-02, A-03, A-04) paid A-07 PHP 17000.00 across 5 transfers within 30 minutes; "
                     "this pattern warrants review.", "evidence_ids": ["RULE-FANIN-01", "TX-0002"]},
            {"text": "A-07 sent TX-0007 (PHP 15500.00), a ratio of 0.91 of its inbound funds, 30 minutes after its "
                     "last inbound transfer.", "evidence_ids": ["RULE-FWD-01", "TX-0007"]},
        ],
        "counterevidence": [{"text": "Device D-01 links only A-01 and A-03 among the senders.",
                             "evidence_ids": ["DL-0001", "DL-0002"]}],
        "unknowns": ["Where funds went after A-09 is unknown (data boundary)."],
        "suggested_checks": ["Review onboarding records for A-01 and A-03."],
    }
)

# --- Sample evidence must agree with the sample case (guards hand-derived figures) ---


def test_sample_evidence_ids_exist_in_case() -> None:
    known = {t.transaction_id for t in VIEW.transactions} | {d.relationship_id for d in VIEW.device_links}
    rule_ids = {f.rule_id for f in rule_flags(EVIDENCE)}
    assert EVIDENCE.evidence_ids - rule_ids <= known


def test_sample_fan_in_figures_match_transactions() -> None:
    fan_in = next(c.output for c in EVIDENCE.calls if c.tool == "detect_fan_in")
    txs = [t for t in VIEW.transactions if t.transaction_id in fan_in["transaction_ids"]]
    assert sum((t.amount for t in txs), Decimal(0)) == Decimal(fan_in["aggregate_amount"])
    assert len({t.sender_account_id for t in txs}) == fan_in["sender_count"]
    assert len(txs) == fan_in["transfer_count"]


def test_sample_forwarding_gap_matches_timestamps() -> None:
    fwd = next(c.output for c in EVIDENCE.calls if c.tool == "detect_rapid_forwarding")
    by_id = {t.transaction_id: t for t in VIEW.transactions}
    gap = by_id[fwd["outbound_transaction_id"]].timestamp - by_id[fwd["last_inbound_transaction_id"]].timestamp
    assert gap.total_seconds() / 60 == fwd["minutes_after_last_inbound"]


# --- Citation navigation (TC-007) ---


def test_rule_citation_highlights_matched_records() -> None:
    assert highlight_for(EVIDENCE, "RULE-FWD-01") == frozenset({"TX-0004", "TX-0005"})


def test_record_citation_highlights_itself_and_unknown_ids_nothing() -> None:
    assert highlight_for(EVIDENCE, "DL-0001") == frozenset({"DL-0001"})
    assert highlight_for(EVIDENCE, "TX-9999") == frozenset()


# --- Export (TC-008) ---


def test_markdown_export_contains_full_brief() -> None:
    from traceguard.ai import run_investigation

    result = run_investigation("S-1", retrieve=sample_retriever, generate=lambda *_: GOOD_BRIEF, model_id="gemini-test")
    md = brief_to_markdown(result.brief, result.evidence, VIEW.case.title, "Sample evidence", "Rule flags (sample)")
    for expected in ("Synthetic data", "gemini-test", "Live AI output", "RULE-FANIN-01", "min_senders=3",
                     "## Observations", "`TX-0005`", "## Counterevidence", "## Unknowns", "data boundary",
                     "## Suggested manual checks", "Generated:"):
        assert expected in md, expected


# --- Page behaviour with a fake model (TC-006, TC-009) ---


class FakeGenerator:
    response = C1_BRIEF
    error: InvestigationError | None = None

    def __init__(self, config: object) -> None:
        pass

    def __call__(self, system_instruction: str, user_prompt: str) -> str:
        if FakeGenerator.error is not None:
            raise FakeGenerator.error
        return FakeGenerator.response


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")
    monkeypatch.setenv("VERTEX_LOCATION", "asia-southeast1")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.setattr(investigation, "GeminiBriefGenerator", FakeGenerator)
    FakeGenerator.error = None
    return AppTest.from_file(APP, default_timeout=60).run()


def _button(at: AppTest, label: str):  # type: ignore[no-untyped-def]
    return next(b for b in at.button if b.label == label)


def test_brief_renders_and_citation_click_highlights(app: AppTest) -> None:
    _button(app, "Run AI investigation").click().run()
    assert not app.exception
    assert any("Live AI output" in s.value for s in app.success)
    _button(app, "RULE-FWD-01").click().run()
    assert any("RULE-FWD-01" in i.value for i in app.info)
    assert app.session_state[investigation.CITED_KEY] == "RULE-FWD-01"


def test_model_error_is_readable_and_page_still_works(app: AppTest) -> None:
    FakeGenerator.error = InvestigationError("timeout", "Gemini did not respond within 30 seconds. Try again.")
    _button(app, "Run AI investigation").click().run()
    assert not app.exception
    assert [e.value for e in app.error] == ["Gemini did not respond within 30 seconds. Try again."]
    assert any(s.value == "Timeline" for s in app.subheader)


def test_rejected_brief_shows_error_not_brief(app: AppTest) -> None:
    FakeGenerator.response = C1_BRIEF.replace("TX-0007", "TX-9999")
    try:
        _button(app, "Run AI investigation").click().run()
        assert any("failed citation or wording checks" in e.value for e in app.error)
        assert not any("Live AI output" in s.value for s in app.success)
    finally:
        FakeGenerator.response = C1_BRIEF


def test_cited_records_are_listed_for_verification() -> None:
    lines = investigation.cited_record_lines(VIEW, highlight_for(EVIDENCE, "RULE-FWD-01"))
    assert lines == [
        "- `TX-0004` A-03 → A-07 · PHP 5,200.00 · 2026-09-30T09:14+08:00",
        "- `TX-0005` A-07 → A-09 · PHP 14,500.00 · 2026-09-30T09:27+08:00",
    ]


def test_sample_retriever_errors_instead_of_truncating_rounds() -> None:
    with pytest.raises(InvestigationError) as exc:
        sample_retriever("S-1", max_rounds=1)
    assert exc.value.kind == "too_many_rounds"


def test_app_uses_the_graph_retriever_with_deterministic_labels() -> None:
    from traceguard.graph.retriever import graph_retriever

    assert investigation.RETRIEVER is graph_retriever
    assert investigation.FLAGS_HEADING == "Rule flags (deterministic)"
    assert "Graph tools" in investigation.EVIDENCE_SOURCE


def test_real_c1_brief_passes_validation_against_graph_evidence() -> None:
    from traceguard.ai import run_investigation
    from traceguard.graph.retriever import graph_retriever

    result = run_investigation("C-1", retrieve=graph_retriever, generate=lambda *_: C1_BRIEF, model_id="gemini-test")
    assert len(result.attempts) == 1


def test_tool_contrasts_are_collected_and_unknown_ids_dropped() -> None:
    from traceguard.ai.evidence import EvidenceBundle, ToolCall
    from traceguard.ui.citations import tool_contrasts

    call = ToolCall(
        tool="detect_fan_in",
        inputs={"account_id": "A-07"},
        output={"rule_id": "RULE-FANIN-01", "matched": True, "contrasts": [
            {"text": "A-02 and A-04 are not linked to a device shared with other senders.", "evidence_ids": ["DL-0001", "DL-9999"]},
            "not a dict",
        ]},
        evidence_ids=frozenset({"RULE-FANIN-01", "DL-0001"}),
    )
    contrasts = tool_contrasts(EvidenceBundle(case_id="C-1", rounds=((call,),)))
    assert [(c.text, c.evidence_ids) for c in contrasts] == [
        ("A-02 and A-04 are not linked to a device shared with other senders.", ("DL-0001",))
    ]


def test_no_contrasts_when_tools_emit_none() -> None:
    from traceguard.ui.citations import tool_contrasts

    assert tool_contrasts(EVIDENCE) == []
