# Build History — TraceGuard

TraceGuard was built in two days, 17–18 October 2026, by a team of two for the AI Builder Cup 2026.
This page records how the work was split and where each piece landed. Product intent lives in the
[PRD](prd.md), architecture in [System Design](system-design.md), and decisions in the [ADRs](adr/).

## How we worked
- **One owner per task,** each on its own branch and pull request, with tests passing before merge.
- **Walking skeleton first:** a public Cloud Run URL making a real Gemini call went live before any
  feature work, so deployment risk was retired on day one.
- **Contracts before code:** the UI and AI layers were built against agreed data shapes
  (System Design §2–3) while the graph layer was in progress, then wired to the real tools.
- **Redeploy after every merge,** so the public URL never drifted far from `main`.
- **Feature freeze** on 18 October at 2 PM Manila. After that, only fixes and submission assets.

## Tasks
| ID | What | Owner | Pull requests | Outcome |
|---|---|---|---|---|
| TASK-000 | Google Cloud project, billing with budget alerts, model check, least-privilege IAM | Dzelle | #6, #7 | APIs enabled; runtime service account holds `roles/aiplatform.user` only; `gemini-3.5-flash` confirmed in `asia-southeast1` with a live call |
| TASK-001 | Walking skeleton on Cloud Run: a button that calls Gemini on Vertex AI | Shieryl, Dzelle | #1 | Public URL live; first live response in 5.9 s |
| TASK-002 | Seeded synthetic dataset (cases C-1, C-2, C-3) and expected outcomes | Dzelle | #8 | Generator reproducible; expected outcomes cross-checked by brute force ([ADR-003](adr/ADR-003-rule-windows-and-thresholds.md)) |
| TASK-003 | Graph loader (MultiDiGraph), five deterministic tools, retriever, contrasts | Dzelle | #9, #16, #19 | Tool outputs match the fixtures for all three cases |
| TASK-004 | Case queue, timeline and interactive graph | Shieryl | #3, #10 | Graph selection returns to Python ([ADR-002](adr/ADR-002-graph-view-streamlit-agraph.md)) |
| TASK-005 | AI brief: schema, prompt, validators, regenerate once | Shieryl | #2, #13, #15 | A live C-1 brief passed validation on the first attempt |
| TASK-006 | Citation navigation, Markdown export, readable errors | Shieryl | #4, #10 | Every citation highlights its records on the graph and timeline |
| TASK-007 | Proposal deck, demo video, submission form | Shieryl (Dzelle: architecture and results slides) | #5, #11, #14, #18 | Submitted on 18 October 2026 |

**Additions after the core build:** LOW thinking for 3–9 s briefs (#12), the Verified-before-display
panel (#20), graph and brief side by side (#21), and the case-scoped follow-up question, F-011 (#22).

**Cut:** F-012 (CSV import and cycle detection), deliberately, to protect the P0 features.
