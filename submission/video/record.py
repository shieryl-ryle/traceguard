"""Record the TraceGuard demo segments: Tracy story scenes (story.html) + the LIVE public app with real Gemini.

Usage: python record.py <segment|all>   segments (story order): meet diff open c1live c2 review c2case c3case arch resolve
Writes raw/<segment>.webm and raw/offsets.json (seconds to trim from each recording's start).
"""

import json
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).parent
RAW = HERE / "raw"
APP = "https://traceguard-343683630064.asia-southeast1.run.app"
W, H = 1600, 900
TIMELINE = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))
TL, LENGTHS = TIMELINE["segments"], TIMELINE["lengths"]
BRIEF_MD = RAW / "c1_brief.md"
FX_JS = (HERE / "fx.js").read_text(encoding="utf-8")

CAPTIONS_JS = """(caps) => {
  let d = document.getElementById('tgcap');
  if (!d) {
    d = document.createElement('div'); d.id = 'tgcap';
    Object.assign(d.style, {position: 'fixed', left: '50%', bottom: '30px', transform: 'translateX(-50%)',
      maxWidth: '1320px', width: 'max-content', background: 'rgba(11,13,18,0.88)', color: '#fff',
      font: '600 26px/1.38 "Segoe UI", Arial, sans-serif', padding: '13px 26px', borderRadius: '14px',
      zIndex: 2147483647, textAlign: 'center', boxShadow: '0 8px 28px rgba(0,0,0,.35)', opacity: 0,
      transition: 'opacity .35s ease', pointerEvents: 'none'});
    document.body.appendChild(d);
  }
  for (const c of caps) {
    setTimeout(() => { d.textContent = c.text; d.style.opacity = 1; }, c.at * 1000);
    setTimeout(() => { if (d.textContent === c.text) d.style.opacity = 0; }, c.until * 1000);
  }
}"""

class Clock:
    def __init__(self) -> None:
        self.t0 = time.monotonic()

    def at(self, sec: float) -> None:
        delay = self.t0 + sec - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def now(self) -> float:
        return time.monotonic() - self.t0


def captions(page: Page, seg: str) -> None:
    """Each caption shows from its line's start until the next line starts (or the segment ends)."""
    lines = TL[seg]
    caps = [{"text": l["text"], "at": l["at"], "until": l.get("until") or ((lines[i + 1]["at"] - 0.15) if i + 1 < len(lines) else LENGTHS[seg] - 0.3)}
            for i, l in enumerate(lines)]
    page.evaluate(CAPTIONS_JS, caps)


def graph_frame(page: Page):
    try:
        page.locator("iframe").first.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass
    for _ in range(40):
        for f in page.frames:
            try:
                if f != page.main_frame and not f.is_detached() and f.query_selector("canvas"):
                    return f
            except Exception:
                pass
        time.sleep(0.5)
    raise RuntimeError("graph frame not found")


def wait_brief(page: Page, timeout: float = 90) -> None:
    page.wait_for_function("() => document.body.innerText.includes('Live AI output') || "
                           "document.querySelector('[data-testid=stAlertContentError]') !== null", timeout=timeout * 1000)
    if "Live AI output" not in page.inner_text("body"):
        raise RuntimeError("AI investigation failed on the live URL: " + page.inner_text("body")[-300:])


def open_app(page: Page) -> None:
    page.goto(APP, timeout=120000)
    page.get_by_text("Case queue").wait_for(timeout=120000)
    graph_frame(page)
    time.sleep(6)  # let the graph physics settle before the segment starts
    page.add_script_tag(content=FX_JS)


def pick_case(page: Page, case_id: str) -> None:
    page.locator("[data-testid=stSidebar] label").filter(has_text=case_id).first.click()
    time.sleep(2.5)
    graph_frame(page)


