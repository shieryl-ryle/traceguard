"""Build the final video from recorded segments + narration.

python build.py <voice_dir>   (voice_dir holds <line id>.wav, e.g. voice_af_heart/)
Segments are chained in timeline.json "order" with cross-fades; every segment after the first starts
"lead" seconds early so the fade happens before its action starts. Narration is placed at absolute
times derived from timeline.json and raw/offsets.json.
Live-app segments ("framed") float as a rounded window on the story background.
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


WIN_W, WIN_H, WIN_X, WIN_Y, RADIUS = 1744, 981, 88, 50, 22   # the framed live-app window (16:9)
ASSETS = HERE / "out/assets"


def frame_assets() -> tuple[Path, Path]:
    """Rounded-corner mask for the window and a soft drop shadow beneath it."""
    from PIL import Image, ImageDraw, ImageFilter
    ASSETS.mkdir(parents=True, exist_ok=True)
    mask, shadow = ASSETS / "mask.png", ASSETS / "shadow.png"
    m = Image.new("L", (WIN_W, WIN_H), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, WIN_W - 1, WIN_H - 1), RADIUS, fill=255)
    m.save(mask)
    a = Image.new("L", (1920, 1080), 0)
    ImageDraw.Draw(a).rounded_rectangle((WIN_X, WIN_Y + 16, WIN_X + WIN_W, WIN_Y + WIN_H + 16), RADIUS, fill=150)
    a = a.filter(ImageFilter.GaussianBlur(30))
    sh = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); sh.putalpha(a); sh.save(shadow)
    return mask, shadow


def render_segment(i: int, seg: str, mask: Path, shadow: Path) -> Path:
    """Pass 1: one segment, trimmed (starting LEAD early after the first), at 1920x1080 30 fps.
    Live-app segments are framed as a rounded window with a shadow on the drifting story background."""
    shift = 0.0 if i == 0 else LEAD
    length = L[seg] + shift
    src = ["-ss", f"{OFF[seg] - shift:.3f}", "-t", f"{length + 0.5:.3f}", "-i", str(HERE / f"raw/{seg}.webm")]
    out = OUT / f"_seg{i:02d}.mp4"
    if seg in TLJ.get("framed", []):
        src += ["-ss", f"{OFF['bg'] + (3 * i) % 20:.3f}", "-t", f"{length + 0.5:.3f}", "-i", str(HERE / "raw/bg.webm"),
                "-loop", "1", "-i", str(mask), "-loop", "1", "-i", str(shadow)]
        fc = (f"[0:v]scale={WIN_W}:{WIN_H}:flags=lanczos,fps=30,setpts=PTS-STARTPTS,format=rgba[w];"
              f"[2:v]format=gray[m];[w][m]alphamerge[wa];"
              f"[1:v]{V},format=rgba[b];[3:v]format=rgba[s];[b][s]overlay=0:0:shortest=1[bs];"
              f"[bs][wa]overlay={WIN_X}:{WIN_Y}:shortest=1,trim=duration={length:.3f},format=yuv420p[v]")
    else:
        fc = f"[0:v]{V},trim=duration={length:.3f}[v]"
    run([FF, "-v", "error", "-y", *src, "-filter_complex", fc, "-map", "[v]", "-an", "-c:v", "libx264", "-preset", "fast",
         "-crf", "14", "-pix_fmt", "yuv420p", "-r", "30", str(out)])
    if dur(out) < length - 0.1:
        raise RuntimeError(f"{seg}: rendered {dur(out):.2f}s, needs {length:.2f}s (is raw/{seg}.webm or raw/bg.webm too short?)")
    return out


def video() -> tuple[dict[str, float], float]:
    """Pass 2: join the rendered segments with the transitions in timeline.json.
    Returns each segment's action start (t0) and the total length."""
    mask, shadow = frame_assets()
    trans = TLJ.get("transitions", {})
    cmd, fc, t0 = [FF, "-v", "error", "-y"], [], {}
    chain, label = 0.0, ""
    for i, seg in enumerate(ORDER):
        shift = 0.0 if i == 0 else LEAD
        length = L[seg] + shift
        cmd += ["-i", str(render_segment(i, seg, mask, shadow))]
        fc.append(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps=30[c{i}]")
        if i == 0:
            label, chain, t0[seg] = "[c0]", length, 0.0
            continue
        start = chain - XF
        fc.append(f"{label}[c{i}]xfade=transition={trans.get(seg, 'fade')}:duration={XF}:offset={start:.3f}[x{i}]")
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
