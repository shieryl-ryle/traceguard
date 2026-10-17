# TraceGuard: Proposal Deck Outline (7 slides)

**Audience:** AI Builder Cup 2026 judges (Google Cloud × Hack2skill), BFSI theme.
**Format:** 7 slides, exported to PDF for the proposal. Each slide leads with the insight, then the evidence.
**Claims rule:** Every claim must be backed by the app, the tests, or the docs. There are no accuracy or
time-saved claims, because we have no data for either (PRD §10).

> **Before you export:** the items marked **FILL** below need real results
> from the deployed app. Interim screenshots are in `screenshots/`. Q1: the BFSI theme is confirmed; check the form category field at submission.

---

## Slide 1: The problem is connections, not single transactions
**Headline:** Fraud analysts review alerts one transaction at a time. The pattern lives in the connections.

- **Who:** fraud operations analysts at banks, e-wallets, and fintechs who are reviewing an existing alert.
- **Theme fit:** fraud investigation through *transaction anomaly analysis* (BFSI theme direction).
- **Today:** analysts piece transfers together by hand across accounts and devices. They have to:
  - separate suspicious patterns from innocent links, such as a household sharing one phone;
  - document the evidence behind every conclusion.
- **Stated as a hypothesis we demonstrate on synthetic cases, not as a measured statistic.**

**Visual:** one alert row, then the hidden web behind it (accounts → one destination → onward).

---

## Slide 2: One case, three questions
**Headline:** C-1 shows convergence and fast forwarding.

- Four wallets send PHP 17,000.00 to A-07 in 5 transfers between 09:01 and 09:31.
- Exactly 30 minutes after the last inbound transfer, A-07 sends PHP 15,500.00 (a ratio of 0.91)
  to A-08, which splits it onward.
- Two of the senders were seen on the same device.
- The trace follows time: a payment out of A-09 that happened *before* the money arrived is not
  counted as part of the trail.
- The analyst needs answers to three questions:
  - Is this pattern worth escalating?
  - What is the evidence?
  - What can't the data tell us?

**Visual:** `screenshots/slide2-c1-graph.png` (real C-1, captured from the live deploy).

---

## Slide 3: TraceGuard is an investigation aid with an evidence-linked brief
**Headline:** From alert to cited brief in one screen.

1. Open the alert from the case queue (every case is labelled "synthetic data").
2. Inspect the relationship graph and the time-ordered timeline. Clicking a node shows its evidence.
3. Run the AI investigation. Gemini explains the evidence the graph tools retrieved.
4. Review the brief:
   - observations, each with evidence IDs;
   - counterevidence;
   - unknowns;
   - suggested manual checks.
5. Click any citation to highlight it on the graph and timeline. Export the brief as Markdown.

**What it is not:** it does not block transfers, declare guilt, file regulatory reports, or give
a risk score.

**Visual:** `screenshots/slide3-brief.png` with `slide3-graph-highlight.png`, or `slide3-citation-records.png` (real C-1, live Gemini).

---

## Slide 4: The graph decides, the AI explains
**Headline:** Every number comes from code. The model only writes the explanation.

| Deterministic graph tools (backend) | Gemini (explanation only) |
|---|---|
| Paths in time order, never collapsing repeat transfers | Summarises tool results in plain language |
| Window, count, and sum calculations | Lists counterevidence and unknowns |
| Rule flags with thresholds shown (fan-in, rapid forwarding) | Suggests manual checks |
| Shared-device lookup | Uses careful wording: "pattern warrants review" |

**Guardrails, enforced in code and tested:**
- **Citations:** every cited ID must exist in the retrieved evidence. A brief that fails is
  regenerated once; if it fails again, no brief is shown.
- **Figures:** any figure or ID in the text that does not appear in the tool output is rejected.
- **Wording:** accusatory, probability, and score wording is rejected.
- **Bounds:** at most 4 tool rounds, a 30-second timeout, and a capped evidence payload.

**Say it plainly:** tool selection is a fixed workflow, not an autonomous agent.

---

## Slide 5: Google Cloud architecture
**Headline:** A single service with live Gemini on Vertex AI and no stored data.

```
Browser (analyst / judge, public URL)
   │ HTTPS
   ▼
Cloud Run "traceguard" (asia-southeast1, max 2 instances, runtime SA traceguard-run)
 └─ Streamlit app (Python 3.12)
     ├─ Graph layer: NetworkX MultiDiGraph in memory + 5 read-only tools
     ├─ AI layer: fixed retrieval → Gemini JSON brief → citation, figure, and wording validation
     └─ Synthetic dataset bundled in the image (no database)
              │ Application Default Credentials (no API keys)
              ▼
        Gemini on Vertex AI: gemini-3.5-flash, asia-southeast1
        (google-genai SDK, structured JSON output)
```

