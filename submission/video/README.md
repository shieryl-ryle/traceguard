# Demo video tooling

The video is three 1-minute parts joined into 3:00, at 1080p with captions burned in. It uses the **live public app with real Gemini**; nothing is scripted or faked (BR-006).

| File | Purpose |
|---|---|
| `timeline.json` | The 16 narration lines and their time slots. The captions and the voice placement both come from this file |
| `motion.html` | Motion-graphics scenes (intro: problem and approach; outro: architecture and close) |
| `record.py` | Records each segment with Playwright: motion graphics, plus live app sessions with captions and callouts |
| `mux.py` | Cleans the recorded voice lines, places them on the timeline, and exports the voiced parts and the 3:00 cut |
| `assemble.py` | Encodes the segments into three 60.0 s parts at 1080p30, with crossfades between the motion and live segments |
| `tts_kokoro.py` | AI voice-over with [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0), voice `af_heart`; run in a Python 3.12 environment with `kokoro-onnx` |
| `NARRATION.md` | The narration script, which also works as a human recording guide |

**Pipeline:** `python record.py all` → `python assemble.py` → `python tts_kokoro.py af_heart` → `python mux.py voice_af_heart`.
The voice-over is AI-generated, and the closing card says so.

The outputs (`raw/`, `out/`, `voice_*/`, `*.mp4`) are not committed.
