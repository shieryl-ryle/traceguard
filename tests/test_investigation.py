"""TC-005, TC-009, TC-013, TC-018: investigation workflow with a fake model."""

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from google.auth.exceptions import RefreshError
from google.genai import errors

from traceguard.ai import EvidenceBundle, InvestigationError, ToolCall, run_investigation
from traceguard.ai.evidence import MAX_EVIDENCE_CHARS
from traceguard.ai.gemini import REQUEST_TIMEOUT_MS, GeminiBriefGenerator, GeminiConfig, build_client
from traceguard.ai.investigate import MAX_TOOL_ROUNDS

FIXED_NOW = datetime(2026, 10, 18, 4, 0, tzinfo=UTC)

FAN_IN = ToolCall(
    tool="detect_fan_in",
    inputs={"account_id": "A-07"},
    output={"sender_count": 3, "aggregate_amount": "15000.00", "currency": "PHP", "rule_id": "RULE-FANIN-01"},
    evidence_ids=frozenset({"TX-0001", "TX-0002", "TX-0003", "RULE-FANIN-01"}),
)
TRACE = ToolCall(
    tool="trace_funds",
    inputs={"account_id": "A-07", "direction": "out"},
    output={"transaction_ids": ["TX-0004"], "truncated": True, "reason": "data boundary"},
    evidence_ids=frozenset({"TX-0004"}),
)


def bundle(rounds: int = 1) -> EvidenceBundle:
    return EvidenceBundle(case_id="C-1", rounds=tuple((FAN_IN, TRACE) for _ in range(rounds)))


def brief_json(evidence_ids: list[str], text: str = "3 senders paid A-07; this pattern warrants review.") -> str:
    return json.dumps(
        {
            "observations": [{"text": text, "evidence_ids": evidence_ids}],
            "counterevidence": [],
            "unknowns": ["The recipient after TX-0004 is unknown (data boundary)."],
            "suggested_checks": ["Review the onboarding records of the three senders."],
        }
    )


class ScriptedModel:
    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def __call__(self, system_instruction: str, user_prompt: str) -> str:
        self.prompts.append(user_prompt)
        return self.responses.pop(0)


def run(model: ScriptedModel, evidence: EvidenceBundle | None = None):  # type: ignore[no-untyped-def]
    return run_investigation(
        "C-1", retrieve=lambda *_: evidence or bundle(), generate=model, model_id="gemini-test", now=lambda: FIXED_NOW
    )


def test_valid_brief_first_try() -> None:
    model = ScriptedModel(brief_json(["TX-0001", "RULE-FANIN-01"]))
    result = run(model)
    assert result.brief.case_id == "C-1"
    assert result.brief.model == "gemini-test"
    assert result.brief.run_at == FIXED_NOW
    assert result.brief.cached is False
    assert len(result.attempts) == 1
    assert [c.tool for c in result.evidence.calls] == ["detect_fan_in", "trace_funds"]


def test_prompt_contains_only_bundle_evidence() -> None:
    model = ScriptedModel(brief_json(["TX-0001"]))
    run(model)
    assert '"citable_evidence_ids": ["RULE-FANIN-01", "TX-0001", "TX-0002", "TX-0003", "TX-0004"]' in model.prompts[0]


def test_invented_citation_regenerates_once_then_passes() -> None:
    model = ScriptedModel(brief_json(["TX-9999"]), brief_json(["TX-0001"]))
    result = run(model)
    assert len(result.attempts) == 2
    assert result.attempts[0].problems == ["Cited ID 'TX-9999' is not in the evidence bundle."]
    assert "TX-9999" in model.prompts[1] and "rejected" in model.prompts[1]


def test_two_failures_raise_and_show_no_brief() -> None:
    model = ScriptedModel(brief_json(["TX-9999"]), brief_json(["TX-8888"]))
    with pytest.raises(InvestigationError) as exc:
        run(model)
    assert exc.value.kind == "validation"
    assert model.responses == []


