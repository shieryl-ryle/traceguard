# Agentic Repo Starter

A project skeleton that AI coding agents (Claude Code, and any tool that reads `AGENTS.md`) can
navigate without chat history: a thin router file, one-owner docs, append-only decision records,
and scoped subagents and skills.

## Use it

1. Create a new repo from this one (GitHub "Use this template", or copy the folder and `git init`).
2. Open it in Claude Code and run: `/bootstrap-project`
   The skill interviews you and fills every `{{placeholder}}`.
3. Start work with `/start-task`. Record decisions with `/write-adr`.

## What's inside

```
CLAUDE.md                      → points to AGENTS.md (one instruction source for every tool)
AGENTS.md                      → router: where to look, commands, rules, definition of done
docs/
  index.md                     → §0 "one fact, one home" ownership map + ID conventions
  prd.md                       → features F-###, business rules BR-###
  system-design.md             → architecture, integrations, security, stack currency
  qa-test-plan.md              → gates, TC-### test cases, exit criteria
  implementation-plan.md       → TASK-### ledger with owners and write scopes
  adr/                         → append-only decision records (template + ADR-001)
.claude/
  agents/                      → subagents: separate workers with restricted tools
    rules-reviewer.md          →   read-only diff review against BR-### rules
    test-runner.md             →   runs gates, reports evidence, never fixes
  skills/                      → procedures loaded into the main session on demand
    bootstrap-project/         →   fill the template (run once)
    start-task/                →   claim TASK-###, branch, load only needed docs
    write-adr/                 →   create an ADR correctly
    add-subagent/              →   add a new specialist agent with the right shape
```

## Subagent or skill?

| | Subagent (`.claude/agents/*.md`) | Skill (`.claude/skills/*/SKILL.md`) |
|---|---|---|
| Runs | In its own context, returns a result | Inside the current session |
| Best for | Isolated jobs: review, test runs, a specialist build | Repeatable procedures and checklists |
| Tool limits | Yes, via `tools:` | Inherits the session's tools |

In both, the `description` frontmatter decides when it is used — write it as "Use when …" with
concrete triggers.

## Principles

- **Route, don't restate.** `AGENTS.md` stays short; details live in exactly one owning doc.
- **Decisions are append-only.** Never edit an Accepted ADR; supersede it.
- **Stable IDs** (`F`, `BR`, `TC`, `TASK`, `ADR`) link intent, rules, tests, and work.
- **Start small.** Add docs, agents, and skills only when a real need recurs.

## Reuse across all projects

Generic agents and skills can also live in `~/.claude/agents/` and `~/.claude/skills/` to apply to
every repo on your machine. Keep project-specific rules (the BR-### checklist) in each repo.
