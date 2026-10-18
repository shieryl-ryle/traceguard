"""Build the final video from recorded segments + narration.

python build.py <voice_dir>   (voice_dir holds <line id>.wav, e.g. voice_af_heart/)
Chapters: A = intro x-fade C-1 live, B = AI brief, C = C-2/C-3 live x-fade outro.
Narration is placed at absolute times derived from timeline.json and the segment offsets.
Outputs out/final/TraceGuard-demo.mp4 and TraceGuard-chapter{1,2,3}.mp4 (H.264 High yuv420p, AAC stereo).
"""
import json, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
FF = shutil.which("ffmpeg") or r"C:/Users/tendi/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"
FP = shutil.which("ffprobe") or r"C:/Users/tendi/AppData/Local/Microsoft/WinGet/Links/ffprobe.exe"
TLJ = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))
SEG, L = TLJ["segments"], TLJ["lengths"]
OFF = json.loads((HERE / "raw/offsets.json").read_text())
XF, LEAD = 0.8, 0.4
V = "scale=1920:1080:flags=lanczos,fps=30,format=yuv420p,setpts=PTS-STARTPTS"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1"]
OUT = HERE / "out/final"


def run(cmd): subprocess.run(cmd, check=True)
def dur(p): return float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True, check=True).stdout)


def chapter(name, first, second=None, fade_in=False, fade_out=False):
    """first/second = (segment, start_shift, length). Returns chapter length in seconds."""
    parts = [first] + ([second] if second else [])
    cmd = [FF, "-v", "error", "-y"]
    for seg, shift, length in parts:
        cmd += ["-ss", f"{OFF[seg] + shift:.3f}", "-t", f"{length + 0.5:.3f}", "-i", str(HERE / f"raw/{seg}.webm")]
    total = first[2] + (second[2] - XF if second else 0)
    if second:
        fc = (f"[0:v]{V},trim=duration={first[2]}[v0];[1:v]{V},trim=duration={second[2]}[v1];"
              f"[v0][v1]xfade=transition=fade:duration={XF}:offset={first[2] - XF}[vx]")
    else:
        fc = f"[0:v]{V},trim=duration={first[2]}[vx]"
    fades = (["fade=t=in:st=0:d=0.6"] if fade_in else []) + ([f"fade=t=out:st={total - 0.8:.2f}:d=0.8"] if fade_out else [])
    fc += f";[vx]{','.join(fades) or 'null'},trim=duration={total:.3f},format=yuv420p[v]"
    run(cmd + ["-filter_complex", fc, "-map", "[v]", "-an", *ENC, str(OUT / f"{name}.mp4")])
    return total


def main(voice_dir: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    a = chapter("_A", ("intro", 0, L["intro"]), ("c1live", -LEAD, L["c1live"] + LEAD), fade_in=True)
    b = chapter("_B", ("c2", 0, L["c2"]))
    c = chapter("_C", ("c3live", 0, L["c3live"]), ("outro", -LEAD, L["outro"] + LEAD), fade_out=True)
    t0 = {"intro": 0.0, "c1live": L["intro"] - XF + LEAD, "c2": a, "c3live": a + b, "outro": a + b + L["c3live"] - XF + LEAD}
    total = a + b + c
    (OUT / "_list.txt").write_text("".join(f"file '{n}.mp4'\n" for n in ("_A", "_B", "_C")))
    run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "_list.txt"), "-c", "copy", str(OUT / "_video.mp4")])
    inputs, filters, labels, report = [], [], [], []
    for seg, lines in SEG.items():
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
    edges = [0, a, a + b, total]
    for n in range(3):
        run([FF, "-v", "error", "-y", "-ss", f"{edges[n]:.3f}", "-to", f"{edges[n + 1]:.3f}", "-i", str(final), *ENC,
             "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(OUT / f"TraceGuard-chapter{n + 1}.mp4")])
    for f in OUT.glob("_*"):
        f.unlink()
    print(f"chapters: {a:.1f}s + {b:.1f}s + {c:.1f}s = {total:.1f}s")
    worst = min(r[3] for r in report)
    print("narration lines:", len(report), "| tightest gap after a line:", f"{worst:.2f}s")
    for lid, s0, s1, gap in report:
        if gap < 0.3: print("  tight:", lid, f"ends {s1:.1f}s, gap {gap:.2f}s")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
