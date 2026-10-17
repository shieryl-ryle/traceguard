# Implementation Plan — TraceGuard

> Living execution ledger. Intent lives in the PRD, architecture in System Design, decisions in ADRs.

**Plan owner:** Shieryl
**Last checkpoint:** 2026-10-17 · Docs bootstrapped; no code yet. Next: billing check + TASK-001.

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
| TASK-000 | GCP project + billing + model check + IAM, per [setup.md §A](setup.md) (60–90 min timebox; fallback: upgrade Shieryl's account) | F-010, Q3, Q5 | Dzelle | ready | none (GCP console) | 2026-10-17: personal billing account open + linked, budget alerts 50/90/100% set; run/cloudbuild/artifactregistry/aiplatform APIs enabled; `traceguard-run` SA has `roles/aiplatform.user` only; Q5 confirmed — live `gemini-3.5-flash` call in `asia-southeast1` → HTTP 200; Shieryl granted the 4 setup.md §A5 roles + `serviceAccountUser` on runtime SA (verified via `get-iam-policy`, no Owner/Editor) |
| TASK-001 | Walking skeleton deployed to Cloud Run (Streamlit button → live Gemini call) | F-010, BR-008 | Shieryl + Dzelle | ready | `app.py`, `Dockerfile`, `requirements.txt`, `.dockerignore` | |
| TASK-002 | Fixture dataset C-1/C-2/C-3 (seeded generator) + expected outcomes | F-001, BR-001, BR-010 | Dzelle | ready | `data/`, `tests/fixtures/` | |
| TASK-003 | Graph loader (MultiDiGraph) + 5 tools + pytest | F-004, BR-003 | Dzelle | ready | `traceguard/graph/`, `tests/` (except `tests/fixtures/`) | |
| TASK-004 | Case queue, detail, timeline, graph view | F-001–F-003 | Shieryl | ready | `traceguard/ui/` | |
| TASK-005 | AI investigation: retrieval → Gemini JSON brief → citation validation | F-005, F-006, BR-002/004/005/006/007 | Shieryl | ready | `traceguard/ai/`, `tests/test_investigation.py`, `tests/test_citations.py`, `tests/test_language.py` | |
| TASK-006 | Citation navigation, Markdown export, error states | F-007–F-009 | Shieryl | ready | `traceguard/ui/` (after TASK-004 merges) | |
| TASK-007 | Proposal PDF + 3-min video + form fields | submission | Shieryl (Dzelle: architecture slide) | ready | `submission/` | |

## 2. Timeline (Asia/Manila)
| When | Milestone |
|---|---|
| Oct 17 evening | Billing resolved; **TASK-001 live on Cloud Run**; TASK-002 started |
| Oct 18, 12 PM | Graph tools + UI + AI brief working on C-1 |
| **Oct 18, 2 PM** | **Feature freeze**; all 3 cases deployed |
| Oct 18, 2–6 PM | Verify cases, citation checks, clean-browser test of public URL (TC-010) |
| Oct 18, 6–9 PM | Proposal PDF, record + upload video, verify public access |
| **Oct 18, 10 PM** | **Submit** |