def test_forbidden_language_triggers_regeneration() -> None:
    model = ScriptedModel(brief_json(["TX-0001"], text="A-07 is a fraudster."), brief_json(["TX-0001"]))
    assert len(run(model).attempts) == 2


def test_malformed_json_counts_as_failed_attempt() -> None:
    model = ScriptedModel("not json", brief_json(["TX-0001"]))
    result = run(model)
    assert result.attempts[0].problems[0].startswith("The response was not valid brief JSON")


def test_too_many_rounds_rejected_before_model_call() -> None:
    model = ScriptedModel()
    with pytest.raises(InvestigationError) as exc:
        run(model, bundle(rounds=MAX_TOOL_ROUNDS + 1))
    assert exc.value.kind == "too_many_rounds"
    assert model.prompts == []


def test_payload_cap_rejected_before_model_call() -> None:
    huge = ToolCall(tool="get_account_context", inputs={}, output={"blob": "x" * MAX_EVIDENCE_CHARS}, evidence_ids=frozenset({"TX-1"}))
    model = ScriptedModel()
    with pytest.raises(InvestigationError) as exc:
        run(model, EvidenceBundle(case_id="C-1", rounds=((huge,),)))
    assert exc.value.kind == "payload_too_large"
    assert model.prompts == []


def test_empty_evidence_rejected() -> None:
    with pytest.raises(InvestigationError) as exc:
        run(ScriptedModel(), EvidenceBundle(case_id="C-3", rounds=()))
    assert exc.value.kind == "validation"


# --- Gemini adapter error mapping (TC-009), no network ---

CONFIG = GeminiConfig(project="test-project", location="asia-southeast1", model="gemini-test")


def generator_raising(exc: Exception) -> GeminiBriefGenerator:
    def generate_content(**_: Any) -> None:
        raise exc

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    return GeminiBriefGenerator(CONFIG, client=client)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("exc", "kind"),
    [
        (httpx.ReadTimeout("timed out"), "timeout"),
        (httpx.ConnectError("unreachable"), "api"),
        (RefreshError("expired"), "credentials"),
        (ValueError("surprise"), "unexpected"),
        (errors.ClientError(403, {"error": {"code": 403, "status": "PERMISSION_DENIED", "message": "x"}}), "permission"),
        (errors.ClientError(404, {"error": {"code": 404, "status": "NOT_FOUND", "message": "x"}}), "not_found"),
        (errors.ClientError(429, {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "x"}}), "quota"),
        (errors.ServerError(503, {"error": {"code": 503, "status": "UNAVAILABLE", "message": "x"}}), "api"),
    ],
)
def test_gemini_errors_are_readable(exc: Exception, kind: str) -> None:
    with pytest.raises(InvestigationError) as raised:
        generator_raising(exc)("system", "prompt")
    assert raised.value.kind == kind
    assert raised.value.user_message


def test_missing_env_is_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GOOGLE_CLOUD_PROJECT", "VERTEX_LOCATION", "GEMINI_MODEL"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(InvestigationError) as exc:
        GeminiConfig.from_env()
    assert exc.value.kind == "config"


# --- Live Vertex AI call (spends quota): python -m pytest -m live ---


@pytest.mark.live
def test_live_gemini_returns_valid_brief() -> None:
    config = GeminiConfig.from_env()
    result = run_investigation("C-1", retrieve=lambda *_: bundle(), generate=GeminiBriefGenerator(config), model_id=config.model)
    assert result.brief.observations


def test_retriever_receives_round_cap() -> None:
    seen: list[int] = []

    def retrieve(case_id: str, max_rounds: int) -> EvidenceBundle:
        seen.append(max_rounds)
        return bundle()

    run_investigation("C-1", retrieve=retrieve, generate=ScriptedModel(brief_json(["TX-0001"])), model_id="m")
    assert seen == [MAX_TOOL_ROUNDS]


def test_client_timeout_is_30_seconds_in_ms() -> None:
    client = build_client(CONFIG)
    assert REQUEST_TIMEOUT_MS == 30_000
    assert client._api_client._http_options.timeout == 30_000
