---
name: write-prd
description: Use when the user wants to write, draft, build, or revise a PRD / product requirements document, define features or business rules, or turn a raw idea into a spec before building. Also run it as the first step of bootstrap-project. Interviews the user, challenges weak answers, and writes docs/prd.md.
---

# Write a PRD

Goal: turn an idea into `docs/prd.md` that an agent can build and test against without asking
follow-up questions. Structure: [template.md](template.md).

## Ground rules
- **Interview, don't invent.** Every fact comes from the user or a cited source. Unknowns go to
  §13 Open questions — never fill them with guesses.
- **Max 4 questions per message.** Offer 2–3 concrete options when the user is unsure.
- **Push back** (one sentence why + a sharper alternative) on:
  - vague rules ("secure", "fast", "user-friendly") → rewrite as testable statements;
  - vanity metrics (sign-ups, page views) → outcome metrics tied to the problem;
  - scope creep → move to §11 Non-goals or a later phase;
  - features with no user story behind them.
- If a `docs/prd.md` already exists with real content, **revise** it: keep existing IDs, append
  new ones, mark removed items `(cut)` — never renumber.

## Interview rounds

1. **Problem & context** — Who has the problem? How do they cope today? Why now? Any hard
   constraints (deadline, budget, platform, legal/privacy, client requirements)?
2. **Users** — 1–3 personas: goal, context, constraint. Which one is primary?
3. **Outcomes** — What changes for the primary user if this works? How will we measure it?
   (→ §3 Goals, §10 Success metrics)
4. **Features** — List what the user wants built, then for each: the user story it serves and
   priority (P0 must-ship / P1 should / P2 later). Challenge any P0 that does not serve the
   primary persona's core job. Aim for ≤ 7 P0s.
5. **Rules that must never break** — data, privacy, consent, money, safety, AI behaviour,
   tone. Each becomes a testable `BR-###`.
6. **Out of scope, risks, dependencies** — What are we explicitly *not* doing? What could
   kill it? What external services/data/people does it depend on?

After round 6, show a one-screen summary (problem, primary persona, P0 list, top BRs, metrics)
and ask for corrections **before** writing the file.

## Writing the file

1. Fill [template.md](template.md) into `docs/prd.md`. Delete template sections that truly do not
   apply rather than leaving them empty — but keep §6 Business rules and §8 Acceptance criteria.
2. IDs: `F-###` features, `UJ-###` journeys, `BR-###` rules, starting at 001, zero-padded.
3. Every P0 feature has ≥ 1 acceptance criterion; every BR is phrased so a test or reviewer can
   say pass/fail.
4. Fill §14 Traceability: each F-### → user story → BR-### it must obey → TC-### placeholder.
5. Set Status to `Draft v0.1` (or bump the minor version on revision) and today's date.

## After writing
- If `docs/qa-test-plan.md` exists, offer to add one `TC-###` per P0 feature and per BR.
- If `.claude/agents/rules-reviewer.md` exists, offer to add the BR checks to its Checklist.
- If a scope decision was contested during the interview, offer to record it with `write-adr`.
- Report: counts (personas, F, BR), the open questions, and the single biggest risk you see.