- **Least-privilege IAM:** the app runs as `traceguard-run`, which has only `roles/aiplatform.user`.
  The build account has only `roles/run.builder`, and the teammate deployer has four narrow roles.
  No Editor role exists anywhere in the project.
- **The graph decides, the AI explains:** every number and rule flag comes from the 5 graph tools.
  The model can only cite the IDs those tools return.
- **Cost controls:** max instances and per-call caps. Budget alerts are a backstop.
- **From the theme's suggested Google Cloud technologies:** Gemini on Vertex AI and Cloud Run.
  BigQuery is the scale-up path (slide 7).

**Owner:** Dzelle (architecture slide). Verified against the live deploy on 2026-10-17
(re-checked on revision `traceguard-00009` on 2026-10-18): region, model ID, runtime service account, max instances, and IAM.
Re-check after the final redeploy.

---

## Slide 6: Demo and evaluation
**Headline:** The tool tells "warrants review", "insufficient evidence", and "unknown" apart.

| Case | Pattern | Expected conclusion | Actual (deployed) |
|---|---|---|---|
| C-1 Convergence & forwarding | Fan-in plus rapid forwarding, shared device | Pattern warrants review | ✅ Both rules flag "Pattern warrants review". The brief cites the 4 senders, the 0.91 ratio, and shared device D-01. Counterevidence quotes both tool contrasts: A-02 and A-04 have no recorded shared device link, and TX-0007 is 1500.00 PHP less than the inbound total. Live brief in 6.9 s. |
| C-2 Benign shared device | Household accounts on one device, no forwarding | Insufficient evidence: device sharing alone is not enough | ✅ No rule matched. The brief lists shared device D-04 as an observation, with the unmatched rules as counterevidence. Live brief in 6.9 s. |
| C-3 Incomplete evidence | Chain ends at the data boundary | Next recipient and intent unknown, not guessed | ✅ Unknowns: "The trace reaches the data boundary at A-22", and where funds went next is unknown. No recipient named. Forwarding flags (ratio 0.96), which is expected. Counterevidence: fan-in not met, and TX-0022 is 500.00 PHP less than the inbound total. Live brief in 4.8 s. |

Verified 2026-10-18 on the public URL (revision `traceguard-00009`) in a clean browser profile with no Google login.
Every brief passed validation on the first attempt.

**Deterministic results (graph tools vs hand-derived expected outcomes, TC-004): 11 of 11 match.**

| Case | What the graph tools found |
|---|---|
| C-1 | Fan-in: 4 senders to A-07 within 30 min, 17000.00 PHP. Rapid forwarding: TX-0007 sent a ratio of 0.91 of that, 30 min after the last inbound. A-01 and A-03 share device D-01. |
| C-2 | Shared device D-04 (A-13, A-14, A-15). No rapid forwarding: the in-hour spend is a ratio of 0.12 (below 0.50), and the large spend came 60 min 1 s after payday (outside the window). |
| C-3 | Fan-in not met (2 senders, threshold 3). Rapid forwarding to A-22 (ratio 0.96, 25 min). The trace stops at A-22 at the data boundary, so the next recipient is unknown. |

Rules (ADR-003): fan-in means ≥ 3 distinct senders within 30 min. Rapid forwarding means an
outbound transfer within 60 min of inbound transfers, worth at least 0.50 of their total.
Boundaries are exact to the second.

**Quality evidence:**
- **Automated tests:** cover repeated transfers, time ordering, exact window boundaries, sums,
  invented-citation rejection, model-computed-figure rejection, wording, and timeout handling.
  168 unit tests pass, plus 1 live Gemini test (2026-10-18).
- **Citation integrity:** briefs shown with an invented citation: **0 by design**. The validator
  blocks display.

---

## Slide 7: Limitations and the path to a bank
**Headline:** Built as a safe demo, with a clear route to production.

**Limitations (honest):**
- Synthetic data only: about 20–40 accounts and one currency.
- No measured accuracy or time saved.
- The tool selection is a fixed workflow.
- The app has no authentication.
- Model wording can vary between runs, so the validator rejects bad output rather than preventing it.

**Production path:**
- **Scale:** Spanner Graph or BigQuery for bank-scale graphs, replacing in-memory NetworkX.
- **Security:** analyst sign-in, case-level access controls, and an audit log of every brief and citation click.
- **Validation:** back-testing on labelled historical alerts with the bank's data under its governance.
  Track analyst agreement rates before any claim of accuracy.
- **Human-led:** the analyst always decides. TraceGuard only prepares the evidence.

**Close:** "Connected evidence, cited and honest about what it doesn't know."
