# Demo video tooling

The demo is one 3:35 video that follows **Maya, a fictional fraud analyst**, through three synthetic cases. The illustrated scenes are labelled "Fictional analyst scenario · illustration". The app footage is the **live public app with real Gemini**, labelled "live app · synthetic demo data". Nothing in the app footage is scripted or faked (BR-006). Captions are burned in, and the AI voice-over is credited on the closing card.

| File | Purpose |
|---|---|
| `timeline.json` | Segment order, narration lines (start times relative to each segment), segment lengths, cross-fade and lead. Captions, voice placement and on-screen actions all follow this file |
| `story.html` | Maya's illustrated scenes (`?part=meet, diff, open, review, arch, resolve`): her desk and queue, the records, the architecture, and the resolution beside the real exported brief |
| `record.py` | Records each segment with Playwright. Live segments run on the public URL with captions, case cards and callouts. The C-1 brief is exported for real, and its text feeds the review and resolution scenes. Fails if the C-3 follow-up is not a refusal |
| `tts_kokoro.py` | AI voice-over with [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0), voice `af_heart`, in a Python 3.12 environment with `kokoro-onnx` |
| `build.py` | Chains every segment with cross-fades (1080p30, H.264 High yuv420p), places every line at its absolute time, normalises loudness to −16 LUFS, and exports the demo |
| `NARRATION.md` | The final narration with absolute timestamps |

**Pipeline:** `python tts_kokoro.py af_heart` → `python record.py all` → `python build.py voice_af_heart`

The outputs (`raw/`, `out/`, `voice_*/`, `*.mp4`) are not committed.
