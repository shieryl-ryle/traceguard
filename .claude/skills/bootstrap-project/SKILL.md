---
name: bootstrap-project
description: Use once, right after creating a repo from this starter template, or when the user says "set up this template" / "fill in the project docs". Interviews the user and replaces every {{placeholder}} in AGENTS.md and docs/.
---

# Bootstrap a project from the starter

1. Find every placeholder: search for `{{` across `AGENTS.md`, `docs/`, and `.claude/`.
2. Interview the user in small batches (max 4 questions at a time), in this order:
   1. Name, one-paragraph overview, target users.
   2. Stack: language/runtime, framework, hosting, data store, external APIs (with versions).
   3. Commands: install, dev, typecheck, test, e2e.
   4. The 3–10 business rules that must never break (become BR-###).
   5. First 3–5 features (become F-###) and what is explicitly out of scope.
3. Push back on vague rules ("be secure") — rewrite them as testable statements.
4. Fill `docs/prd.md`, `docs/system-design.md`, `docs/qa-test-plan.md` (one TC per BR and per
   Must feature), and `AGENTS.md`. Verify stack versions against official docs; mark any you could
   not verify as `unverified`.
5. Add project-specific checks to `.claude/agents/rules-reviewer.md`, each tied to a BR-###.
6. Fill dates in `docs/index.md` and `docs/adr/ADR-001-agentic-repo-structure.md`.
7. Seed `docs/implementation-plan.md` with 3–8 first tasks.
8. Re-search for `{{` and report anything left unfilled. Delete this skill folder if the user
   agrees it is no longer needed.
