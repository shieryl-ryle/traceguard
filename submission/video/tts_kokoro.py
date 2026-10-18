"""Generate narration lines with Kokoro-82M (Apache-2.0) for each voice given: python tts_kokoro.py af_heart af_bella"""
import json, re, sys
from pathlib import Path
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).parent
MODEL = HERE.parent / "kokoro_model"
SPOKEN = [(r"\bA-0?(\d+)\b", lambda m: "A " + ("oh " + m.group(1) if m.group(0).startswith("A-0") else m.group(1))),
          (r"\bC-(\d)\b", r"C \1"), (r"\bTraceGuard\b", "Trace Guard"), (r"\bGemini on Vertex AI\b", "Gemini on Vertex A.I.")]

def spoken(text: str) -> str:
    for pat, rep in SPOKEN:
        text = re.sub(pat, rep, text)
    return text

kokoro = Kokoro(str(MODEL / "kokoro-v1.0.onnx"), str(MODEL / "voices-v1.0.bin"))
lines = [l for clip in json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))["clips"].values() for l in clip]
for voice in sys.argv[1:]:
    out = HERE / f"voice_{voice}"
    out.mkdir(exist_ok=True)
    for l in lines:
        audio, sr = kokoro.create(spoken(l["text"]), voice=voice, speed=1.0, lang="en-us")
        sf.write(out / f"{l['id']}.wav", audio, sr)
    print(voice, "->", out.name, len(lines), "lines")
print("sample:", spoken(lines[5]["text"]))
