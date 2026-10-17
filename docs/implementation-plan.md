# Implementation Plan — TraceGuard

> Living execution ledger. Intent lives in the PRD, architecture in System Design, decisions in ADRs.

**Plan owner:** Shieryl
**Last checkpoint:** 2026-10-17 · TASK-000–006 done; all 3 cases on real graph evidence; next: live checks, deck numbers, video (TASK-007)

## 0. Rules
- One owner per task. Edit only your task's write scope.
- Avoid cross-task dependencies: code against agreed contracts and use fixtures until the real
  piece lands. TASK-004 builds against sample JSON shaped like System Design §3 until TASK-003 lands.
- Same file needed by two tasks → the plan owner splits it or schedules pairing.
- **Walking skeleton first:** no feature work merges before TASK-001 is live on Cloud Run.
- **Redeploy after every merged task** so the public URL never drifts far from `main`.
- **Feature freeze 2026-10-18 2 PM Manila.** Cut order: F-012 → F-011 → polish. Never cut F-005, F-006, F-010.

## 1. Task ledger
Statuses: `ready` · `in-progress` · `in-review` · `done` · `cut`

| ID | Title | Traces to | Owner | Status | Write scope | Evidence (PR / result) |
|---|---|---|---|---|---|---|
| TASK-000 | GCP project + billing + model check + IAM, per [setup.md §A](setup.md) (60–90 min timebox; fallback: upgrade Shieryl's account) | F-010, Q3, Q5 | Dzelle | done | none (GCP console) | 2026-10-17: personal billing account open + linked, budget alerts 50/90/100% set; run/cloudbuild/artifactregistry/aiplatform APIs enabled; `traceguard-run` SA has `roles/aiplatform.user` only; Q5 confirmed — live `gemini-3.5-flash` call in `asia-southeast1` → HTTP 200; Shieryl granted the 4 setup.md §A5 roles + `serviceAccountUser` on runtime SA (verified via `get-iam-policy`, no Owner/Editor) |
| TASK-001 | Walking skeleton deployed to Cloud Run (Streamlit button → live Gemini call) | F-010, BR-008 | Shieryl + Dzelle | done | `app.py`, `Dockerfile`, `requirements.txt`, `.dockerignore` | PR #1; public URL live; clean-browser Call Gemini → live response 5.9 s (2026-10-17) |
| TASK-002 | Fixture dataset C-1/C-2/C-3 (seeded generator) + expected outcomes | F-001, BR-001, BR-010 | Dzelle | done | `data/`, `tests/fixtures/` | PR #8; `data/generate.py --check` up to date; expected outcomes in `tests/fixtures/` cross-checked by brute force (2026-10-17) |
| TASK-003 | Graph loader (MultiDiGraph) + 5 tools + pytest | F-004, BR-003 | Dzelle | done | `traceguard/graph/`, `tests/` (except `tests/fixtures/`) | PR #9; 134 tests, mypy clean; tool outputs match C-1/C-2/C-3 fixtures (2026-10-17) |
| TASK-004 | Case queue, detail, timeline, graph view | F-001–F-003 | Shieryl | done | `traceguard/ui/` | PRs #3, #10; queue loads C-1..C-3 via graph loader; public-URL browser check passed |
| TASK-005 | AI investigation: retrieval → Gemini JSON brief → citation validation | F-005, F-006, BR-002/004/005/006/007 | Shieryl | done | `traceguard/ai/`, `tests/test_investigation.py`, `tests/test_citations.py`, `tests/test_language.py` | PR #2; validators + regenerate-once; live C-1 brief passed validation on first attempt |
| TASK-006 | Citation navigation, Markdown export, error states | F-007–F-009 | Shieryl | done | `traceguard/ui/` (after TASK-004 merges) | PRs #4, #10; citations, export, errors; wired to graph retriever |
| TASK-007 | Proposal PDF + 3-min video + form fields | submission | Shieryl (Dzelle: architecture slide) | ready | `submission/` | |

## 2. Timeline (Asia/Manila)
| When | Milestone |
|---|---|
| Oct 17 evening | Billing resolved; **TASK-001 live on Cloud Run**; TASK-002 started |
| Oct 18, 12 PM | Graph tools + UI + AI brief working on C-1 |
| **Oct 18, 2 PM** | **Feature freeze**; all 3 cases deployed |
| Oct 18, 2–6 PM | Verify cases, citation checks, clean-browser test of public URL (TC-010) |
| Oct 18, 6–9 PM | Proposal PDF, record + upload video, verify public access |
| **Oct 18, 10 PM** | **Submit** (internal target) |
| Oct 19, 2:29 AM | Portal closes (hard deadline). Buffer for upload or form issues only |
