"""Brief validation before display: citations (BR-002), figures (BR-003), language (BR-004/005)."""

import re
from dataclasses import dataclass
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

from traceguard.ai.evidence import EvidenceBundle
from traceguard.ai.schema import ModelBrief

# Account, device, transaction, relationship, and rule IDs: uppercase prefix, hyphen, contains a digit.
ID_TOKEN = re.compile(r"\b[A-Z][A-Z0-9]*-(?=[A-Z0-9-]*\d)[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
NUMBER = re.compile(r"(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.])\d+(?:\.\d+)?")

# BR-004 / BR-005. Accusations, verdicts, probabilities, scores, and "same money" claims.
# Review with Shieryl before changing.
FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "fraudster": re.compile(r"\bfraudsters?\b", re.IGNORECASE),
    "scammer": re.compile(r"\bscammers?\b", re.IGNORECASE),
    "criminal": re.compile(r"\bcriminals?\b", re.IGNORECASE),
    "launderer": re.compile(r"\blaunderers?\b", re.IGNORECASE),
    "guilty": re.compile(r"\bguilt(y|iness)?\b", re.IGNORECASE),
    "confirmed fraud": re.compile(r"\b(confirmed|proven|definite(ly)?)\s+(fraud|laundering)\b", re.IGNORECASE),
    "probability": re.compile(r"\bprobabl[ey]\b|\bprobabilit(y|ies)\b|\blikel(y|ihood)\b", re.IGNORECASE),
    "chance": re.compile(r"\b(chances?|odds)\b", re.IGNORECASE),
    "percentage": re.compile(r"\d\s*%|\bper\s?cent(age)?s?\b", re.IGNORECASE),
    "score": re.compile(r"\bscor(e|es|ed|ing)\b|\b\d{1,3}\s*/\s*100\b", re.IGNORECASE),
    "same money": re.compile(r"\bsame (money|funds)\b", re.IGNORECASE),
}


def _texts(brief: ModelBrief) -> Iterable[str]:
    for statement in (*brief.observations, *brief.counterevidence):
        yield statement.text
    yield from brief.unknowns
    yield from brief.suggested_checks


def _numbers(text: str) -> set[Decimal]:
    values: set[Decimal] = set()
    for match in NUMBER.findall(ID_TOKEN.sub(" ", text)):
        try:
            values.add(Decimal(match.replace(",", "")))
        except InvalidOperation:
            continue
    return values


def citation_problems(brief: ModelBrief, evidence: EvidenceBundle) -> list[str]:
    problems: list[str] = []
    for index, observation in enumerate(brief.observations, start=1):
        if not observation.evidence_ids:
            problems.append(f"Observation {index} cites no evidence IDs.")
    for statement in (*brief.observations, *brief.counterevidence):
        for evidence_id in statement.evidence_ids:
            if evidence_id not in evidence.evidence_ids:
                problems.append(f"Cited ID '{evidence_id}' is not in the evidence bundle.")
    known_tokens = set(ID_TOKEN.findall(evidence.to_prompt_json()))
    for text in _texts(brief):
        for token in ID_TOKEN.findall(text):
            if token not in known_tokens:
                problems.append(f"ID '{token}' in the text does not appear in the tool results.")
    return problems


def figure_problems(brief: ModelBrief, evidence: EvidenceBundle) -> list[str]:
    known = _numbers(evidence.to_prompt_json())
    problems: list[str] = []
    for text in _texts(brief):
        for value in sorted(_numbers(text) - known):
            problems.append(
                f"The figure {value} does not appear in the tool results; quote figures exactly as given."
            )
    return problems


def language_problems(brief: ModelBrief) -> list[str]:
    problems: list[str] = []
    for text in _texts(brief):
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"Forbidden wording ({label}): '{text}'")
    return problems


def structure_problems(brief: ModelBrief) -> list[str]:
    problems: list[str] = []
    if not brief.observations:
        problems.append("The brief has no observations.")
    if not brief.unknowns:
        problems.append("The brief lists no unknowns; state at least what the data cannot show.")
    if not brief.suggested_checks:
        problems.append("The brief suggests no manual checks.")
    return problems


def validate_brief(brief: ModelBrief, evidence: EvidenceBundle) -> list[str]:
    return [
        *structure_problems(brief),
        *citation_problems(brief, evidence),
        *figure_problems(brief, evidence),
        *language_problems(brief),
    ]


@dataclass(frozen=True)
class ValidationSummary:
    """What the validator checked on a brief that passed (shown to the analyst as proof, F-006)."""

    citations: int
    distinct_citations: int
    figures: int
    ids_in_text: int
    statements: int
    passed: bool


def validation_summary(brief: ModelBrief, evidence: EvidenceBundle) -> ValidationSummary:
    cited = [i for s in (*brief.observations, *brief.counterevidence) for i in s.evidence_ids]
    texts = list(_texts(brief))
    return ValidationSummary(
        citations=len(cited),
        distinct_citations=len(set(cited)),
        figures=sum(len(_numbers(t)) for t in texts),
        ids_in_text=sum(len(ID_TOKEN.findall(t)) for t in texts),
        statements=len(texts),
        passed=not validate_brief(brief, evidence),
    )
