// TraceGuard demo overlay: a spotlight that tracks live elements, a smooth cursor, and an auto-zoom camera.
// Injected into the live app by record.py. Targets are re-measured every frame, so highlights stay on their
// element through scrolling, Streamlit reruns and camera moves.
(() => {
  if (window.FX) return;
  const AMBER = '#f2a900', ROW_H = 35;
  const css = document.createElement('style');
  css.textContent = `
    #fx-spot { position: fixed; z-index: 2147483640; pointer-events: none; border-radius: 14px; opacity: 0;
      border: 3px solid ${AMBER}; box-shadow: 0 0 0 9999px rgba(6,8,14,0.42), 0 0 26px rgba(242,169,0,.55);
      transition: opacity .45s ease; }
    #fx-label { position: fixed; z-index: 2147483641; pointer-events: none; opacity: 0; background: ${AMBER}; color: #111;
      font: 700 20px 'Segoe UI', Arial, sans-serif; padding: 7px 14px; border-radius: 10px; white-space: nowrap;
      box-shadow: 0 6px 18px rgba(0,0,0,.3); transition: opacity .35s ease; }
    #fx-cursor { position: fixed; z-index: 2147483645; pointer-events: none; left: 0; top: 0; width: 30px; height: 30px;
      transform: translate(-100px, -100px); filter: drop-shadow(0 3px 5px rgba(0,0,0,.45)); }
    .fx-ripple { position: fixed; z-index: 2147483644; pointer-events: none; width: 16px; height: 16px; margin: -8px 0 0 -8px;
      border-radius: 50%; border: 3px solid ${AMBER}; animation: fx-rip .6s ease-out forwards; }
    @keyframes fx-rip { from { transform: scale(.4); opacity: 1; } to { transform: scale(3.4); opacity: 0; } }
    [data-testid=stApp] { transform-origin: 0 0; transition: transform 1.1s cubic-bezier(.65,0,.35,1); will-change: transform; }`;
  document.head.appendChild(css);
  const spot = Object.assign(document.createElement('div'), {id: 'fx-spot'});
  const label = Object.assign(document.createElement('div'), {id: 'fx-label'});
  const cursor = Object.assign(document.createElement('div'), {id: 'fx-cursor'});
  cursor.innerHTML = '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M4 2 L4 19 L8.6 14.9 L11.6 21.6 L14.6 20.3 L11.7 13.8 L18 13.6 Z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/></svg>';
  document.body.append(spot, label, cursor);
  const app = () => document.querySelector('[data-testid=stApp]');

  // ---------- target resolution (all rects are live viewport rects) ----------
  const textEl = (t) => { const all = [...document.querySelectorAll('body *')].filter(e => !e.closest('#tgcap,#tgchip,#fx-label,#fx-spot'));
    return all.find(e => e.textContent.trim() === t && ![...e.children].some(c => c.textContent.trim() === t)) || all.filter(e => e.textContent.includes(t)).pop(); };
  const union = (rs) => rs.reduce((a, r) => r.height === 0 ? a : !a ? {l: r.left, t: r.top, r: r.right, b: r.bottom}
    : {l: Math.min(a.l, r.left), t: Math.min(a.t, r.top), r: Math.max(a.r, r.right), b: Math.max(a.b, r.bottom)}, null);
  const STOP = '[data-testid=stHeading],[data-testid=stButton],[data-testid=stDownloadButton],[data-testid=stTextInput],[data-testid=stExpander],[data-testid=stAlert],[data-testid=stDataFrame],iframe';
  const isHeading = (c) => { if (c.dataset.testid !== 'stElementContainer') return false;
    const p = c.querySelector('[data-testid=stMarkdownContainer] > p'), s = p && p.querySelector(':scope > strong');
    return !!((s && p.textContent.trim() === s.textContent.trim()) || c.querySelector(STOP)); };
  function sectionRect(text) {
    const start = textEl(text); if (!start) return null;
    const first = start.closest('[data-testid=stElementContainer]') || start; const rs = [first.getBoundingClientRect()];
    for (let c = first.nextElementSibling; c && !isHeading(c); c = c.nextElementSibling) rs.push(c.getBoundingClientRect());
    const u = union(rs); return u && {l: u.l, t: u.t, r: u.r, b: u.b};
  }
  function elRect(text) { const e = textEl(text); if (!e) return null; const b = (e.closest('button') || e).getBoundingClientRect();
    return {l: b.left, t: b.top, r: b.right, b: b.bottom}; }
  function rowRect(tx) {
    const df = document.querySelector('[data-testid=stDataFrame]'); if (!df) return null;
    const row = [...df.querySelectorAll('[role=row]')].find(r => r.textContent.includes(tx)); if (!row) return null;
    const idx = +row.getAttribute('aria-rowindex') - 1, sc = df.querySelector('.dvn-scroller'), g = df.getBoundingClientRect();
    const k = g.width / df.offsetWidth, top = g.top + (ROW_H * idx - (sc ? sc.scrollTop : 0)) * k;
    return {l: g.left + 2, t: top, r: g.right - 2, b: top + ROW_H * k};
  }
  let nodeCache = null, nodeAt = 0;
  function nodeRect() {
    const f = document.querySelector('iframe'); if (!f) return null;
    if (performance.now() - nodeAt > 150) { nodeAt = performance.now();
      try { const c = f.contentDocument.querySelector('canvas'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let sx = 0, sy = 0, n = 0;
        for (let i = 0; i < d.length; i += 16) { if (Math.abs(d[i]-0xE4) < 8 && Math.abs(d[i+1]-0x57) < 8 && Math.abs(d[i+2]-0x56) < 8) { const p = i / 4; sx += p % c.width; sy += Math.floor(p / c.width); n++; } }
        if (n) { const cr = c.getBoundingClientRect(); nodeCache = {x: cr.left + sx / n / c.width * cr.width, y: cr.top + sy / n / c.height * cr.height}; }
      } catch (e) {} }
    if (!nodeCache) return null;
    const b = f.getBoundingClientRect(), k = b.width / f.offsetWidth, x = b.left + nodeCache.x * k, y = b.top + nodeCache.y * k, h = 30 * k;
    return {l: x - h, t: y - h, r: x + h, b: y + h};
  }
  function frameRect() { const f = document.querySelector('iframe'); if (!f) return null; const b = f.getBoundingClientRect();
    return {l: b.left, t: b.top, r: b.right, b: Math.min(b.bottom, b.top + 540 * b.width / f.offsetWidth)}; }
  const resolve = (s) => !s ? null : s.kind === 'section' ? sectionRect(s.text) : s.kind === 'el' ? elRect(s.text)
    : s.kind === 'row' ? rowRect(s.tx) : s.kind === 'node' ? nodeRect() : s.kind === 'frame' ? frameRect() : null;

  // ---------- spotlight: eased tracking of the live target ----------
  let target = null, cur = null, pad = 10, changedAt = 0;
  function tick() {
    const host = app();
    // the spotlight lives inside the zoomed app layer, so it moves with the content in the same frame
    if (host && spot.parentElement !== host) host.append(spot, label);
    const r = resolve(target);
    if (r && host) {
      const m = new DOMMatrix(getComputedStyle(host).transform), a = m.a || 1;
      const L = (v, o) => (v - o) / a;   // viewport -> layout coordinates of the app layer
      const want = {l: L(r.l, m.e) - pad, t: L(r.t, m.f) - pad, r: L(r.r, m.e) + pad, b: L(r.b, m.f) + pad};
      if (!cur) cur = {...want};
      // glide only while moving to a new target; afterwards stay locked to the element (scroll, zoom, reflow)
      const glide = performance.now() - changedAt < 650;
      for (const k of ['l', 't', 'r', 'b']) cur[k] = glide ? cur[k] + (want[k] - cur[k]) * 0.22 : want[k];
      Object.assign(spot.style, {left: cur.l + 'px', top: cur.t + 'px', width: (cur.r - cur.l) + 'px', height: (cur.b - cur.t) + 'px'});
      const vis = {l: L(0, m.e), t: L(0, m.f), r: L(innerWidth, m.e)};
      const lh = label.offsetHeight || 36, above = cur.t - lh - 10 > vis.t + 8;
      Object.assign(label.style, {left: Math.max(vis.l + 8, Math.min(cur.l - 3, vis.r - label.offsetWidth - 8)) + 'px',
        top: (above ? cur.t - lh - 10 : cur.b + 10) + 'px'});
    }
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  // ---------- camera: scale [data-testid=stApp] so the target sits in view ----------
  let cam = {s: 1, x: 0, y: 0};
  function camera(s, spec) {
    const W = innerWidth, H = innerHeight;
    if (s <= 1 || !spec) { cam = {s: 1, x: 0, y: 0}; }
    else { const r = resolve(spec); if (!r) return;
      // undo the current transform to get layout coordinates, then centre the target
      const m = new DOMMatrix(getComputedStyle(app()).transform);   // the live (possibly mid-transition) transform
      const cx = ((r.l + r.r) / 2 - m.e) / m.a, cy = ((r.t + r.b) / 2 - m.f) / m.a;
      cam = {s, x: Math.min(0, Math.max(W - W * s, W / 2 - cx * s)), y: Math.min(0, Math.max(H - H * s, H * 0.46 - cy * s))}; }
    app().style.transform = `translate(${cam.x}px, ${cam.y}px) scale(${cam.s})`;
  }

  // ---------- cursor ----------
  let cpos = {x: innerWidth * 0.62, y: innerHeight * 0.7};
  function moveCursor(x, y, ms) {
    const from = {...cpos}, t0 = performance.now();
    return new Promise(done => { (function step(now) {
      const k = Math.min(1, (now - t0) / ms), e = k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
      const bend = Math.sin(Math.PI * k) * 40;   // a gentle arc, like a hand moving the mouse
      cpos = {x: from.x + (x - from.x) * e, y: from.y + (y - from.y) * e - bend * (1 - Math.abs(x - from.x) / (Math.abs(x - from.x) + 200))};
      cursor.style.transform = `translate(${cpos.x - 5}px, ${cpos.y - 3}px)`;
      k < 1 ? requestAnimationFrame(step) : done(); })(t0); });
  }

  window.FX = {
    focus(spec, text, p = 10) { const same = target && JSON.stringify(target) === JSON.stringify(spec); target = spec; pad = p; if (!same) changedAt = performance.now();
      if (!same && spot.style.opacity !== '1') cur = null;
      spot.style.borderRadius = spec.kind === 'node' ? '50%' : '14px';
      spot.style.opacity = 1; label.style.opacity = text ? 1 : 0; if (text) label.textContent = text; },
    clear() { spot.style.opacity = 0; label.style.opacity = 0; setTimeout(() => { if (spot.style.opacity === '0') { target = null; cur = null; } }, 500); },
    camera,
    async cursorTo(spec, ms = 800) { const r = typeof spec.x === 'number' ? {l: spec.x, r: spec.x, t: spec.y, b: spec.y} : resolve(spec);
      if (r) await moveCursor((r.l + r.r) / 2, (r.t + r.b) / 2, ms); },
    async cursorAt(x, y, ms = 800) { await moveCursor(x, y, ms); },
    ripple() { const d = document.createElement('div'); d.className = 'fx-ripple'; d.style.left = cpos.x + 'px'; d.style.top = cpos.y + 'px';
      document.body.appendChild(d); setTimeout(() => d.remove(), 700); },
    pos: () => cpos,
    rect: (spec) => resolve(spec),
  };
})();
