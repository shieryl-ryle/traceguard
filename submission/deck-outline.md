# TraceGuard: Proposal Deck Outline (7 slides)

**Audience:** AI Builder Cup 2026 judges (Google Cloud × Hack2skill), BFSI theme.
**Format:** 7 slides, exported to PDF for the proposal. Each slide leads with the insight, then the evidence.
**Claims rule:** Every claim must be backed by the app, the tests, or the docs. There are no accuracy or
time-saved claims, because we have no data for either (PRD §10).

> **Before you export:** the four items marked **FILL** below need real screenshots or numbers
> from the deployed app. **Q1** (category label) is still open with the organisers.

---

## Slide 1: The problem is connections, not single transactions
**Headline:** Fraud analysts review alerts one transaction at a time. The pattern lives in the connections.

- **Who:** fraud operations analysts at banks, e-wallets, and fintechs who are reviewing an existing alert.
- **Today:** analysts piece transfers together by hand across accounts and devices. They have to:
  - separate suspicious patterns from innocent links, such as a household sharing one phone;
  - document the evidence behind every conclusion.
- **Stated as a hypothesis we demonstrate on synthetic cases, not as a measured statistic.**

**Visual:** one alert row, then the hidden web behind it (accounts → one destination → onward).

---

## Slide 2: One case, three questions
**Headline:** C-1 shows convergence and fast forwarding.

- Three wallets send PHP 15,000.00 to A-07 in 4 transfers between 09:01 and 09:14.
- A-07 sends PHP 14,500.00 on to A-09 13 minutes after the last inbound transfer.
- Two of the senders were seen on the same device.
- The analyst needs answers to three questions:
  - Is this pattern worth escalating?
  - What is the evidence?
  - What can't the data tell us?

**Visual:** the C-1 graph screenshot. **FILL:** take it from the deployed app.

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

**Visual:** the brief with one citation highlighted. **FILL:** screenshot.

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
        Gemini on Vertex AI (google-genai SDK, structured JSON output)
```

- **Least-privilege IAM:** the runtime identity has only `roles/aiplatform.user`. There are no Owner or Editor roles.
- **Cost controls:** max instances and per-call caps. Budget alerts are a backstop.

**Owner:** Dzelle (architecture slide). **FILL:** check that the region, model ID, and service
account match the live deploy.

---

## Slide 6: Demo and evaluation
**Headline:** The tool tells "warrants review", "insufficient evidence", and "unknown" apart.

| Case | Pattern | Expected conclusion | Actual (deployed) |
|---|---|---|---|
| C-1 Convergence & forwarding | Fan-in plus rapid forwarding, shared device | Pattern warrants review | **FILL** |
| C-2 Benign shared device | Household accounts on one device, no forwarding | Insufficient evidence: device sharing alone is not enough | **FILL** |
| C-3 Incomplete evidence | Chain ends at the data boundary | Next recipient and intent unknown, not guessed | **FILL** |

**Quality evidence:**
- **Automated tests:** cover repeated transfers, time ordering, exact window boundaries, sums,
  invented-citation rejection, model-computed-figure rejection, wording, and timeout handling.
  **FILL:** final pass count from `pytest`.
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
