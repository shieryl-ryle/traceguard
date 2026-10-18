"""Record the TraceGuard demo segments: motion graphics + the LIVE public app with real Gemini.

Usage: python record.py <segment|all>   segments: intro c1live c2 c3live outro
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
TL = json.loads((HERE / "timeline.json").read_text(encoding="utf-8"))["clips"]

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

BOX_JS = """([id, x, y, w, h, label]) => {
  let b = document.getElementById(id);
  if (!b) { b = document.createElement('div'); b.id = id; document.body.appendChild(b); }
  Object.assign(b.style, {position: 'fixed', left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px',
    border: '4px solid #f2a900', borderRadius: '14px', boxShadow: '0 0 0 9999px rgba(0,0,0,0.0)', zIndex: 2147483646,
    pointerEvents: 'none', transition: 'all .3s ease'});
  b.innerHTML = label ? `<div style="position:absolute;left:-4px;top:-46px;background:#f2a900;color:#111;
    font:700 21px 'Segoe UI',Arial,sans-serif;padding:7px 14px;border-radius:10px;white-space:nowrap">${label}</div>` : '';
}"""
UNBOX_JS = "(id) => { const b = document.getElementById(id); if (b) b.remove(); }"
FIND_RED = """() => { const c = document.querySelector('canvas'); if (!c) return null;
  const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; const k = c.width / c.clientWidth;
  let sx = 0, sy = 0, n = 0;
  for (let i = 0; i < d.length; i += 4) { if (Math.abs(d[i]-0xE4) < 8 && Math.abs(d[i+1]-0x57) < 8 && Math.abs(d[i+2]-0x56) < 8) {
    const p = i / 4; sx += p % c.width; sy += Math.floor(p / c.width); n++; } }
  return n ? {x: sx / n / k, y: sy / n / k} : null; }"""


class Clock:
    def __init__(self) -> None:
        self.t0 = time.monotonic()

    def at(self, sec: float) -> None:
        delay = self.t0 + sec - time.monotonic()
        if delay > 0:
            time.sleep(delay)

    def now(self) -> float:
        return time.monotonic() - self.t0


def captions(page: Page, clip: str, shift: float = 0.0, lo: float = 0.0, hi: float = 999.0) -> None:
    caps = [{"text": c["text"], "at": c["at"] - shift, "until": c["until"] - shift}
            for c in TL[clip] if lo <= c["at"] < hi]
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


def box_around(page: Page, locator, bid: str, label: str, pad: int = 10, w: int | None = None, h: int | None = None) -> None:
    bb = locator.bounding_box()
    if bb:
        page.evaluate(BOX_JS, [bid, bb["x"] - pad, bb["y"] - pad, (w or bb["width"]) + 2 * pad, (h or bb["height"]) + 2 * pad, label])


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


def pick_case(page: Page, case_id: str) -> None:
    page.locator("[data-testid=stSidebar] label").filter(has_text=case_id).first.click()
    time.sleep(2.5)
    graph_frame(page)


# ---------------- segments ----------------

def seg_intro(page: Page) -> float:
    page.goto((HERE / "motion.html").as_uri() + "?part=intro")
    time.sleep(1.0)
    c = Clock()
    captions(page, "clip1", lo=0, hi=40)
    page.evaluate("() => window.__start()")
    c.at(40.9)
    return c


def seg_outro(page: Page) -> float:
    page.goto((HERE / "motion.html").as_uri() + "?part=outro")
    time.sleep(1.0)
    c = Clock()
    captions(page, "clip3", shift=36, lo=36, hi=99)
    page.evaluate("() => window.__start()")
    c.at(24.2)
    return c


def seg_c1live(page: Page) -> float:
    open_app(page)
    c = Clock()
    captions(page, "clip1", shift=40, lo=40, hi=99)
    fr = graph_frame(page)
    red = fr.evaluate(FIND_RED)
    ifb = page.locator("iframe").first.bounding_box()
    c.at(1.5)
    if red:
        fr.locator("canvas").click(position={"x": red["x"], "y": red["y"]})
    c.at(4)
    fr = graph_frame(page)
    red = fr.evaluate(FIND_RED) or red
    ifb = page.locator("iframe").first.bounding_box()
    if red:
        page.evaluate(BOX_JS, ["b1", ifb["x"] + red["x"] - 46, ifb["y"] + red["y"] - 46, 92, 92, "A-07 · 4 senders · PHP 17,000.00 in 30 min"])
    c.at(10.5)
    page.evaluate(UNBOX_JS, "b1")
    grid = page.locator("[data-testid=stDataFrame]").first
    grid.scroll_into_view_if_needed()
    time.sleep(0.8)
    gb = grid.bounding_box()
    row_h = 35
    page.evaluate(BOX_JS, ["b2", gb["x"] + 4, gb["y"] + row_h * 8 + 1, gb["width"] - 8, row_h - 2, "TX-0007 · A-07 → A-08 · PHP 15,500.00"])
    c.at(15)
    page.evaluate(BOX_JS, ["b3", gb["x"] + 4, gb["y"] + row_h * 2 + 1, gb["width"] - 8, row_h - 2, "TX-0008 · 09:00 · before the money arrived → not counted"])
    c.at(20.2)
    return c


def seg_c2(page: Page) -> float:
    open_app(page)
    c = Clock()
    captions(page, "clip2")
    c.at(1.5)
    page.get_by_role("button", name="Run AI investigation").click()
    wait_brief(page)
    c.at(10.5)
    v = page.get_by_text("Verified before display").first
    v.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, v, "b1", "Checked before display", pad=14, w=430, h=250)
    c.at(22.5)
    page.evaluate(UNBOX_JS, "b1")
    ctr = page.get_by_text("Contrasts (deterministic, from graph tools)").first
    ctr.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, ctr, "b2", "Computed by the graph tools", pad=12, w=560, h=190)
    c.at(28.5)
    page.evaluate(UNBOX_JS, "b2")
    ce = page.get_by_text("Counterevidence", exact=True).first
    ce.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, ce, "b3", "Gemini quotes them as counterevidence", pad=12, w=560, h=230)
    c.at(34.5)
    page.evaluate(UNBOX_JS, "b3")
    chip = page.get_by_role("button", name="RULE-FWD-01").first
    chip.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.4)
    chip.click()
    time.sleep(4.5)
    graph_frame(page)
    ifb = page.locator("iframe").first.bounding_box()
    page.evaluate(BOX_JS, ["b4", ifb["x"] - 6, ifb["y"] - 6, ifb["width"] + 12, min(ifb["height"], 520) + 12, "Cited records highlighted on the graph"])
    c.at(44.5)
    page.evaluate(UNBOX_JS, "b4")
    q = page.get_by_placeholder("e.g. Why is A-08 relevant? or Who owns A-22?")
    q.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    q.click()
    q.press_sequentially("Who owns A-22?", delay=90)
    c.at(49.5)
    page.get_by_role("button", name="Ask").click()
    page.wait_for_function("() => document.body.innerText.includes('Q: Who owns A-22?')", timeout=60000)
    time.sleep(0.8)
    ans = page.get_by_text("Not answerable from this data").first
    ans.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.4)
    box_around(page, ans, "b5", "Refused, not guessed", pad=12, w=420, h=140)
    c.at(60.2)
    return c


def seg_c3live(page: Page) -> float:
    open_app(page)
    c = Clock()
    captions(page, "clip3", lo=0, hi=36)
    c.at(0.8)
    pick_case(page, "C-2")
    page.get_by_role("button", name="Run AI investigation").click()
    wait_brief(page)
    flags = page.get_by_text("Rule flags (deterministic)").first
    flags.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, flags, "b1", "No rule matched", pad=12, w=560, h=300)
    c.at(11)
    page.evaluate(UNBOX_JS, "b1")
    ce = page.get_by_text("Counterevidence", exact=True).first
    ce.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, ce, "b2", "Why the evidence is insufficient", pad=12, w=560, h=260)
    c.at(18.5)
    page.evaluate(UNBOX_JS, "b2")
    pick_case(page, "C-3")
    page.get_by_role("button", name="Run AI investigation").click()
    wait_brief(page)
    un = page.get_by_text("Unknowns", exact=True).first
    un.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, un, "b3", "Stated as unknown, not guessed", pad=12, w=560, h=150)
    c.at(36.9)
    return c


SEGMENTS = {"intro": seg_intro, "c1live": seg_c1live, "c2": seg_c2, "c3live": seg_c3live, "outro": seg_outro}


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
