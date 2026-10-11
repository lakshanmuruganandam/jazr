/* JAZR toy twin — JavaScript port of twin/jazr_twin.py (reduced-order plan-view particle model).
 * Model-based simulation (toy twin, validated against our Python model, not field data).
 *
 * Physics (same as Python):
 *   coast y = 0 (reflecting, y -> |y|); intake at origin; half-plane radial sink u = -Q/(pi r h), Q = 400 m3/s, h = 3.5 m
 *   M2 alongshore tide u = U0 sin(wt), U0 = 0.117 m/s, T = 12.42 h; residual drift (ur, vr); optional wind drift
 *   jellyfish = drifters + random-heading swimming with persistent heading noise (theta += N(0, 0.3) per step)
 *   captured by the intake (leak) if r < 60 m
 * System:
 *   optional outer ring/guide line at r = 500 m (eta_g per inward crossing)
 *   inner guard / angled screen at r = 120 m (eta_r per inward crossing) -> routed to a pocket at x = +/-600 m
 *   release policies: immediate (pocket gate 600, 150) | near (1200, 5000) | far (10000, 3000) | auto (far if vr < 0)
 *   "hold" (keep until end, no release) exists ONLY to reproduce the removed v4 "recover" validation case.
 *
 * This file runs three ways:
 *   1. as a Web Worker  (new Worker('twin.worker.js'))
 *   2. loaded by <script> in the page -> exposes window.jazrTwinMain so app.js can build a Blob worker (file:// fallback)
 *   3. in Node          (require('./twin.worker.js')) for headless validation (validate.js)
 */
