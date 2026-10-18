"""Write NARRATION.md (absolute timestamps) from timeline.json and out/final/segments.json: python narration_doc.py"""
import json
from pathlib import Path

HERE = Path(__file__).parent
TITLES = {
    "meet": "1 · Meet Tracy (illustration · fictional analyst scenario)",
    "diff": "2 · Her difficulty (illustration)",
    "open": "3 · TraceGuard enters her workflow (illustration)",
    "c1live": "4 · Follow the evidence: C-1 graph and timeline (live app · synthetic demo data)",
    "c2": "5 · An explanation she can inspect: brief, checks, citation, counterevidence, export (live app, real Gemini)",
    "review": "5b · Tracy's review (illustration, text from the real exported brief)",
    "c2case": "6 · A connection she should question: Tracy's next case, C-2 (live app)",
    "c3case": "7 · A question she cannot answer: Tracy's final case, C-3 follow-up (live app)",
    "arch": "8 · How it works: Cloud Run, graph tools, Gemini on Vertex AI, validation (motion graphic)",
    "resolve": "9 · Resolution, the value of TraceGuard, end card (illustration)",
}


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


def main() -> None:
    d = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))
    t0 = json.loads((HERE / "out/final/segments.json").read_text())
    end = t0[d["order"][-1]] + d["lengths"][d["order"][-1]]
    out = ["# TraceGuard demo video: Tracy's story (final narration)", "",
           "**Audience:** hackathon judges. **Story:** Tracy, a fictional fraud analyst, works three synthetic cases with TraceGuard.",
           f"**Length:** {mmss(end)[:-2]} · voice-over: Kokoro-82M `af_heart` (AI-generated).",
           "Captions show the same text. On-screen actions are anchored to each line's start (see `video/record.py`).",
           'On screen: "Fictional analyst scenario · illustration" on Tracy\'s scenes; "live app · synthetic demo data" on app footage.', ""]
    for seg in d["order"]:
        out += [f"## {mmss(t0[seg])} · {TITLES[seg]}", "", "| Time | Line |", "|---|---|"]
        out += [f"| {mmss(t0[seg] + line['at'])} | {line['text']} |" for line in d["segments"][seg]]
        out.append("")
    (HERE / "NARRATION.md").write_text("\n".join(out), encoding="utf-8")
    print("NARRATION.md:", sum(len(v) for v in d["segments"].values()), "lines")


if __name__ == "__main__":
    main()
