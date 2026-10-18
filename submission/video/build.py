"""Build the final video from recorded segments + narration.

python build.py <voice_dir>   (voice_dir holds <line id>.wav, e.g. voice_af_heart/)
Segments are chained in timeline.json "order" with cross-fades; every segment after the first starts
"lead" seconds early so the fade happens before its action starts. Narration is placed at absolute
times derived from timeline.json and raw/offsets.json.
Output: out/final/TraceGuard-demo.mp4 (1920x1080 30 fps, H.264 High yuv420p, AAC stereo, -16 LUFS).
"""
import json, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
FF = shutil.which("ffmpeg") or r"C:/Users/tendi/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"
FP = shutil.which("ffprobe") or r"C:/Users/tendi/AppData/Local/Microsoft/WinGet/Links/ffprobe.exe"
TLJ = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))
ORDER, SEG, L = TLJ["order"], TLJ["segments"], TLJ["lengths"]
XF, LEAD = TLJ["xfade"], TLJ["lead"]
OFF = json.loads((HERE / "raw/offsets.json").read_text())
V = "scale=1920:1080:flags=lanczos,fps=30,format=yuv420p,setpts=PTS-STARTPTS"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1"]
OUT = HERE / "out/final"


def run(cmd): subprocess.run(cmd, check=True)
def dur(p): return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True).stdout)


def video() -> tuple[dict[str, float], float]:
    """Render the cross-faded picture track. Returns each segment's action start (t0) and the total length."""
    cmd, fc, t0 = [FF, "-v", "error", "-y"], [], {}
    chain, label = 0.0, ""
    for i, seg in enumerate(ORDER):
        shift = 0.0 if i == 0 else LEAD
        length = L[seg] + shift
        cmd += ["-ss", f"{OFF[seg] - shift:.3f}", "-t", f"{length + 0.5:.3f}", "-i", str(HERE / f"raw/{seg}.webm")]
        fc.append(f"[{i}:v]{V},trim=duration={length:.3f}[c{i}]")
        if i == 0:
            label, chain, t0[seg] = "[c0]", length, 0.0
            continue
        start = chain - XF
        fc.append(f"{label}[c{i}]xfade=transition=fade:duration={XF}:offset={start:.3f}[x{i}]")
        label, chain, t0[seg] = f"[x{i}]", start + length, start + shift
    fc.append(f"{label}fade=t=in:st=0:d=0.6,fade=t=out:st={chain - 0.9:.3f}:d=0.9,trim=duration={chain:.3f},format=yuv420p[v]")
    run(cmd + ["-filter_complex", ";".join(fc), "-map", "[v]", "-an", *ENC, str(OUT / "_video.mp4")])
    return t0, chain


def main(voice_dir: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0, total = video()
    inputs, filters, labels, report = [], [], [], []
    for seg in ORDER:
        lines = SEG[seg]
        for i, line in enumerate(lines):
            src = voice_dir / f"{line['id']}.wav"
            d = dur(src)
            start = t0[seg] + line["at"]
            nxt = (t0[seg] + lines[i + 1]["at"]) if i + 1 < len(lines) else t0[seg] + L[seg]
            report.append((line["id"], start, start + d, nxt - (start + d)))
            idx = len(labels) + 1
            inputs += ["-i", str(src)]
            filters.append(f"[{idx}:a]aresample=48000,pan=stereo|c0=c0|c1=c0,adelay={int(start * 1000)}:all=1[a{idx}]")
            labels.append(f"[a{idx}]")
    mix = "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad,atrim=0:{total:.3f},loudnorm=I=-16:TP=-1.5:LRA=9[aout]"
    final = OUT / "TraceGuard-demo.mp4"
    run([FF, "-v", "error", "-y", "-i", str(OUT / "_video.mp4"), *inputs, "-filter_complex", ";".join(filters + [mix]),
         "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-t", f"{total:.3f}",
         "-movflags", "+faststart", str(final)])
    for f in OUT.glob("_*"):
        f.unlink()
    (OUT / "segments.json").write_text(json.dumps({k: round(v, 2) for k, v in t0.items()}, indent=1))
    print(f"total: {total:.1f}s ({int(total // 60)}:{total % 60:04.1f})")
    print("segment starts:", ", ".join(f"{k} {v:.1f}" for k, v in t0.items()))
    worst = min(r[3] for r in report)
    print("narration lines:", len(report), "| tightest gap after a line:", f"{worst:.2f}s")
    for lid, s0, s1, gap in report:
        if gap < 0.3: print("  tight:", lid, f"ends {s1:.1f}s, gap {gap:.2f}s")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
