"""Markdown export of a validated brief (F-008)."""

from traceguard.ai.evidence import EvidenceBundle
from traceguard.ai.schema import Brief, Statement
from traceguard.ui.citations import rule_flags


def _statement(s: Statement) -> str:
    ids = ", ".join(f"`{e}`" for e in s.evidence_ids)
    return f"- {s.text}" + (f" — evidence: {ids}" if ids else "")


def _bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None stated."]


def brief_to_markdown(
    brief: Brief, evidence: EvidenceBundle, title: str, evidence_source: str, flags_heading: str
) -> str:
    output_label = "Cached AI output" if brief.cached else "Live AI output"
    lines = [
        f"# TraceGuard case brief — {brief.case_id}: {title}",
        "",
        "> **Synthetic data.** Investigation aid only: this brief is not a decision, does not block",
        "> transfers, and is not a regulatory report. Rule flags come from tool output, not the model.",
        "",
        f"- **Model:** {brief.model} ({output_label})",
        f"- **Generated:** {brief.run_at.isoformat(timespec='seconds')}",
        f"- **Evidence source:** {evidence_source}",
        "",
        f"## {flags_heading}",
    ]
    flags = rule_flags(evidence)
    for flag in flags:
        status = "matched" if flag.matched else "not matched"
        params = ", ".join(f"{k}={v}" for k, v in flag.config.items())
        lines.append(f"- `{flag.rule_id}` {status} ({params}). {flag.explanation}")
    if not flags:
        lines.append("- No rule results.")
    lines += ["", "## Observations", *(_statement(s) for s in brief.observations)]
    lines += ["", "## Counterevidence", *([_statement(s) for s in brief.counterevidence] or ["- None stated."])]
    lines += ["", "## Unknowns", *_bullets(brief.unknowns)]
    lines += ["", "## Suggested manual checks", *_bullets(brief.suggested_checks)]
    lines += ["", "## Evidence retrieved", *(f"- `{c.tool}` → {', '.join(sorted(c.evidence_ids))}" for c in evidence.calls)]
    return "\n".join(lines) + "\n"
