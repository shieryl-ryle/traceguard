# Implementation Plan — {{PROJECT_NAME}}

> Living execution ledger. Intent lives in the PRD, architecture in System Design, decisions in ADRs.

**Plan owner:** {{name}}
**Last checkpoint:** {{YYYY-MM-DD}} · {{one-line state}}

## 0. Rules
- One owner per task. Edit only your task's write scope.
- Avoid cross-task dependencies: code against agreed contracts and use fixtures until the real
  piece lands.
- Same file needed by two tasks → the plan owner splits it or schedules pairing.

## 1. Task ledger
Statuses: `ready` · `in-progress` · `in-review` · `done` · `cut`

| ID | Title | Traces to | Owner | Status | Write scope | Evidence (PR / result) |
|---|---|---|---|---|---|---|
| TASK-001 | Scaffold repo and CI | infra | {{name}} | ready | `/`, `.github/` | |
