"""AI investigation section (F-005, F-006, F-007, F-008, F-009).

Runs the fixed workflow on button press, shows the tool log, rule flags from tool output, and the
validated brief. Evidence-ID buttons set the citation highlight used by the graph and timeline.
Errors are shown inline; the graph and timeline above keep working (F-009).
"""

from dataclasses import dataclass

import streamlit as st

from traceguard.ai import InvestigationError, InvestigationResult, Statement, run_investigation
from traceguard.ai.gemini import GeminiBriefGenerator, GeminiConfig
from traceguard.ai.investigate import Retriever
from traceguard.graph.retriever import graph_retriever
from traceguard.ui.citations import highlight_for, rule_flags, tool_contrasts
from traceguard.ui.export import brief_to_markdown
from traceguard.ui.models import CaseView

CITED_KEY = "cited_evidence_id"
RETRIEVER: Retriever = graph_retriever
EVIDENCE_SOURCE = "Graph tools (deterministic, computed by the backend from the bundled dataset)"
FLAGS_HEADING = "Rule flags (deterministic)"
WORKFLOW_SOURCE = "runs a fixed set of graph tools for this case"


@dataclass(frozen=True)
class Outcome:
    result: InvestigationResult | None = None
    error: InvestigationError | None = None


def _state_key(case_id: str) -> str:
    return f"investigation:{case_id}"


def run_ai_investigation(case_id: str) -> Outcome:
    try:
        config = GeminiConfig.from_env()
        result = run_investigation(
            case_id, retrieve=RETRIEVER, generate=GeminiBriefGenerator(config), model_id=config.model
        )
    except InvestigationError as exc:
        return Outcome(error=exc)
    return Outcome(result=result)


def citation_highlight(view: CaseView) -> frozenset[str]:
    outcome = st.session_state.get(_state_key(view.case.case_id))
    cited = st.session_state.get(CITED_KEY)
    if not isinstance(outcome, Outcome) or outcome.result is None or not isinstance(cited, str):
        return frozenset()
    return highlight_for(outcome.result.evidence, cited)


def _cite(evidence_id: str) -> None:
    st.session_state[CITED_KEY] = evidence_id


def cited_record_lines(view: CaseView, ids: frozenset[str]) -> list[str]:
    """The cited records themselves, shown next to the brief so the analyst can verify in place."""
    lines = [
        f"- `{t.transaction_id}` {t.sender_account_id} → {t.receiver_account_id} · "
        f"{t.currency} {t.amount:,.2f} · {t.timestamp.isoformat(timespec='minutes')}"
        for t in sorted(view.transactions, key=lambda t: t.timestamp)
        if t.transaction_id in ids
    ]
    lines += [
        f"- `{d.relationship_id}` {d.account_id} on device {d.device_id} · seen {d.observed_at.isoformat(timespec='minutes')}"
        for d in view.device_links
        if d.relationship_id in ids
    ]
    return lines or ["- No matching records in this case view."]


def _clear_cite() -> None:
    st.session_state.pop(CITED_KEY, None)


def _statement(s: Statement, key: str) -> None:
    st.markdown(f"- {s.text}")
    if s.evidence_ids:
        row = st.container(horizontal=True, gap="small")
        for evidence_id in s.evidence_ids:
            row.button(
                evidence_id,
                key=f"{key}:{evidence_id}",
                type="tertiary",
                icon=":material/link:",
                on_click=_cite,
                args=(evidence_id,),
                help="Highlight this evidence in the graph and timeline",
            )


def _render_result(view: CaseView, result: InvestigationResult) -> None:
    brief = result.brief
    st.success("Live AI output" if not brief.cached else "Cached AI output", icon=":material/smart_toy:")
    st.caption(
        f"Model `{brief.model}` · generated {brief.run_at.isoformat(timespec='seconds')} · "
        f"{len(result.attempts)} attempt(s) · citations validated against retrieved evidence"
    )
    st.caption(f"Evidence source: {EVIDENCE_SOURCE}")

    st.markdown(f"**{FLAGS_HEADING}**")
    for flag in rule_flags(result.evidence):
        params = ", ".join(f"{k} = {v}" for k, v in flag.config.items())
        label = "Pattern warrants review" if flag.matched else "Rule not matched"
        st.markdown(f"- `{flag.rule_id}` — {label} ({params}). {flag.explanation}")

    contrasts = tool_contrasts(result.evidence)
    if contrasts:
        st.markdown("**Contrasts (deterministic, from graph tools)**")
        for i, c in enumerate(contrasts):
            _statement(Statement(text=c.text, evidence_ids=list(c.evidence_ids)), f"con{i}")

    st.markdown("**Observations**")
    for i, s in enumerate(brief.observations):
        _statement(s, f"obs{i}")
    st.markdown("**Counterevidence**")
    for i, s in enumerate(brief.counterevidence):
        _statement(s, f"ctr{i}")
    if not brief.counterevidence:
        st.caption("None stated.")
    st.markdown("**Unknowns**")
    st.markdown("\n".join(f"- {u}" for u in brief.unknowns))
    st.markdown("**Suggested manual checks**")
    st.markdown("\n".join(f"- {c}" for c in brief.suggested_checks))

    cited = st.session_state.get(CITED_KEY)
    if isinstance(cited, str):
        st.info(f"Highlighting evidence for `{cited}` in the graph and timeline above.", icon=":material/link:")
        st.markdown("\n".join(cited_record_lines(view, highlight_for(result.evidence, cited))))
        st.button("Clear highlight", on_click=_clear_cite)

    st.download_button(
        "Export brief (Markdown)",
        data=brief_to_markdown(brief, result.evidence, view.case.title, EVIDENCE_SOURCE, FLAGS_HEADING),
        file_name=f"traceguard-{brief.case_id}-brief.md",
        mime="text/markdown",
        icon=":material/download:",
    )


def render_investigation(view: CaseView) -> None:
    st.subheader("AI investigation")
    st.caption(
        f"Fixed workflow: the app {WORKFLOW_SOURCE}, then Gemini explains the results. "
        "The model does not choose tools, compute figures, or decide flags."
    )
    key = _state_key(view.case.case_id)
    if st.button("Run AI investigation", type="primary", icon=":material/search:"):
        st.session_state.pop(CITED_KEY, None)
        with st.spinner("Retrieving evidence and asking Gemini…"):
            st.session_state[key] = run_ai_investigation(view.case.case_id)

    outcome = st.session_state.get(key)
    if not isinstance(outcome, Outcome):
        return
    if outcome.error is not None:
        st.error(outcome.error.user_message, icon=":material/error:")
        st.caption("The graph and timeline above are still available.")
        return
    if outcome.result is not None:
        with st.expander("Tool and retrieval log"):
            st.caption(EVIDENCE_SOURCE)
            for n, round_ in enumerate(outcome.result.evidence.rounds, start=1):
                for call in round_:
                    st.markdown(
                        f"Round {n} · `{call.tool}` {call.inputs} → " + ", ".join(sorted(call.evidence_ids))
                    )
            for attempt in outcome.result.attempts:
                if attempt.problems:
                    st.caption(f"Attempt {attempt.number} rejected: " + "; ".join(attempt.problems))
        _render_result(view, outcome.result)
