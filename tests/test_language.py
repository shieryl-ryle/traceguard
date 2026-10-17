"""TC-015 (BR-004): careful language — no accusations, verdicts, probabilities, or scores."""

import pytest

from traceguard.ai.schema import ModelBrief, Statement
from traceguard.ai.validate import language_problems


def brief_with(text: str) -> ModelBrief:
    return ModelBrief(
        observations=[Statement(text=text, evidence_ids=["TX-0001"])],
        counterevidence=[],
        unknowns=["Intent is unknown."],
        suggested_checks=["Check KYC records manually."],
    )


@pytest.mark.parametrize(
    "text",
    [
        "Account A-01 belongs to a fraudster.",
        "These SCAMMERS moved funds quickly.",
        "The holder is a criminal.",
        "The account holder is guilty.",
        "This is confirmed fraud.",
        "There is a high probability of laundering.",
        "Funds were probably stolen.",
        "The pattern is 85% suspicious.",
        "Confidence is 90 percent.",
        "Risk score: 92.",
        "Likely a money launderer.",
        "A known launderer pattern.",
        "There is a high likelihood of misuse.",
        "The chance of misuse is high.",
        "The odds favour coordination.",
        "Suspicion score of 87.",
        "Rated 92/100.",
        "Ninety per cent of funds left.",
        "Similar amounts show the same money moved on."
    ],
)
def test_forbidden_wording_rejected(text: str) -> None:
    assert language_problems(brief_with(text)), text


@pytest.mark.parametrize(
    "text",
    [
        "This pattern warrants review.",
        "There is insufficient evidence that the shared device indicates coordinated activity.",
        "Five accounts sent PHP 12,500.00 to A-07 within 30 minutes (rule RULE-FANIN-01, threshold 3 senders).",
        "The trace ends at the data boundary; the next recipient is unknown.",
    ],
)
def test_careful_wording_accepted(text: str) -> None:
    assert language_problems(brief_with(text)) == []


def test_all_sections_are_checked() -> None:
    b = ModelBrief(
        observations=[Statement(text="Pattern warrants review.", evidence_ids=["TX-0001"])],
        counterevidence=[Statement(text="The sender is not guilty.", evidence_ids=[])],
        unknowns=["Whether the fraudster has other accounts."],
        suggested_checks=["Assign a risk score."],
    )
    assert len(language_problems(b)) == 3


def test_system_instruction_keeps_safety_clauses() -> None:
    # TC-016 (BR-005) and BR-003/004: these clauses must survive prompt edits.
    from traceguard.ai.prompt import SYSTEM_INSTRUCTION

    for clause in (
        "Never cite an ID that is not in that list",
        "Do not calculate amounts",
        "Do not decide whether a rule matched",
        "this pattern warrants review",
        "insufficient",
        "data boundary",
        "Similar amounts appearing",
        "not proof that the same money moved",
    ):
        assert clause in SYSTEM_INSTRUCTION, clause


def test_system_instruction_bans_bookkeeping_and_filler_counterevidence() -> None:
    from traceguard.ai.prompt import SYSTEM_INSTRUCTION

    assert "known_account" in SYSTEM_INSTRUCTION
    assert 'never describe an account as "flagged"' in SYSTEM_INSTRUCTION
    assert "Never pad this section with" in SYSTEM_INSTRUCTION


def test_system_instruction_requires_tool_contrasts() -> None:
    from traceguard.ai.prompt import SYSTEM_INSTRUCTION

    assert 'If a tool result has a "contrasts" list, include every entry as counterevidence' in SYSTEM_INSTRUCTION
