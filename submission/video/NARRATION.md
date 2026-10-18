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
| `L01` | 6 s | Fraud analysts review alerts one transaction at a time. |
| `L02` | 10 s | But the risky pattern often hides in the connections between accounts and devices. |
| `L03` | 8 s | Rebuilding that picture by hand is slow, and an innocent link is easy to mistake for a suspicious one. |
| `L04` | 8 s | TraceGuard traces those connections and writes an evidence-linked brief with Gemini on Vertex AI. |
| `L05` | 8 s | The graph decides, the AI explains, and every claim is checked before you see it. |
| `L06` | 10 s | Case C-1: four wallets send five transfers into A-07 within thirty minutes, seventeen thousand pesos in total. |
| `L07` | 9 s | Thirty minutes later, A-07 sends fifteen thousand five hundred onward. A payment made before the money arrived isn't counted. |

## Part 2 (1:00-2:00): AI brief, verification, citation, follow-up

| File | Slot | Say |
|---|---|---|
| `L08` | 10 s | I run the AI investigation: a fixed workflow runs the graph tools, then Gemini explains the results. |
| `L09` | 12 s | Before anything is shown, every citation and every figure is checked against the tool output. This panel shows what was verified. |
| `L10` | 12 s | Both rules flag a pattern that warrants review. The counterevidence comes from the tools: two senders aren't on the shared device, and less went out than came in. |
| `L11` | 10 s | Clicking a citation highlights the exact records on the graph, right beside the brief. |
| `L12` | 15 s | I can ask a follow-up. Who owns A-22? The data can't say, so TraceGuard refuses instead of guessing. |

## Part 3 (2:00-3:00): C-2, C-3, architecture, close

| File | Slot | Say |
|---|---|---|
| `L13` | 18 s | C-2 is three accounts sharing one tablet. No rule matches, so the evidence is insufficient: device sharing alone proves nothing. |
| `L14` | 18 s | In C-3 the money trail reaches the edge of the data at A-22. The next recipient and the intent are stated as unknown. |
| `L15` | 14 s | TraceGuard runs on Cloud Run with Gemini on Vertex AI, least-privilege access and no API keys. |
| `L16` | 9 s | Connected evidence, cited, and honest about what it doesn't know. That's TraceGuard. |

## Pronunciation
- "A-07": "A oh seven"
- "C-1": "C one"
- "TraceGuard": "trace guard"
- "Vertex": "VER-tex"

## Then
Put the files in the `my-voice-recordings` folder next to this guide (`C:/Users/tendi/Videos/TraceGuard/`) and tell assistant.
assistant runs `python submission/video/mux.py <that folder>` to produce the voiced parts and the 3:00 video.
