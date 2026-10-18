# Demo video tooling

The video is three 1-minute parts joined into 3:00, at 1080p with captions burned in. It uses the **live public app with real Gemini**; nothing is scripted or faked (BR-006).

| File | Purpose |
|---|---|
| `timeline.json` | The 16 narration lines and their time slots. The captions and the voice placement both come from this file |
| `motion.html` | Motion-graphics scenes (intro: problem and approach; outro: architecture and close) |
| `record.py` | Records each segment with Playwright: motion graphics, plus live app sessions with captions and callouts |
| `mux.py` | Cleans the recorded voice lines, places them on the timeline, and exports the voiced parts and the 3:00 cut |
| `NARRATION.md` | The recording guide for the voice-over |

The outputs (`raw/`, `out/`, `*.mp4`) are not committed.
