# TraceGuard demo video: final narration

**Audience:** hackathon judges. **Perspective:** the viewer is the analyst who received the alert.
**Length:** 2:59.0 · voice-over: Kokoro-82M `af_heart` (AI-generated, credited on the closing card).
Captions show the same text. On-screen actions are anchored to each line's start (see `video/record.py`).

## 0:00.0 · Opening: the analyst's alert (motion graphics)

| Time | Line |
|---|---|
| 0:00.4 | An alert lands in your queue. What would you investigate, and how would you explain why? |
| 0:05.8 | Several wallets send money into one account. Soon after, a large payment moves out. To explain it, you need to see how the accounts connect, and when each transfer happened. |
| 0:17.0 | Looking at the payments one row at a time gives you only pieces of the story. |
| 0:22.0 | Some connections deserve a closer look. Others may have an ordinary explanation: two people sharing a tablet should not become a conclusion about wrongdoing. |
| 0:32.1 | That's where TraceGuard helps. It brings the connected evidence into view, and uses Gemini on Vertex AI to explain the retrieved results in an evidence-linked brief. |
| 0:43.7 | The graph tools calculate the paths and rule matches. Gemini explains those results. You remain responsible for the judgment. |

## 0:51.8 · Follow the alert: case C-1 (live app)

| Time | Line |
|---|---|
| 0:52.2 | Now follow the alert. Does the timing reveal a pattern that warrants review? Four wallets send five transfers into A-07, all within thirty minutes. |
| 1:02.3 | Together that's seventeen thousand pesos. Thirty minutes after the last one arrives, fifteen thousand five hundred moves on to A-08. |
| 1:10.9 | Order matters too. This payment out of A-09 happened before the money arrived, so it isn't counted as part of the trail. |

## 1:18.4 · Inspect the evidence: AI brief, checks, citation, counterevidence (live, real Gemini)

| Time | Line |
|---|---|
| 1:19.0 | I run the AI investigation. The graph tools flag both rules, convergence and rapid forwarding, so this pattern warrants review. |
| 1:28.2 | But an explanation is useful only if you can inspect its evidence. Every citation and figure is checked against the tool output first. A brief that fails is regenerated once, then blocked. |
| 1:40.8 | Follow any citation, and its supporting records light up on the graph, right beside the brief. |
| 1:46.9 | You also need the details that complicate the picture. Two senders have no recorded shared device link, and less went out than came in. Neither settles the question. They are context for your review. |

## 2:00.4 · Different alerts: C-2 shared device, C-3 end of trail and follow-up (live, real Gemini)

| Time | Line |
|---|---|
| 2:00.8 | Now consider a different alert. What if the connection is simply a shared device? |
| 2:08.8 | Three accounts share one tablet, but no rule matches. The connection is visible. The evidence is still insufficient. TraceGuard keeps that distinction clear. |
| 2:18.8 | And what happens when the data runs out? Here, A-19 forwards most of what it received to A-22, and the trail ends there. |
| 2:28.6 | You ask who owns A-22. The available data cannot tell you. TraceGuard states that limit, instead of filling the gap with a guess. |

## 2:38.5 · Architecture and close (motion graphics)

| Time | Line |
|---|---|
| 2:38.9 | TraceGuard runs on Cloud Run and calls Gemini on Vertex AI, with least-privilege access and no API keys. |
| 2:47.7 | You started with an alert. Now you can explain what warrants review, point to the supporting evidence, and show what remains unknown. |
| 2:55.8 | TraceGuard. Follow the connections. Keep the judgment human. |
