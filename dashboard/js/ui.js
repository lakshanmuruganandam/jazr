/* UI helpers: DOM, formatting, ECharts theming, faceplates, sparklines. */
(function () {
  'use strict';
  const JZ = window.JZ;
  const U = (JZ.ui = {});
  U.$ = (s, r = document) => r.querySelector(s);
  U.$$ = (s, r = document) => [...r.querySelectorAll(s)];
  U.h = function (html) { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
  U.esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  U.n = function (x, d = 0) { if (x == null || !isFinite(x)) return '—'; return Number(x).toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }); };
  U.big = function (x) { if (x == null || !isFinite(x)) return '—'; const a = Math.abs(x); if (a >= 1e9) return (x / 1e9).toFixed(2) + ' B'; if (a >= 1e6) return (x / 1e6).toFixed(2) + ' M'; if (a >= 1e4) return (x / 1e3).toFixed(1) + ' k'; return U.n(x, 0); };
  U.pct = (x, d = 1) => (x == null || !isFinite(x) ? '—' : (x * 100).toFixed(d) + ' %');
  U.dur = function (s) { if (s == null) return '—'; s = Math.max(0, Math.round(s)); const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60; return h ? `${h}h ${String(m).padStart(2, '0')}m` : `${m}:${String(ss).padStart(2, '0')}`; };
  U.css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  U.toast = function (msg) { const t = U.$('#toast'); t.textContent = msg; t.classList.add('on'); clearTimeout(U._tt); U._tt = setTimeout(() => t.classList.remove('on'), 2600); };
  U.prio = (p, off) => `<span class="prio p${p}${off ? ' off' : ''}" title="Priority ${p} — ${JZ.PRI[p]}">${p}</span>`;

  // ---------------------------------------------------------------- charts
  const charts = []; U.charts = charts;
  U.theme = function () {
    return { ink: U.css('--ink'), ink2: U.css('--ink2'), ink3: U.css('--ink3'), line: U.css('--line'), line2: U.css('--line2'), panel: U.css('--panel'), inset: U.css('--inset'),
      data: U.css('--data'), data2: U.css('--data2'), data3: U.css('--data3'), sp: U.css('--sp'), eq: U.css('--eq'), eqon: U.css('--eq-on'), eqfill: U.css('--eq-fill'),
      p1: U.css('--p1'), p2: U.css('--p2'), p3: U.css('--p3'), p4: U.css('--p4'), ok: U.css('--ok'), sel: U.css('--sel') };
  };
  U.ax = function (o = {}) {
    const c = U.theme();
    return Object.assign({ type: 'value', nameTextStyle: { color: c.ink3, fontSize: 10.5 }, nameGap: 8,
      axisLine: { lineStyle: { color: c.line2 } }, axisTick: { lineStyle: { color: c.line2 } }, axisLabel: { color: c.ink3, fontSize: 10.5, hideOverlap: true },
      splitLine: { lineStyle: { color: c.line, type: [2, 3] } } }, o);
  };
  U.tax = (o = {}) => U.ax(Object.assign({ type: 'value', min: 'dataMin', max: 'dataMax', axisLabel: { color: U.theme().ink3, fontSize: 10.5, formatter: (v) => JZ.fmtT(v).slice(7), hideOverlap: true }, splitLine: { show: false } }, o));
  U.base = function (o) {
    const c = U.theme();
    return Object.assign({ animation: false, textStyle: { fontFamily: getComputedStyle(document.body).fontFamily, color: c.ink2 }, grid: { left: 48, right: 14, top: 26, bottom: 26, containLabel: false },
      tooltip: { trigger: 'axis', backgroundColor: c.panel, borderColor: c.line2, textStyle: { color: c.ink, fontSize: 11.5 }, confine: true },
      legend: { top: 0, right: 0, textStyle: { color: c.ink2, fontSize: 10.5 }, itemWidth: 14, itemHeight: 8, icon: 'roundRect' } }, o);
  };
  U.line = (name, data, color, extra = {}) => Object.assign({ name, type: 'line', data, showSymbol: false, smooth: false, lineStyle: { width: 1.6, color }, itemStyle: { color } }, extra);
  U.chart = function (el, fn, page) {
    if (!window.echarts) { el.innerHTML = '<div class="placeholder">Chart library (ECharts 5.5.0, cdnjs) did not load — check network.</div>'; return null; }
    const inst = echarts.init(el, null, { renderer: 'canvas' });
    const c = { el, fn, inst, page };
    charts.push(c);
    try { inst.setOption(fn(), true); } catch (e) { console.warn(e); }
    new ResizeObserver(() => inst.resize()).observe(el);
    return c;
  };
  U.refreshCharts = function (page, full) {
    charts.forEach((c) => { if (c.page !== page) return; if (c.el.offsetParent === null) return; try { c.inst.setOption(c.fn(), full ? true : { replaceMerge: ['series'] }); } catch (e) { console.warn(e); } });
  };
  U.rethemeCharts = function () { charts.forEach((c) => { c.inst.dispose(); c.inst = echarts.init(c.el); try { c.inst.setOption(c.fn(), true); } catch (e) {} }); };

  // shaded band [[x, lo, hi], ...] drawn as one polygon (avoids stacked-area artefacts on value axes)
  U.band = (name, pts, color, op = 0.18) => ({ type: 'custom', name, silent: true, data: pts, encode: { x: 0, y: [1, 2] }, z: 1, tooltip: { show: false },
    renderItem: (params, api) => { if (params.dataIndex !== 0 || pts.length < 2) return null; const top = pts.map((p) => api.coord([p[0], p[2]])), bot = pts.map((p) => api.coord([p[0], p[1]])).reverse();
      return { type: 'polygon', shape: { points: top.concat(bot) }, style: { fill: color, opacity: op } }; } });
  // sparkline (inline svg)
  U.spark = function (svg, vals, opts = {}) {
    const w = 200, hgt = 38, v = vals.filter((x) => x != null && isFinite(x));
    if (v.length < 2) { svg.innerHTML = ''; return; }
    let lo = opts.min != null ? opts.min : Math.min(...v), hi = opts.max != null ? opts.max : Math.max(...v); if (hi - lo < 1e-9) { hi += 1; lo -= 1; }
    const pts = vals.map((x, i) => (x == null || !isFinite(x) ? null : [(i / (vals.length - 1)) * w, hgt - 3 - ((x - lo) / (hi - lo)) * (hgt - 6)])).filter(Boolean);
    let lim = '';
    if (opts.lim != null) { const y = hgt - 3 - ((opts.lim - lo) / (hi - lo)) * (hgt - 6); if (y > 0 && y < hgt) lim = `<line x1="0" x2="${w}" y1="${y}" y2="${y}" stroke="var(--ink3)" stroke-dasharray="3 3" stroke-width="1"/>`; }
    svg.setAttribute('viewBox', `0 0 ${w} ${hgt}`); svg.setAttribute('preserveAspectRatio', 'none');
    svg.innerHTML = `${lim}<polyline fill="none" stroke="var(--data)" stroke-width="1.6" vector-effect="non-scaling-stroke" points="${pts.map((p) => p.join(',')).join(' ')}"/>`;
  };

  // ---------------------------------------------------------------- faceplate
  U.fp = { cur: null };
  U.openFP = function (title, render, sub) {
    const fp = U.$('#fp'); U.fp.cur = { title, render, sub };
    U.$('#fpTitle').textContent = title; U.$('#fpSub').textContent = sub || '';
    fp.classList.add('on'); U.$('#fpBack').classList.add('on');
    U.renderFP(true);
    const b = U.$('#fpClose'); b && b.focus();
  };
  U.renderFP = function (first) {
    if (!U.fp.cur) return; const body = U.$('#fpBody');
    if (first || !body.contains(document.activeElement) || document.activeElement === body) { const st = body.scrollTop; U.fp.cur.render(body, first); body.scrollTop = st; }
    else U.fp.cur.render(body, false, true);
  };
  U.closeFP = function () { U.fp.cur = null; U.$('#fp').classList.remove('on'); U.$('#fpBack').classList.remove('on'); };
  U.confirm = function (msg) { return window.confirm(msg); };

  // CSV
  U.csv = function (name, rows) {
    if (!rows.length) { U.toast('Nothing to export yet'); return; }
    const keys = Object.keys(rows[0]);
    const q = (v) => { const s = v == null ? '' : typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toFixed(4)) : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    const txt = '# SIMULATED DATA — illustrative (JAZR Bloom Incident OS demo)\n' + keys.join(',') + '\n' + rows.map((r) => keys.map((k) => q(r[k])).join(',')).join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], { type: 'text/csv' })); a.download = name; document.body.appendChild(a); a.click(); a.remove();
    U.toast('Exported ' + name);
  };
})();
