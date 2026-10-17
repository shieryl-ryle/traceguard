"""AI investigation section (F-005, F-006, F-007, F-008, F-009).

Runs the fixed workflow on button press, shows the tool log, rule flags from tool output, and the
validated brief. Evidence-ID buttons set the citation highlight used by the graph and timeline.
Errors are shown inline; the graph and timeline above keep working (F-009).
"""

from dataclasses import dataclass

import streamlit as st

from traceguard.ai import Brief, InvestigationError, InvestigationResult, Statement, run_investigation
from traceguard.ai.followup import MAX_QUESTION_CHARS, FollowUpAnswer, FollowUpResult, ask_follow_up
from traceguard.ai.gemini import GeminiBriefGenerator, GeminiConfig
from traceguard.ai.investigate import Retriever
from traceguard.graph.retriever import graph_retriever
from traceguard.ai.validate import validation_summary
from traceguard.ui.citations import highlight_for, rule_description, rule_flags, tool_contrasts
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


def render_verified_panel(brief: Brief, result: InvestigationResult) -> None:
    """Shows what was checked before this brief was displayed (BR-002, BR-003, BR-004)."""
    summary = validation_summary(brief, result.evidence)
    rejected = sum(1 for a in result.attempts if a.problems)
    with st.container(border=True):
        st.markdown(":material/verified: **Verified before display**")
        with st.container(horizontal=True, gap="small"):
            st.badge(f"{summary.citations} citations ({summary.distinct_citations} records) found in the evidence",
                     icon=":material/check:", color="green")
            st.badge(f"{summary.figures} figures matched to tool output", icon=":material/check:", color="green")
            st.badge(f"{summary.ids_in_text} IDs in the text checked", icon=":material/check:", color="green")
            st.badge("No accusatory or probability wording", icon=":material/check:", color="green")
            st.badge(f"Attempt {len(result.attempts)} of 2" + (f" ({rejected} rejected)" if rejected else ""),
                     icon=":material/replay:", color="blue")
        st.caption("Any brief that cites an unknown record, states a figure not in the tool output, or uses "
                   "accusatory wording is regenerated once, then blocked.")


def _follow_up_key(case_id: str) -> str:
    return f"follow_up:{case_id}"


def run_follow_up(question: str, result: InvestigationResult) -> FollowUpResult | InvestigationError:
    try:
        config = GeminiConfig.from_env()
        return ask_follow_up(question, result.evidence, GeminiBriefGenerator(config, schema=FollowUpAnswer))
    except InvestigationError as exc:
        return exc


def render_follow_up(view: CaseView, result: InvestigationResult) -> None:
    """F-011: one case-scoped question, answered from the same evidence with the same checks."""
    st.markdown("**Ask a follow-up about this case**")
    st.caption("Answered only from this case's tool results, with the same citation and wording checks. "
               "Questions the data can't answer are refused, not guessed.")
    key = _follow_up_key(view.case.case_id)
    with st.form(f"follow_up_form:{view.case.case_id}", clear_on_submit=False, border=False):
        question = st.text_input("Question", max_chars=MAX_QUESTION_CHARS, label_visibility="collapsed",
                                 placeholder="e.g. Why is A-08 relevant? or Who owns A-22?")
        asked = st.form_submit_button("Ask", icon=":material/help:")
    if asked:
        with st.spinner("Asking Gemini about this case…"):
            st.session_state[key] = run_follow_up(question, result)
    outcome = st.session_state.get(key)
    if isinstance(outcome, InvestigationError):
        st.error(outcome.user_message, icon=":material/error:")
    elif isinstance(outcome, FollowUpResult):
        st.markdown(f"*Q: {outcome.question}*")
        if outcome.answer.answerable:
            st.badge("Answered from case evidence · verified", icon=":material/verified:", color="green")
            _statement(Statement(text=outcome.answer.text, evidence_ids=outcome.answer.evidence_ids), "fu")
        else:
            st.badge("Not answerable from this data", icon=":material/block:", color="gray")
            st.markdown(outcome.answer.text)


def _render_result(view: CaseView, result: InvestigationResult) -> None:
    brief = result.brief
    st.success("Live AI output" if not brief.cached else "Cached AI output", icon=":material/smart_toy:")
    st.caption(
        f"Model `{brief.model}` · generated {brief.run_at.isoformat(timespec='seconds')} · "
        f"evidence: {EVIDENCE_SOURCE}"
    )
    render_verified_panel(brief, result)

    st.markdown(f"**{FLAGS_HEADING}**")
    for flag in rule_flags(result.evidence):
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            st.markdown(f"`{flag.rule_id}`")
            if flag.matched:
                st.badge("Pattern warrants review", icon=":material/flag:", color="red")
            else:
                st.badge("Rule not matched", icon=":material/remove:", color="gray")
        st.caption(f"{rule_description(flag)}. {flag.explanation}")

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
    render_follow_up(view, result)


def render_investigation(view: CaseView) -> None:
    st.subheader("AI investigation")
    st.caption(
        f"Fixed workflow: the app {WORKFLOW_SOURCE}, then Gemini explains the results. "
        "The model does not choose tools, compute figures, or decide flags."
    )
    key = _state_key(view.case.case_id)
    if st.button("Run AI investigation", type="primary", icon=":material/search:"):
        st.session_state.pop(CITED_KEY, None)
        st.session_state.pop(_follow_up_key(view.case.case_id), None)
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
