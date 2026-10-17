# TraceGuard: 3-Minute Demo Video Script

**Audience:** hackathon judges watching a public video.
**Length:** 3:00 hard limit. The narration is about 370 words, roughly 125 words per minute, which leaves time for the on-screen clicks.
**Recording:** screen capture of the **deployed public URL** in a clean browser window, plus voice-over.
**Rules:**
- Show live AI output only.
- If a take uses a cached brief, the on-screen label must say so (BR-006).
- Never say "fraudster", "guilty", or give a percentage (BR-004).

**Before recording:**
- [ ] All 3 cases are deployed. C-2 and C-3 need TASK-002 and TASK-003.
- [ ] Run each case once to warm up the service.
- [ ] Browser zoom is 110%, the sidebar is open, and notifications are off.
- [ ] Have a backup take ready in case Gemini is slow. Don't edit out errors in a way that hides what happened.

---

## 0:00–0:25 · Problem (about 55 words)
**Screen:** title, then the case queue with the "Synthetic data" badge.

> Fraud analysts review alerts one transaction at a time. But the risky pattern often sits in the
> connections: several accounts paying one destination, money moving on within minutes, shared
> devices. Analysts rebuild that picture by hand. TraceGuard is an investigation aid that traces
> those connections and writes an evidence-linked brief. Everything you'll see runs on synthetic data.

## 0:25–1:20 · Case, graph, and trace (about 105 words)
**Screen:** open C-1. Pan across the graph. Click A-07 to show the selection panel. Select timeline
rows TX-0001 to TX-0004, then TX-0005, so they highlight.

> Here's case C-1. The graph shows accounts as circles and devices as squares, and every transfer
> is its own arrow, so repeated payments never merge. Clicking A-07 lists every record that touches
> it. In the timeline, three wallets send four transfers into A-07 between 9:01 and 9:14. Thirteen
> minutes later, A-07 sends funds on to A-09. Selecting rows highlights those transfers on the graph.
> These paths, windows, and sums are calculated by deterministic graph tools in the backend. The
> AI doesn't do any of this arithmetic. Two of the senders were also seen on the same device. That's
> worth noting, but on its own it proves nothing.

## 1:20–2:15 · AI brief with citations and counterevidence (about 115 words)
**Screen:** click **Run AI investigation**. Open the tool log briefly. Scroll the brief. Click the
`RULE-FWD-01` chip to show the highlight and the cited records. Click **Export**.

> Now I run the AI investigation. This is a fixed workflow: the app runs the graph tools, and then
> Gemini on Vertex AI explains the results. The log shows exactly what was retrieved. The brief says
> the pattern warrants review, and every observation carries evidence IDs. Clicking a citation
> highlights the exact records on the graph and lists them right here, so I can verify each claim.
> The brief also includes counterevidence and unknowns. Before anything is shown, the app checks
> that every cited ID and every figure really exists in the tool output. If it doesn't, the brief
> is regenerated once or blocked. Then I export it as Markdown for the case file.

## 2:15–2:40 · Benign and incomplete cases (about 50 words)
**Screen:** open C-2 and show its brief's conclusion. Open C-3 and show the Unknowns section.

> C-2 is a household sharing one phone, with no rapid forwarding. TraceGuard says the evidence is
> insufficient, because device sharing alone isn't enough. In C-3 the money trail hits the edge of
> the data. TraceGuard says the next recipient and the intent are unknown, and it doesn't guess.

## 2:40–3:00 · Architecture and close (about 40 words)
**Screen:** architecture slide (deck slide 5), then return to the app.

> TraceGuard runs as a single Cloud Run service with Gemini on Vertex AI, least-privilege IAM, and
> no API keys. The graph decides, the AI explains, and the analyst stays in charge. Connected
> evidence, cited, and honest about what it doesn't know.

---

**If C-2 or C-3 aren't deployed by recording time:** don't fake them. Shorten 2:15–2:40 to one
line ("We also built benign and incomplete-evidence cases; see the repo tests") and extend the C-1
citation demo. Decide this before recording, and update deck slide 6 to match.
