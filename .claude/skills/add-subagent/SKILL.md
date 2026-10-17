---
name: add-subagent
description: Use when the user wants a new specialist agent in .claude/agents/, or when the same kind of delegated task has been requested three or more times. Writes a scoped subagent definition.
---

# Add a subagent

Only add one when a task recurs and benefits from isolated context or restricted tools.
Prefer a skill instead when the need is a *procedure* the main session should follow.

1. Check existing `.claude/agents/*.md` — if an agent's description overlaps, extend it instead.
2. Create `.claude/agents/<kebab-name>.md` with frontmatter:
   - `name`: same as the filename.
   - `description`: starts with "Use when/before/after …" and names concrete triggers. This
     line is how the agent gets chosen, so make it specific and non-overlapping.
   - `tools`: the minimum set. Reviewers and runners get no Edit/Write.
   - `model`: `inherit` unless there is a reason to pin one.
3. Body sections: **Purpose**, **Inputs** (which docs, by path), **Outputs** (exact format),
   **Caution** (what it must not do), **Done when** (observable stop condition).
4. Add the agent to the "Build agents" line in `AGENTS.md`.
