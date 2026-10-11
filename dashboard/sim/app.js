/* JAZR Simulation module — UI, map renderer, charts. Physics lives in twin.worker.js.
 * Model-based simulation (toy twin, validated against our Python model, not field data). */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const css = getComputedStyle(document.documentElement);
  const C = {
    bg: css.getPropertyValue('--bg').trim(), panel: css.getPropertyValue('--panel').trim(), line: css.getPropertyValue('--line').trim(),
    text: css.getPropertyValue('--text').trim(), muted: css.getPropertyValue('--muted').trim(), dim: css.getPropertyValue('--dim').trim(),
    teal: css.getPropertyValue('--teal').trim(), teal2: css.getPropertyValue('--teal2').trim(), leak: css.getPropertyValue('--leak').trim(),
    grey: css.getPropertyValue('--grey').trim(), sea: css.getPropertyValue('--sea').trim(), land: css.getPropertyValue('--land').trim(),
  };
  const SURVIVAL = 0.9782, SURV_MC = 0.76;   // engineering budget; conservative Monte Carlo 0.76 (0.68-0.85)
  function survK(j, s) { const h = j.hist; let n = 0, a = 0; for (let k = 1; k < h.length; k++) { n += h[k]; a += h[k] * Math.pow(s, k); } return n ? a / n : 1; }
  const TW = window.jazrTwinMain ? window.jazrTwinMain(null) : null;   // local copy for constants / drift arrows
  const K = TW ? TW.CONST : { Q: 400, H: 3.5, U0: 0.117, R_CAP: 60, R_I: 500, R_G: 120, POCKET_X: 600, GATE_Y: 150, OUTLETS: { near: [1200, 5000], far: [10000, 3000], immediate: [600, 150] } };
  const embedded = window.self !== window.top;
  if (embedded) document.body.classList.add('embedded');

  // ------------------------------------------------------------------ workers (file:// safe)
  function makeWorker(onmsg) {
    let w = null;
    try { if (location.protocol !== 'file:') w = new Worker('twin.worker.js'); } catch (e) { w = null; }
    if (!w && window.jazrTwinMain) {
      try {
        const src = '(' + window.jazrTwinMain.toString() + ')(self);';
        w = new Worker(URL.createObjectURL(new Blob([src], { type: 'text/javascript' })));
      } catch (e) { w = null; }
    }
    if (!w && window.jazrTwinMain) {   // last resort: same-thread shim
      const scope = { postMessage: (m) => setTimeout(() => fake.onmessage && fake.onmessage({ data: m }), 0) };
      const fake = { postMessage: (m) => setTimeout(() => scope.onmessage({ data: m }), 0), onmessage: null };
      window.jazrTwinMain(scope); w = fake;
    }
    w.onmessage = (e) => onmsg(e.data);
    if (w.addEventListener) w.addEventListener('error', (e) => setStatus('Worker error: ' + (e.message || e)));
    return w;
  }
  const live = makeWorker(onLive);
  const batch = makeWorker(onBatch);      // η_r sweep
  const retW = makeWorker(onBatch);       // outlet-distance sweep
  const nMC = Math.max(2, Math.min(4, (navigator.hardwareConcurrency || 4) - 2));
  const mcW = Array.from({ length: nMC }, () => makeWorker(onBatch));

  // ------------------------------------------------------------------ state + controls
  const Q = new URLSearchParams(location.search);
  const S = { dur: 72, swim: 0.036, speed: 12, zoom: 5000, frame: null, mc: null, eta: null, ret: null, running: true, job: 0 };
  function segInit(id, key, cast) {
    const el = $(id);
    el.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => {
      el.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
      S[key] = cast(b.dataset.v); el.dispatchEvent(new Event('change'));
    }));
  }
  function segSet(id, key, v) {
    $(id).querySelectorAll('button').forEach((b) => { const on = Number(b.dataset.v) === Number(v); b.classList.toggle('on', on); if (on) S[key] = Number(v); });
  }
  segInit('dur', 'dur', Number); segInit('swim', 'swim', Number); segInit('speed', 'speed', Number); segInit('zoom', 'zoom', Number);

  // URL overrides (handy for embedding / screenshots): ?eta=0.9&policy=far&days=10&vr=2.5&ur=0&N=2000&seed=1&speed=40&sbs=1&zoom=12000
  if (Q.has('eta')) { const v = Q.get('eta'); const opt = [...$('etaPreset').options].find((o) => o.value === v); $('etaPreset').value = opt ? v : 'manual'; $('eta').value = v; }
  if (Q.has('policy')) $('policy').value = Q.get('policy');
  if (Q.has('days')) segSet('dur', 'dur', Number(Q.get('days')) >= 10 ? 240 : 72);
  ['vr', 'ur', 'N', 'seed', 'dens', 'wind'].forEach((k) => { if (Q.has(k)) $(k).value = Q.get(k); });
  if (Q.has('swim')) segSet('swim', 'swim', Number(Q.get('swim')));
  if (Q.has('speed')) segSet('speed', 'speed', Number(Q.get('speed')));
  if (Q.has('zoom')) segSet('zoom', 'zoom', Number(Q.get('zoom')));
  if (Q.get('sbs') === '1') $('sbs').checked = true;
  if (Q.get('ring') === '1') $('ring').checked = true;

  function params() {
    return {
      N: +$('N').value, hours: S.dur, dt: 60, swim: S.swim, ur: +$('ur').value / 100, vr: -$('vr').value / 100,
      windSpeed: +$('wind').value, windDir: +$('windDir').value, ring: $('ring').checked, eta_g: +$('etag').value,
      eta_r: +$('eta').value, policy: $('policy').value, phase0: 0, seed: Math.max(1, +$('seed').value | 0), dens: +$('dens').value, mass: 0.33,
    };
  }
  function labels() {
    const p = params();
    $('oEta').textContent = p.eta_r.toFixed(3);
    $('oVr').textContent = (+$('vr').value).toFixed(1) + ' cm/s';
    $('oUr').textContent = (+$('ur').value >= 0 ? '+' : '') + (+$('ur').value).toFixed(1) + ' cm/s';
    $('oWind').textContent = (+$('wind').value).toFixed(1) + ' m/s (1% drift)';
    $('oDens').textContent = p.dens.toFixed(2) + ' /m³';
    $('oN').textContent = p.N.toLocaleString();
    $('oEg').textContent = p.ring ? p.eta_g.toFixed(2) : 'off';
    $('etag').disabled = !p.ring;
  }
  $('etaPreset').addEventListener('change', () => { const v = $('etaPreset').value; if (v !== 'manual') $('eta').value = v; restart(); });
  $('eta').addEventListener('input', () => { $('etaPreset').value = [...$('etaPreset').options].some((o) => o.value === $('eta').value) ? $('eta').value : 'manual'; labels(); });
  ['eta', 'vr', 'ur', 'wind', 'dens', 'N', 'etag'].forEach((id) => { $(id).addEventListener('input', labels); $(id).addEventListener('change', restart); });
  ['policy', 'windDir', 'seed', 'ring', 'today', 'dur', 'swim'].forEach((id) => $(id).addEventListener('change', restart));
  $('speed').addEventListener('change', () => live.postMessage({ cmd: 'speed', value: S.speed }));
  $('zoom').addEventListener('change', () => draw());
  $('sbs').addEventListener('change', layoutMaps);
  $('bRun').addEventListener('click', restart);
  $('bPause').addEventListener('click', () => {
    if (S.frame && S.frame.done) return restart();
    S.running = !S.running; live.postMessage({ cmd: S.running ? 'resume' : 'pause' }); $('bPause').textContent = S.running ? 'Pause' : 'Resume';
  });
  $('bMC').addEventListener('click', () => {
    const p = params(); p.N = Math.min(p.N, 1500);
    const reps = Math.max(4, Math.min(60, +$('reps').value | 0));
    S.job++; S.mcAcc = { job: S.job, reps, got: 0, jazr: [], today: [], ends: [] }; S.mc = null;
    setStatus(`Monte Carlo: ${reps} replicates on ${nMC} workers…`); $('bMC').disabled = true;
    const per = Math.ceil(reps / nMC);
    mcW.forEach((w, i) => { const s0 = i * per, cnt = Math.min(per, reps - s0); if (cnt > 0) w.postMessage({ cmd: 'mc', job: S.job, params: p, repStart: s0, repCount: cnt }); });
  });
  function mcFan() {
    const A = S.mcAcc, q = TW.quantile, hrs = A.jazr[0].length - 1;
    const fan = (arr) => { const o = { p10: [], p50: [], p90: [] }; for (let h = 0; h <= hrs; h++) { const v = arr.map((s) => s[h]).sort((x, y) => x - y); o.p10.push(q(v, 0.1)); o.p50.push(q(v, 0.5)); o.p90.push(q(v, 0.9)); } return o; };
    const e = A.ends.slice().sort((x, y) => x - y);
    S.mc = { reps: A.got, jazr: fan(A.jazr), today: fan(A.today), endP: [q(e, 0.1), q(e, 0.5), q(e, 0.9)] };
  }
  $('bSweep').addEventListener('click', () => {
    const p = params(); p.N = 1000;
    S.job++; setStatus('η_r sweep…'); $('bSweep').disabled = true;
    batch.postMessage({ cmd: 'sweepEta', job: S.job, params: p, values: [0.5, 0.6, 0.7, 0.773, 0.85, 0.9, 0.953, 0.99, 0.996] });
  });
  $('bCSV').addEventListener('click', exportCSV);
  $('bPNG').addEventListener('click', exportPNG);

  let retTimer = null;
  function restart() {
    labels(); S.mc = null; S.mcAcc = null; $('bMC').disabled = false; S.running = true; $('bPause').textContent = 'Pause';
    live.postMessage({ cmd: 'start', params: params(), today: $('today').checked || $('sbs').checked, speed: S.speed });
    $('mcNote').textContent = 'Monte Carlo fan: press “Monte Carlo” (P10–P90 over tide phase and seed).';
    clearTimeout(retTimer); retTimer = setTimeout(runReturnSweep, 600);
  }
  function runReturnSweep() {
    const p = params(); p.N = 800;
    $('retNote').textContent = 'Quick sweep running (N = 800)…';
    retW.postMessage({ cmd: 'sweepOutlet', job: 'ret', params: p, distances: [1000, 2500, 5000, 7500, 10000, 15000] });
  }
  function setStatus(t) { $('status').textContent = t; }

  // ------------------------------------------------------------------ messages
  let lastChart = 0;
  function onLive(m) {
    if (m.type === 'error') { setStatus('Twin error: ' + m.message); console.warn(m.message); return; }
    if (m.type !== 'frame') return;
    S.frame = m;
    if (m.done) { S.running = false; $('bPause').textContent = 'Run again'; }
    draw(); kpis();
    $('prog').style.width = (100 * m.hour / m.hours).toFixed(1) + '%';
    const now = performance.now();
    if (now - lastChart > 250 || m.done || !m.running) { lastChart = now; charts(); ledger(); postParent(); }
  }
  function onBatch(m) {
    if (m.type === 'error') { setStatus('Batch error: ' + m.message); $('bMC').disabled = $('bSweep').disabled = false; return; }
    if (m.type === 'progress') { if (m.job !== 'ret') setStatus(`${m.job === S.job ? 'Running' : 'Batch'}: ${m.done}/${m.total}`); return; }
    if (m.type === 'mcRep') {
      const A = S.mcAcc; if (!A || m.job !== A.job) return;
      A.jazr.push(m.jazr); A.today.push(m.today); A.ends.push(m.end); A.got++;
      mcFan(); setStatus(A.got < A.reps ? `Monte Carlo: ${A.got}/${A.reps}` : '');
      if (A.got >= A.reps) $('bMC').disabled = false;
      $('mcNote').textContent = `Monte Carlo, ${A.got}/${A.reps} replicates (tide phase + seed, N ≤ 1,500): JAZR at end P10 ${(S.mc.endP[0] * 100).toFixed(1)}% · P50 ${(S.mc.endP[1] * 100).toFixed(1)}% · P90 ${(S.mc.endP[2] * 100).toFixed(1)}%`;
      charts(); kpis();
    } else if (m.type === 'sweepEta') { S.eta = m.rows; $('bSweep').disabled = false; setStatus(''); etaChart(); }
    else if (m.type === 'sweepOutlet') {
      S.ret = m.rows; retChart();
      const p = params();
      $('retNote').textContent = `Quick sweep (N = 800, ${p.hours / 24} days, onshore ${(-p.vr * 100).toFixed(1)} cm/s). Return = released animals that come back to the screen or plant.`;
    }
  }

  // ------------------------------------------------------------------ map
  const cvs = { jazr: $('cvJazr'), today: $('cvToday') };
  function layoutMaps() {
    const sbs = $('sbs').checked;
    $('maps').classList.toggle('sbs', sbs); $('boxToday').style.display = sbs ? '' : 'none';
    if (sbs && !$('today').checked) { restart(); return; }
    sizeCanvases(); draw();
  }
  function sizeCanvases() {
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    for (const k of ['jazr', 'today']) {
      const c = cvs[k]; const w = c.parentElement.clientWidth || 600;
      const avail = $('controls').clientHeight - 48; const h = Math.round(Math.max(w * ($('sbs').checked ? 0.6 : 0.45), Math.min(avail, w * ($('sbs').checked ? 1.25 : 0.85))));
      c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); c.style.height = h + 'px'; c._dpr = dpr;
    }
  }
  window.addEventListener('resize', () => { sizeCanvases(); draw(); if (window.echarts) Object.values(CH).forEach((c) => c && c.resize()); });

  function draw() {
    const f = S.frame; if (!f) return;
    drawMap(cvs.jazr, f.jazr, 'JAZR', true, f);
    if ($('sbs').checked && f.today) drawMap(cvs.today, f.today, 'TODAY', false, f);
  }
  function drawMap(cv, d, title, sys, f) {
    const ctx = cv.getContext('2d'), W = cv.width, Hh = cv.height, dpr = cv._dpr || 1;
    const half = S.zoom, sc = W / (2 * half), coast = 16 * dpr;
    const X = (x) => W / 2 + x * sc, Y = (y) => Hh - coast - y * sc;
    ctx.fillStyle = C.sea; ctx.fillRect(0, 0, W, Hh);
    // scale grid (1 km or 500 m)
    const step = half > 6000 ? 2000 : half > 2000 ? 1000 : 250;
    ctx.strokeStyle = 'rgba(255,255,255,0.04)'; ctx.lineWidth = 1;
    for (let gx = -Math.ceil(half / step) * step; gx <= half; gx += step) { ctx.beginPath(); ctx.moveTo(X(gx), 0); ctx.lineTo(X(gx), Hh - coast); ctx.stroke(); }
    for (let gy = step; Y(gy) > 0; gy += step) { ctx.beginPath(); ctx.moveTo(0, Y(gy)); ctx.lineTo(W, Y(gy)); ctx.stroke(); }
    // drift arrows (tide + residual + wind + sink) at the current tide phase
    const p = params(), uw = 0.01 * p.windSpeed * Math.cos(p.windDir * Math.PI / 180), vw = 0.01 * p.windSpeed * Math.sin(p.windDir * Math.PI / 180);
    ctx.strokeStyle = 'rgba(160,175,185,0.28)'; ctx.fillStyle = 'rgba(160,175,185,0.28)'; ctx.lineWidth = 1 * dpr;
    const ax = half / 5;
    for (let gx = -half + ax / 2; gx < half; gx += ax) for (let gy = ax / 2; Y(gy) > 10 * dpr; gy += ax) {
      const r = Math.hypot(gx, gy), us = -K.Q / (Math.PI * r * K.H);
      const u = f.tideU + p.ur + uw + us * gx / r, v = p.vr + vw + us * gy / r;
      const sp = Math.hypot(u, v); if (sp < 1e-4) continue;
      const L = Math.min(26, 8 + 120 * sp) * dpr, ux = u / sp, vy = v / sp;
      const x0 = X(gx), y0 = Y(gy), x1 = x0 + ux * L, y1 = y0 - vy * L;
      ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 - ux * 5 * dpr + vy * 3 * dpr, y1 + vy * 5 * dpr + ux * 3 * dpr); ctx.lineTo(x1 - ux * 5 * dpr - vy * 3 * dpr, y1 + vy * 5 * dpr - ux * 3 * dpr); ctx.fill();
    }
    // land
    ctx.fillStyle = C.land; ctx.fillRect(0, Hh - coast, W, coast);
    ctx.fillStyle = C.muted; ctx.font = `${10 * dpr}px sans-serif`; ctx.textAlign = 'left';
    ctx.fillText('plant coast', 6 * dpr, Hh - 4 * dpr);
    // rings
    const ring = (r, col, dash, w) => { ctx.strokeStyle = col; ctx.setLineDash(dash.map((v) => v * dpr)); ctx.lineWidth = w * dpr; ctx.beginPath(); ctx.arc(X(0), Y(0), Math.max(1.5, r * sc), Math.PI, 2 * Math.PI); ctx.stroke(); ctx.setLineDash([]); };
    if (sys && p.ring) ring(K.R_I, 'rgba(127,211,200,0.45)', [6, 5], 1);
    if (sys) ring(K.R_G, C.teal, [4, 3], 1.6);
    ring(K.R_CAP, 'rgba(229,72,77,0.55)', [], 1);
    // intake
    ctx.fillStyle = '#c9d0d6'; ctx.fillRect(X(0) - 4 * dpr, Y(0) - 3 * dpr, 8 * dpr, 4 * dpr);
    // pockets + outlets
    if (sys) {
      ctx.fillStyle = C.teal;
      for (const s of [-1, 1]) ctx.fillRect(X(s * K.POCKET_X) - 3 * dpr, Y(30) - 3 * dpr, 6 * dpr, 6 * dpr);
      const o = f.outlet;
      for (const s of [-1, 1]) {
        const ox = s * o.gx, oy = o.gy, inView = Math.abs(ox) < half && Y(oy) > 0;
        if (inView) {
          ctx.strokeStyle = C.teal2; ctx.lineWidth = 1.5 * dpr; ctx.beginPath(); ctx.arc(X(ox), Y(oy), 6 * dpr, 0, 2 * Math.PI); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(X(ox) - 3 * dpr, Y(oy)); ctx.lineTo(X(ox) + 3 * dpr, Y(oy)); ctx.moveTo(X(ox), Y(oy) - 3 * dpr); ctx.lineTo(X(ox), Y(oy) + 3 * dpr); ctx.stroke();
          ctx.fillStyle = C.teal2; ctx.textAlign = 'center'; ctx.fillText('outlet', X(ox), Y(oy) - 9 * dpr);
        } else {   // edge marker
          const ex = Math.max(10 * dpr, Math.min(W - 10 * dpr, X(ox))), ey = Math.max(12 * dpr, Math.min(Hh - coast - 8 * dpr, Y(oy)));
          ctx.fillStyle = C.teal2; ctx.textAlign = s > 0 ? 'right' : 'left';
          ctx.fillText((s > 0 ? '' : '◂ ') + `outlet ${(Math.abs(ox) / 1000).toFixed(1)} km, ${(oy / 1000).toFixed(1)} km out` + (s > 0 ? ' ▸' : ''), ex + (s > 0 ? -2 : 2) * dpr, ey);
        }
      }
    }
    // particles: draw by state so leaks stay on top
    const pos = d.pos, ds = d.ds, n = ds.length, sz = Math.max(2.6, 3.2 * dpr);
    const cols = [C.grey, C.teal, C.leak, C.teal2], order = [0, 3, 1, 2];
    for (const s of order) {
      ctx.fillStyle = cols[s]; ctx.globalAlpha = s === 0 ? 0.75 : 0.95;
      for (let i = 0; i < n; i++) {
        if (ds[i] !== s) continue;
        let px = X(pos[2 * i]), py = Y(pos[2 * i + 1]);
        if (s === 2) {   // leaked: fan out in a small "plant" plume below the intake so the count is visible
          const a = (i * 2.399) % (2 * Math.PI), rr = Math.sqrt((i % 97) / 97) * 9 * dpr; px = X(0) + Math.cos(a) * rr; py = Y(0) + Math.abs(Math.sin(a)) * rr * 0.6 + 2 * dpr;
        }
        if (px < -2 || px > W + 2 || py < -2 || py > Hh) continue;
        ctx.fillRect(px - sz / 2, py - sz / 2, sz, sz);
      }
    }
    ctx.globalAlpha = 1;
    // title + counts
    const capPct = 100 * d.res.captured_frac;
    ctx.textAlign = 'left'; ctx.font = `600 ${12 * dpr}px sans-serif`; ctx.fillStyle = sys ? C.teal2 : C.text;
    ctx.fillText(title, 10 * dpr, 18 * dpr);
    ctx.font = `${11 * dpr}px sans-serif`; ctx.fillStyle = C.muted;
    ctx.fillText(`t = ${f.hour.toFixed(0)} / ${f.hours} h`, 10 * dpr, 33 * dpr);
    ctx.fillStyle = C.leak; ctx.fillText(`reached plant ${capPct.toFixed(1)}%`, 10 * dpr, 47 * dpr);
    // scale bar
    const sb = step, sbx = W - 14 * dpr - sb * sc, sby = Hh - coast - 10 * dpr;
    ctx.strokeStyle = C.muted; ctx.lineWidth = 1.5 * dpr; ctx.beginPath(); ctx.moveTo(sbx, sby); ctx.lineTo(sbx + sb * sc, sby); ctx.stroke();
    ctx.fillStyle = C.muted; ctx.textAlign = 'center'; ctx.fillText(sb >= 1000 ? `${sb / 1000} km` : `${sb} m`, sbx + sb * sc / 2, sby - 4 * dpr);
    // tide clock
    const cx = W - 34 * dpr, cy = 34 * dpr, cr = 20 * dpr;
    ctx.strokeStyle = C.line; ctx.lineWidth = 2 * dpr; ctx.beginPath(); ctx.arc(cx, cy, cr, 0, 2 * Math.PI); ctx.stroke();
    ctx.fillStyle = C.panel; ctx.fill();
    const ang = f.tidePhase - Math.PI / 2;
    ctx.strokeStyle = C.teal; ctx.lineWidth = 2 * dpr; ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(cx + Math.cos(ang) * (cr - 4 * dpr), cy + Math.sin(ang) * (cr - 4 * dpr)); ctx.stroke();
    ctx.fillStyle = C.muted; ctx.font = `${9.5 * dpr}px sans-serif`; ctx.textAlign = 'right';
    ctx.fillText('M2 tide', cx - cr - 5 * dpr, cy - 4 * dpr);
    ctx.fillStyle = C.text; ctx.fillText(`${f.tideU >= 0 ? '→' : '←'} ${(Math.abs(f.tideU) * 100).toFixed(1)} cm/s`, cx - cr - 5 * dpr, cy + 9 * dpr);
  }

  // ------------------------------------------------------------------ KPIs, ledger
  const fmt = (v, d = 1) => (v == null || isNaN(v) ? '—' : v.toLocaleString(undefined, { maximumFractionDigits: d, minimumFractionDigits: d }));
  function kpis() {
    const f = S.frame; if (!f) return;
    const j = f.jazr, t = f.today, jp = 100 * j.res.captured_frac, tp = t ? 100 * t.res.captured_frac : null;
    const relT = j.cum.released * j.tonPer;
    const B = '<span class="tg b">BEFORE</span>', W = '<span class="tg w">WITH JAZR</span>';
    const items = [
      ['before', B + 'Reached plant', tp == null ? '—' : fmt(tp) + '%', 'today, no system'],
      ['jz', W + 'Reached plant', fmt(jp) + '%', S.mc ? `MC P50 ${fmt(S.mc.endP[1] * 100)}% at end` : `≈ 1 − η_r = ${fmt(100 * (1 - params().eta_r))}%`],
      ['jz', W + 'Reduction vs BEFORE', tp ? fmt(tp - jp) + ' pp' : '—', tp ? `${fmt(tp > 0 ? tp / Math.max(jp, 0.01) : 0)}× fewer` : ''],
      ['jz', B + '0 t → ' + W + 'saved alive', fmt(relT * SURVIVAL, 0) + ' t', `released ×${SURVIVAL} · cons. ${fmt(relT * SURV_MC, 0)} t`],
      ['jz', W + 'Diverted (cum.)', fmt(j.cum.routed * j.tonPer, 0) + ' t', `${fmt(j.res.mean_handlings, 2)} handlings / animal`],
      ['leak', W + 'Leaked to plant', fmt(j.cum.captured * j.tonPer, 0) + ' t', tp ? `BEFORE ${fmt(t.cum.captured * t.tonPer, 0)} t` : ''],
      ['', W + 'Return fraction', fmt(100 * j.res.return_frac) + '%', `outlet ${f.outlet.pol}`],
      ['', 'Sim clock', `${fmt(f.hour, 0)} h`, `of ${f.hours} h · ${S.speed >= 1000 ? 'max' : S.speed + '×'}`],
    ];
$('kpis').innerHTML = items.map(([c, l, v, s]) => `<div class="kpi ${c}"><div class="l">${l}</div><div class="v">${v}</div><div class="s">${s}</div></div>`).join('');
  }
  function ledger() {
    const f = S.frame; if (!f) return;
    const j = f.jazr, tp = j.tonPer, sw = j.res.swarm_tonnes;
    const rel = j.cum.released * tp, dead = rel * (1 - SURVIVAL);
    const rows = [
      ['Swarm (' + fmt(sw * 1000 / 0.33 / 1e6, 2) + ' M animals × 0.33 kg)', sw, C.grey],
      ['Diverted by inner screen (events)', j.cum.routed * tp, C.teal],
      ['Released alive (× 0.978 budget)', rel * SURVIVAL, C.teal2],
      ['Handling mortality est. (budget) → reuse', dead, C.muted],
      ['In system now', j.nHeld * tp, C.teal],
      ['Dispersed > 2 km', j.res.far_frac * sw, C.grey],
      ['Leaked to plant (JAZR)', j.cum.captured * tp, C.leak],
    ];
    if (f.today) rows.push(['Leaked to plant (Today)', f.today.cum.captured * f.today.tonPer, C.leak]);
    const max = Math.max(...rows.map((r) => r[1]), 1);
    $('ledger').innerHTML = '<table><tr><th>Tonnes (cumulative)</th><th>t</th></tr>' + rows.map(([l, v, c]) =>
      `<tr><td>${l}<div class="bar"><div style="width:${(100 * v / max).toFixed(1)}%;background:${c}"></div></div></td><td>${fmt(v, 0)}</td></tr>`).join('') + '</table>' +
      `<table style="margin-top:8px"><tr><th>Survival per handling</th><th>est.</th><th>alive, t</th></tr>` +
      `<tr><td>Engineering budget (9-stage chain)</td><td>${SURVIVAL}</td><td>${fmt(rel * SURVIVAL, 0)}</td></tr>` +
      `<tr><td>Conservative Monte Carlo (0.68–0.85)</td><td>${SURV_MC}</td><td>${fmt(rel * SURV_MC, 0)}</td></tr>` +
      `<tr><td>Design target</td><td>≥ 0.95</td><td>${fmt(rel * 0.95, 0)}</td></tr></table>` +
      `<div class="note">Estimates, not measurements (TESTS/10_mechanisms/survival_budget.csv; conservative MC). Animals handled k times survive s^k: mean ${fmt(100 * j.res.survival_handled, 1)}% (budget) / ${fmt(100 * survK(j, SURV_MC), 1)}% (conservative) over handled animals.</div>`;
  }

  // ------------------------------------------------------------------ charts
  const CH = {};
  const base = () => ({
    backgroundColor: 'transparent', animation: false, textStyle: { color: C.muted, fontSize: 11 },
    grid: { left: 44, right: 12, top: 26, bottom: 30 },
    tooltip: { trigger: 'axis', backgroundColor: C.panel, borderColor: C.line, textStyle: { color: C.text, fontSize: 11 } },
    legend: { top: 0, right: 0, textStyle: { color: C.muted, fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
    xAxis: { type: 'value', axisLine: { lineStyle: { color: C.line } }, splitLine: { show: false }, axisLabel: { color: C.muted } },
    yAxis: { type: 'value', axisLine: { lineStyle: { color: C.line } }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisLabel: { color: C.muted } },
  });
  function chart(id) {
    if (!window.echarts) { $(id).innerHTML = '<div class="note">Chart library unavailable (offline?).</div>'; return null; }
    if (!CH[id]) CH[id] = echarts.init($(id), null, { renderer: 'canvas' });
    return CH[id];
  }
  // P10-P90 band as one closed polygon (custom series): robust on a value x-axis
  function band(xs, lo, hi, col) {
    return { type: 'custom', silent: true, z: 1, tooltip: { show: false }, data: [[xs[0], lo[0]]],
      renderItem: (prm, api) => {
        const pts = xs.map((x, i) => api.coord([x, hi[i]])).concat(xs.map((x, i) => api.coord([x, lo[i]])).reverse());
        return { type: 'polygon', shape: { points: pts }, style: { fill: col, opacity: 0.2 } };
      } };
  }
  const pairs = (h, v) => h.map((x, i) => [x, +v[i].toFixed(3)]);
  function charts() {
    const f = S.frame; if (!f) return;
    const hrs = f.hours;
    // 1. % reaching the plant
    const c1 = chart('chCap');
    if (c1) {
      const series = [];
      if (S.mc) {
        const H = S.mc.jazr.p10.map((_, i) => i);
        const fan = (o, name, col) => [
          band(H, o.p10, o.p90, col),
          { name: name + ' P50', type: 'line', data: pairs(H, o.p50), lineStyle: { color: col, type: 'dashed', width: 1 }, itemStyle: { color: col }, symbol: 'none' },
        ];
        series.push(...fan(S.mc.today, 'MC Today', C.grey), ...fan(S.mc.jazr, 'MC JAZR', C.teal));
      }
      if (f.today) series.push({ name: 'Today', type: 'line', data: pairs(f.today.series.h, f.today.series.capPct), symbol: 'none', lineStyle: { color: C.grey, width: 2 }, itemStyle: { color: C.grey } });
      series.push({ name: 'JAZR', type: 'line', data: pairs(f.jazr.series.h, f.jazr.series.capPct), symbol: 'none', lineStyle: { color: C.teal, width: 2.5 }, itemStyle: { color: C.teal } });
      c1.setOption(Object.assign(base(), {
        legend: Object.assign(base().legend, { data: ['Today', 'JAZR'].concat(S.mc ? ['MC Today P50', 'MC JAZR P50'] : []) }),
        xAxis: Object.assign(base().xAxis, { min: 0, max: hrs, name: 'h', nameGap: 4 }), yAxis: Object.assign(base().yAxis, { min: 0, max: 100, axisLabel: { color: C.muted, formatter: '{value}%' } }),
        series,
      }), true);
    }
    // 2. flows t/h
    const c2 = chart('chFlow');
    if (c2) {
      const s = f.jazr.series, series = [
        { name: 'Diverted', type: 'line', data: pairs(s.h, s.divTph), symbol: 'none', lineStyle: { color: C.teal, width: 1.8 }, itemStyle: { color: C.teal } },
        { name: 'Released', type: 'line', data: pairs(s.h, s.relTph), symbol: 'none', lineStyle: { color: C.teal2, width: 1.2, type: 'dotted' }, itemStyle: { color: C.teal2 } },
        { name: 'Leaked', type: 'line', data: pairs(s.h, s.leakTph), symbol: 'none', lineStyle: { color: C.leak, width: 1.8 }, itemStyle: { color: C.leak } },
      ];
      if (f.today) series.push({ name: 'Leaked · Today', type: 'line', data: pairs(f.today.series.h, f.today.series.leakTph), symbol: 'none', lineStyle: { color: C.leak, width: 1, type: 'dashed', opacity: 0.6 }, itemStyle: { color: C.leak } });
      c2.setOption(Object.assign(base(), { xAxis: Object.assign(base().xAxis, { min: 0, max: hrs, name: 'h', nameGap: 4 }), yAxis: Object.assign(base().yAxis, { name: 't/h', nameGap: 6 }), series }), true);
    }
    // 4. histogram
    const c4 = chart('chHist');
    if (c4) {
      const h = f.jazr.hist, N = h.reduce((a, b) => a + b, 0);
      c4.setOption(Object.assign(base(), {
        tooltip: Object.assign(base().tooltip, { trigger: 'item', formatter: (p) => `${p.name} handlings: ${p.value.toFixed(1)}% of animals` }),
        xAxis: { type: 'category', data: ['0', '1', '2', '3', '4', '5', '6+'], axisLine: { lineStyle: { color: C.line } }, axisLabel: { color: C.muted }, name: 'handlings', nameLocation: 'middle', nameGap: 20 },
        yAxis: Object.assign(base().yAxis, { axisLabel: { color: C.muted, formatter: '{value}%' } }),
        series: [{ type: 'bar', data: h.map((v, i) => ({ value: 100 * v / N, itemStyle: { color: i === 0 ? C.grey : C.teal } })), barWidth: '60%' }],
      }), true);
    }
  }
  function retChart() {
    const c = chart('chRet'); if (!c || !S.ret) return;
    const r = S.ret;
    c.setOption(Object.assign(base(), {
      tooltip: Object.assign(base().tooltip, { valueFormatter: (v) => v.toFixed(1) + '%' }),
      xAxis: Object.assign(base().xAxis, { name: 'km', nameGap: 4, min: 0, max: 16 }), yAxis: Object.assign(base().yAxis, { min: 0, axisLabel: { color: C.muted, formatter: '{value}%' } }),
      series: [
        { name: 'Alongshore (3 km out)', type: 'line', data: r.map((x) => [x.d / 1000, 100 * x.alongReturn]), lineStyle: { color: C.teal, width: 2 }, itemStyle: { color: C.teal }, symbolSize: 5 },
        { name: 'Offshore (x 1.2 km)', type: 'line', data: r.map((x) => [x.d / 1000, 100 * x.offReturn]), lineStyle: { color: C.grey, width: 2 }, itemStyle: { color: C.grey }, symbolSize: 5 },
      ],
    }), true);
  }
  function etaChart() {
    const c = chart('chEta'); if (!c || !S.eta) return;
    const r = S.eta, cur = params().eta_r;
    c.setOption(Object.assign(base(), {
      tooltip: Object.assign(base().tooltip, { valueFormatter: (v) => (typeof v === 'number' ? v.toFixed(1) + '%' : v) }),
      legend: Object.assign(base().legend, { data: ['Reaching plant', '1 − η_r'] }),
      xAxis: Object.assign(base().xAxis, { min: 0.5, max: 1, name: 'η_r', nameGap: 4 }), yAxis: Object.assign(base().yAxis, { min: 0, axisLabel: { color: C.muted, formatter: '{value}%' } }),
      series: [
        band(r.map((x) => x.eta_r), r.map((x) => 100 * x.lo), r.map((x) => 100 * x.hi), C.teal),
        { name: 'Reaching plant', type: 'line', data: r.map((x) => [x.eta_r, 100 * x.mean]), lineStyle: { color: C.teal, width: 2 }, itemStyle: { color: C.teal }, symbolSize: 5,
          markLine: { symbol: 'none', silent: true, lineStyle: { color: C.muted, type: 'dotted' }, label: { show: false }, data: [{ xAxis: cur }] } },
        { name: '1 − η_r', type: 'line', data: [[0.5, 50], [1, 0]], lineStyle: { color: C.grey, type: 'dashed', width: 1 }, symbol: 'none', itemStyle: { color: C.grey } },
      ],
    }), true);
  }

  // ------------------------------------------------------------------ export
  function download(name, blob) { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); }
  function exportCSV() {
    const f = S.frame; if (!f) return;
    const p = params(), s = f.jazr.series, t = f.today && f.today.series;
    const lines = ['# JAZR toy twin export. Model-based simulation (toy twin, validated against our Python model, not field data)',
      '# params ' + JSON.stringify(p),
      'hour,today_reaching_pct,jazr_reaching_pct,diverted_t_per_h,released_t_per_h,leaked_t_per_h,in_system_t' + (S.mc ? ',mc_jazr_p10,mc_jazr_p50,mc_jazr_p90,mc_today_p50' : '')];
    for (let i = 0; i < s.h.length; i++) {
      const row = [s.h[i], t && t.capPct[i] != null ? t.capPct[i].toFixed(3) : '', s.capPct[i].toFixed(3), s.divTph[i].toFixed(3), s.relTph[i].toFixed(3), s.leakTph[i].toFixed(3), s.heldT[i].toFixed(3)];
      if (S.mc) { const h = s.h[i]; row.push(S.mc.jazr.p10[h].toFixed(3), S.mc.jazr.p50[h].toFixed(3), S.mc.jazr.p90[h].toFixed(3), S.mc.today.p50[h].toFixed(3)); }
      lines.push(row.join(','));
    }
    if (S.eta) { lines.push('', 'eta_r,mean_reaching_pct,lo_pct,hi_pct'); S.eta.forEach((r) => lines.push([r.eta_r, (100 * r.mean).toFixed(2), (100 * r.lo).toFixed(2), (100 * r.hi).toFixed(2)].join(','))); }
    if (S.ret) { lines.push('', 'outlet_km,alongshore_return_pct,alongshore_reaching_pct,offshore_return_pct,offshore_reaching_pct'); S.ret.forEach((r) => lines.push([r.d / 1000, (100 * r.alongReturn).toFixed(2), (100 * r.alongCap).toFixed(2), (100 * r.offReturn).toFixed(2), (100 * r.offCap).toFixed(2)].join(','))); }
    download('jazr_sim.csv', new Blob([lines.join('\n')], { type: 'text/csv' }));
  }
  function exportPNG() {
    const maps = [cvs.jazr]; if ($('sbs').checked) maps.unshift(cvs.today);
    const imgs = ['chCap', 'chFlow', 'chHist'].map((id) => CH[id]).filter(Boolean).map((c) => c.getDataURL({ pixelRatio: 2, backgroundColor: C.panel }));
    const W = 1800, mapH = maps.length === 2 ? Math.round(W / 2 * 0.75) : Math.round(W * 0.5), chH = 420, out = document.createElement('canvas');
    out.width = W; out.height = 60 + mapH + chH + 30; const g = out.getContext('2d');
    g.fillStyle = C.bg; g.fillRect(0, 0, out.width, out.height);
    g.fillStyle = C.text; g.font = '600 26px sans-serif'; g.fillText('JAZR v5 · Live Simulation', 20, 38);
    g.fillStyle = C.muted; g.font = '18px sans-serif'; g.fillText('Model-based simulation (toy twin, validated against our Python model, not field data)', 360, 38);
    maps.forEach((c, i) => g.drawImage(c, i * W / maps.length, 60, W / maps.length, mapH));
    let done = 0; const y = 60 + mapH + 10;
    const finish = () => { g.fillStyle = C.dim; g.font = '14px sans-serif'; g.fillText('params ' + JSON.stringify(params()), 20, out.height - 10); out.toBlob((b) => download('jazr_sim.png', b), 'image/png'); };
    if (!imgs.length) return finish();
    imgs.forEach((src, i) => { const im = new Image(); im.onload = () => { g.drawImage(im, i * W / imgs.length + 5, y, W / imgs.length - 10, chH - 10); if (++done === imgs.length) finish(); }; im.src = src; });
  }
  function postParent() {
    if (!embedded || !S.frame) return;
    const f = S.frame;
    try { window.parent.postMessage({ source: 'jazr-sim', hour: f.hour, jazrPct: 100 * f.jazr.res.captured_frac, todayPct: f.today ? 100 * f.today.res.captured_frac : null, params: params() }, '*'); } catch (e) { /* ignore */ }
  }
  // expose a tiny API for the host dashboard / tests
  window.JAZRSim = { restart, params, state: S, runMC: () => $('bMC').click(), runSweep: () => $('bSweep').click() };

  labels(); sizeCanvases(); layoutMaps(); restart();
  if (Q.get('mc') === '1') setTimeout(() => $('bMC').click(), 300);
  if (Q.get('sweep') === '1') setTimeout(() => $('bSweep').click(), 300);
})();