CASE_JS = """([title, chip]) => {
  if (title) {
    const card = document.createElement('div');
    Object.assign(card.style, {position: 'fixed', left: '50%', top: '42%', transform: 'translate(-50%,-50%) scale(.92)', zIndex: 2147483647,
      background: 'rgba(11,13,18,0.93)', color: '#fff', padding: '26px 44px', borderRadius: '20px', textAlign: 'center',
      font: '700 40px "Segoe UI", Arial, sans-serif', boxShadow: '0 20px 60px rgba(0,0,0,.45)', opacity: 0,
      transition: 'opacity .5s ease, transform .6s cubic-bezier(.34,1.56,.64,1)', pointerEvents: 'none'});
    card.innerHTML = title + '<div style="font:500 22px Segoe UI,Arial;color:#9aa0a6;margin-top:10px">Live app · synthetic demo data</div>';
    document.body.appendChild(card);
    setTimeout(() => { card.style.opacity = 1; card.style.transform = 'translate(-50%,-50%) scale(1)'; }, 800);
    setTimeout(() => { card.style.opacity = 0; }, 2900); setTimeout(() => card.remove(), 3500);
  }
  const c = document.createElement('div'); c.id = 'tgchip';
  Object.assign(c.style, {position: 'fixed', right: '70px', top: '14px', zIndex: 2147483646, background: 'rgba(11,13,18,0.86)', color: '#e8eaed',
    font: '600 16px "Segoe UI", Arial, sans-serif', padding: '7px 15px', borderRadius: '999px', opacity: 0, transition: 'opacity .5s', pointerEvents: 'none'});
  c.textContent = chip; document.body.appendChild(c); setTimeout(() => { c.style.opacity = 1; }, title ? 3100 : 800);
}"""


def brief_data() -> dict:
    """Review/resolution text taken from the REAL brief exported during the c2 recording."""
    md = BRIEF_MD.read_text(encoding="utf-8")
    sec: dict[str, list[str]] = {}
    cur = None
    for line in md.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            sec[cur] = []
        elif cur and line.startswith("- "):
            sec[cur].append(line[2:].strip())

    def clean(t: str) -> str:
        return t.split(" — evidence:")[0].replace("`", "").strip()

    def short(t: str, n: int = 170) -> str:
        return t if len(t) <= n else t[: n - 1].rsplit(" ", 1)[0] + "…"

    flags = [clean(x) for k, v in sec.items() if k.startswith("Rule flags") for x in v]
    matched = [f.split(":")[0] for f in flags if "pattern warrants review" in f]
    verified = sec.get("Verified before display", [""])[0]
    contrasts = [clean(x) for k, v in sec.items() if k.startswith("Contrasts") for x in v]
    unknown = [clean(x) for x in sec.get("Unknowns", [])]
    return {"warrants": f"{' and '.join(matched)}: pattern warrants review (deterministic rule flags)",
            "support": short(verified[0].upper() + verified[1:] + ". Each claim links back to its records."),
            "contrasts": short(" · ".join(contrasts), 240), "unknown": short(unknown[0] if unknown else ""),
            "file": "traceguard-C-1-brief.md"}


# ---------------- segments (action times are anchored to the narration in timeline.json) ----------------

def motion(page: Page, part: str, data: dict | None = None) -> Clock:
    page.goto((HERE / "story.html").as_uri() + f"?part={part}")
    time.sleep(1.0)
    if data:
        page.evaluate("d => { window.__data = d; }", data)
    c = Clock()
    captions(page, part)
    page.evaluate("() => window.__start()")
    c.at(LENGTHS[part] + 0.6)
    return c


def seg_meet(page: Page) -> Clock: return motion(page, "meet")
def seg_diff(page: Page) -> Clock: return motion(page, "diff")
def seg_open(page: Page) -> Clock: return motion(page, "open")
def seg_arch(page: Page) -> Clock: return motion(page, "arch")
def seg_review(page: Page) -> Clock: return motion(page, "review", brief_data())
def seg_resolve(page: Page) -> Clock: return motion(page, "resolve", brief_data())


def seg_bg(page: Page) -> Clock:
    """The story background alone (drifting light), placed behind the framed live-app window by build.py."""
    page.goto((HERE / "story.html").as_uri() + "?part=bg")
    time.sleep(1.0)
    c = Clock()
    c.at(max(LENGTHS[s] for s in TIMELINE["framed"]) + 24.0)   # build.py starts each framed segment at a different point
    return c


# ---- live-app overlay helpers (fx.js: one camera move, then a spotlight locked to the target) ----

def go(page: Page, spec: dict | None = None, scale: float = 1.0, label: str = "", pad: int = 10,
       spot: bool = True, ms: int = 1100) -> None:
    """Scroll + zoom to `spec` as one eased move (or back to the full page with scale 1), then draw the spotlight."""
    page.evaluate("([s, o]) => FX.go(s, o)", [spec, {"scale": scale, "label": label, "pad": pad, "spot": spot, "ms": ms}])


