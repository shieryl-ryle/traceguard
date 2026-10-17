# {{PROJECT_NAME}} — Agent Guide

> Keep this file under ~150 lines. It routes; it does not explain. Details live in the owning doc.

## Project overview
{{Two or three sentences: who it is for, what it does, the one thing it must never do.}}

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
{{One paragraph: runtime, hosting, data store, external services. Link System Design.}}

## Build & run
```
{{install command}}
{{dev command}}
```

## Test
```
{{typecheck command}}
{{test command}}
```
All changes must pass tests before they are considered done.

## Working a task
Use the `start-task` skill: claim one `ready` `TASK-###`, branch `task/TASK-###-slug`, stay inside
its write scope.

## Code style & conventions
- Language / runtime: {{e.g. TypeScript, Node >= 22}}
- Naming: soft IDs (`F-###`, `BR-###`, `TC-###`, `TASK-###`) stay stable once assigned
- Avoid: {{project-specific anti-patterns}}

## Stack currency (verify before coding — overrides training memory)
Confirm pinned versions in System Design before emitting framework APIs. If unverified, say so.

| ❌ Stale / from memory | ✅ Current (this project) | Why |
|------------------------|---------------------------|-----|
| {{old pattern}} | {{current pattern}} | {{ADR-### or doc link}} |

## Ask before changing
- Business rules in `docs/prd.md` (`BR-###`)
- Thresholds, model IDs, pricing/quota assumptions — need an ADR
- Secrets / `.env*` — never commit

## Definition of done
- Build and tests pass.
- Code ties to an `F-###` where applicable; the **owning** doc is updated if intended behaviour changed.
- Real decision or pivot → new ADR.
- No secrets committed.

## Build agents
`.claude/agents/`: `rules-reviewer` (read-only, checks BR-### rules), `test-runner` (runs gates,
never fixes). Add more with the `add-subagent` skill only when a task recurs.

## References
[Docs index](./docs/index.md) · [ADRs](./docs/adr/) · [PRD](./docs/prd.md) ·
[System Design](./docs/system-design.md) · [QA](./docs/qa-test-plan.md)
