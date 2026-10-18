"""Encode the recorded segments into three 60.0 s parts (1080p30, crossfades between motion and live)."""
import json, subprocess
from pathlib import Path
FF = r"C:/Users/tendi/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe"
HERE = Path(__file__).parent
off = json.loads((HERE / "raw/offsets.json").read_text())
V = "scale=1920:1080:flags=lanczos,fps=30,format=yuv420p,setpts=PTS-STARTPTS"
XF = 0.8

def part(name, a, b=None, fade_in=False, fade_out=False):
    """a/b = (segment, start_shift, duration); with b, crossfade a -> b."""
    cmd = [FF, "-v", "error", "-y"]
    for seg, shift, dur in [a] + ([b] if b else []):
        cmd += ["-ss", f"{off[seg] + shift:.3f}", "-t", f"{dur + 0.5:.3f}", "-i", str(HERE / f"raw/{seg}.webm")]
    cmd += ["-f", "lavfi", "-t", "60", "-i", "anullsrc=r=48000:cl=stereo"]
    if b:
        fc = (f"[0:v]{V},trim=duration={a[2]}[v0];[1:v]{V},trim=duration={b[2]}[v1];"
              f"[v0][v1]xfade=transition=fade:duration={XF}:offset={a[2] - XF}[vx]")
        last, audio = "[vx]", "2:a"
    else:
        fc, last, audio = f"[0:v]{V},trim=duration={a[2]}[vx]", "[vx]", "1:a"
    fades = []
    if fade_in: fades.append("fade=t=in:st=0:d=0.6")
    if fade_out: fades.append("fade=t=out:st=59.2:d=0.8")
    fc += f";{last}{','.join(fades) if fades else 'null'},trim=duration=60[v]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", audio, "-t", "60",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "128k", str(HERE / f"out/{name}.mp4")]
    subprocess.run(cmd, check=True)
    print(name, "ok")

(HERE / "out").mkdir(exist_ok=True)
part("TraceGuard-part1", ("intro", 0, 40.4), ("c1live", -0.4, 20.4), fade_in=True)
part("TraceGuard-part2", ("c2", 0, 60.0))
part("TraceGuard-part3", ("c3live", 0, 36.4), ("outro", -0.4, 24.4), fade_out=True)