def focus(page: Page, spec: dict, label: str = "", pad: int = 10) -> None:
    page.evaluate("([s, l, p]) => FX.focus(s, l, p)", [spec, label, pad])


def mark(locator, name: str) -> dict:
    """Tag an element so fx.js can target it, and return its target spec."""
    locator.evaluate(f"e => e.setAttribute('data-fx', '{name}')")
    return {"kind": "sel", "sel": f"[data-fx={name}]"}


def click(page: Page, locator, ms: int = 650) -> None:
    """The cursor appears, travels to the element, presses, and the real click lands on that exact point."""
    bb = locator.bounding_box()
    x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
    page.evaluate("([x, y, ms]) => FX.clickAt(x, y, ms)", [x, y, ms])
    page.mouse.click(x, y)


def section(text: str) -> dict:
    return {"kind": "section", "text": text}


def wait_text(page: Page, text: str) -> None:
    page.wait_for_function("t => document.body.innerText.includes(t)", arg=text, timeout=30000)
    time.sleep(0.3)


def seg_c1live(page: Page) -> Clock:
    open_app(page)
    c = Clock()
    captions(page, "c1live")
    page.evaluate(CASE_JS, ["Tracy's investigation · C-1", "Tracy's investigation · C-1 · live app · synthetic demo data"])
    c.at(2.4)                                     # M07: the graph brings the relationships into view
    go(page, {"kind": "frame"}, 1.25, spot=False)
    c.at(4.4)
    node = page.evaluate("() => FX.rect({kind: 'node'})")
    x, y = (node["l"] + node["r"]) / 2, (node["t"] + node["b"]) / 2
    page.evaluate("([x, y]) => FX.clickAt(x, y, 800)", [x, y])
    page.mouse.click(x, y)
    focus(page, {"kind": "node"}, "A-07", pad=6)
    c.at(9.9)                                     # M08: the incoming window
    go(page, {"kind": "node"}, 1.6, "Into A-07 · 4 wallets · 5 transfers · PHP 17,000.00 · 30 min", pad=6, ms=900)
    c.at(16.4)                                    # M09: the onward transfer (graph -> timeline in one move)
    go(page, {"kind": "row", "tx": "TX-0007"}, 1.3, "TX-0007 · 30 min after the last incoming · PHP 15,500.00 → A-08", pad=3, ms=1400)
    c.at(24.2)                                    # M10: the earlier payment is excluded
    go(page, {"kind": "row", "tx": "TX-0008"}, 1.3, "TX-0008 · 09:00 · before the money reached A-09 → not part of this trail", pad=3, ms=900)
    c.at(32.6)                                    # M11: a pattern to investigate, not intent
    go(page, None, 1.0, ms=1200)
    c.at(LENGTHS["c1live"] + 0.3)
    return c


def seg_c2(page: Page) -> Clock:
    open_app(page)
    c = Clock()
    captions(page, "c2")
    page.evaluate(CASE_JS, ["", "Tracy's investigation · C-1 · live app · synthetic demo data"])
    c.at(0.9)                                     # M12: run the investigation
    click(page, page.get_by_role("button", name="Run AI investigation"))
    wait_brief(page)
    wait_text(page, "Rule flags (deterministic)")
    go(page, section("Rule flags (deterministic)"), 1.3, "Graph tool results: both rules flag a pattern for review")
    c.at(9.6)                                     # M13: what the validators check
    go(page, section("Verified before display"), 1.45, "Checked: citations · figures · wording")
    c.at(24.4)                                    # M14: follow a citation
    chip = page.get_by_role("button", name="RULE-FWD-01").first
    go(page, mark(chip, "chip"), 1.2, spot=False, ms=1000)
    click(page, chip)
    time.sleep(1.4)
    graph_frame(page)
    go(page, {"kind": "frame"}, 1.15, "Supporting records highlighted in the graph", pad=4, ms=1200)
    c.at(29.9)                                    # M15: what complicates the picture
    go(page, section("Counterevidence"), 1.3, "Details that complicate the picture", ms=1200)
    c.at(37.2)                                    # the real export feeds the review and resolution scenes
    exp = page.get_by_role("button", name="Export brief (Markdown)")
    spec = mark(exp, "export")
    go(page, spec, 1.25, spot=False, ms=1000)
    with page.expect_download() as dl:
        click(page, exp)
    dl.value.save_as(str(BRIEF_MD))
    focus(page, spec, "Exported: traceguard-C-1-brief.md", pad=8)
    c.at(LENGTHS["c2"] + 0.3)
    return c


