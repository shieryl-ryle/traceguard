"""Static sample retriever for the UI sample case until the TASK-003 graph tools land.

The output is labelled "sample evidence" in the UI (BR-006). It follows the same `Retriever`
contract the graph layer will implement, so swapping it is a one-line change in `investigation.py`.
"""

import json
from pathlib import Path

from traceguard.ai.errors import InvestigationError
from traceguard.ai.evidence import EvidenceBundle, ToolCall

SAMPLE_EVIDENCE_PATH = Path(__file__).with_name("sample_evidence.json")


def sample_retriever(case_id: str, max_rounds: int) -> EvidenceBundle:
    data = json.loads(SAMPLE_EVIDENCE_PATH.read_text(encoding="utf-8"))
    if data["case_id"] != case_id:
        raise InvestigationError("validation", f"No sample evidence is available for case {case_id}.")
    if len(data["rounds"]) > max_rounds:
        raise InvestigationError(
            "too_many_rounds",
            f"The sample evidence has {len(data['rounds'])} tool rounds; the limit is {max_rounds}.",
        )
    rounds = tuple(
        tuple(
            ToolCall(
                tool=call["tool"],
                inputs=call["inputs"],
                output=call["output"],
                evidence_ids=frozenset(call["evidence_ids"]),
            )
            for call in round_
        )
        for round_ in data["rounds"]
    )
    return EvidenceBundle(case_id=case_id, rounds=rounds)