function jazrTwinMain(scope) {
  'use strict';
  const Q = 400.0, H = 3.5, U0 = 0.117, W = 2 * Math.PI / (12.42 * 3600);
  const R_CAP = 60.0, R_I = 500.0, R_G = 120.0, POCKET_X = 600.0, GATE_Y = 150.0;
  const BAND_X0 = -4000, BAND_X1 = 4000, BAND_Y0 = 50, BAND_Y1 = 1500;
  const SURVIVAL = 0.9782;   // TESTS/10_mechanisms/survival_budget.csv, end-to-end HydroLift chain (ESTIMATE)
  const WINDAGE = 0.01;      // assumed: 1% of wind speed as surface drift on the bells (assumption, not measured)
  const OUTLETS = { immediate: [POCKET_X, GATE_Y], near: [1200, 5000], far: [10000, 3000], hold: [1200, 5000] };

  // ------------------------------------------------------------- seeded RNG (sfc32 + Box-Muller)
  function makeRng(seed) {
    let a = 0x9E3779B9 ^ (seed | 0), b = 0x243F6A88 + (seed * 2654435761 >>> 0), c = 0xB7E15162 ^ (seed << 7), d = 1 ^ seed;
    function next() {
      a >>>= 0; b >>>= 0; c >>>= 0; d >>>= 0;
      let t = (a + b) | 0; a = b ^ (b >>> 9); b = (c + (c << 3)) | 0; c = (c << 21) | (c >>> 11);
      d = (d + 1) | 0; t = (t + d) | 0; c = (c + t) | 0;
      return (t >>> 0) / 4294967296;
    }
    for (let i = 0; i < 20; i++) next();
    let spare = null;
    function normal() {
      if (spare !== null) { const s = spare; spare = null; return s; }
      let u = 0; while (u === 0) u = next();
      const v = next(), m = Math.sqrt(-2 * Math.log(u));
      spare = m * Math.sin(2 * Math.PI * v); return m * Math.cos(2 * Math.PI * v);
    }
    return { random: next, normal };
  }

  const DEFAULTS = {
    N: 1500, hours: 72, dt: 60, swim: 0.036, ur: 0, vr: 0, windSpeed: 0, windDir: 90,
    system: true, ring: false, eta_g: 0.4, eta_r: 0.9, policy: 'far', gate_x: null, gate_y: null,
    phase0: 0, seed: 1, dens: 0.1, mass: 0.33,
  };

  function resolveOutlet(p) {
    let pol = p.policy;
    if (pol === 'auto') pol = p.vr < 0 ? 'far' : 'near';
    const o = OUTLETS[pol] || OUTLETS.immediate;
    return { pol, gx: p.gate_x != null ? p.gate_x : o[0], gy: p.gate_y != null ? p.gate_y : o[1] };
  }

  function Twin(params) {
    const p = Object.assign({}, DEFAULTS, params);
    const N = p.N | 0, rng = makeRng(p.seed | 0);
    const out = resolveOutlet(p);
    const x = new Float64Array(N), y = new Float64Array(N), th = new Float64Array(N), rprev = new Float64Array(N);
    const st = new Uint8Array(N), side = new Int8Array(N), heldT = new Float64Array(N), nInt = new Uint16Array(N);
    const relFlag = new Uint8Array(N), everRel = new Uint8Array(N);
    let n = 0;
    while (n < N) {   // initial band outside the ring (the alert gives lead time)
      const xs = BAND_X0 + (BAND_X1 - BAND_X0) * rng.random(), ys = BAND_Y0 + (BAND_Y1 - BAND_Y0) * rng.random();
      if (Math.sqrt(xs * xs + ys * ys) > R_I + 50) { x[n] = xs; y[n] = ys; n++; }
    }
    for (let i = 0; i < N; i++) { th[i] = 2 * Math.PI * rng.random(); rprev[i] = Math.sqrt(x[i] * x[i] + y[i] * y[i]); }
    const app = p.dens * (BAND_X1 - BAND_X0) * (BAND_Y1 - BAND_Y0) * H / N;   // animals per particle
    const tonPer = app * p.mass / 1000;
    const wr = p.windDir * Math.PI / 180;   // direction the wind drift goes TOWARD: 0 = +x alongshore, 90 = offshore (+y), 270 = onshore
    const uw = WINDAGE * p.windSpeed * Math.cos(wr), vw = WINDAGE * p.windSpeed * Math.sin(wr);
    const etaG = p.ring ? p.eta_g : 0.0;
    const S = {
      p, out, N, x, y, st, nInt, everRel, app, tonPer, k: 0, t: p.phase0 / W,
      steps: Math.round(p.hours * 3600 / p.dt), stepsPerHour: Math.round(3600 / p.dt),
      cum: { routed: 0, released: 0, captured: 0, returns: 0 }, hourAcc: { routed: 0, released: 0, captured: 0 },
      series: { h: [0], capPct: [0], divTph: [0], relTph: [0], leakTph: [0], heldT: [0] },
      peakHeld: 0, nHeld: 0,
    };
    const dt = p.dt, swim = p.swim, ur = p.ur + uw, vr = p.vr + vw, system = !!p.system, etaR = p.eta_r;
    S.done = () => S.k >= S.steps;
    S.step = function (nsteps) {
      for (let s = 0; s < nsteps && S.k < S.steps; s++) {
        const uT = U0 * Math.sin(W * S.t);
        const sgn = uT !== 0 ? Math.sign(uT) : 1;
        let routedN = 0, capN = 0, relN = 0;
        // release decision (same for all held animals this step)
        let relAll = false;
        if (system) relAll = out.pol !== 'hold';
        for (let i = 0; i < N; i++) {
          const sti = st[i];
          th[i] += 0.3 * rng.normal();
          if (sti !== 0) {
            if (sti === 1 && system) {           // held in the pocket
              heldT[i] += dt;
              if (relAll) {
                st[i] = 0; x[i] = side[i] * out.gx; y[i] = out.gy;
                rprev[i] = Math.sqrt(x[i] * x[i] + y[i] * y[i]);
                relFlag[i] = 1; everRel[i] = 1; relN++;
              }
            }
            continue;
          }
          const xi = x[i], yi = y[i];
          const r0 = Math.sqrt(xi * xi + yi * yi) + 1e-9;
          const us = -Q / (Math.PI * r0 * H);
          const u = uT + ur + us * xi / r0, v = vr + us * yi / r0;
          let nx = xi + (u + swim * Math.cos(th[i])) * dt;
          let ny = yi + (v + swim * Math.sin(th[i])) * dt;
          if (ny < 0) ny = -ny;
          x[i] = nx; y[i] = ny;
          const r = Math.sqrt(nx * nx + ny * ny);
          const rp = rprev[i];
          if (system) {
            let routed = false;
            if (rp >= R_I && r < R_I && etaG > 0 && rng.random() < etaG) routed = true;
            else if (rp >= R_G && r < R_G && rng.random() < etaR) routed = true;
            if (routed) {
              if (relFlag[i]) { S.cum.returns++; relFlag[i] = 0; }
              side[i] = sgn; st[i] = 1; heldT[i] = 0; nInt[i]++; routedN++;
              x[i] = sgn * POCKET_X; y[i] = 30.0;
              if (relAll) {     // immediate-style release in the same step (Python releases after routing)
                st[i] = 0; x[i] = sgn * out.gx; y[i] = out.gy; relFlag[i] = 1; everRel[i] = 1; relN++;
              }
              rprev[i] = Math.sqrt(x[i] * x[i] + y[i] * y[i]);
              continue;
            }
          }
          if (r < R_CAP) { st[i] = 2; capN++; if (relFlag[i]) { S.cum.returns++; relFlag[i] = 0; } }
          rprev[i] = r;
        }
        S.cum.routed += routedN; S.cum.released += relN; S.cum.captured += capN;
        S.hourAcc.routed += routedN; S.hourAcc.released += relN; S.hourAcc.captured += capN;
        let held = 0; for (let i = 0; i < N; i++) if (st[i] === 1) held++;
        S.nHeld = held; if (held > S.peakHeld) S.peakHeld = held;
        S.t += dt; S.k++;
        if (S.k % S.stepsPerHour === 0) {
          const ser = S.series;
          ser.h.push(S.k / S.stepsPerHour);
          ser.capPct.push(100 * S.cum.captured / N);
          ser.divTph.push(S.hourAcc.routed * tonPer);
          ser.relTph.push(S.hourAcc.released * tonPer);
          ser.leakTph.push(S.hourAcc.captured * tonPer);
          ser.heldT.push(held * tonPer);
          S.hourAcc = { routed: 0, released: 0, captured: 0 };
        }
      }
    };
    S.tideU = () => U0 * Math.sin(W * S.t);
    S.tidePhase = () => (W * S.t) % (2 * Math.PI);
    S.result = function () {
      let mh = 0, far = 0, alive = 0, handled = 0;
      for (let i = 0; i < N; i++) {
        mh += nInt[i];
        if (st[i] === 0 && Math.sqrt(x[i] * x[i] + y[i] * y[i]) > 2000) far++;
        if (nInt[i] > 0) { handled++; alive += Math.pow(SURVIVAL, nInt[i]); }
      }
      return {
        captured_frac: S.cum.captured / N, captured_tonnes: S.cum.captured * tonPer, swarm_tonnes: N * tonPer,
        mean_handlings: mh / N, peak_held_tonnes: S.peakHeld * tonPer, still_held_frac: S.nHeld / N, far_frac: far / N,
        return_frac: S.cum.released ? S.cum.returns / S.cum.released : 0, releases: S.cum.released,
        handled_frac: handled / N, survival_handled: handled ? alive / handled : 1,
      };
    };
    S.histogram = function () {   // re-handling histogram: 0,1,2,...,6+
      const h = new Array(7).fill(0);
      for (let i = 0; i < N; i++) h[Math.min(6, nInt[i])]++;
      return h;
    };
    S.snapshot = function () {   // positions (float32) + display state: 0 free, 1 held, 2 leaked, 3 free after release
      const pos = new Float32Array(2 * N), ds = new Uint8Array(N);
      for (let i = 0; i < N; i++) {
        pos[2 * i] = x[i]; pos[2 * i + 1] = y[i];
        ds[i] = st[i] === 0 ? (everRel[i] ? 3 : 0) : st[i];
      }
      return { pos, ds };
    };
    return S;
  }

  function runToEnd(params) { const T = Twin(params); T.step(T.steps); return T; }

  function quantile(sorted, q) {
    const pos = (sorted.length - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
  }

  const api = { Twin, runToEnd, resolveOutlet, quantile, makeRng,
    CONST: { Q, H, U0, W, R_CAP, R_I, R_G, POCKET_X, GATE_Y, SURVIVAL, WINDAGE, OUTLETS, BAND: [BAND_X0, BAND_X1, BAND_Y0, BAND_Y1] } };
  if (!scope) return api;

  // ------------------------------------------------------------- worker protocol
  let live = null, timer = null, speed = 1, running = false;
  const post = (m, tr) => scope.postMessage(m, tr || []);

  function liveFrame() {
    const J = live.jazr, T = live.today;
    const sj = J.snapshot(), st = T ? T.snapshot() : null;
    const tr = [sj.pos.buffer, sj.ds.buffer];
    if (st) tr.push(st.pos.buffer, st.ds.buffer);
    post({
      type: 'frame', hour: J.k / J.stepsPerHour, hours: J.p.hours, done: J.done(), running,
      tideU: J.tideU(), tidePhase: J.tidePhase(), outlet: J.out,
      jazr: { pos: sj.pos, ds: sj.ds, series: J.series, cum: J.cum, res: J.result(), hist: J.histogram(), tonPer: J.tonPer, nHeld: J.nHeld },
      today: T ? { pos: st.pos, ds: st.ds, series: T.series, cum: T.cum, res: T.result(), tonPer: T.tonPer } : null,
    }, tr);
  }
  function tick() {
    timer = null;
    if (!live || !running) return;
    const t0 = Date.now();
    // 1x = 1 simulated hour per real second; frame every ~33 ms
    let steps = speed >= 1000 ? 1e9 : Math.max(1, Math.round(speed * live.jazr.stepsPerHour / 30));
    if (speed >= 1000) {   // max: as much as fits in ~30 ms
      while (Date.now() - t0 < 30 && !live.jazr.done()) { live.jazr.step(10); if (live.today) live.today.step(10); }
    } else { live.jazr.step(steps); if (live.today) live.today.step(steps); }
    if (live.jazr.done()) running = false;
    liveFrame();
    if (running) timer = setTimeout(tick, Math.max(0, 33 - (Date.now() - t0)));
  }

  function batch(m) {
    const P = m.params;
    if (m.cmd === 'mc') {   // replicates [repStart, repStart+repCount): raw hourly series, the page merges them into a fan
      const r0 = makeRng((P.seed | 0) * 7919 + 13), ph = [];
      for (let k = 0; k < m.repStart + m.repCount; k++) ph.push(2 * Math.PI * r0.random());
      for (let k = m.repStart; k < m.repStart + m.repCount; k++) {
        const sd = (P.seed | 0) * 1000 + k + 1;
        const a = runToEnd(Object.assign({}, P, { phase0: ph[k], seed: sd, system: true }));
        const b = runToEnd(Object.assign({}, P, { phase0: ph[k], seed: sd, system: false }));
        post({ type: 'mcRep', job: m.job, rep: k, jazr: a.series.capPct, today: b.series.capPct, end: a.result().captured_frac });
      }
    } else if (m.cmd === 'sweepEta') {
      const vals = m.values, rows = [];
      const phases = [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2];
      let done = 0;
      for (const e of vals) {
        const c = [];
        for (const ph of phases) { c.push(runToEnd(Object.assign({}, P, { eta_r: e, phase0: ph, system: true })).result().captured_frac); done++; post({ type: 'progress', job: m.job, done, total: vals.length * phases.length }); }
        c.sort((a, b) => a - b);
        rows.push({ eta_r: e, mean: c.reduce((a, b) => a + b, 0) / c.length, lo: c[0], hi: c[c.length - 1] });
      }
      post({ type: 'sweepEta', job: m.job, rows });
    } else if (m.cmd === 'sweepOutlet') {
      const dists = m.distances, rows = [];
      let done = 0;
      for (const d of dists) {
        const along = runToEnd(Object.assign({}, P, { policy: 'near', gate_x: d, gate_y: 3000, system: true })).result();
        done++; post({ type: 'progress', job: m.job, done, total: dists.length * 2 });
        const off = runToEnd(Object.assign({}, P, { policy: 'near', gate_x: 1200, gate_y: d, system: true })).result();
        done++; post({ type: 'progress', job: m.job, done, total: dists.length * 2 });
        rows.push({ d, alongReturn: along.return_frac, alongCap: along.captured_frac, offReturn: off.return_frac, offCap: off.captured_frac });
      }
      post({ type: 'sweepOutlet', job: m.job, rows });
    }
  }

  scope.onmessage = function (e) {
    const m = e.data || {};
    try {
      if (m.cmd === 'start') {
        if (timer) clearTimeout(timer);
        const P = m.params;
        live = { jazr: Twin(Object.assign({}, P, { system: true })), today: m.today === false ? null : Twin(Object.assign({}, P, { system: false })) };
        speed = m.speed || speed; running = m.autoplay !== false;
        liveFrame(); if (running) timer = setTimeout(tick, 33);
      } else if (m.cmd === 'pause') { running = false; if (timer) { clearTimeout(timer); timer = null; } if (live) liveFrame(); }
      else if (m.cmd === 'resume') { if (live && !live.jazr.done()) { running = true; if (!timer) timer = setTimeout(tick, 0); } }
      else if (m.cmd === 'speed') { speed = m.value; }
      else if (m.cmd === 'stepHours') { if (live) { const n = live.jazr.stepsPerHour * (m.value || 1); live.jazr.step(n); if (live.today) live.today.step(n); liveFrame(); } }
      else if (m.cmd === 'mc' || m.cmd === 'sweepEta' || m.cmd === 'sweepOutlet') batch(m);
    } catch (err) { post({ type: 'error', message: String(err && err.stack || err) }); }
  };
  return api;
}

// ------------------------------------------------------------- bootstrap
(function () {
  if (typeof module !== 'undefined' && module.exports) { module.exports = jazrTwinMain(null); return; }
  if (typeof WorkerGlobalScope !== 'undefined' && typeof self !== 'undefined' && self instanceof WorkerGlobalScope) { jazrTwinMain(self); return; }
  if (typeof window !== 'undefined') { window.jazrTwinMain = jazrTwinMain; }
})();
