/* JAZR Bloom Incident OS — simulated plant + control logic (illustrative).
 * SIMULATED DATA. Physics is simplified; numbers are chosen to be consistent with
 * JAZR v4.1 / v5 design notes and the TESTS/ folder, not measured.
 * Control logic mirrors TESTS/08_controls_extremes_FEA/D_controls/controller.py
 * (pulse rule K=1, lowering L=6, 2oo3 voting, filtered blockage index, persistence,
 * stuck-drive FAULT latch, comms-loss local TDMA + hard-wired busy loop) and
 * TESTS/04_biology_wildlife_ops/bloom_os.py (close RED alert auto-deploy, operator veto).
 * v4.1: RECOVER (lethal) mode removed -> Release-Near / Release-Far only.
 * v5: moving-belt screens (0.5-1.0x sweep), water-only HydroLift (no screws),
 *     side-stream dissolved O2 (no bubbles), eta_r 0.95-0.99 by camera counts. */
(function () {
  'use strict';
  const JZ = (window.JZ = window.JZ || {});

  // ---------------------------------------------------------------- constants
  const C = (JZ.C = {
    LANES: 4, BAYS: 42,
    Q_LANE: 101,          // m3/s per unit, nominal (gives 12 t/h at 0.1/m3, 0.33 kg)  [00_data]
    Q_MAX: 172.5,         // design max per lane                                       [v4 #3]
    MASS: 0.33,           // kg per animal, C. perezi n=503                             [00_data #9]
    SWEEP: 0.50,          // m/s sweep velocity along the 11 deg face (illustrative)
    BELT_RATIO_MIN: 0.5, BELT_RATIO_MAX: 1.0,
    BAY_AREA: 33,         // m2 wetted per bay (<=4.8 m wide)
    COVER: 0.15,          // m2 of mesh blinded per kg of bells (illustrative)
    DP_CLEAN: 60,         // Pa at mean tide, nominal flow (illustrative)
    DP_HARD: 450,         // Pa  -> passive shear-pin relief flap
    BI_H: 0.35, BI_HH: 0.55, PERSIST_S: 20, FILTER_TAU: 30,
    LOWER_S: 80, RAISE_S: 80, L_CONC: 6, K_RAISE: 1,
    DEPLOY_S: 573,        // modelled alert->OPERATE                                    [08 D9]
    VETO_S: 120,          // auto-deploy veto window
    LOCK_CH: 3, LOCK_FILL: 70, LOCK_RISE: 60, LOCK_XFER: 45, LOCK_DRAIN: 45, LOCK_HEAD: 6.0,
    Q_LIFT_LANE: 0.5,     // m3/s per lane to the head tank (2.0 total = pipe)
    PIPE_D: 1.6, PIPE_NEAR_KM: 5.2, PIPE_FAR_KM: 10.5, Q_PIPE: 2.0,
    HT_AREA: 150, HT_SP: 2.5,
    O2_RESP: 0.0715,      // mg O2 / L / h per kg/m3 (0.05 mL/h/g, 30 C)               [04 T1]
    O2_SP_TAIL: 5.5, O2_MIN: 5.0, O2_LL: 3.0, O2_MAX_DISSOLVED: 14,
    DIFFUSER_AREA: 2.4,   // m2 outlet diffuser port area -> exit velocity
    DOA_BASE: 0.008,      // dead/badly damaged on arrival (ASSUMED placeholder)
    TURTLE_CLEAR_S: 60,
  });

  // survival chain — v5 ESTIMATE (no measurements yet; T09/P02 decide)
  JZ.SURV = [ // TESTS/10_mechanisms/survival_budget.csv (all ESTIMATE)
    { k: 'Screen face (belt)', p: 0.998, lo: 0.99, hi: 0.999 },
    { k: 'Entrance + flare', p: 0.999, lo: 0.995, hi: 1.0 },
    { k: 'Dewatering (flat plate)', p: 0.997, lo: 0.985, hi: 0.999 },
    { k: 'Turtle excluder', p: 0.998, lo: 0.99, hi: 0.999 },
    { k: 'HydroLift (water-only)', p: 0.998, lo: 0.99, hi: 0.999 },
    { k: 'Head tank + down-leg', p: 0.999, lo: 0.995, hi: 1.0 },
    { k: 'Pipe 10.5 km, 2.9 h, O2 held', p: 0.995, lo: 0.97, hi: 0.998 },
    { k: 'Diffuser outlet ≤1 m/s', p: 0.999, lo: 0.995, hi: 1.0 },
    { k: 'Post-release 24–96 h', p: 0.995, lo: 0.95, hi: 0.998 },
  ];
  JZ.survEnd = () => JZ.SURV.reduce((a, s) => a * s.p, 1);

  // ---------------------------------------------------------------- RNG
  function rng(seed) {
    let a = seed >>> 0;
    const f = () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
    f.n = () => { let u = 0, v = 0; while (u === 0) u = f(); v = f(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
    return f;
  }
  JZ.rng = rng;
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

  // ---------------------------------------------------------------- scenarios
  const H = 3600;
  JZ.SCENARIOS = {
    calm: { name: 'Calm — no bloom', desc: 'Watch state. No alert, all bays stowed dry. Shows how quiet a high-performance HMI should be.',
      seed: 11, alert: null, peak: 0, dur: 0, eta: 0.995, Hs: 0.25, wind: 4, sst: 31.4, fc: { on: 1.2, al: -0.3 }, events: [], warp: 1800 },
    typical: { name: 'Typical bloom 0.3/m³', desc: 'Alert 2 h ahead (not close) → operator approves → deploy ≈10 min → operate. Typical real onshore drift (2.5 cm/s, Oct–Nov data) → Release-Far, alive.',
      seed: 21, alert: { t: 60, lead: 2.0, level: 'RED' }, peak: 0.3, dur: 30, eta: 0.995, Hs: 0.35, wind: 4.2, sst: 31.4, fc: { on: 2.5, al: -0.3 }, events: [], warp: 6 * H },
    severe: { name: 'Severe bloom 1/m³ (stress)', desc: 'Beyond the 0.3/m³ design density: 8 entrances (high-flux), onshore drift → Release-Far, pipe O₂ margin becomes the limit.',
      seed: 31, alert: { t: 60, lead: 3.0, level: 'RED' }, peak: 1.0, dur: 40, eta: 0.99, Hs: 0.6, wind: 7.5, sst: 33.0, fc: { on: 2.5, al: -0.4 }, events: [], warp: 7 * H },
    late: { name: 'Late alert (24 min lead)', desc: 'Close RED alert, pre-authorised: auto-deploy after a 120 s veto window. Test 04: two approvals → 5% in time; auto → 59%.',
      seed: 41, alert: { t: 60, lead: 0.4, level: 'RED' }, peak: 0.3, dur: 24, eta: 0.995, Hs: 0.3, wind: 4, sst: 31.4, fc: { on: 2.5, al: -0.3 }, events: [], warp: 150 },
    bayfault: { name: 'Bay fault (belt seize + stuck ΔP transmitter)', desc: 'Lane 2 bay 23: belt drive seizes (overcurrent trip) and its winch brake jams → raise fails → stuck-drive FAULT latched → blockage climbs → passive shear-pin flap opens (no power, no comms). Lane 1 bay 8 ΔP transmitter A sticks high → masked by 2oo3 voting.',
      seed: 51, alert: { t: 60, lead: 1.5, level: 'RED' }, peak: 0.3, dur: 30, eta: 0.995, Hs: 0.4, wind: 4.5, sst: 31.4, fc: { on: 2.5, al: -0.3 },
      events: [{ t: 2.4 * H, type: 'xmtr', lane: 0, bay: 7 }, { t: 3.0 * H, type: 'seize', lane: 1, bay: 22 }], warp: 3.25 * H },
    turtle: { name: 'Turtle event', desc: 'Green turtle reaches the lane 3 excluder: grid diverts it to the escape chute, camera+sonar+chute vote 3/3, lock holds. A 1-of-3 sonar ghost also holds the lock (fail-safe). Dugong seen by patrol.',
      seed: 61, alert: { t: 60, lead: 1.5, level: 'RED' }, peak: 0.3, dur: 30, eta: 0.995, Hs: 0.35, wind: 4, sst: 31.4, fc: { on: -0.6, al: -0.3 },
      events: [{ t: 2.6 * H, type: 'turtle', lane: 2, ch: [1, 1, 1], species: 'Green turtle (Chelonia mydas), juvenile' },
        { t: 2.75 * H, type: 'sighting', species: 'Dugong (Dugong dugon)', where: '1.8 km NE of intake breakwater', src: 'Patrol observer' },
        { t: 3.1 * H, type: 'turtle', lane: 0, ch: [0, 1, 0], species: 'Unconfirmed (sonar only)' }], warp: 2.62 * H },
    comms: { name: 'Comms loss (OT network)', desc: 'OT network lost for 40 min: lanes go to local mode (TDMA slot + hard-wired busy loop keeps one bay raising at a time), lowering inhibited, HMI values marked STALE.',
      seed: 71, alert: { t: 60, lead: 1.5, level: 'RED' }, peak: 0.3, dur: 30, eta: 0.995, Hs: 0.5, wind: 5, sst: 31.4, fc: { on: 2.5, al: -0.3 },
      events: [{ t: 2.5 * H, type: 'comms', dur: 40 * 60 }], warp: 2.6 * H },
    onshore: { name: 'Long onshore-drift bloom (10 d) → far release', desc: '10-day bloom with 4.7 cm/s onshore drift (Oct–Nov 10-day p90). Near outlet would return ~half; twin recommends Release-Far ~10 km alongshore down-drift.',
      seed: 81, alert: { t: 60, lead: 3.0, level: 'RED' }, peak: 0.3, dur: 240, eta: 0.995, Hs: 0.45, wind: 6, sst: 30.2, fc: { on: 4.7, al: -0.5 }, events: [], warp: 30 * H },
  };

  // ---------------------------------------------------------------- tide (harmonic, illustrative of the site range ~1.4 m)
  const W = (h) => (2 * Math.PI) / (h * H);
  function tide(t) {
    const t0 = t + 3.2 * H;
    return 0.62 * Math.cos(W(12.42) * t0) + 0.18 * Math.cos(W(12.0) * t0 + 0.7) + 0.16 * Math.cos(W(23.93) * t0 + 1.1) + 0.1 * Math.cos(W(25.82) * t0 + 2.0);
  }
  JZ.tide = tide;
  JZ.tidePhase = (t) => (((W(12.42) * (t + 3.2 * H)) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);

  // ---------------------------------------------------------------- drift ensemble (Release-Near/Far forecast)
  // x alongshore (+ = 070 ENE, towards Ruwais), y offshore (km). Intake mouth at (0,0).
  JZ.GEO = {
    intake: [0, 0], near: [0.6, 5.0], far: [-10.0, 3.0],
    zones: [
      { name: 'Ruwais industrial intakes →', kind: 'intake', x0: 14, x1: 20, y0: 0, y1: 2.5 },
      { name: 'Reef (illustrative)', kind: 'reef', x0: -19, x1: -15.5, y0: 1.0, y1: 3.6 },
      { name: 'Seagrass / turtle foraging (illustrative)', kind: 'reef', x0: 4.5, x1: 9, y0: 0.6, y1: 2.2 },
      { name: 'Beach (illustrative)', kind: 'beach', x0: -6, x1: -2.5, y0: 0, y1: 0.4 },
      { name: 'Beach (illustrative)', kind: 'beach', x0: 10, x1: 13, y0: 0, y1: 0.4 },
    ],
  };
  function ensemble(fc, seed, members = 48, days = 10) {
    const r = rng(seed);
    const out = {};
    for (const key of ['near', 'far']) {
      const [x0, y0] = JZ.GEO[key];
      const steps = days * 24, dist = [], ret = new Array(steps + 1).fill(0), tracks = [];
      const ds = [];
      for (let m = 0; m < members; m++) {
        let x = x0, y = y0, done = false, returned = false;
        const on = (fc.on + 1.0 * r.n()) / 100, al = (fc.al + 0.5 * r.n()) / 100, ph = r() * 6.283;
        const d = [], tr = [[x, y]];
        for (let s = 0; s <= steps; s++) {
          if (s > 0 && !done) {
            const t = s * H;
            const u = 0.09 * Math.sin(W(12.42) * t + ph) + al + 0.004 * r.n();
            const v = -on + 0.003 * r.n();
            x += (u * H) / 1000; y += (v * H) / 1000;
            if (y <= 0) { y = 0; done = true; }
            if (s % 6 === 0) tr.push([x, y]);
          }
          const dd = Math.hypot(x, y);
          if (dd < 3) returned = true;
          d.push(dd);
          if (returned) ret[s]++;
        }
        ds.push(d); tracks.push(tr);
      }
      const pct = (arr, p) => { const a = arr.slice().sort((a, b) => a - b); return a[Math.floor(p * (a.length - 1))]; };
      for (let s = 0; s <= steps; s++) { const col = ds.map((d) => d[s]); dist.push([pct(col, 0.1), pct(col, 0.25), pct(col, 0.5), pct(col, 0.75), pct(col, 0.9)]); }
      out[key] = { dist, ret: ret.map((c) => c / members), risk: ret[steps] / members, tracks };
    }
    return out;
  }
  JZ.ensemble = ensemble;

  // closed-form approximation of the twin (calibrated to twin rows; NOT the twin)
  JZ.whatIf = function (eta, drift, days, policy) {
    const tau = 4.4 * (2.5 / Math.max(drift, 0.05));
    let R;
    if (drift <= 0) R = policy === 'near' ? 0.04 : 0.01;
    else if (policy === 'near') R = 0.99 * (1 - Math.exp(-days / tau));
    else if (policy === 'none') return 1.0;
    else R = Math.min(0.3, 0.15 * (drift / 2.5)) * (1 - Math.exp(-days / (2 * tau)));
    return Math.min(1, (1 - eta) / (1 - eta * R));
  };

  // ---------------------------------------------------------------- simulator
  class Sim {
    constructor(id, opts = {}) {
      const sc = JZ.SCENARIOS[id];
      this.id = id; this.sc = sc; this.r = rng(sc.seed); this.t = 0;
      this.autopilot = opts.autopilot !== false;
      this.os = 'IDLE'; this.osSince = 0; this.countdown = null; this.vetoed = false; this.alert = null;
      this.commsOk = true; this.commsUntil = 0; this.windHigh = false; this.seismic = false;
      this.deployT = null; this.bloomStart = sc.alert ? sc.alert.t + sc.alert.lead * H : Infinity;
      this.patch = 1; this.highFlux = false;
      this.lanes = [];
      for (let l = 0; l < C.LANES; l++) {
        const bays = [];
        for (let b = 0; b < C.BAYS; b++) {
          bays.push({ st: 'UP', pos: 0, load: 0, ratio: 0.6, v: 0, I: 0, ch: [0, 0, 0], dp: 0, bi: 0, pers: 0, flap: false, pin: 'OK',
            seized: false, trip: false, xStuck: false, devT: 0, dwell: 0, hours: 400 + 3000 * this.r(), wear: 0.08 + 0.45 * this.r() ** 2, I_base: 0 });
        }
        if (l === 1) bays[22].wear = 0.71;
        if (l === 3) bays[5].wear = 0.66;
        this.lanes.push({ bays, split: 0.18, ratioSP: 0.6, entrances: 4, etaBase: sc.eta - 0.004 * l + 0.002 * this.r(),
          collector: 0, l2: { on: true, p: 2.0, eta2: 0, jetQ: 0, skimQ: 0, caught: 0, rate: 0 }, fillS: 70, camBias: 0.004 * this.r.n(), manualHold: false, lock: [0, 1, 2].map((k) => ({ ph: 'FILL', tp: (k * 220) / 3, level: 0.4, n: 0 })), lockHold: false, hold: 0,
          votes: [0, 0, 0], turtle: null, lastTurtleClear: -1e9, released: 0, guidedRate: 0, leakRate: 0, arrRate: 0, eta: 0,
          cam: { g: 0, l: 0 }, etaHat: sc.eta, etaVar: 0.02 ** 2, fish: 0, grid: 0 });
      }
      this.ht = { level: C.HT_SP, qin: 0, qout: 0, valve: false };
      this.o2 = { sp: C.O2_SP_TAIL, head: 5.9, tail: 5.9, inj: 0, prof: [], sat: 5.9 };
      this.pipeQ = []; this.inPipe = 0;
      this.outlet = { approved: 'FAR', rec: null, pending: null };
      this.fc = null; this.fcT = -1e9; this.fcFresh = true;
      this.k = { arrived: 0, arrivedSince: 0, leakSince: 0, leakPre: 0, diverted: 0, lifted: 0, released: 0, relNear: 0, relFar: 0,
        doa: 0, transitMort: 0, l2caught: 0, turtles: 0, turtleConfirmed: 0, fish: 0, fishReleased: 0, crewSaved: 0, lockHolds: 0, pulses: 0, bioReleasedKg: 0 };
      this.alarms = new JZ.AlarmMgr(this);
      this.logs = { os: [], decisions: [], releases: [], sightings: [], excluder: [], holds: [], ledger: [], wo: [], ai: [] };
      this.hist = []; this.bayHist = { n: 0, cap: 480, bi: [], I: [], v: [] };
      for (let i = 0; i < C.LANES * C.BAYS; i++) { this.bayHist.bi.push(new Float32Array(480)); this.bayHist.I.push(new Float32Array(480)); this.bayHist.v.push(new Float32Array(480)); }
      this.histT = []; this.relAcc = null; this.ledgerAcc = null; this.evIdx = 0;
      this.maint = JZ.makeMaint(this);
      this.copilot = []; this.cpSeen = {};
      this.logOS('IDLE', 'Scenario start: ' + sc.name, 'system');
      this.logs.decisions.push({ t: 0, kind: 'Outlet', from: '—', to: 'FAR', basis: 'Standing default: FAR outlet (conservative, pre-approved in the EAD release plan) until the forecast recommends otherwise', by: 'Procedure', status: 'DEFAULT' });
      this.runForecast();
      this.eventsSched = (sc.events || []).slice().sort((a, b) => a.t - b.t);
    }

    // ------------------------------------------------ helpers
    logOS(to, why, by = 'auto') { this.logs.os.push({ t: this.t, from: this.os, to, why, by }); }
    go(to, why, by) { this.logOS(to, why, by); this.os = to; this.osSince = this.t; }
    dens() {
      const sc = this.sc; if (!sc.peak) return 0;
      const tb = this.t - this.bloomStart; if (tb < 0) return 0;
      const ramp = Math.min(1, tb / H), end = sc.dur * H, dec = tb > end ? Math.exp(-(tb - end) / (2 * H)) : 1;
      return sc.peak * ramp * dec * this.patch;
    }
    bloomActive() { return this.dens() > 0.01; }
    stale() { return !this.commsOk; }

    // ------------------------------------------------ operator / external inputs
    receiveAlert() {
      const a = this.sc.alert; this.alert = { t: this.t, lead: a.lead, level: a.level, close: a.lead < 1.0, eta: this.t + a.lead * H };
      this.go('ALERT', `Bloom alert ${a.level}, lead ${a.lead} h (regional early-warning feed)`, 'feed');
      this.go('READY', 'Crew notified, gantry checks OK, forecast run', 'auto');
      this.runForecast();
      if (this.alert.close && a.level === 'RED') { this.countdown = this.t + C.VETO_S; this.logOS('READY', `Close RED alert (<1 h) — pre-authorised AUTO-DEPLOY in ${C.VETO_S} s unless vetoed`, 'auto'); }
    }
    veto(by = 'Operator') { if (this.countdown != null) { this.countdown = null; this.vetoed = true; this.logOS('READY', 'Auto-deploy VETOED — manual approval now required', by); } }
    approveDeploy(by = 'Operator') { if (this.os === 'READY') { this.countdown = null; this.startDeploy(by); } }
    startDeploy(by) {
      if (!this.commsOk || this.windHigh) { this.logOS(this.os, 'Deploy inhibited by interlock (comms/wind)', 'interlock'); return; }
      this.go('DEPLOYING', 'Deploy: gantries lowering cassettes (L=6 per lane)', by); this.deployT = this.t;
      this.lanes.forEach((ln) => { ln.highFlux = this.sc.peak >= 0.8; ln.entrances = ln.highFlux ? 8 : 4; ln.split = ln.highFlux ? 0.2 : 0.18; });
      this.highFlux = this.sc.peak >= 0.8;
    }
    approveStanddown(by = 'Operator') { if (this.os === 'OPERATE' || this.os === 'DEPLOYING') this.go('STANDDOWN', 'Stand-down approved: staged raise (face clear first)', by); }
    approveOutlet(by = 'Operator') {
      const p = this.outlet.pending; if (!p) return;
      this.outlet.approved = p.to; this.outlet.pending = null;
      this.logs.decisions.push({ t: this.t, kind: 'Outlet', from: p.from, to: p.to, basis: p.basis, by, status: 'APPROVED' });
    }
    rejectOutlet(by = 'Operator') {
      const p = this.outlet.pending; if (!p) return; this.outlet.pending = null;
      this.logs.decisions.push({ t: this.t, kind: 'Outlet', from: p.from, to: p.to, basis: p.basis, by, status: 'REJECTED' });
    }
    manualAlert(lead = 2, level = 'RED', by = 'Operator') {
      if (this.os !== 'IDLE') return false;
      this.alert = { t: this.t, lead, level, close: lead < 1.0, eta: this.t + lead * H, manual: true };
      this.go('ALERT', `Manual alert by operator (${level}, lead ${lead} h)`, by); this.go('READY', 'Crew notified, forecast run', 'auto'); this.runForecast();
      if (this.alert.close && level === 'RED') this.countdown = this.t + C.VETO_S;
      return true;
    }
    emergencyRaise(by = 'Operator') { if (this.os === 'SAFE') return; this.countdown = null; this.go('SAFE', 'EMERGENCY RAISE-ALL: staged raise (pulse rule kept), lowering blocked', by); }
    resetSafe(by = 'Operator') { if (this.os === 'SAFE' && this.lanes.every((l) => l.bays.every((b) => b.st === 'UP' || b.st === 'FAULT'))) { this.go('IDLE', 'SAFE reset approved: all bays up', by); return true; } return false; }
    bayCmd(li, bi, cmd, by = 'Operator') {
      const ln = this.lanes[li], b = ln.bays[bi];
      if (cmd === 'RAISE') {
        if (!(b.st === 'DOWN' || b.st === 'LOWERING')) return 'Bay is not down';
        b.manualUp = true; b.manualHold = true; this.logOS(this.os, `Bay L${li + 1}-B${bi + 1} manual RAISE requested (queued under pulse rule K=1)`, by); return 'OK';
      }
      if (cmd === 'LOWER') {
        if (!(this.os === 'DEPLOYING' || this.os === 'OPERATE')) return 'Interlock: lowering only in DEPLOY/OPERATE';
        if (!this.commsOk) return 'Interlock: comms loss (local mode) — lowering inhibited';
        if (this.windHigh) return 'Interlock: wind high';
        if (b.st === 'FAULT' || b.flap) return 'Interlock: bay FAULT / flap open — local reset required';
        if (b.st !== 'UP') return 'Bay is not up';
        b.manualHold = false; b.dwell = 0; this.logOS(this.os, `Bay L${li + 1}-B${bi + 1} manual LOWER`, by); return 'OK';
      }
      return 'Unknown command';
    }
    crewOnShift() { const op = this.os === 'OPERATE' || this.os === 'DEPLOYING' || this.os === 'STANDDOWN'; const faults = this.lanes.some((l) => l.bays.some((b) => b.st === 'FAULT' || b.trip)); return (op ? 2 : 1) + (faults ? 3 : 0); }
    addSighting(s) { this.logs.sightings.push(Object.assign({ t: this.t, ack: false }, s)); }

    runForecast() {
      if (!this.commsOk) return;
      const fc = this.sc.fc;
      this.fc = ensemble({ on: fc.on + 0.2 * this.r.n(), al: fc.al }, this.sc.seed * 7 + Math.floor(this.t / 21600));
      this.fc.on = fc.on; this.fc.al = fc.al; this.fc.t = this.t; this.fcT = this.t;
      const rn = this.fc.near.risk, rf = this.fc.far.risk;
      const rec = rn <= 0.1 ? 'NEAR' : 'FAR';
      const basis = `10-day ensemble (48 members): return risk near ${(rn * 100).toFixed(0)}%, far ${(rf * 100).toFixed(0)}%; mean onshore ${fc.on.toFixed(1)} cm/s`;
      this.outlet.rec = rec; this.outlet.basis = basis; this.outlet.risk = { NEAR: rn, FAR: rf };
      if (rec !== this.outlet.approved && (!this.outlet.pending || this.outlet.pending.to !== rec)) {
        this.outlet.pending = { t: this.t, from: this.outlet.approved, to: rec, basis };
        this.logs.decisions.push({ t: this.t, kind: 'Outlet', from: this.outlet.approved, to: rec, basis, by: 'Twin (advisory)', status: 'RECOMMENDED' });
      }
    }

    // ------------------------------------------------ scenario events
    fire(ev) {
      if (ev.type === 'seize') { const b = this.lanes[ev.lane].bays[ev.bay]; b.seized = true; b.jam = true; b.seizeT = this.t; }
      if (ev.type === 'xmtr') { this.lanes[ev.lane].bays[ev.bay].xStuck = true; }
      if (ev.type === 'turtle') {
        const ln = this.lanes[ev.lane]; ln.turtle = { t: this.t, until: this.t + 75, ch: ev.ch, species: ev.species };
        const n = ev.ch.reduce((a, b) => a + b, 0);
        this.logs.excluder.push({ t: this.t, lane: ev.lane, species: ev.species, votes: ev.ch.slice(), confirmed: n >= 2, path: n >= 2 ? 'Grid → escape chute → open water' : 'No animal seen at chute (ghost?)' });
        if (n >= 2) { this.k.turtles++; this.k.turtleConfirmed++; this.addSighting({ species: ev.species, where: `Lane ${ev.lane + 1} excluder → escape chute`, src: 'Camera + sonar + chute (3/3)', action: 'Diverted alive; HydroLift held' }); }
      }
      if (ev.type === 'sighting') this.addSighting({ species: ev.species, where: ev.where, src: ev.src, action: 'Logged; no works in sector; EAD notified (sim)' });
      if (ev.type === 'comms') { this.commsOk = false; this.commsUntil = this.t + ev.dur; }
    }

    // ------------------------------------------------ main step
    advance(seconds) {
      let rem = seconds;
      while (rem > 0) { const dt = Math.min(rem, seconds > 600 ? 10 : 5); this.step(dt); rem -= dt; }
    }

    step(dt) {
      const sc = this.sc, r = this.r; this.t += dt; const t = this.t;
      // events
      while (this.evIdx < this.eventsSched.length && this.eventsSched[this.evIdx].t <= t) this.fire(this.eventsSched[this.evIdx++]);
      if (!this.commsOk && t >= this.commsUntil) { this.commsOk = true; this.runForecast(); }
      if (sc.alert && !this.alert && t >= sc.alert.t) this.receiveAlert();
      // patchiness AR(1), 20 min
      const a = Math.exp(-dt / 1200); this.patch = Math.max(0.3, a * this.patch + (1 - a) * 1 + 0.08 * Math.sqrt(1 - a * a) * r.n() * 3);
      this.windHigh = sc.wind > 15;
      // forecast every 6 h
      this.fcFresh = t - this.fcT < 9 * H;
      if (t - this.fcT >= 6 * H) this.runForecast();

      // ---------------- incident OS
      if (this.countdown != null && t >= this.countdown) { this.countdown = null; this.startDeploy('pre-authorised auto'); }
      if (this.autopilot) {
        if (this.os === 'READY' && this.countdown == null && !this.vetoed && t - this.osSince > 240) this.approveDeploy('Training autopilot (SIM)');
        if (this.outlet.pending && t - this.outlet.pending.t > 420 && this.os !== 'IDLE') this.approveOutlet('Training autopilot (SIM)');
        if (this.os === 'OPERATE' && this.bloomStart < t && this.dens() < 0.005 && t > this.bloomStart + 3 * H) this.approveStanddown('Training autopilot (SIM)');
      }
      const d = this.dens(), tideH = tide(t);
      const depthF = (7 / (7 + tideH)) ** 2, qF = 1 + 0.02 * Math.sin(t / 5000);
      const dpClean = C.DP_CLEAN * qF * qF * depthF;
      const lowerOk = (this.os === 'DEPLOYING' || this.os === 'OPERATE') && this.commsOk && !this.windHigh && !this.seismic;
      const operating = this.os === 'OPERATE';
      let allDown = true, allUp = true;
      let totArr = 0, totLeak = 0, totGuided = 0, totLiftQ = 0, totLift = 0;

      this.lanes.forEach((ln, li) => {
        const Q = C.Q_LANE * qF; const arr = d * Q; // animals/s
        const massIn = arr * C.MASS;
        let lowering = 0, raising = 0, notDown = 0, flaps = 0;
        ln.bays.forEach((b) => { if (b.st === 'LOWERING') lowering++; if (b.st === 'RAISING') raising++; });
        const sweep = C.SWEEP * (Q / C.Q_LANE) * Math.sqrt(depthF);
        ln.sweep = sweep;
        ln.bays.forEach((b, bi) => {
          // --- drive + mesh load
          const inKg = (massIn / C.BAYS) * (b.st === 'DOWN' ? 1 : b.st === 'LOWERING' || b.st === 'RAISING' ? b.pos : 0);
          if (b.st === 'DOWN' || b.st === 'LOWERING') {
            const ratioSP = clamp(ln.ratioSP + 0.9 * Math.max(0, b.bi - 0.1), C.BELT_RATIO_MIN, C.BELT_RATIO_MAX);
            b.ratio = b.trip ? 0 : ratioSP; b.v = b.ratio * sweep;
          } else { b.ratio = 0; b.v = 0; }
          if (b.seized && !b.trip && (b.st === 'DOWN')) { b.v = 0; b.ratio = 0; b.I = Math.min(46, (b.I || 12) + dt * 1.8); if (b.I > 40) { b.trip = true; b.tripT = t; } }
          else if (b.trip || b.v === 0) b.I = 0;
          else b.I = 6 + 18 * b.v + 0.03 * b.load + (b.wear > 0.6 ? 2.5 * (b.wear - 0.6) * 10 : 0) + 0.25 * r.n();
          const tau = b.v > 0.02 ? 60 * (0.4 / b.v) : 1e9;
          const ss = inKg * tau;
          if (tau > 1e8) b.load += inKg * dt; else b.load = ss + (b.load - ss) * Math.exp(-dt / tau);
          if (b.pos <= 0) b.load = Math.max(0, b.load - dt * 2);
          let block = clamp((b.load * C.COVER) / C.BAY_AREA, 0, 0.92);
          if (b.flap) block = Math.min(block, 0.25);
          const dpTrue = b.pos <= 0 ? 0 : (dpClean * b.pos * b.pos) / (1 - block) ** 2;
          // --- 3 channels: dP A, dP B, load-cell estimate C; 2oo3 median
          const A = b.xStuck ? 920 : dpTrue * (1 + 0.02 * r.n()), B = dpTrue * (1 + 0.02 * r.n());
          const Cc = b.pos <= 0 ? 0 : (dpClean * b.pos * b.pos) / (1 - clamp((b.load * C.COVER) / C.BAY_AREA, 0, 0.92)) ** 2 * (1 + 0.05 * r.n());
          const f = 1 - Math.exp(-dt / C.FILTER_TAU);
          b.ch = [b.ch[0] + f * (A - b.ch[0]), b.ch[1] + f * (B - b.ch[1]), b.ch[2] + f * (Cc - b.ch[2])];
          const s = b.ch.slice().sort((x, y) => x - y); b.dp = s[1];
          b.dev = Math.abs(b.ch[0] - b.dp) > 0.25 * Math.max(b.dp, 30) ? (b.devT += dt) : (b.devT = 0);
          const exp = dpClean * Math.max(0.05, b.pos * b.pos);
          b.bi = b.pos > 0 ? clamp(1 - Math.sqrt(exp / Math.max(b.dp, exp)), 0, 0.99) : 0;
          // --- passive shear-pin relief (mechanical, needs no power/comms)
          if (!b.flap && dpTrue >= C.DP_HARD) { b.flap = true; b.pin = 'SHEARED'; b.flapT = t; this.k.pulses++; }
          // --- persistence -> raise request
          b.pers = b.bi >= C.BI_HH ? b.pers + dt : 0;
          b.want = (b.st === 'DOWN' || b.st === 'LOWERING') && (b.pers >= C.PERSIST_S || b.flap || b.manualUp || this.os === 'STANDDOWN' || this.os === 'SAFE' || this.os === 'IDLE' || this.os === 'READY');
          if (b.st !== 'DOWN') notDown++;
          if (b.flap) flaps++;
          b.hours += b.st === 'DOWN' ? dt / H : 0;
          b.wear = Math.min(0.99, b.wear + (b.v * dt * (1 + b.load / 50)) / 4.0e7);
        });
        // --- arbitration (pulse rule K=1 per lane). comms OK: central priority; lost: TDMA slot + hard-wired busy loop
        const cands = ln.bays.map((b, i) => [b, i]).filter(([b]) => b.want && (b.st === 'DOWN' || b.st === 'LOWERING'));
        if (cands.length) {
          const standdownFree = this.os === 'STANDDOWN' || this.os === 'IDLE' || this.os === 'READY' || this.os === 'SAFE';
          let permits = [];
          if (standdownFree) {
            // stand-down: faces clear (BI<5%) may raise 6 at a time; loaded faces K=1
            const clean = cands.filter(([b]) => b.bi < 0.05 && !b.flap), dirty = cands.filter(([b]) => !(b.bi < 0.05 && !b.flap));
            permits = clean.slice(0, Math.max(0, C.L_CONC - raising));
            if (!raising && !permits.length && dirty.length) permits = [dirty[0]];
          } else if (this.commsOk) {
            if (raising < C.K_RAISE) permits = cands.sort((p, q) => (q[0].flap || q[0].trip) - (p[0].flap || p[0].trip) || q[0].bi - p[0].bi).slice(0, 1);
          } else {
            const slot = Math.floor(t / 90) % C.BAYS; const busy = raising > 0;
            if (!busy) permits = cands.filter(([, i]) => Math.abs(i - slot) < 3).slice(0, 1);
          }
          permits.forEach(([b]) => { b.st = 'RAISING'; raising++; this.k.leakSince += this.deployT != null ? b.load / C.MASS : 0; ln.pulseKg = b.load; });
        }
        // --- motion
        ln.bays.forEach((b) => {
          if (b.st === 'RAISING' && b.jam) { b.stall = (b.stall || 0) + dt; if (b.stall >= 60) { b.st = 'FAULT'; b.stuck = true; } }
          else if (b.st === 'RAISING') { b.pos = Math.max(0, b.pos - dt / C.RAISE_S); if (b.pos <= 0) { b.st = b.trip || b.flap ? 'FAULT' : 'UP'; b.dwell = 60; b.load = 0; b.manualUp = false; } }
          else if (b.st === 'LOWERING') { b.pos = Math.min(1, b.pos + dt / C.LOWER_S); if (b.pos >= 1) b.st = 'DOWN'; }
          else if (b.st === 'UP') {
            b.dwell = Math.max(0, b.dwell - dt);
            if (lowerOk && b.dwell === 0 && !b.manualHold && lowering < C.L_CONC) { b.st = 'LOWERING'; lowering++; }
          }
          if (b.st !== 'DOWN' && b.st !== 'FAULT') allDown = allDown && false;
          if (b.st !== 'UP' && b.st !== 'FAULT') allUp = false;
        });
        if (ln.bays.some((b) => b.st !== 'DOWN' && b.st !== 'FAULT')) allDown = false;
        // --- guidance: raised/missing bays pass ~2x their flow share (08 D11)
        const coverage = ln.bays.reduce((a, b) => a + ((b.st === 'DOWN' || b.st === 'FAULT') && b.pos >= 1 ? (b.flap ? 0.5 : 1) : b.st === 'LOWERING' || b.st === 'RAISING' ? b.pos * 0.5 : b.st === 'FAULT' ? -1 : 0), 0) / C.BAYS;
        const split = ln.split, splitEff = clamp(0.97 + (split - 0.15) * 0.6, 0.9, 1.0); // entrance flow effect (07 virtual tank trend, normalised)
        const ratioEff = clamp(0.99 + 0.02 * (ln.ratioSP - 0.5), 0.98, 1.0); // belt carries bells toward apex (v5)
        ln.eta = this.deployT == null ? 0 : clamp(ln.etaBase * splitEff * ratioEff * clamp(coverage, 0, 1), 0, 0.995);
        const guided1 = arr * ln.eta, leak1 = arr - guided1;
        // Layer 2: hydro-jet curtain (water only, no air) lifts leakers to a surface skimmer feeding the same collector
        const l2 = ln.l2; l2.eta2 = this.deployT != null && (operating || this.os === 'DEPLOYING') && l2.on ? clamp(0.5 + 0.2 * (l2.p - 1), 0.5, 0.9) : 0;
        l2.jetQ = l2.eta2 ? 0.55 * l2.p : 0; l2.skimQ = l2.eta2 ? 1.4 + 0.3 * l2.p : 0;
        const caught2 = leak1 * l2.eta2; l2.caught += caught2 * dt; l2.rate = caught2; this.k.l2caught += caught2 * dt;
        const guided = guided1 + caught2, leak = leak1 - caught2; ln.leak1 = leak1;
        ln.arrRate = arr; ln.guidedRate = guided; ln.leakRate = leak;
        totArr += arr; totLeak += leak; totGuided += guided;
        // camera counts -> eta_r estimate (Kalman on hourly-equivalent observations)
        ln.cam.g += guided1 * dt * (1 + 0.04 * r.n() * Math.sqrt(5 / dt)); ln.cam.l += leak1 * dt * (1 + 0.08 * r.n() * Math.sqrt(5 / dt));
        if (guided > 0.5 && ((t % 300) < dt)) {
          const z = ln.cam.g / Math.max(1, ln.cam.g + ln.cam.l) + ln.camBias + 0.006 * r.n(), R = 0.012 ** 2;
          const Kg = ln.etaVar / (ln.etaVar + R); ln.etaHat += Kg * (z - ln.etaHat); ln.etaVar = Math.max((1 - Kg) * ln.etaVar, 0.006 ** 2);
          ln.cam.g = 0; ln.cam.l = 0;
        }
        // --- wildlife: excluder + 3-channel vote; lock HOLDS on any 1 channel (fail-safe), confirmed on 2oo3
        if (ln.turtle && t >= ln.turtle.until) { ln.turtle = null; ln.lastTurtleClear = t; }
        ln.votes = ln.turtle ? ln.turtle.ch.slice() : [0, 0, 0];
        const anyVote = ln.votes.some((v) => v);
        const wasHold = ln.lockHold;
        ln.lockHold = anyVote || (t - ln.lastTurtleClear < C.TURTLE_CLEAR_S);
        if (ln.lockHold && !wasHold) { this.k.lockHolds++; this.logs.holds.push({ t, lane: li, why: ln.votes.reduce((a, b) => a + b, 0) >= 2 ? 'Turtle confirmed 2oo3' : 'Single channel (1oo3) — fail-safe hold', votes: ln.votes.slice() }); }
        // fish (sonar estimate): ~17 small fish /h per lane in a bloom (04 T3 range)
        if (d > 0.01) { const nf = (dt / H) * 17 * (0.6 + 0.8 * r()); ln.fish += nf; this.k.fish += nf; }
        // --- collector -> flat-plate dewatering -> excluder -> HydroLift (water-only, 3 chambers)
        const doa = guided * dt * C.DOA_BASE * (1 + (d > 0.5 ? 1 : 0)); this.k.doa += doa;
        ln.collector += guided * dt - doa;
        this.k.diverted += guided * dt;
        const canRun = (operating || this.os === 'STANDDOWN') && !ln.lockHold && !ln.manualHold;
        let lifted = 0, liftQ = 0;
        const FILL = ln.fillS, cyc = FILL + C.LOCK_RISE + C.LOCK_XFER + C.LOCK_DRAIN;
        ln.lock.forEach((ch) => {
          if (!canRun && ch.ph === 'FILL') { ch.hold = true; return; }
          ch.hold = false; ch.tp += dt; if (ch.tp >= cyc) ch.tp -= cyc;
          const ph = ch.tp < FILL ? 'FILL' : ch.tp < FILL + C.LOCK_RISE ? 'RISE' : ch.tp < FILL + C.LOCK_RISE + C.LOCK_XFER ? 'TRANSFER' : 'DRAIN';
          if (ph === 'FILL') { const take = Math.min(ln.collector, ln.collector * (dt / 30)); ch.n += take; ln.collector -= take; ch.level = 0.4 + 0.3 * (ch.tp / FILL); }
          if (ph === 'RISE') ch.level = 0.7 + (C.LOCK_HEAD - 0.7) * ((ch.tp - FILL) / C.LOCK_RISE);
          if (ph === 'TRANSFER') { if (ch.ph !== 'TRANSFER') { lifted += ch.n; ch.n = 0; } ch.level = C.LOCK_HEAD; liftQ += (C.Q_LIFT_LANE * 4) / 3 * (C.LOCK_XFER / cyc) * 3 / 1; }
          if (ph === 'DRAIN') ch.level = C.LOCK_HEAD - (C.LOCK_HEAD - 0.4) * ((ch.tp - FILL - C.LOCK_RISE - C.LOCK_XFER) / C.LOCK_DRAIN);
          ch.ph = ph;
        });
        ln.running = canRun; ln.cycle = cyc;
        ln.liftQ = canRun ? C.Q_LIFT_LANE : 0;
        totLiftQ += ln.liftQ; totLift += lifted; this.k.lifted += lifted;
        ln.liftedRate = ln.liftedRate == null ? 0 : ln.liftedRate * Math.exp(-dt / 600) + (lifted / dt) * (1 - Math.exp(-dt / 600));
        ln.grid = ln.collector > 5e5 ? 1 : 0;
      });
      // ---------------- OS transitions
      if (this.os === 'DEPLOYING' && allDown) this.go('OPERATE', 'All bays down; belts running; HydroLifts cycling', 'auto');
      if (this.os === 'STANDDOWN' && allUp && this.inPipe < 1) { this.go('IDLE', 'All cassettes stowed raised and dry', 'auto'); this.alert = null; this.deployT = this.deployT; }

      // ---------------- counters
      totArr *= dt; totLeak *= dt;
      this.k.arrived += totArr;
      if (this.deployT != null) { this.k.arrivedSince += totArr; this.k.leakSince += totLeak; } else this.k.leakPre += totLeak;
      if (this.bloomActive() && operating) {
        const lf = totArr > 0 ? totLeak / totArr : 0;
        this.k.crewSaved += (dt / H) * (13 - Math.max(2, 20 * lf)); // 04 T6: today low baseline 13 extra persons
      }
      // ---------------- head tank + pipe + O2
      const ht = this.ht; ht.valve = operating || this.os === 'STANDDOWN';
      ht.qin = totLiftQ; ht.qout = ht.valve ? C.Q_PIPE * Math.sqrt(Math.max(0, ht.level) / C.HT_SP) : 0;
      ht.level = clamp(ht.level + ((ht.qin - ht.qout) / C.HT_AREA) * dt, 0, 3.6);
      const A = Math.PI * (C.PIPE_D / 2) ** 2; const vPipe = Math.max(0.05, (ht.qout || C.Q_PIPE) / A);
      const km = this.outlet.approved === 'NEAR' ? C.PIPE_NEAR_KM : C.PIPE_FAR_KM;
      this.pipe = { v: ht.qout / A, km, transit: (km * 1000) / vPipe, exitV: ht.qout / C.DIFFUSER_AREA };
      if (totLift > 0) this.pipeQ.push({ ta: t + this.pipe.transit, n: totLift, outlet: this.outlet.approved });
      this.inPipe += totLift;
      // O2: side-stream dissolution at the head tank (no bubbles); hold tail >= setpoint
      const sat = 5.56 + (35.8 - this.sc.sst) * 0.07; this.o2.sat = sat;
      const conc = ht.qout > 0.1 ? (this.lanes.reduce((a, l) => a + l.liftedRate, 0) * C.MASS) / ht.qout : 0; // kg/m3
      const rate0 = conc * C.O2_RESP; // mg/L/h (instantaneous)
      const ka = 1 - Math.exp(-dt / 1800); this.o2.rateS = this.o2.rateS == null ? rate0 : this.o2.rateS + ka * (rate0 - this.o2.rateS); const rate = this.o2.rateS; // pipe mixes ~30 min of loading
      const drop = rate * (this.pipe.transit / H);
      const head = clamp(this.o2.sp + drop, sat, C.O2_MAX_DISSOLVED);
      this.o2.head = ht.qout > 0.1 ? head : sat; this.o2.rate = rate; this.o2.conc = conc;
      this.o2.inj = ht.qout > 0.1 ? Math.max(0, (head - sat) * ht.qout * 3.6) : 0; // kg O2/h
      this.o2.prof = []; for (let i = 0; i <= 10; i++) { const x = (km * i) / 10; this.o2.prof.push([x, Math.max(0, this.o2.head - rate * ((x * 1000) / vPipe / H)) + 0.02 * r.n()]); }
      this.o2.tail = this.o2.prof[10][1];
      // arrivals at outlet
      while (this.pipeQ.length && this.pipeQ[0].ta <= t) {
        const p = this.pipeQ.shift(); this.inPipe -= p.n;
        const mort = p.n * (this.o2.tail < 2.6 ? 0.15 + (2.6 - this.o2.tail) * 0.1 : this.o2.tail < 4 ? 0.02 : 0.0);
        const alive = p.n - mort; this.k.transitMort += mort; this.k.released += alive; this.k.bioReleasedKg += alive * C.MASS;
        if (p.outlet === 'NEAR') this.k.relNear += alive; else this.k.relFar += alive;
        if (!this.relAcc) this.relAcc = { t0: t, outlet: p.outlet, n: 0, kg: 0, o2: [], appr: this.lastApproval() };
        this.relAcc.n += alive; this.relAcc.kg += alive * C.MASS; this.relAcc.o2.push(this.o2.tail);
        if (p.outlet !== this.relAcc.outlet) this.flushRel(t);
      }
      if (this.relAcc && t - this.relAcc.t0 >= H) this.flushRel(t);

      // ---------------- alarms, history, copilot
      this.alarms.evaluate(dt);
      if (Math.floor((t - dt) / 60) !== Math.floor(t / 60)) this.sample();
      if (Math.floor((t - dt) / H) !== Math.floor(t / H)) this.hourly();
    }
    lastApproval() { const a = this.logs.decisions.filter((d) => d.status === 'APPROVED'); return a.length ? `${a[a.length - 1].by} @ ${JZ.fmtT(a[a.length - 1].t)}` : 'Default FAR (conservative, pre-approved in EAD plan)'; }
    flushRel(t) {
      const a = this.relAcc; if (!a || a.n < 1) { this.relAcc = null; return; }
      const o2 = a.o2.reduce((x, y) => x + y, 0) / a.o2.length;
      this.logs.releases.push({ t0: a.t0, t1: t, outlet: a.outlet, n: a.n, kg: a.kg, o2, sst: this.sc.sst, exitV: this.pipe.exitV, appr: a.appr });
      this.relAcc = null;
    }
    hourly() {
      const k = this.k, prev = this.ledgerPrev || { arrived: 0, leakSince: 0, leakPre: 0, diverted: 0, released: 0, doa: 0, transitMort: 0 };
      const row = { t: this.t, dens: this.dens(), arrived: k.arrived - prev.arrived, leak: k.leakSince + k.leakPre - prev.leakSince - prev.leakPre, diverted: k.diverted - prev.diverted, released: k.released - prev.released, doa: k.doa - prev.doa, transitMort: k.transitMort - prev.transitMort, outlet: this.outlet.approved, os: this.os };
      if (row.arrived > 0 || row.released > 0) this.logs.ledger.push(row);
      this.ledgerPrev = Object.assign({}, k);
    }
    sample() {
      const L = this.lanes, t = this.t;
      const etaHat = L.reduce((a, l) => a + l.etaHat, 0) / 4, etaSd = Math.sqrt(L.reduce((a, l) => a + l.etaVar, 0) / 16);
      const arr = L.reduce((a, l) => a + l.arrRate, 0), leak = L.reduce((a, l) => a + l.leakRate, 0);
      this.hist.push({ t, dens: this.dens(), tide: tide(t), arr, leak, guided: L.reduce((a, l) => a + l.guidedRate, 0),
        leakPct: arr > 0 ? leak / arr : null, eta: arr > 0 ? 1 - leak / arr : null, etaHat: this.deployT != null && arr > 0 ? etaHat : null, etaSd,
        laneBI: L.map((l) => l.bays.reduce((a, b) => a + b.bi, 0) / C.BAYS), laneBImax: L.map((l) => Math.max(...l.bays.map((b) => b.bi))),
        tput: L.map((l) => (l.liftedRate * C.MASS * 3.6)), lvl: this.ht.level, o2tail: this.o2.tail, o2head: this.o2.head, inj: this.o2.inj,
        transit: this.pipe ? this.pipe.transit : 0, ratio: L.map((l) => l.ratioSP), split: L.map((l) => l.split), os: this.os,
        stale: !this.commsOk, lockQ: L.map((l) => l.liftQ) });
      if (this.hist.length > 20000) this.hist.splice(0, 5000);
      const bh = this.bayHist, i = bh.n % bh.cap; this.histT[i] = t;
      L.forEach((l, li) => l.bays.forEach((b, bi) => { const k = li * C.BAYS + bi; bh.bi[k][i] = b.bi; bh.I[k][i] = b.I; bh.v[k][i] = b.v; }));
      bh.n++;
      JZ.copilotEval && JZ.copilotEval(this);
      this.maint.tick(this);
    }
    bayTrend(li, bi) {
      const bh = this.bayHist, k = li * C.BAYS + bi, n = Math.min(bh.n, bh.cap), out = [];
      for (let j = bh.n - n; j < bh.n; j++) { const i = j % bh.cap; out.push([this.histT[i], bh.bi[k][i], bh.I[k][i], bh.v[k][i]]); }
      return out;
    }
    // high-rate dP trace for the wave filter view (120 s at 0.5 s)
    waveTrace(li, bi, HsO) {
      const b = this.lanes[li].bays[bi], r = rng(Math.floor(this.t / 10)), Hs = HsO != null ? HsO : this.sc.Hs, out = [];
      let f = b.dp, pers = 0, naive = 0, filtTrips = 0; const base = Math.max(b.dp, b.st === 'DOWN' ? 40 : 0);
      const comps = [0, 1, 2, 3].map(() => ({ a: (0.5 + r()) * 0.5, T: 2.4 + r() * 1.2, p: r() * 6.28 }));
      for (let i = 0; i <= 240; i++) {
        const tt = i * 0.5;
        const w = b.st === 'DOWN' ? 140 * Hs * comps.reduce((a, c) => a + c.a * Math.sin((6.283 * tt) / c.T + c.p), 0) : 0;
        const raw = base + w + 4 * r.n();
        f += (1 - Math.exp(-0.5 / C.FILTER_TAU)) * (raw - f);
        if (raw > 200 && (out.length === 0 || out[out.length - 1][1] <= 200)) naive++;
        pers = f > 200 ? pers + 0.5 : 0; if (pers >= C.PERSIST_S && pers - 0.5 < C.PERSIST_S) filtTrips++;
        out.push([tt, raw, f]);
      }
      return { pts: out, naive, filtTrips };
    }
    snapshot() { return JSON.stringify({ t: this.t, os: this.os, k: this.k }); }
  }
  JZ.Sim = Sim;

  JZ.fmtT = function (t) {
    const base = Date.UTC(2026, 9, 14, 1, 0, 0) + t * 1000 + 4 * H * 1000; // display GST (UTC+4)
    const d = new Date(base); const p = (n) => String(n).padStart(2, '0');
    return `${p(d.getUTCDate())} Oct ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
  };
  JZ.fmtTs = function (t) { const d = new Date(Date.UTC(2026, 9, 14, 5, 0, 0) + t * 1000); const p = (n) => String(n).padStart(2, '0'); return `${p(d.getUTCHours())}:${p(d.getUTCMinutes())}:${p(d.getUTCSeconds())}`; };
  JZ.fmtISO = function (t) { return new Date(Date.UTC(2026, 9, 14, 5, 0, 0) + t * 1000).toISOString().replace('.000Z', '+04:00').replace('Z', ''); };
})();
