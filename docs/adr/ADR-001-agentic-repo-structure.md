# ADR-001 — Agent-readable repo structure

- **Date:** 2026-10-17
- **Status:** Accepted
- **Owners:** Shieryl, Dzelle
- **Related:** `AGENTS.md`, `docs/index.md`

### Context
Humans and AI coding agents both work in this repo. Agents start every session without memory of
prior chats, so intent, rules, and decisions must be discoverable from files alone.

### Why now
Without a structure from day one, facts get duplicated across docs, drift, and agents act on
stale copies.

### Options considered
1. **Single large README.** Pros: one file. Cons: loads everything into every session;
   becomes stale and contradictory as it grows.
2. **Thin router + one-owner docs + append-only ADRs + scoped agents/skills.** Pros: small context
   per task, one source of truth per concern, auditable decisions. Cons: needs discipline to keep
   owners reconciled.

### Decision
1. `AGENTS.md` is the router. Kept under ~150 lines.
2. `docs/index.md` §0 assigns one canonical owner per concern.
3. `docs/adr/` is the sole decision audit root; append-only.
4. Specialist helpers and repeatable procedures are local tooling, kept outside the repo.

### Why this option
It keeps per-task context small and makes "why" questions answerable without chat history.

### Overrides
- **Prior ADRs:** none
- **Docs to reconcile:** none
- **Out of scope:** tooling choices for the product itself

### Consequences
- **Easier:** onboarding people and agents; reviewing decisions.
- **Harder / owed:** every behaviour change must update its owning doc.
- **Follow-up:** none
