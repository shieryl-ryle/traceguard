# Demo video tooling

The demo is one 3-minute video, also exported as three chapter files. It uses the **live public app with real Gemini**: nothing is scripted or faked (BR-006). Captions are burned in, and the AI voice-over is credited on the closing card.

| File | Purpose |
|---|---|
| `timeline.json` | The narration lines, with start times relative to their segment, and the segment lengths. Captions, voice placement and on-screen actions all follow this file |
| `motion.html` | Motion-graphics scenes: the intro (alert → connections → separate rows and the shared tablet → brief → "Graph tools compute. AI explains. You judge."), the architecture scene, and the close |
| `record.py` | Records each segment with Playwright: the motion graphics, plus live app sessions with captions and callouts. Fails if the C-3 follow-up is not a refusal |
| `tts_kokoro.py` | AI voice-over with [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0), voice `af_heart`, in a Python 3.12 environment with `kokoro-onnx` |
| `build.py` | Encodes the chapters (1080p30, H.264 High yuv420p, crossfades), places every line at its absolute time, normalises loudness, and exports the demo and chapter files |
| `NARRATION.md` | The final narration with absolute timestamps |

**Pipeline:** `python record.py all` → `python tts_kokoro.py af_heart` → `python build.py voice_af_heart`

The outputs (`raw/`, `out/`, `voice_*/`, `*.mp4`) are not committed.
