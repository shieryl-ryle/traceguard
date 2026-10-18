"""Mix recorded narration lines into the three 1-minute clips and the full 3:00 video.

Usage: python mux.py <voice_dir>
<voice_dir> holds one file per line, named after its id: L01.m4a, L02.wav, ... (any format ffmpeg reads).
Each line is cleaned (silence trimmed, noise reduced, loudness evened), placed at its timeline slot,
and sped up slightly (at most 1.15x) only if it would overrun its slot. Missing lines stay silent.
Outputs out/TraceGuard-part{1,2,3}-voice.mp4 and out/TraceGuard-demo-3min-voice.mp4.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "out"
FF = shutil.which("ffmpeg") or r"C:/Users/tendi/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"
FP = shutil.which("ffprobe") or r"C:/Users/tendi/AppData/Local/Microsoft/WinGet/Links/ffprobe.exe"
MAX_TEMPO = 1.15
CLIPS = {"clip1": "TraceGuard-part1", "clip2": "TraceGuard-part2", "clip3": "TraceGuard-part3"}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def duration(path: Path) -> float:
    out = subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def clean(src: Path, dst: Path) -> None:
    trim = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,"
            "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.12,areverse")
    run([FF, "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", "48000",
         "-af", f"highpass=f=80,{trim},afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=7", str(dst)])


def main(voice_dir: Path) -> None:
    timeline = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))["clips"]
    work = OUT / "voice_work"
    work.mkdir(parents=True, exist_ok=True)
    for clip, base in CLIPS.items():
        inputs, filters, labels = [], [], []
        for line in timeline[clip]:
            src = next(iter(sorted(voice_dir.glob(f"{line['id']}.*"))), None)
            if src is None:
                print(f"  {line['id']}: missing, left silent")
                continue
            cleaned = work / f"{line['id']}.wav"
            clean(src, cleaned)
            slot = line["until"] - line["at"]
            length = duration(cleaned)
            tempo = min(MAX_TEMPO, max(1.0, length / slot))
            if length / tempo > slot + 0.05:
                print(f"  {line['id']}: {length:.1f}s is too long for its {slot:.1f}s slot even at {MAX_TEMPO}x; re-record shorter")
            idx = len(inputs) // 2 + 1
            inputs += ["-i", str(cleaned)]
            filters.append(f"[{idx}:a]atempo={tempo:.3f},adelay={int(line['at'] * 1000)}:all=1[a{idx}]")
            labels.append(f"[a{idx}]")
            print(f"  {line['id']}: {length:.1f}s in a {slot:.1f}s slot" + (f", sped up {tempo:.2f}x" if tempo > 1 else ""))
        video = OUT / f"{base}.mp4"
        target = OUT / f"{base}-voice.mp4"
        if not labels:
            shutil.copy(video, target)
            continue
        mix = "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad,atrim=0:60[aout]"
        run([FF, "-v", "error", "-y", "-i", str(video), *inputs, "-filter_complex", ";".join([*filters, mix]),
             "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", "60", str(target)])
        print(f"{target.name}: done")
    listing = OUT / "full_voice.txt"
    listing.write_text("".join(f"file '{b}-voice.mp4'\n" for b in CLIPS.values()))
    run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy",
         str(OUT / "TraceGuard-demo-3min-voice.mp4")])
    print("TraceGuard-demo-3min-voice.mp4: done")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
