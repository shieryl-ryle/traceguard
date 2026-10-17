"""Evidence bundle passed to the model (BR-002, BR-007, BR-010).

Contract with `traceguard/graph/` (TASK-003): every tool result is recorded as a `ToolCall`
with JSON-serialisable `output` and the evidence IDs it returned (`transaction_id`,
`relationship_id`, or `rule_id`). Only IDs listed here are citable.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from traceguard.ai.errors import InvestigationError

MAX_EVIDENCE_CHARS = 60_000  # BR-007, provisional (PRD Q6)


@dataclass(frozen=True)
class ToolCall:
    tool: str
    inputs: dict[str, Any]
    output: dict[str, Any]
    evidence_ids: frozenset[str]


@dataclass(frozen=True)
class EvidenceBundle:
    case_id: str
    rounds: tuple[tuple[ToolCall, ...], ...]
    evidence_ids: frozenset[str] = field(init=False)

    def __post_init__(self) -> None:
        ids = frozenset().union(*(call.evidence_ids for call in self.calls))
        object.__setattr__(self, "evidence_ids", ids)

    @property
    def calls(self) -> tuple[ToolCall, ...]:
        return tuple(call for round_ in self.rounds for call in round_)

    def to_prompt_json(self, max_chars: int = MAX_EVIDENCE_CHARS) -> str:
        payload = {
            "case_id": self.case_id,
            "citable_evidence_ids": sorted(self.evidence_ids),
            "tool_results": [
                {"tool": c.tool, "inputs": c.inputs, "output": c.output, "evidence_ids": sorted(c.evidence_ids)}
                for c in self.calls
            ],
        }
        text = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        if len(text) > max_chars:
            raise InvestigationError(
                "payload_too_large",
                f"The evidence for this case is too large to send to the model "
                f"({len(text):,} characters; limit {max_chars:,}). Narrow the case and try again.",
            )
        return text
