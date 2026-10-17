# PRD — TraceGuard

**Status:** Draft v0.1 · **Owner:** Shieryl · **Last updated:** 2026-10-17

**Conventions.** `F-###` features, `UJ-###` user journeys, `BR-###` business rules. Acceptance
criteria are plain, testable bullets. IDs are never renumbered; removed items are marked `(cut)`.

**Sources.**
| Source | Used for |
|---|---|
| TraceGuard bootstrap input (Shieryl + Dzelle, 2026-10-17) | all sections |
| AI Builder Cup 2026 rules (Google Cloud × Hack2skill) — theme BFSI: Intelligent Risk, Fraud & Financial Experiences | §2, BR-009, F-010 |

---

## 1. Problem
Fraud operations analysts at banks, e-wallets, and fintechs review alerts one transaction at a
time. That view hides connected behaviour across accounts and devices: funds that converge on
one destination, accounts that share a device, chains that forward money within minutes.
Analysts reconstruct transfers by hand, must separate suspicious patterns from innocent links
(e.g. a household sharing a phone), and then document their evidence for review.
**This is a hypothesis to demonstrate with synthetic cases, not a validated statistic.**

## 2. Context & constraints
- **Why now:** AI Builder Cup 2026 submission, BFSI theme.
- **Deadline:** 2026-10-18 11:59 PM Asia/Manila (confirmed by Shieryl 2026-10-17). Internal submit target
  **2026-10-18 10:00 PM Asia/Manila**; feature freeze **2 PM Manila**.
- **Budget:** no organiser credits. Project on Dzelle's personal Google Cloud account (free trial or personal billing). No employer project, account, or billing.
- **Platform:** web app (Streamlit) on Google Cloud Run, publicly reachable, Gemini on Vertex AI.
- **Legal / privacy:** synthetic data only (BR-001). No PII, no customer or employer data.
- **Team:** Shieryl (UI, AI prompts, demo, deck) · Dzelle (graph backend, fixtures, deploy).
- **Priority order (non-negotiable):** (1) deployed on Cloud Run with a real Gemini call →
  (2) seed case → graph evidence → real AI brief end to end on the public URL → (3) submission
  assets (proposal PDF, 3-min public video, form fields) → (4) everything else.

## 3. Goals
| # | Goal (outcome, not output) | Measured by (§10) |
|---|---|---|
| G1 | An analyst can see connected evidence (paths, timing, devices) for an alert without reconstructing it by hand | M1, M2 |
| G2 | The AI brief explains the evidence without inventing facts, citations, or guilt | M3, M4 |
| G3 | The tool distinguishes "warrants review" from "insufficient evidence" and "unknown" | M2 |
| G4 | Judges can run the full flow on the public URL | M5 |

## 4. Personas
| Persona | Goal | Context | Constraint | Primary? |
|---|---|---|---|---|
| Fraud operations analyst (bank / e-wallet / fintech) | Decide whether an existing alert warrants deeper review and document why | Works an alert queue; already has an alert, needs the connected picture | Must not accuse without evidence; must cite records | ✅ |
| Hackathon judge | Understand the product and verify it works in 3 minutes | Clean browser, public URL, no account | Limited time; no setup | |

## 5. Features & user stories
| ID | Feature | User story | Priority |
|---|---|---|---|
| F-001 | Case queue | As an analyst, I want to see open alert cases, so that I can pick one to investigate | P0 |
| F-002 | Case detail + timeline | As an analyst, I want a case's transactions in time order, so that I can see the sequence of events | P0 |
| F-003 | Interactive relationship graph | As an analyst, I want to see accounts, devices, and transfer direction, so that I can spot connected behaviour | P0 |
| F-004 | Deterministic graph tools | As an analyst, I want paths, windows, counts, and sums computed by code, so that the numbers are exact and reproducible | P0 |
| F-005 | AI investigation (Gemini on Vertex AI) | As an analyst, I want an AI to summarise the retrieved evidence, so that I can review faster | P0 |
| F-006 | Evidence-linked brief | As an analyst, I want observations tied to evidence IDs with counterevidence and unknowns, so that my write-up is defensible | P0 |
| F-007 | Citation navigation | As an analyst, I want to click an evidence ID and see its record, so that I can verify each claim | P0 |
| F-008 | Export | As an analyst, I want to download the brief as Markdown, so that I can attach it to the case | P0 |
| F-009 | Error handling | As an analyst, I want a readable message when the AI fails, so that I can keep using the graph | P0 |
| F-010 | Public Cloud Run deployment | As a judge, I want a working public URL, so that I can verify the product myself | P0 |
| F-011 | Case-scoped follow-up question | As an analyst, I want to ask one follow-up about this case, so that I can probe a specific link | P1 |
| F-012 | CSV import, cycle detection | As an analyst, I want to load my own synthetic data and detect cycles | P2 |

