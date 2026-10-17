---
name: write-adr
description: Use when a product, architecture, security, or plan decision has been made or changed, or when someone asks "why do we do it this way?" and no ADR answers it. Creates a new append-only ADR in docs/adr/.
---

# Write an ADR

1. List `docs/adr/` and take the next unused number (never reuse or renumber; check for numbers
   reserved in open tasks).
2. Copy `docs/adr/ADR-000-template.md` to `docs/adr/ADR-NNN-short-slug.md`.
3. Fill every section. Require at least two real options — "do nothing" counts if it is genuine.
4. Write the Decision as numbered, testable statements.
5. **Never edit an existing Accepted ADR.** If this replaces one, say so in the new ADR's
   Overrides section ("Supersedes ADR-###"); the only permitted change to the old file is its
   Status line → `Superseded by ADR-NNN`.
6. List every owning doc that now disagrees under "Docs to reconcile", and either update them in
   the same change or add a TASK-### for it.
7. Status starts as `Proposed` unless the user confirms the decision is made.