def seg_c2case(page: Page) -> Clock:
    open_app(page)
    pick_case(page, "C-2")
    time.sleep(3)
    c = Clock()
    captions(page, "c2case")
    page.evaluate(CASE_JS, ["Tracy's next case · C-2", "Tracy's next case · C-2 · live app · synthetic demo data"])
    c.at(3.0)
    click(page, page.get_by_role("button", name="Run AI investigation"))
    wait_brief(page)
    wait_text(page, "Rule flags (deterministic)")
    c.at(8.4)                                     # M18: no rule matched
    go(page, section("Rule flags (deterministic)"), 1.3, "No configured rule matched")
    c.at(14.0)                                    # M19: document without accusing
    go(page, section("Counterevidence"), 1.3, "Visible connection · insufficient evidence")
    c.at(LENGTHS["c2case"] - 2.0)
    go(page, None, 1.0, ms=1200)
    c.at(LENGTHS["c2case"] + 0.3)
    return c


def seg_c3case(page: Page) -> Clock:
    open_app(page)
    pick_case(page, "C-3")
    time.sleep(3)
    c = Clock()
    captions(page, "c3case")
    page.evaluate(CASE_JS, ["Tracy's final case · C-3", "Tracy's final case · C-3 · live app · synthetic demo data"])
    c.at(2.8)
    click(page, page.get_by_role("button", name="Run AI investigation"))
    wait_brief(page)
    wait_text(page, "Unknowns")
    go(page, section("Unknowns"), 1.4, "Trail ends at A-22 · what happens next is unknown")
    c.at(9.9)                                     # M21: the ownership question
    q = page.get_by_placeholder("e.g. Why is A-08 relevant? or Who owns A-22?")
    go(page, mark(q, "question"), 1.25, spot=False, ms=1000)
    click(page, q, 600)
    q.press_sequentially("Who owns A-22?", delay=55)
    click(page, page.get_by_role("button", name="Ask"), 450)
    page.wait_for_function("() => document.body.innerText.includes('Q: Who owns A-22?')", timeout=60000)
    time.sleep(0.3)
    if "Not answerable from this data" not in page.inner_text("body"):
        raise RuntimeError("C-3 follow-up did not return a refusal; narration M21-M23 would not match the footage")
    c.at(14.6)                                    # M22: the limit is stated
    go(page, section("Not answerable from this data"), 1.45, "TraceGuard states the limit")
    c.at(LENGTHS["c3case"] - 2.0)
    go(page, None, 1.0, ms=1200)
    c.at(LENGTHS["c3case"] + 0.3)
    return c


SEGMENTS = {"meet": seg_meet, "diff": seg_diff, "open": seg_open, "c1live": seg_c1live, "c2": seg_c2, "review": seg_review,
            "c2case": seg_c2case, "c3case": seg_c3case, "arch": seg_arch, "resolve": seg_resolve, "bg": seg_bg}




def record(name: str) -> None:
    out_dir = RAW / f"tmp_{name}"
    shutil.rmtree(out_dir, ignore_errors=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(viewport={"width": W, "height": H}, record_video_dir=str(out_dir),
                                  record_video_size={"width": W, "height": H})
        page = ctx.new_page()
        t_page = time.monotonic()
        clock = SEGMENTS[name](page)
        offset = clock.t0 - t_page
        video = page.video.path()
        ctx.close()
        browser.close()
    target = RAW / f"{name}.webm"
    shutil.move(video, target)
    shutil.rmtree(out_dir, ignore_errors=True)
    offsets_path = RAW / "offsets.json"
    offsets = json.loads(offsets_path.read_text()) if offsets_path.exists() else {}
    offsets[name] = round(offset, 3)
    offsets_path.write_text(json.dumps(offsets, indent=2))
    print(f"{name}: recorded, action starts at {offset:.2f}s -> {target.name}")


if __name__ == "__main__":
    names = list(SEGMENTS) if sys.argv[1] == "all" else sys.argv[1:]
    for n in names:
        record(n)
