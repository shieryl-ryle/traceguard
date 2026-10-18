# Documentation Index — TraceGuard

**Maintained by:** Team Chilli
**Last updated:** 2026-10-18

## 0. Source-of-truth map (one fact, one home)

Each concern has exactly one canonical owner. Other docs **link** to it instead of restating it.
When two docs disagree, the owner wins until the other is reconciled.

| Concern | Canonical owner | Note |
|---|---|---|
| Decision *why* / pivots (**audit root**) | [ADRs](adr/) | append-only; newest Accepted wins |
| What we build: features `F-###`, business rules `BR-###` | [PRD](prd.md) | |
| How it's built: architecture, integrations, security, stack versions | [System Design](system-design.md) | |
| Tests, cases `TC-###`, commands, exit criteria | [QA Test Plan](qa-test-plan.md) | |
| Build history: `TASK-###`, owners, pull requests | [Build History](implementation-plan.md) | |
| Deploy your own: project setup and local run | [Setup](setup.md) | roles and commands owned by System Design |

Add a row (and a doc) only when a concern outgrows its current owner — e.g. split Data Model out
of System Design once the schema is large. Fewer docs is better.

## 1. ID conventions

| Prefix | Meaning | Home |
|---|---|---|
| `F-###` | Feature | PRD |
| `BR-###` | Business / safety rule (testable) | PRD |
| `TC-###` | Test case | QA Test Plan |
| `TASK-###` | Unit of work | Implementation Plan |
| `ADR-###` | Decision record | `adr/` |

IDs are never reused or renumbered. Retired items are marked `(cut)` rather than deleted.
