# PRD — {{PROJECT_NAME}}

**Status:** {{Draft v0.1}} · **Owner:** {{name}} · **Last updated:** {{YYYY-MM-DD}}

**Conventions.** `F-###` features, `UJ-###` user journeys, `BR-###` business rules. Acceptance
criteria are plain, testable bullets. IDs are never renumbered; removed items are marked `(cut)`.

**Sources.**
| Source | Used for |
|---|---|
| {{interview with owner, client brief, research link}} | {{sections}} |

---

## 1. Problem
{{Who has the problem, how they cope today, what that costs them. 3–6 sentences.}}

## 2. Context & constraints
- **Why now:** {{trigger}}
- **Deadline / budget:** {{…}}
- **Platform:** {{web / mobile / API …}}
- **Legal / privacy:** {{GDPR, local law, consent needs}}

## 3. Goals
| # | Goal (outcome, not output) | Measured by (§10) |
|---|---|---|
| G1 | {{…}} | {{metric}} |

## 4. Personas
| Persona | Goal | Context | Constraint | Primary? |
|---|---|---|---|---|
| {{…}} | {{…}} | {{…}} | {{…}} | ✅ |

## 5. Features & user stories
| ID | Feature | User story ("As a…, I want…, so that…") | Priority |
|---|---|---|---|
| F-001 | {{…}} | {{…}} | P0 |

**Hard cuts (this phase):** {{feature — reason}}

## 6. Business rules
Testable statements. Reviewers and agents check every diff against these.

### {{Group, e.g. Data & privacy}}
| ID | Rule | Applies to |
|---|---|---|
| BR-001 | {{e.g. "A user's entries are never visible to another account unless shared explicitly."}} | F-### |

## 7. User journeys
### UJ-001 — {{name}}
1. {{step}}
2. {{step}}
- **Edge cases:** {{empty state, error, offline, permission denied}}

## 8. Acceptance criteria
### F-001 — {{feature}}
- [ ] {{Given/when/then or plain testable bullet}}

## 9. Vocabulary
| Term | Meaning in this product |
|---|---|
| {{…}} | {{…}} |

## 10. Success metrics
| Metric | Target | Why it matters (not a vanity metric) |
|---|---|---|
| {{…}} | {{…}} | {{…}} |

## 11. Non-goals
- {{What we are deliberately not doing, and why}}

## 12. Risks & dependencies
| Risk / dependency | Impact | Mitigation |
|---|---|---|
| {{…}} | {{…}} | {{…}} |

## 13. Open questions
| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | {{…}} | {{…}} | {{F-### / nothing}} |

## 14. Traceability
| Feature | Story / journey | Rules | Tests |
|---|---|---|---|
| F-001 | UJ-001 | BR-001 | TC-001 |
