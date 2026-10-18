"""Record the TraceGuard demo segments: Maya story scenes (story.html) + the LIVE public app with real Gemini.

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


CASE_JS = """([title, chip]) => {
  if (title) {
    const card = document.createElement('div');
    Object.assign(card.style, {position: 'fixed', left: '50%', top: '42%', transform: 'translate(-50%,-50%) scale(.92)', zIndex: 2147483647,
      background: 'rgba(11,13,18,0.93)', color: '#fff', padding: '26px 44px', borderRadius: '20px', textAlign: 'center',
      font: '700 40px "Segoe UI", Arial, sans-serif', boxShadow: '0 20px 60px rgba(0,0,0,.45)', opacity: 0,
      transition: 'opacity .5s ease, transform .6s cubic-bezier(.34,1.56,.64,1)', pointerEvents: 'none'});
    card.innerHTML = title + '<div style="font:500 22px Segoe UI,Arial;color:#9aa0a6;margin-top:10px">Live app · synthetic demo data</div>';
    document.body.appendChild(card);
    requestAnimationFrame(() => { card.style.opacity = 1; card.style.transform = 'translate(-50%,-50%) scale(1)'; });
    setTimeout(() => { card.style.opacity = 0; }, 2300); setTimeout(() => card.remove(), 2900);
  }
  const c = document.createElement('div'); c.id = 'tgchip';
  Object.assign(c.style, {position: 'fixed', right: '70px', top: '14px', zIndex: 2147483646, background: 'rgba(11,13,18,0.86)', color: '#e8eaed',
    font: '600 16px "Segoe UI", Arial, sans-serif', padding: '7px 15px', borderRadius: '999px', opacity: 0, transition: 'opacity .5s', pointerEvents: 'none'});
  c.textContent = chip; document.body.appendChild(c); setTimeout(() => { c.style.opacity = 1; }, title ? 2500 : 0);
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


def seg_c1live(page: Page) -> Clock:
    open_app(page)
    c = Clock()
    captions(page, "c1live")
    page.evaluate(CASE_JS, ["Maya's investigation · C-1", "Maya's investigation · C-1 · live app · synthetic demo data"])
    fr = graph_frame(page)
    red = fr.evaluate(FIND_RED)
    c.at(4.5)                                     # M07: relationships into view
    if red:
        fr.locator("canvas").click(position={"x": red["x"], "y": red["y"]})
    c.at(10.4)                                    # M08: incoming window
    fr = graph_frame(page)
    red = fr.evaluate(FIND_RED) or red
    ifb = page.locator("iframe").first.bounding_box()
    if red:
        page.evaluate(BOX_JS, ["b1", ifb["x"] + red["x"] - 46, ifb["y"] + red["y"] - 46, 92, 92,
                               "Into A-07 · 4 wallets · 5 transfers · PHP 17,000.00 · 30 min"])
    c.at(17.2)                                    # M09: onward transfer
    page.evaluate(UNBOX_JS, "b1")
    grid = page.locator("[data-testid=stDataFrame]").first
    grid.scroll_into_view_if_needed()
    time.sleep(0.8)
    gb = grid.bounding_box()
    row_h = 35
    page.evaluate(BOX_JS, ["b2", gb["x"] + 4, gb["y"] + row_h * 8 + 1, gb["width"] - 8, row_h - 2,
                           "TX-0007 · 30 min after the last incoming · PHP 15,500.00 → A-08"])
    c.at(24.6)                                    # M10: the earlier payment is excluded
    page.evaluate(BOX_JS, ["b3", gb["x"] + 4, gb["y"] + row_h * 2 + 1, gb["width"] - 8, row_h - 2,
                           "TX-0008 · 09:00 · before the money reached A-09 → not part of this trail"])
    c.at(LENGTHS["c1live"] + 0.3)
    return c


def seg_c2(page: Page) -> Clock:
    open_app(page)
    c = Clock()
    captions(page, "c2")
    page.evaluate(CASE_JS, ["", "Maya's investigation · C-1 · live app · synthetic demo data"])
    c.at(1.0)                                     # M12: run the investigation
    page.get_by_role("button", name="Run AI investigation").click()
    wait_brief(page)
    flags = page.get_by_text("Rule flags (deterministic)").first
    flags.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.5)
    box_around(page, flags, "b1", "Graph tool results: both rules flag a pattern for review", pad=12, w=560, h=230)
    c.at(10.1)                                    # M13: what the validators check
    page.evaluate(UNBOX_JS, "b1")
    v = page.get_by_text("Verified before display").first
    v.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, v, "b2", "Checked: citations · figures · wording", pad=14, w=430, h=250)
    c.at(25.5)                                    # M14: follow a citation
    page.evaluate(UNBOX_JS, "b2")
    chip = page.get_by_role("button", name="RULE-FWD-01").first
    chip.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.4)
    chip.click()
    time.sleep(2.0)
    graph_frame(page)
    ifb = page.locator("iframe").first.bounding_box()
    page.evaluate(BOX_JS, ["b3", ifb["x"] - 6, ifb["y"] - 6, ifb["width"] + 12, min(ifb["height"], 520) + 12, "Supporting records highlighted"])
    c.at(30.4)                                    # M15: what complicates the picture
    page.evaluate(UNBOX_JS, "b3")
    ce = page.get_by_text("Counterevidence", exact=True).first
    ce.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.6)
    box_around(page, ce, "b4", "Details that complicate the picture", pad=12, w=560, h=230)
    c.at(38.4)                                    # the real export feeds the review and resolution scenes
    page.evaluate(UNBOX_JS, "b4")
    exp = page.get_by_role("button", name="Export brief (Markdown)")
    exp.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.4)
    with page.expect_download() as dl:
        exp.click()
    dl.value.save_as(str(BRIEF_MD))
    box_around(page, exp, "b5", "Exported: traceguard-C-1-brief.md", pad=10)
    c.at(LENGTHS["c2"] + 0.3)
    return c


