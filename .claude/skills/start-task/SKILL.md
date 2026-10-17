---
name: start-task
description: Use when beginning work on a TASK-### from docs/implementation-plan.md, or when the user says "pick up a task" / "what should I work on". Claims the task, creates the branch, and loads only the docs that task needs.
---

# Start a task

1. Open `docs/implementation-plan.md` §1. If no task ID was given, list `ready` tasks and ask
   which one.
2. Confirm the task is `ready` and unowned (or owned by the current user).
3. Create branch `task/TASK-###-short-slug` from an up-to-date `main`.
4. Read the task's "Traces to" IDs: open only the owning docs for those IDs (via `docs/index.md` §0).
5. State back, before coding:
   - the goal in one sentence,
   - the write scope (files/folders you may touch),
   - the TC-### that will prove it works.
6. Work inside the write scope only. If you must touch another scope, stop and ask.
7. Before finishing: run the `test-runner` agent; run `rules-reviewer` if the change touches
   anything in PRD §6; update owning docs if behaviour changed; write an ADR if a decision was made.
8. Report evidence (commands + results, PR link) for the Evidence column. Do not change task
   status yourself if the plan has a designated plan owner.
