# TraceGuard: 3-Minute Demo Video Script

**Audience:** hackathon judges watching a public video.
**Length:** 3:00 hard limit. The narration is about 380 words, roughly 127 words per minute, which leaves time for the on-screen clicks.
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

## 0:25–1:20 · Case, graph, and trace (about 115 words)
**Screen:** open C-1. Click A-07 to show the selection panel. In the timeline, select TX-0002 to
TX-0006, then TX-0007, so they highlight. Point at TX-0008 (A-09 → A-06 at 09:00).

> Here's case C-1. Accounts are circles, devices are squares, and every transfer is its own arrow,
> so repeated payments never merge. Clicking A-07 lists every record that touches it. Four wallets
> send five transfers into A-07 between 9:01 and 9:31, seventeen thousand pesos in total. Exactly
> thirty minutes later, A-07 sends fifteen thousand five hundred on to A-08, which splits it again.
> The trace follows time, not just lines: this payment from A-09 happened before the money arrived,
> so it isn't counted. Every path, window and sum here comes from deterministic graph tools, not the
> AI. Two senders share a device. That's worth noting, but on its own it proves nothing.

## 1:20–2:15 · AI brief, verification and follow-up (about 120 words)
**Screen:** click **Run AI investigation** and pause on the **Verified before display** panel. Scroll
to the counterevidence. Click the `RULE-FWD-01` chip, so the graph on the left highlights. In the
follow-up box type "Who owns A-22?" and click **Ask**. Click **Export**.

> Now I run the AI investigation. It's a fixed workflow: the app runs the graph tools, then Gemini on
> Vertex AI explains the results. Before anything is shown, every citation and every figure is checked
> against the tool output, and this panel shows what was verified. The brief says the pattern warrants
> review, and the counterevidence comes straight from the tools: two senders aren't on the shared
> device, and less went out than came in. Clicking a citation highlights it on the graph, right beside
> the brief. I can also ask a follow-up. "Who owns A-22?" is refused, because the data can't say.
> Then I export the brief for the case file.

## 2:15–2:40 · Benign and incomplete cases (about 50 words)
**Screen:** open C-2 and show its brief's conclusion. Open C-3 and show the Unknowns section.

> C-2 is three accounts sharing one tablet, with no rapid forwarding. TraceGuard says the evidence is
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
