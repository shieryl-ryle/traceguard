"""Citation navigation (F-007): map a cited evidence ID to the graph/timeline elements to highlight."""

from dataclasses import dataclass
from typing import Any

from traceguard.ai.evidence import EvidenceBundle


@dataclass(frozen=True)
class RuleFlag:
    rule_id: str
    matched: bool
    config: dict[str, Any]
    explanation: str
    evidence_ids: frozenset[str]


def rule_flags(evidence: EvidenceBundle) -> list[RuleFlag]:
    """Deterministic rule results straight from tool output (BR-003, BR-004: shown with thresholds)."""
    flags: list[RuleFlag] = []
    for call in evidence.calls:
        rule_id = call.output.get("rule_id")
        if isinstance(rule_id, str):
            flags.append(
                RuleFlag(
                    rule_id=rule_id,
                    matched=bool(call.output.get("matched")),
                    config=dict(call.output.get("config", {})),
                    explanation=str(call.output.get("explanation", "")),
                    evidence_ids=call.evidence_ids - {rule_id},
                )
            )
    return flags


def highlight_for(evidence: EvidenceBundle, cited_id: str) -> frozenset[str]:
    """A transaction or device link highlights itself; a rule highlights the records it matched."""
    for flag in rule_flags(evidence):
        if flag.rule_id == cited_id:
            return flag.evidence_ids
    return frozenset({cited_id}) if cited_id in evidence.evidence_ids else frozenset()
