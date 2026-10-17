"""Fixed investigation workflow (F-005, BR-006): retrieve -> generate -> validate -> regenerate once.

Tool selection is a fixed workflow, not autonomous agent behaviour. A "tool round" is one batch
of tool calls; the retriever returns its rounds and this module enforces the BR-007 cap.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from pydantic import ValidationError

from traceguard.ai.errors import InvestigationError
from traceguard.ai.evidence import EvidenceBundle
from traceguard.ai.prompt import SYSTEM_INSTRUCTION, build_user_prompt
from traceguard.ai.schema import Brief, ModelBrief
from traceguard.ai.validate import validate_brief

MAX_TOOL_ROUNDS = 4  # BR-007
MAX_ATTEMPTS = 2  # BR-002: first attempt + one regeneration

# (case_id, max_rounds) -> bundle. The retriever must stop at max_rounds; the check below is a backstop.
Retriever = Callable[[str, int], EvidenceBundle]
Generator = Callable[[str, str], str]

logger = logging.getLogger(__name__)


@dataclass
class Attempt:
    number: int
    problems: list[str]


@dataclass
class InvestigationResult:
    brief: Brief
    evidence: EvidenceBundle
    attempts: list[Attempt] = field(default_factory=list)


PROBLEM_KINDS = (
    ("Cited ID", "invented_citation"),
    ("ID '", "unknown_id_in_text"),
    ("The figure", "unsupported_figure"),
    ("Forbidden wording", "forbidden_wording"),
    ("Observation", "uncited_observation"),
    ("The response was not valid", "invalid_json"),
    ("The brief", "missing_section"),
)


def problem_kinds(problems: list[str]) -> dict[str, int]:
    """Counts problems by category for logs. Never logs brief text, IDs, or evidence (System Design §2)."""
    kinds: dict[str, int] = {}
    for problem in problems:
        kind = next((k for prefix, k in PROBLEM_KINDS if problem.startswith(prefix)), "other")
        kinds[kind] = kinds.get(kind, 0) + 1
    return kinds


def _parse(raw: str) -> tuple[ModelBrief | None, list[str]]:
    try:
        return ModelBrief.model_validate_json(raw), []
    except ValidationError as exc:
        return None, [f"The response was not valid brief JSON ({exc.error_count()} schema errors)."]


def run_investigation(
    case_id: str,
    retrieve: Retriever,
    generate: Generator,
    model_id: str,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> InvestigationResult:
    evidence = retrieve(case_id, MAX_TOOL_ROUNDS)
    if len(evidence.rounds) > MAX_TOOL_ROUNDS:
        raise InvestigationError(
            "too_many_rounds",
            f"The investigation needed {len(evidence.rounds)} tool rounds; the limit is {MAX_TOOL_ROUNDS}.",
        )
    if not evidence.evidence_ids:
        raise InvestigationError(
            "validation", "The graph tools returned no evidence for this case, so no brief was generated."
        )
    evidence_json = evidence.to_prompt_json()

    attempts: list[Attempt] = []
    feedback: list[str] | None = None
    for number in range(1, MAX_ATTEMPTS + 1):
        raw = generate(SYSTEM_INSTRUCTION, build_user_prompt(evidence_json, feedback))
        model_brief, problems = _parse(raw)
        if model_brief is not None:
            problems = validate_brief(model_brief, evidence)
        attempts.append(Attempt(number=number, problems=problems))
        if model_brief is not None and not problems:
            brief = Brief(**model_brief.model_dump(), case_id=case_id, model=model_id, run_at=now())
            return InvestigationResult(brief=brief, evidence=evidence, attempts=attempts)
        logger.warning("Brief attempt %s rejected: %s", number, problem_kinds(problems))
        feedback = problems

    raise InvestigationError(
        "validation",
        "The AI brief failed citation or wording checks twice, so it was not shown. "
        "The graph and timeline are still available.",
    )
