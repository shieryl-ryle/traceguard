# TraceGuard — Agent Guide

> Keep this file under ~150 lines. It routes; it does not explain. Details live in the owning doc.

## Project overview
TraceGuard is a graph-powered AI investigation assistant for fraud operations analysts at banks,
e-wallets, and fintechs. It traces suspicious fund movements across accounts and devices on
synthetic data and produces an evidence-linked case brief with Gemini on Vertex AI. It is an
investigation aid: it must **never** show an invented citation, declare anyone guilty, or let the
model compute numbers or decide flags (PRD BR-002, BR-003, BR-004). Hackathon: AI Builder Cup 2026, BFSI.

## Docs navigation (cheap — do this every task)
1. **[`docs/index.md`](./docs/index.md) §0** — find the *one* doc that owns the concern you are changing.
2. **Open only that owner.** Stop.
3. **"Why did we choose X?"** → read [`docs/adr/`](./docs/adr/) newest-first.

| Need | Open |
|------|------|
| What we build (features `F-###`, rules `BR-###`) | [PRD](./docs/prd.md) |
| How it's built | [System Design](./docs/system-design.md) |
| Tests (`TC-###`) | [QA Test Plan](./docs/qa-test-plan.md) |
| What to work on now (`TASK-###`) | [Implementation Plan](./docs/implementation-plan.md) |
| **Why / pivots / audit** | **[`docs/adr/`](./docs/adr/) only** |

## Decisions (ADRs)
Use the `write-adr` skill. Rules: one decision per file, never reuse a number, never edit an
Accepted ADR — supersede it. Newest Accepted ADR wins until the owning doc is reconciled.

## Architecture
One Python 3.12 Streamlit service (UI + backend) on Google Cloud Run. Synthetic dataset bundled in
the image and loaded into an in-memory NetworkX `MultiDiGraph`; no database, no state. Five
read-only deterministic graph tools feed a fixed retrieval workflow; Gemini on Vertex AI
(`google-genai`, `vertexai=True`, ADC via the `traceguard-run` service account) writes a structured
JSON brief that is citation-validated before display. See [System Design](./docs/system-design.md).

## Build & run
```
python -m pip install -r requirements.txt -r requirements-dev.txt
streamlit run app.py        # local Gemini calls need ADC: gcloud auth application-default login
```
Deploy: see [System Design §7](./docs/system-design.md). Redeploy after every merged task.

## Test
```
python -m mypy traceguard app.py
python -m pytest -m "not live"   # live Vertex tests: -m live (spends quota — only when asked)
```
All changes must pass tests before they are considered done.

## Working a task
Use the `start-task` skill: claim one `ready` `TASK-###`, branch `task/TASK-###-slug`, stay inside
its write scope.

## Code style & conventions
- Language / runtime: Python 3.12, type-hinted; English only (BR-009)
- Naming: soft IDs (`F-###`, `BR-###`, `TC-###`, `TASK-###`) stay stable once assigned
- Avoid: model-computed numbers or flags (BR-003); collapsing repeat transfers into one edge;
  free-form graph queries or model-generated code; API keys (BR-008); app code reading `tests/`
  (BR-010); "fraudster" / "guilty" / risk scores (BR-004); feature work before TASK-001 is deployed

## Stack currency (verify before coding — overrides training memory)
Confirm pinned versions in System Design before emitting framework APIs. If unverified, say so.

| ❌ Stale / from memory | ✅ Current (this project) | Why |
|------------------------|---------------------------|-----|
| `google-generativeai` / `import google.generativeai` | `google-genai`: `from google import genai`; `genai.Client(vertexai=True, project=..., location=...)` | [System Design §6](./docs/system-design.md) |
| `vertexai.generative_models.GenerativeModel` | `client.models.generate_content(model=GEMINI_MODEL, ...)` | [System Design §6](./docs/system-design.md) |
| Hard-coded model ID, `gemini-2.5-*` (retires 2026-10-20), or `GOOGLE_API_KEY` | `GEMINI_MODEL` + `VERTEX_LOCATION` env vars, ADC only | BR-008 |
| `nx.DiGraph` for transfers | `nx.MultiDiGraph`, one edge per `transaction_id` | PRD F-004 |
| Any path = money trail | Time-ordered paths only | PRD BR-003 |

## Ask before changing
- Business rules in `docs/prd.md` (`BR-###`)
- Thresholds, model IDs, pricing/quota assumptions — need an ADR
- Secrets / `.env*` — never commit

## Definition of done
- Build and tests pass.
- Code ties to an `F-###` where applicable; the **owning** doc is updated if intended behaviour changed.
- Real decision or pivot → new ADR.
- No secrets committed.

## Review helpers
Two optional local helpers (not stored in the repo): `rules-reviewer` (read-only, checks BR-### rules)
and `test-runner` (runs the gates, never fixes).

## References
[Docs index](./docs/index.md) · [ADRs](./docs/adr/) · [PRD](./docs/prd.md) ·
[System Design](./docs/system-design.md) · [QA](./docs/qa-test-plan.md)
