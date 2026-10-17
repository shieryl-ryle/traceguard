"""Hand-made UI test sample S-1: a small case view and matching static tool results.

Test-only. The app reads the bundled dataset through `traceguard.graph`; nothing here ships.
"""

import json
from pathlib import Path

from traceguard.ai.errors import InvestigationError
from traceguard.ai.evidence import EvidenceBundle, ToolCall
from traceguard.ui.models import CaseView, case_view_from_dict

HERE = Path(__file__).parent


def load_sample_case() -> CaseView:
    return case_view_from_dict(json.loads((HERE / "sample_case.json").read_text(encoding="utf-8")))


def sample_retriever(case_id: str, max_rounds: int) -> EvidenceBundle:
    data = json.loads((HERE / "sample_evidence.json").read_text(encoding="utf-8"))
    if data["case_id"] != case_id:
        raise InvestigationError("validation", f"No sample evidence for case {case_id}.")
    if len(data["rounds"]) > max_rounds:
        raise InvestigationError("too_many_rounds", f"The sample has {len(data['rounds'])} rounds; limit {max_rounds}.")
    rounds = tuple(
        tuple(
            ToolCall(tool=c["tool"], inputs=c["inputs"], output=c["output"], evidence_ids=frozenset(c["evidence_ids"]))
            for c in round_
        )
        for round_ in data["rounds"]
    )
    return EvidenceBundle(case_id=case_id, rounds=rounds)
