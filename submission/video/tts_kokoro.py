"""Generate narration lines with Kokoro-82M (Apache-2.0): python tts_kokoro.py af_heart [more voices]

Reads timeline.json and writes voice_<voice>/<line id>.wav. Captions keep exact IDs; the spoken
form reads them naturally ("A-07" -> "A oh 7", "C-1" -> "C 1"). "AI" is left as written: Kokoro reads it
as one word (/ˌeɪˈaɪ/); spelling it "A.I." splits it into two sentences with a pause between.
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
MODEL = HERE.parent / "kokoro_model"
SPOKEN = [(r"\bA-0(\d)\b", r"A oh \1"), (r"\bA-(\d\d)\b", r"A \1"), (r"\bC-(\d)\b", r"C \1"),
          (r"\bTraceGuard\b", "Trace Guard"), (r"\bA\.I\.", "AI")]


def spoken(text: str) -> str:
    for pat, rep in SPOKEN:
        text = re.sub(pat, rep, text)
    return text


def main(voices: list[str]) -> None:
    import soundfile as sf
    from kokoro_onnx import Kokoro

    kokoro = Kokoro(str(MODEL / "kokoro-v1.0.onnx"), str(MODEL / "voices-v1.0.bin"))
    clips = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))["segments"]
    lines = [line for clip in clips.values() for line in clip]
    for voice in voices:
        out = HERE / f"voice_{voice}"
        out.mkdir(exist_ok=True)
        for line in lines:
            audio, sr = kokoro.create(spoken(line["text"]), voice=voice, speed=1.0, lang="en-us")
            sf.write(out / f"{line['id']}.wav", audio, sr)
        print(voice, "->", out.name, len(lines), "lines")


if __name__ == "__main__":
    main(sys.argv[1:])
