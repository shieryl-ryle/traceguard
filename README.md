# TraceGuard

A graph-powered AI investigation assistant that helps fraud analysts trace suspicious fund
movements across accounts and devices and produce an evidence-linked case brief.
Python 3.12 · Streamlit · NetworkX · Gemini on Vertex AI · Cloud Run. **All data is synthetic.**

Built for the AI Builder Cup 2026 (Google Cloud × Hack2skill), BFSI theme, by Shieryl and Dzelle.

## Start here
1. **Set up your machine and the Google Cloud project:** [docs/setup.md](docs/setup.md)
2. **Open the repo in Claude Code:** run `claude` in the repo folder. It reads
   [CLAUDE.md](CLAUDE.md) → [AGENTS.md](AGENTS.md) automatically.
3. **Pick up work:** type `/start-task` (or `/start-task TASK-002`). It claims the task,
   creates the branch, and loads only the docs that task needs.

## Docs
| Need | Open |
|---|---|
| What we build (features `F-###`, rules `BR-###`) | [docs/prd.md](docs/prd.md) |
| How it's built, IAM roles, deploy | [docs/system-design.md](docs/system-design.md) |
| Tests and gates | [docs/qa-test-plan.md](docs/qa-test-plan.md) |
| Who does what, timeline | [docs/implementation-plan.md](docs/implementation-plan.md) |
| Why we decided X | [docs/adr/](docs/adr/) |

## Claude Code helpers in this repo
| Command / agent | Use it to |
|---|---|
| `/start-task` | Begin a `TASK-###` on its own branch |
| `/write-adr` | Record a decision (model change, library choice, scope cut) |
| `/write-prd` | Revise features or business rules |
| `rules-reviewer` agent | Check a diff against BR-001…BR-010 before merging |
| `test-runner` agent | Run the test gates and report results |
