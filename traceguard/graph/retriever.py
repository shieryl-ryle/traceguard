"""Graph retriever for the AI workflow (System Design §2 "AI module contract").

Fixed two-round workflow per case: (1) account context for each seed; (2) fan-in, rapid
forwarding and outbound trace for each seed, plus shared devices across the case accounts.
Only IDs go to the tools; case title, description and scenario label never reach model input.
"""

from typing import Any

from traceguard.ai.errors import InvestigationError
from traceguard.ai.evidence import EvidenceBundle, ToolCall
from traceguard.graph import tools
from traceguard.graph.config import DEFAULT_MAX_DEPTH
from traceguard.graph.loader import Dataset, case_account_ids, get_case, load_dataset

ROUNDS_NEEDED = 2


def _call(name: str, inputs: dict[str, Any], result: tools.ToolResult) -> ToolCall:
    return ToolCall(tool=name, inputs=inputs, output=result.output, evidence_ids=result.evidence_ids)


def retrieve_evidence(dataset: Dataset, case_id: str, max_rounds: int) -> EvidenceBundle:
    try:
        case = get_case(dataset, case_id)
    except KeyError:
        raise InvestigationError("validation", f"Case {case_id} is not in the dataset.") from None
    if ROUNDS_NEEDED > max_rounds:
        raise InvestigationError(
            "too_many_rounds",
            f"The investigation needs {ROUNDS_NEEDED} tool rounds; the limit is {max_rounds}.",
        )
    graph = dataset.graph
    seeds: list[str] = list(case["seed_ids"])

    context = tuple(
        _call("get_account_context", {"account_id": s}, tools.get_account_context(graph, s)) for s in seeds
    )
    rules: list[ToolCall] = []
    for s in seeds:
        rules.append(_call("detect_fan_in", {"account_id": s}, tools.detect_fan_in(graph, s)))
        rules.append(_call("detect_rapid_forwarding", {"account_id": s}, tools.detect_rapid_forwarding(graph, s)))
    accounts = case_account_ids(dataset, case_id)
    rules.append(_call("find_shared_devices", {"account_ids": accounts}, tools.find_shared_devices(graph, accounts)))
    for s in seeds:
        inputs: dict[str, Any] = {"account_id": s, "direction": "out", "max_depth": DEFAULT_MAX_DEPTH}
        rules.append(_call("trace_funds", inputs, tools.trace_funds(graph, s, "out", DEFAULT_MAX_DEPTH)))
    return EvidenceBundle(case_id=case_id, rounds=(context, tuple(rules)))


def graph_retriever(case_id: str, max_rounds: int) -> EvidenceBundle:
    """`Retriever` for `run_investigation` over the bundled dataset."""
    return retrieve_evidence(load_dataset(), case_id, max_rounds)
