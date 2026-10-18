// TraceGuard demo overlay for the live app: one camera (scroll + zoom moved together on a single easing curve),
// a spotlight that is drawn on its target after each move and stays locked to it, and a cursor that only
// appears when the analyst clicks. Injected by record.py; nothing here changes what the app computes.
(() => {
  if (window.FX) return;
  const AMBER = '#f2a900', ROW_H = 35;
  const css = document.createElement('style');
  css.textContent = `
    #fx-spot { position: fixed; z-index: 2147483640; pointer-events: none; border-radius: 14px; opacity: 0;
      border: 3px solid ${AMBER}; box-shadow: 0 0 0 9999px rgba(6,8,14,0.40), 0 0 24px rgba(242,169,0,.5); }
    #fx-label { position: fixed; z-index: 2147483641; pointer-events: none; opacity: 0; background: ${AMBER}; color: #111;
      font: 700 20px 'Segoe UI', Arial, sans-serif; padding: 7px 14px; border-radius: 10px; white-space: nowrap;
      box-shadow: 0 6px 18px rgba(0,0,0,.3); }
    #fx-cursor { position: fixed; z-index: 2147483645; pointer-events: none; left: 0; top: 0; opacity: 0;
      filter: drop-shadow(0 2px 4px rgba(0,0,0,.4)); transition: opacity .25s ease; }
    #fx-cursor svg { display: block; transform-origin: 4px 3px; transition: transform .12s ease; }
    #fx-cursor.down svg { transform: scale(.82); }
    .fx-ripple { position: fixed; z-index: 2147483644; pointer-events: none; width: 14px; height: 14px; margin: -7px 0 0 -7px;
      border-radius: 50%; border: 2.5px solid ${AMBER}; animation: fx-rip .55s ease-out forwards; }
    @keyframes fx-rip { from { transform: scale(.5); opacity: .95; } to { transform: scale(3); opacity: 0; } }
    [data-testid=stApp] { transform-origin: 0 0; will-change: transform; }`;
  document.head.appendChild(css);
  const spot = Object.assign(document.createElement('div'), {id: 'fx-spot'});
  const label = Object.assign(document.createElement('div'), {id: 'fx-label'});
  const cursor = Object.assign(document.createElement('div'), {id: 'fx-cursor'});
  cursor.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M4 2.5 L4 18.6 L8.3 14.7 L11.2 21.2 L14 20 L11.2 13.6 L17.3 13.4 Z" fill="#fff" stroke="#111" stroke-width="1.3" stroke-linejoin="round"/></svg>';
  document.body.appendChild(cursor);
  const app = () => document.querySelector('[data-testid=stApp]');
  const ease = (k) => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  // ---------- target resolution (live viewport rects) ----------
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
    return union(rs);
  }
  function elRect(text) { const e = textEl(text); if (!e) return null; const b = (e.closest('button') || e).getBoundingClientRect();
    return {l: b.left, t: b.top, r: b.right, b: b.bottom}; }
  const rowIdx = {};
  function rowRect(tx) {
    const df = document.querySelector('[data-testid=stDataFrame]'); if (!df) return null;
    const row = [...df.querySelectorAll('[role=row]')].find(r => r.textContent.includes(tx));
    if (row) rowIdx[tx] = +row.getAttribute('aria-rowindex') - 1;   // the grid's accessibility rows can come and go; keep the index
    const idx = rowIdx[tx]; if (idx === undefined) return null;
    const sc = df.querySelector('.dvn-scroller'), g = df.getBoundingClientRect();
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
    : s.kind === 'row' ? rowRect(s.tx) : s.kind === 'node' ? nodeRect() : s.kind === 'frame' ? frameRect()
    : s.kind === 'sel' ? (() => { const e = document.querySelector(s.sel); if (!e) return null; const b = e.getBoundingClientRect();
        return {l: b.left, t: b.top, r: b.right, b: b.bottom}; })() : null;
  const matrix = () => new DOMMatrix(getComputedStyle(app()).transform);

  // ---------- spotlight: lives inside the zoomed app layer and stays locked to its target ----------
  let target = null, pad = 10;
  function place() {
    const host = app(); if (!host) return;
    if (spot.parentElement !== host) host.append(spot, label);
    const r = resolve(target); if (!r) return;
    const m = matrix(), a = m.a || 1, L = (v, o) => (v - o) / a;
    const box = {l: L(r.l, m.e) - pad, t: L(r.t, m.f) - pad, r: L(r.r, m.e) + pad, b: L(r.b, m.f) + pad};
    Object.assign(spot.style, {left: box.l + 'px', top: box.t + 'px', width: (box.r - box.l) + 'px', height: (box.b - box.t) + 'px'});
    const vis = {l: L(0, m.e), t: L(0, m.f), r: L(innerWidth, m.e)};
    const lh = label.offsetHeight || 36, above = box.t - lh - 10 > vis.t + 8;
    Object.assign(label.style, {left: Math.max(vis.l + 8, Math.min(box.l - 3, vis.r - label.offsetWidth - 8)) + 'px',
      top: (above ? box.t - lh - 10 : box.b + 10) + 'px'});
  }
  (function tick() { try { if (target) place(); } catch (err) { window.__fxErr = String(err); } requestAnimationFrame(tick); })();
  function hideSpot(ms = 260) {
    if (+getComputedStyle(spot).opacity > 0) { spot.animate([{opacity: 1}, {opacity: 0}], {duration: ms, fill: 'forwards'});
      label.animate([{opacity: 1}, {opacity: 0}], {duration: ms * .8, fill: 'forwards'}); }
    return sleep(ms);
  }
  function showSpot(spec, text, p) {
    target = spec; pad = p; spot.style.borderRadius = spec.kind === 'node' ? '50%' : '14px';
    label.textContent = text || ''; place();
    spot.animate([{opacity: 0, transform: 'scale(1.05)'}, {opacity: 1, transform: 'scale(1)'}], {duration: 480, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'forwards'});
    label.animate([{opacity: 0, transform: 'translateY(6px)'}, {opacity: text ? 1 : 0, transform: 'none'}], {duration: 380, delay: 160, easing: 'ease-out', fill: 'forwards'});
  }

  // ---------- camera: scroll and zoom animated together, one easing curve ----------
  // the element a target lives in (used to find every scroll container between it and the page)
  function elemOf(s) {
    if (!s) return null;
    if (s.kind === 'sel') return document.querySelector(s.sel);
    if (s.kind === 'row') return document.querySelector('[data-testid=stDataFrame]');
    if (s.kind === 'node' || s.kind === 'frame') return document.querySelector('iframe');
    const e = textEl(s.text); return e && (e.closest('[data-testid=stElementContainer]') || e);
  }
  const scrollables = (el) => { const out = []; for (let n = el && el.parentElement; n; n = n.parentElement) {
    const st = getComputedStyle(n); if (/(auto|scroll)/.test(st.overflowY) && n.scrollHeight > n.clientHeight) out.push(n); } return out; };
  function plan(spec, s) {
    const W = innerWidth, H = innerHeight, m = matrix(), a = m.a || 1, el = elemOf(spec), scs = scrollables(el);
    const from = scs.map(n => n.scrollTop), ancestors = [];
    for (let n = el && el.parentElement; n; n = n.parentElement) ancestors.push([n, n.scrollLeft]);
    // let the browser work out where every container must scroll to centre the target, measure, then put it all back
    if (el) el.scrollIntoView({block: 'center', inline: 'nearest', behavior: 'instant'});
    ancestors.forEach(([n, x]) => { if (n.scrollLeft !== x) n.scrollLeft = x; });   // vertical moves only: never shift the page sideways
    const to = scs.map(n => n.scrollTop), r = spec && resolve(spec);
    scs.forEach((n, i) => n.scrollTo({top: from[i], behavior: 'instant'}));
    let cx = W / 2, cy = H / 2;
    if (r) { cx = ((r.l + r.r) / 2 - m.e) / a; cy = ((r.t + r.b) / 2 - m.f) / a; }   // layout coordinates after the scroll
    const t = s <= 1 ? {s: 1, x: 0, y: 0} : {s, x: Math.min(0, Math.max(W - W * s, W / 2 - cx * s)), y: Math.min(0, Math.max(H - H * s, H * 0.47 - cy * s))};
    return {scs, from, to, t, cam: {s: a, x: m.e, y: m.f}};
  }
  function move(p, ms) {
    const host = app(), t0 = performance.now(), c = p.cam;
    return new Promise(done => { (function step(now) {
      const k = Math.min(1, (now - t0) / ms), e = ease(k);
      p.scs.forEach((n, i) => n.scrollTo({top: p.from[i] + (p.to[i] - p.from[i]) * e, behavior: 'instant'}));   // our easing, not CSS smooth-scroll
      const s = c.s + (p.t.s - c.s) * e, x = c.x + (p.t.x - c.x) * e, y = c.y + (p.t.y - c.y) * e;
      host.style.transform = `translate(${x}px, ${y}px) scale(${s})`;
      k < 1 ? requestAnimationFrame(step) : done(); })(t0); });
  }

  // ---------- cursor: visible only around a click ----------
  let cpos = null, hideTimer = null;
  function setCursor(x, y) { cpos = {x, y}; cursor.style.transform = `translate(${x - 4}px, ${y - 3}px)`; }
  async function pointTo(x, y, ms = 650) {
    clearTimeout(hideTimer);
    if (!cpos || cursor.style.opacity !== '1') { setCursor(x + 150, y + 110); cursor.style.opacity = 1; await sleep(120); }
    const from = {...cpos}, t0 = performance.now();
    await new Promise(done => { (function step(now) { const k = Math.min(1, (now - t0) / ms), e = ease(k);
      setCursor(from.x + (x - from.x) * e, from.y + (y - from.y) * e); k < 1 ? requestAnimationFrame(step) : done(); })(t0); });
  }
  function press() {
    cursor.classList.add('down'); setTimeout(() => cursor.classList.remove('down'), 140);
    const d = document.createElement('div'); d.className = 'fx-ripple'; d.style.left = cpos.x + 'px'; d.style.top = cpos.y + 'px';
    document.body.appendChild(d); setTimeout(() => d.remove(), 600);
    hideTimer = setTimeout(() => { cursor.style.opacity = 0; }, 900);
  }

  window.FX = {
    // Move the camera to `spec` (or back to the full page when scale <= 1), then draw the spotlight there.
    async go(spec, {scale = 1, label: text = '', pad: p = 10, spot: show = true, ms = 1100} = {}) {
      cursor.style.opacity = 0;
      await hideSpot();
      await move(plan(spec, scale), ms);
      if (spec && show) { showSpot(spec, text, p); await sleep(300); } else { target = null; }
    },
    // Draw the spotlight on a target without moving the camera.
    async focus(spec, text = '', p = 10) { await hideSpot(200); showSpot(spec, text, p); },
    async clear() { await hideSpot(); target = null; },
    async clickAt(x, y, ms = 650) { await pointTo(x, y, ms); press(); },
    rect: (spec) => resolve(spec),
  };
})();