**P0 count is 10, above the usual ≤ 7.** Accepted because F-007–F-009 are small and F-010 is a
hackathon entry requirement. **Cut order if behind:** F-012 → F-011 → cosmetic polish.
**Never cut:** F-005, F-006, F-010.

**Hard cuts (this phase):** see §11.

## 6. Business rules
Testable statements. Reviewers and agents check every diff against these.

### Data & confidentiality
| ID | Rule | Applies to |
|---|---|---|
| BR-001 | All data in the repo, image, prompts, and demo is synthetic and generated from public fraud patterns. No employer or customer data, internal fraud rules, proprietary code, or confidential workflows (including Dzelle's fintech employer). Every case is labelled "synthetic data" in the UI. | F-001, all |
| BR-008 | No secrets in code, repo, chat, or prompts. Vertex AI is reached only through the Cloud Run runtime service account (ADC). No API keys. | F-005, F-010 |

### Evidence & detection
| ID | Rule | Applies to |
|---|---|---|
| BR-002 | Every evidence ID shown in a brief exists in the evidence retrieved for that case. Briefs are validated before display; on failure, regenerate once, then show an error. An invented citation is never displayed. | F-005, F-006, F-007, F-011 |
| BR-003 | Paths, time windows, amounts, counts, and rule matches are computed by the backend. The model explains them; it never calculates numbers or decides flags. Rule flags in the UI come from tool output, not model text. | F-004, F-005, F-006 |
| BR-005 | Questions the data cannot answer are refused or qualified. The brief states what is unknown (e.g. where a chain ends at the data boundary). Similar amounts later are never presented as proof that the same money moved. | F-006, F-011 |
| BR-010 | Expected fixture outcomes live only in `tests/` and are never loaded into model input or the app. | F-004, F-005 |

### Language & honesty
| ID | Rule | Applies to |
|---|---|---|
| BR-004 | UI and brief use "pattern warrants review" / "insufficient evidence". Never "fraudster", "guilty", "criminal", or a probability. No 0–100 risk score; show rule flags and evidence counts with their thresholds. | F-003, F-006, F-011 |
| BR-006 | Cached or scripted AI output is labelled as such in the UI. The fixed retrieval workflow is described as a fixed workflow, never as autonomous agent behaviour. | F-005, deck, video |
| BR-009 | English for code, UI, docs, deck, and video (hackathon rule). | all |

### AI bounds
| ID | Rule | Applies to |
|---|---|---|
| BR-007 | Each investigation makes at most 4 tool rounds and 1 regeneration; each Gemini request times out after 30 s (provisional); evidence payload sent to the model is capped at 60,000 characters (provisional — Q6). Exceeding a cap produces a readable error, not a silent truncation. | F-005, F-011 |

## 7. User journeys
### UJ-001 — Investigate convergence & forwarding (C-1)
1. Open the app → case queue shows C-1, C-2, C-3 labelled "synthetic data".
2. Select C-1 → timeline lists its transactions in time order; graph shows accounts, devices,
   and directed transfers.
3. Click a node → panel shows its IDs and linked evidence.
4. Click "Run AI investigation" → tool/retrieval log shows each tool run and its outputs.
5. Brief appears: observations with evidence IDs, counterevidence, unknowns, suggested manual
   checks, model ID, run time; verdict wording "pattern warrants review".
6. Click an evidence ID → matching timeline row / graph element is highlighted.
7. Click "Export" → `.md` file downloads.
- **Edge cases:** model timeout, quota, or permission error → readable message, graph and
  timeline still work (F-009); citation validation fails twice → error, no brief shown (BR-002).

### UJ-002 — Benign shared device (C-2)
1. Select C-2 → graph shows household accounts sharing one device.
2. Run AI investigation → rapid-forwarding tool returns no match; brief explains that device
  sharing alone is insufficient evidence.

### UJ-003 — Incomplete evidence (C-3)
1. Select C-3 → trace ends at the data boundary; `trace_funds` returns a truncation notice.
2. Run AI investigation → brief lists the next recipient and intent as unknown; never names one.

## 8. Acceptance criteria
### F-001 — Case queue
- [ ] Exactly 3 cases (C-1, C-2, C-3) load from the bundled dataset on every cold start.
- [ ] Each case shows title, scenario label, and a visible "synthetic data" label.

### F-002 — Case detail + timeline
- [ ] Selecting a case lists all its transactions sorted ascending by timezone-aware timestamp.
- [ ] Each row shows transaction ID, sender, receiver, amount, currency (PHP), timestamp.

### F-003 — Interactive relationship graph
- [ ] Account and device nodes are visually distinct; transfer edges show direction.
- [ ] Repeated transfers between the same pair render as separate edges (MultiDiGraph).
- [ ] Selecting a node shows its ID and the evidence IDs attached to it.

### F-004 — Deterministic graph tools
- [ ] The 5 tools in System Design §2 return outputs that match `tests/fixtures/` expected
  outcomes for C-1, C-2, C-3 (paths, window boundaries, sender counts, aggregate sums).
- [ ] `trace_funds` only follows transfers in non-decreasing time order.
- [ ] C-2 returns no rapid-forwarding match; C-3 returns a truncation notice.

### F-005 — AI investigation
- [ ] Clicking "Run AI investigation" makes a real server-side Gemini call on Vertex AI.
- [ ] A tool/retrieval log lists each tool called, its inputs, and the evidence IDs returned.
- [ ] Request obeys BR-007 caps; output is structured JSON parsed against the brief schema.

### F-006 — Evidence-linked brief
- [ ] Brief has observations (each with ≥ 1 evidence ID), counterevidence, unknowns,
  suggested manual checks, model ID, and run timestamp.
- [ ] All evidence IDs pass validation (BR-002); wording passes BR-004.

### F-007 — Citation navigation
- [ ] Clicking an evidence ID highlights the matching timeline row or graph element.

### F-008 — Export
- [ ] "Export" downloads a Markdown file containing the full brief, evidence IDs, model ID,
  run time, and the "synthetic data" label.

### F-009 — Error handling
- [ ] Timeout, quota (429), and permission (403) errors each show a readable message.
- [ ] After an AI error, case queue, timeline, and graph remain usable without a reload.

### F-010 — Public Cloud Run deployment
- [ ] The submitted URL loads in a clean browser (incognito, no Google login) and completes
  UJ-001 including a live Gemini call.
- [ ] Service runs with `--max-instances 2` and the `traceguard-run` runtime service account.

### F-011 — Follow-up question (P1)
- [ ] One text box per case; answer uses the same retrieved evidence and passes BR-002/004/005.

## 9. Vocabulary
| Term | Meaning in this product |
|---|---|
| Case / alert | A pre-existing alert an analyst reviews; seeded by `seed_ids` |
| Evidence ID | A `transaction_id`, `relationship_id`, or rule-result ID returned by a tool |
| Money trail | A path of transfers in non-decreasing time order — a static path is not a money trail |
| Convergence / fan-in | Several senders paying one receiver within a window |
| Rapid forwarding | Funds received then sent onward within a configured window |
| Pattern warrants review | Deterministic rules matched; a human should look further. Not a finding of guilt |
| Insufficient evidence | Links exist but do not meet any rule |
| Data boundary | Where the bundled dataset ends; anything past it is unknown |

## 10. Success metrics
No claims of production accuracy or analyst time saved (we have no data for either).

| Metric | Target | Why it matters (not a vanity metric) |
|---|---|---|
| M1 Fixture tool outputs matching expected outcomes | 100% of assertions for C-1/C-2/C-3 | Proves the numbers the analyst sees are correct |
| M2 Cases with the correct conclusion class (warrants review / insufficient / unknown) | 3 / 3 | Proves the tool separates suspicious from innocent and incomplete |
| M3 Displayed citations that exist in retrieved evidence | 100% (0 invented) | Core trust property (BR-002) |
| M4 Briefs containing forbidden terms (BR-004) | 0 across 5 runs per case | Proves careful language holds across model variance |
| M5 Clean-browser run of UJ-001 on the public URL | passes on 2026-10-18 before 9 PM Manila | Hackathon requirement |

## 11. Non-goals
- Real payments or account ingestion, KYC, auto-freeze or transfer blocking, regulatory filing.
- Declaring guilt, giving financial advice, credit scoring, scam-message classification.
- Trained or GNN models, graph embeddings, vector DB, graph database, multi-agent systems.
- Authentication, mobile app, broad banking chat.
- Autonomous tool selection by the model for the main flow (fixed workflow; Gemini
  function-calling only for F-011 if time allows).

## 12. Risks & dependencies
| Risk / dependency | Impact | Mitigation |
|---|---|---|
| GCP billing / credits not available (Q3) | Blocks F-010 and real Gemini call | 60–90 min timebox: personal free trial → Dzelle's personal project; then escalate to organisers. Never claim a local mock meets the rules |
| Gemini model ID / region not available in `asia-southeast1` (Q5) | Deploy or call fails | `VERTEX_LOCATION` and `GEMINI_MODEL` are env vars, separate from Cloud Run region |
| Graph component cannot return click selection to Python | F-003/F-007 degrade | Pick component after docs check; fallback: selectbox-driven highlight |
| Model returns invalid citations or forbidden language | Breaks BR-002/BR-004 live in demo | Validator + one regeneration; wording check; pre-demo 5-run test per case |
| Late submission | Disqualification | Internal target 10 PM Manila, 2 h before the 11:59 PM Manila deadline |
| Scope creep into P1/P2 before P0 is deployed | P0 incomplete at freeze | Feature freeze 2 PM Manila; cut order in §5 |

## 13. Open questions
| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | Category label — rules list "Healthcare, Education, Sustainability, Accessibility, Social Good", not the six challenge themes. Confirm with organisers/FAQ | Shieryl | submission form |
| Q2 | (resolved 2026-10-17) Deadline is 2026-10-18 11:59 PM Asia/Manila | Shieryl | — |
| Q3 | (resolved 2026-10-17) No organiser credits; Shieryl's trial already used. Dzelle sets up the project on her personal account (TASK-000) | Dzelle | — |
| Q4 | (resolved 2026-10-17) Yes, Shieryl + Dzelle are registered as a duo | Shieryl | — |
| Q5 | Gemini model ID + Vertex location confirmed in Model Garden | Dzelle | F-005, TASK-001 |
| Q6 | Final BR-007 values: timeout (30 s provisional), evidence payload cap (60,000 chars provisional) | Shieryl | F-005 |
| Q7 | (resolved 2026-10-17 by [ADR-003](adr/ADR-003-rule-windows-and-thresholds.md)) Fan-in ≥ 3 senders in 30 min; forwarding within 60 min and ratio ≥ 0.50; trace depth 3; boundaries inclusive | Dzelle | — |

## 14. Traceability
| Feature | Story / journey | Rules | Tests |
|---|---|---|---|
| F-001 | UJ-001 | BR-001 | TC-001 |
| F-002 | UJ-001 | BR-003 | TC-002 |
| F-003 | UJ-001, UJ-002 | BR-004 | TC-003 |
| F-004 | UJ-001–003 | BR-003, BR-010 | TC-004 |
| F-005 | UJ-001 | BR-002, BR-006, BR-007, BR-008 | TC-005 |
| F-006 | UJ-001–003 | BR-002, BR-004, BR-005 | TC-006 |
| F-007 | UJ-001 | BR-002 | TC-007 |
| F-008 | UJ-001 | BR-001 | TC-008 |
| F-009 | UJ-001 edge | BR-007 | TC-009 |
| F-010 | UJ-001 | BR-008 | TC-010 |
| F-011 | — | BR-002, BR-004, BR-005, BR-007 | TC-011 |
| F-012 | — | BR-001 | — |
