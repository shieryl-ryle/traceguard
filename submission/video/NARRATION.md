# Narration: recording guide

**You record 16 short lines, one file per line.** The script does the rest: it trims silences, reduces noise,
evens out the volume, and places each line at the right moment in the video.

## How to record
- Use a quiet room, with your phone 20–30 cm from your mouth. A voice memo or voice recorder app is fine.
- Record one file per line, named exactly as below: `L01.m4a`, `L02.m4a` and so on. `.wav` and `.mp3` also work.
- Speak calmly, as if you're explaining to a colleague. Pauses and breaths before and after each line are removed automatically.
- If you fluff a line, re-record just that file.
- Each line must fit its slot (shown in the table). There's plenty of room, so read at a relaxed pace.
- Listen once to `PACING-GUIDE-robot-voice-do-not-submit.mp4` to hear where each line lands.

## Part 1 (0:00-1:00): problem, approach, case C-1

| File | Slot | Say |
|---|---|---|
| `L01` | 6 s | Fraud analysts usually review alerts one transaction at a time, from a long queue. |
| `L02` | 10 s | But the risky pattern often hides in the connections: several accounts paying one destination, money moving on within minutes, and shared devices. |
| `L03` | 8 s | Analysts rebuild that picture by hand, and an innocent link, like a family tablet, is easy to misread. |
| `L04` | 8 s | TraceGuard traces those connections automatically and writes an evidence-linked case brief with Gemini on Vertex AI. |
| `L05` | 8 s | The rule is simple: the graph decides, the AI explains, and every claim is checked before anyone sees it. |
| `L06` | 10 s | Here's case C-1. Four wallets send five transfers into A-07 within thirty minutes: seventeen thousand pesos in total. |
| `L07` | 9 s | Thirty minutes later, A-07 sends fifteen thousand five hundred onward. A payment made before the money arrived isn't counted. |

## Part 2 (1:00-2:00): AI brief, verification, citation, follow-up

| File | Slot | Say |
|---|---|---|
| `L08` | 10 s | Now I run the AI investigation. A fixed workflow runs every graph tool for this case, then Gemini explains the results. |
| `L09` | 12 s | Before anything is shown, every citation and every figure is checked against the tool output. This panel shows exactly what was verified, and which attempt passed. |
| `L10` | 12 s | Both rules flag a pattern that warrants review. The counterevidence comes from the tools: two senders aren't on the shared device, and less went out than came in. |
| `L11` | 10 s | Clicking a citation highlights the exact records on the graph, right beside the brief, so the analyst can check each claim in place. |
| `L12` | 7 s | I can also ask a follow-up question about the case. For example: who owns account A-22? |
| `L12b` | 8 s | The case data can't answer that, so TraceGuard refuses to guess and says which records would be needed. |

## Part 3 (2:00-3:00): C-2, C-3, architecture, close

| File | Slot | Say |
|---|---|---|
| `L13` | 9 s | Case C-2 is three accounts sharing one tablet. Both rules were checked for each account, and none of them matched. |
| `L13b` | 8 s | So the brief says the evidence is insufficient: a shared device on its own is not proof of anything. |
| `L14` | 8 s | In case C-3, A-19 forwards most of what it received to A-22, so the forwarding rule flags it for review. |
| `L14b` | 8 s | But the trail reaches the edge of the data at A-22, so the next recipient and the intent are stated as unknown. |
| `L15` | 7 s | TraceGuard runs as one Cloud Run service, calling Gemini on Vertex AI through least-privilege access. |
| `L15b` | 6 s | There are no API keys, the data is synthetic, and every model call is capped. |
| `L16` | 9 s | Connected evidence, cited, and honest about what it doesn't know. That's TraceGuard, built by team Chilli for the AI Builder Cup. |

## Pronunciation
- "A-07": "A oh seven"
- "C-1": "C one"
- "TraceGuard": "trace guard"
- "Vertex": "VER-tex"

## Then
Put the files in the `my-voice-recordings` folder next to this guide (`C:/Users/tendi/Videos/TraceGuard/`) and tell Claude.
Claude runs `python submission/video/mux.py <that folder>` to produce the voiced parts and the 3:00 video.