def seg_c2case(page: Page) -> Clock:
    open_app(page)
    pick_case(page, "C-2")
    time.sleep(3)
    c = Clock()
    captions(page, "c2case")
    page.evaluate(CASE_JS, ["Maya's next case · C-2", "Maya's next case · C-2 · live app · synthetic demo data"])
    c.at(3.0)
    page.get_by_role("button", name="Run AI investigation").click()
    wait_brief(page)
    c.at(8.8)                                     # M18: no rule matched
    flags = page.get_by_text("Rule flags (deterministic)").first
    flags.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.5)
    box_around(page, flags, "b1", "No configured rule matched", pad=12, w=560, h=300)
    c.at(14.4)                                    # M19: document without accusing
    page.evaluate(UNBOX_JS, "b1")
    ce = page.get_by_text("Counterevidence", exact=True).first
    ce.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.5)
    box_around(page, ce, "b2", "Visible connection · insufficient evidence", pad=12, w=560, h=260)
    c.at(LENGTHS["c2case"] + 0.3)
    return c


def seg_c3case(page: Page) -> Clock:
    open_app(page)
    pick_case(page, "C-3")
    time.sleep(3)
    c = Clock()
    captions(page, "c3case")
    page.evaluate(CASE_JS, ["Maya's final case · C-3", "Maya's final case · C-3 · live app · synthetic demo data"])
    c.at(2.8)
    page.get_by_role("button", name="Run AI investigation").click()
    wait_brief(page)
    un = page.get_by_text("Unknowns", exact=True).first
    un.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.4)
    box_around(page, un, "b1", "Trail ends at A-22 · what happens next is unknown", pad=12, w=560, h=150)
    c.at(10.4)                                    # M21: the ownership question
    page.evaluate(UNBOX_JS, "b1")
    q = page.get_by_placeholder("e.g. Why is A-08 relevant? or Who owns A-22?")
    q.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.3)
    q.click()
    q.press_sequentially("Who owns A-22?", delay=60)
    page.get_by_role("button", name="Ask").click()
    page.wait_for_function("() => document.body.innerText.includes('Q: Who owns A-22?')", timeout=60000)
    time.sleep(0.5)
    if "Not answerable from this data" not in page.inner_text("body"):
        raise RuntimeError("C-3 follow-up did not return a refusal; narration M21-M23 would not match the footage")
    c.at(15.0)                                    # M22: the limit is stated
    ans = page.get_by_text("Not answerable from this data").first
    ans.evaluate("e => e.scrollIntoView({block: 'center'})")
    time.sleep(0.4)
    box_around(page, ans, "b2", "TraceGuard states the limit", pad=12, w=440, h=150)
    c.at(LENGTHS["c3case"] + 0.3)
    return c


SEGMENTS = {"meet": seg_meet, "diff": seg_diff, "open": seg_open, "c1live": seg_c1live, "c2": seg_c2, "review": seg_review,
            "c2case": seg_c2case, "c3case": seg_c3case, "arch": seg_arch, "resolve": seg_resolve}




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
