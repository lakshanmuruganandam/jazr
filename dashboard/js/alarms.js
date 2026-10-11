/* ISA-18.2 alarm management, predictive maintenance and the advisory copilot (SIMULATED). */
(function () {
  'use strict';
  const JZ = window.JZ, C = JZ.C;
  const PRI = (JZ.PRI = { 1: 'Urgent', 2: 'High', 3: 'Medium', 4: 'Low' });

  // ---- master alarm database (rationalised: cause / consequence / response / time-to-respond)
  function conds(s) {
    const out = [], add = (o) => out.push(o);
    const on = (tag) => { const x = s.alarms.map.get(tag); return !!(x && x.active); }; // for deadband (ISA-18.2 chatter control)
    const idle = s.os === 'IDLE' || s.os === 'ALERT';
    const op = s.os === 'OPERATE' || s.os === 'DEPLOYING';
    add({ tag: 'JZ-OS-010', desc: 'Bloom reaching intake with JAZR not deployed', pri: 1, active: s.dens() > 0.01 && s.deployT == null,
      cause: 'Alert missed / deploy vetoed or inhibited', conseq: 'Plant screens take full bloom load; possible unit trip', action: 'Approve deploy now or brief shift supervisor', ttr: '< 5 min' });
    add({ tag: 'JZ-OS-011', desc: 'Auto-deploy pending — veto window open', pri: 2, active: s.countdown != null, value: s.countdown != null ? Math.max(0, s.countdown - s.t).toFixed(0) + ' s' : '',
      cause: 'Close RED alert (lead < 1 h), pre-authorised', conseq: 'Cassettes lower automatically at end of countdown', action: 'Let it run, or VETO with reason', ttr: '< 2 min' });
    add({ tag: 'JZ-OS-001', desc: 'Bloom alert — deployment awaiting approval', pri: 3, active: s.os === 'READY' && s.countdown == null,
      cause: 'Regional early-warning alert received', conseq: 'Late deployment if not approved', action: 'Review forecast, approve deploy', ttr: '< 15 min' });
    s.lanes.forEach((ln, li) => {
      let nH = 0;
      ln.bays.forEach((b, bi) => {
        const id = `L${li + 1}-B${String(bi + 1).padStart(2, '0')}`;
        if (b.bi >= C.BI_H && b.bi < C.BI_HH) nH++;
        add({ tag: `JZ-${id}-BI-H`, desc: `Blockage index high ${id}`, pri: 3, active: b.bi >= (on(`JZ-${id}-BI-H`) ? C.BI_H - 0.03 : C.BI_H) && b.bi < C.BI_HH, value: (b.bi * 100).toFixed(0) + ' %', sp: '35 %', bay: true, floodSupp: true,
          cause: 'Bells accumulating faster than belt clears', conseq: 'Rising ΔP, possible raise request', action: 'Belt auto-speeds up; check neighbouring bays', ttr: '< 30 min' });
        add({ tag: `JZ-${id}-BI-HH`, desc: `Blockage index high-high ${id}`, pri: 2, active: b.bi >= (on(`JZ-${id}-BI-HH`) ? C.BI_HH - 0.03 : C.BI_HH), value: (b.bi * 100).toFixed(0) + ' %', sp: '55 %', bay: true,
          cause: 'Face blinded (belt slow/stopped)', conseq: 'Staged raise under pulse rule; local leak', action: 'Confirm raise permit granted; inspect belt', ttr: '< 10 min' });
        add({ tag: `JZ-${id}-DRV-TRIP`, desc: `Belt drive overcurrent trip ${id}`, pri: 2, active: b.trip, value: 'tripped', bay: true,
          cause: 'Seized belt / jammed sprocket', conseq: 'Mesh stops cleaning; blockage climbs', action: 'Dispatch maintenance; do not reset remotely', ttr: '< 10 min' });
        add({ tag: `JZ-${id}-STUCK`, desc: `Gantry drive stuck — FAULT latched ${id}`, pri: 2, active: b.st === 'FAULT' && !!b.stuck, value: 'latched', bay: true,
          cause: 'No limit-switch progress within timeout', conseq: 'Bay cannot raise; relief flap is the backup', action: 'Local inspection; manual brake release per procedure', ttr: '< 10 min' });
        add({ tag: `JZ-${id}-FLAP`, desc: `Shear-pin relief flap OPEN ${id}`, pri: 2, active: b.flap, value: 'pin sheared', bay: true,
          cause: 'ΔP exceeded 450 Pa (passive, no power/comms needed)', conseq: 'Bay passes ~50 % flow unscreened; plant protected', action: 'Replace shear pin at next stow window', ttr: '< 60 min' });
        add({ tag: `JZ-${id}-PDT-DEV`, desc: `ΔP transmitter A deviation (2oo3 masking) ${id}`, pri: 4, active: b.devT > 60, value: b.ch[0].toFixed(0) + ' Pa', bay: true, floodSupp: true,
          cause: 'Transmitter stuck/drifted', conseq: 'None while 2oo3 holds; loss of redundancy', action: 'Raise calibration work order', ttr: '< 24 h' });
      });
      add({ tag: `JZ-L${li + 1}-BI-GRP`, desc: `Lane ${li + 1}: ${nH} bays BI-H (flood grouping)`, pri: 3, active: s.alarms.flood && nH > 0, value: nH + ' bays',
        cause: 'Alarm flood: per-bay BI-H grouped by lane', conseq: '—', action: 'Watch lane trend', ttr: '< 30 min' });
      add({ tag: `JZ-L${li + 1}-ETA-L`, desc: `Lane ${li + 1} guidance η_r below 0.93`, pri: 3, active: s.os === 'OPERATE' && ln.arrRate > 1 && ln.eta < 0.93, value: ln.eta.toFixed(3), sp: '0.93',
        cause: 'Bays raised / faulted / low entrance split', conseq: 'More bells reach the plant screens', action: 'Check bay states; consider split 20 %', ttr: '< 30 min' });
      add({ tag: `JZ-L${li + 1}-LOCK-HOLD`, desc: `Lane ${li + 1} HydroLift HELD — wildlife vote`, pri: 2, active: ln.lockHold && op, value: ln.votes.join('/'),
        cause: 'Camera / sonar / chute detection (1oo3 holds, 2oo3 confirms)', conseq: 'Lift paused; collector buffers', action: 'Confirm on camera; lock restarts 60 s after clear', ttr: '< 5 min' });
      add({ tag: `JZ-L${li + 1}-COLL-H`, desc: `Lane ${li + 1} collector backlog high`, pri: 3, active: ln.collector > 4e4, value: Math.round(ln.collector).toLocaleString(),
        cause: 'Lift paused or capacity exceeded', conseq: 'Crowding in collector', action: 'Check lock cycle; high-flux mode', ttr: '< 15 min' });
    });
    const ht = s.ht, o2 = s.o2;
    add({ tag: 'JZ-HT-LT-L', desc: 'Head tank level low', pri: 3, active: ht.valve && ht.level < 1.2, value: ht.level.toFixed(2) + ' m', sp: '1.20 m', supp: !op,
      cause: 'Lift inflow below pipe draw', conseq: 'Air entrainment risk at down-leg', action: 'Check locks; throttle outlet valve', ttr: '< 10 min' });
    add({ tag: 'JZ-HT-LT-H', desc: 'Head tank level high', pri: 3, active: ht.level > 3.2, value: ht.level.toFixed(2) + ' m', sp: '3.20 m', supp: !op,
      cause: 'Pipe restriction', conseq: 'Overflow weir returns water to lane', action: 'Check pipe ΔP and outlet valve', ttr: '< 10 min' });
    add({ tag: 'JZ-O2-AT-L', desc: 'Pipe O₂ at outlet low (< 5.0 mg/L)', pri: 2, active: ht.qout > 0.1 && o2.tail < (on('JZ-O2-AT-L') ? C.O2_MIN + 0.3 : C.O2_MIN) && !(o2.tail < C.O2_LL || (on('JZ-O2-AT-LL') && o2.tail < C.O2_LL + 0.3)), value: o2.tail.toFixed(1) + ' mg/L', sp: '5.0', supp: !op,
      cause: 'Biomass loading above dissolver capacity', conseq: 'Welfare stress in transit', action: 'Documented response: near route if forecast allows; add O₂ lines; throttle entrance flow', ttr: '< 15 min' });
    add({ tag: 'JZ-O2-AT-LL', desc: 'Pipe O₂ at outlet LOW-LOW (< 3.0 mg/L) — beyond design density', pri: 1, active: ht.qout > 0.1 && o2.tail < (on('JZ-O2-AT-LL') ? C.O2_LL + 0.3 : C.O2_LL), value: o2.tail.toFixed(1) + ' mg/L', sp: '3.0', supp: !op,
      cause: 'Bloom density beyond the 0.3/m³ design density (stress case)', conseq: 'Transit mortality — no-harm goal at risk', action: 'Documented response: near route if forecast allows; add O₂ lines; throttle entrance flow; log for EAD', ttr: '< 5 min' });
    add({ tag: 'JZ-O2-DIS-MAX', desc: 'O₂ side-stream dissolver at maximum', pri: 3, active: ht.qout > 0.1 && o2.head >= C.O2_MAX_DISSOLVED - (on('JZ-O2-DIS-MAX') ? 0.4 : 0.05), value: o2.head.toFixed(1) + ' mg/L', supp: !op,
      cause: 'Setpoint unreachable', conseq: 'Outlet O₂ falls below target', action: 'See O₂ AT-L response', ttr: '< 15 min' });
    add({ tag: 'JZ-OUT-DIFF-V', desc: 'Outlet diffuser exit velocity > 1 m/s', pri: 3, active: s.pipe && s.pipe.exitV > 1.0, value: s.pipe ? s.pipe.exitV.toFixed(2) + ' m/s' : '', sp: '1.0',
      cause: 'Pipe flow above design', conseq: 'Impact stress at release', action: 'Open second diffuser port', ttr: '< 30 min' });
    add({ tag: 'JZ-NET-COMMS', desc: 'OT network lost — lanes in LOCAL mode (TDMA + busy loop)', pri: 2, active: !s.commsOk, value: 'LOCAL',
      cause: 'OT switch/fibre fault', conseq: 'No lowering; HMI values stale; hard-wired pulse rule holds', action: 'Dispatch I&C; do not attempt remote resets', ttr: '< 10 min' });
    add({ tag: 'JZ-FC-STALE', desc: 'Drift forecast stale (> 9 h)', pri: 3, active: !s.fcFresh, value: ((s.t - s.fcT) / 3600).toFixed(1) + ' h',
      cause: 'Twin / met feed unavailable', conseq: 'Outlet held at last approved (FAR default)', action: 'Check IT data diode feed', ttr: '< 60 min' });
    add({ tag: 'JZ-REL-RISK', desc: 'Return risk > 10 % on both outlets', pri: 3, active: s.outlet.risk && s.outlet.risk.NEAR > 0.1 && s.outlet.risk.FAR > 0.1,
      cause: 'Strong onshore forecast', conseq: 'Some released animals may drift back (no Recover mode in v4.1)', action: 'Keep FAR; inform EAD liaison', ttr: '< 60 min' });
    add({ tag: 'JZ-REL-PEND', desc: 'Outlet change recommended — awaiting operator approval', pri: 3, active: !!s.outlet.pending && !idle,
      cause: 'New 10-day ensemble', conseq: 'Release continues to last approved outlet', action: 'Review on Release page; approve or reject', ttr: '< 30 min' });
    return out;
  }

  class AlarmMgr {
    constructor(sim) { this.sim = sim; this.map = new Map(); this.journal = []; this.ann = []; this.flood = false; this.silenced = false; }
    evaluate() {
      const s = this.sim, t = s.t;
      this.ann = this.ann.filter((x) => t - x < 600);
      this.flood = this.ann.length > 10;
      const seen = new Set();
      for (const c of conds(s)) {
        if (!c.active && !this.map.has(c.tag)) continue;
        seen.add(c.tag);
        let a = this.map.get(c.tag);
        if (!a) { a = { tag: c.tag, active: false, acked: true, shelvedUntil: 0, count: 0, hist: [] }; this.map.set(c.tag, a); }
        Object.assign(a, { desc: c.desc, pri: c.pri, value: c.value, sp: c.sp, cause: c.cause, conseq: c.conseq, action: c.action, ttr: c.ttr });
        if (a.shelvedUntil && t >= a.shelvedUntil) { a.shelvedUntil = 0; this.log(a, 'UNSHELVED (timer)'); }
        a.supp = !!c.supp || (this.flood && (c.pri === 4 || c.floodSupp));
        if (c.active && !a.active) {
          a.active = true; a.tOn = t; a.count++; a.hist.push(t); a.hist = a.hist.filter((x) => t - x < 3600);
          if (!a.shelvedUntil && !a.supp) { a.acked = false; this.ann.push(t); this.silenced = false; this.log(a, 'ALARM'); }
          else this.log(a, a.shelvedUntil ? 'ALARM (shelved)' : 'ALARM (suppressed)');
        } else if (!c.active && a.active) { a.active = false; a.tOff = t; this.log(a, 'RTN'); }
      }
      for (const [tag, a] of this.map) if (!seen.has(tag) && a.active) { a.active = false; a.tOff = t; this.log(a, 'RTN'); }
    }
    log(a, ev) { this.journal.push({ t: this.sim.t, tag: a.tag, desc: a.desc, pri: a.pri, ev, value: a.value || '' }); if (this.journal.length > 5000) this.journal.splice(0, 1000); }
    state(a) {
      if (a.shelvedUntil) return 'SHELVED';
      if (a.supp && a.active) return 'SUPPRESSED';
      if (a.active && !a.acked) return 'UNACK';
      if (a.active) return 'ACKED';
      if (!a.acked) return 'RTN-UNACK';
      return 'NORMAL';
    }
    list() {
      return [...this.map.values()].filter((a) => { const st = this.state(a); return st !== 'NORMAL'; })
        .map((a) => Object.assign({ st: this.state(a), chatter: a.hist.length >= 4 }, a))
        .sort((x, y) => (x.st === 'SHELVED' || x.st === 'SUPPRESSED') - (y.st === 'SHELVED' || y.st === 'SUPPRESSED') || x.pri - y.pri || (y.tOn || 0) - (x.tOn || 0));
    }
    counts() {
      const l = this.list(), c = { 1: 0, 2: 0, 3: 0, 4: 0, unack: 0, shelved: 0, supp: 0, standing: 0 };
      l.forEach((a) => { if (a.st === 'SHELVED') c.shelved++; else if (a.st === 'SUPPRESSED') c.supp++; else { c[a.pri]++; if (a.st === 'UNACK' || a.st === 'RTN-UNACK') c.unack++; if (a.active) c.standing++; } });
      return c;
    }
    ack(tag, by = 'Operator') { const a = this.map.get(tag); if (a && !a.acked) { a.acked = true; this.log(a, 'ACK by ' + by); } }
    ackAll(by = 'Operator') { for (const a of this.map.values()) if (!a.acked && !a.shelvedUntil && !a.supp) { a.acked = true; this.log(a, 'ACK (page) by ' + by); } }
    shelve(tag, min, reason, by = 'Operator') {
      const a = this.map.get(tag); if (!a || a.pri === 1) return false; // ISA-18.2: urgent alarms not shelvable here
      a.shelvedUntil = this.sim.t + min * 60; a.acked = true; a.shelveReason = reason; this.log(a, `SHELVED ${min} min by ${by}: ${reason}`); return true;
    }
    unshelve(tag, by = 'Operator') { const a = this.map.get(tag); if (a && a.shelvedUntil) { a.shelvedUntil = 0; this.log(a, 'UNSHELVED by ' + by); } }
    rate10() { // annunciations per 10-min bucket from the journal
      const b = new Map(); this.journal.filter((j) => j.ev === 'ALARM').forEach((j) => { const k = Math.floor(j.t / 600); b.set(k, (b.get(k) || 0) + 1); });
      const n = Math.floor(this.sim.t / 600), out = []; for (let k = Math.max(0, n - 143); k <= n; k++) out.push([k * 600, b.get(k) || 0]); return out;
    }
    badActors() {
      const m = new Map(); this.journal.filter((j) => j.ev.startsWith('ALARM')).forEach((j) => m.set(j.tag, (m.get(j.tag) || 0) + 1));
      return [...m.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    }
  }
  JZ.AlarmMgr = AlarmMgr;

  // ---------------------------------------------------------------- predictive maintenance
  JZ.makeMaint = function (sim) {
    const r = JZ.rng(sim.sc.seed + 999);
    const assets = [];
    for (let l = 0; l < 4; l++) {
      for (let g = 0; g < 2; g++) assets.push({ id: `GW-L${l + 1}-${g ? 'B' : 'A'}`, kind: 'Gantry winch drum', lane: l, hi: 0.6 + 0.35 * r(), rate: 0.0006 + 0.001 * r(), sig: 'Rope wear / brake torque' });
      for (let c = 0; c < 3; c++) assets.push({ id: `FL-L${l + 1}-C${c + 1}`, kind: 'HydroLift chamber gates', lane: l, hi: 0.55 + 0.4 * r(), rate: 0.0008 + 0.001 * r(), sig: 'Gate seal leakage / cycle time drift', cycles: Math.round(4000 + 9000 * r()) });
      assets.push({ id: `DW-L${l + 1}`, kind: 'Flat-plate dewatering ramp', lane: l, hi: 0.7 + 0.25 * r(), rate: 0.0005, sig: 'Plate porosity (fouling)' });
    }
    assets.push({ id: 'O2-SSD-1', kind: 'O₂ side-stream dissolver', lane: -1, hi: 0.82, rate: 0.0009, sig: 'Transfer efficiency' });
    assets.push({ id: 'OUT-DIFF-N', kind: 'Near outlet diffuser', lane: -1, hi: 0.9, rate: 0.0004, sig: 'Port fouling (ROV survey)' });
    assets.push({ id: 'OUT-DIFF-F', kind: 'Far outlet diffuser', lane: -1, hi: 0.86, rate: 0.0004, sig: 'Port fouling (ROV survey)' });
    assets[3].hi = 0.31; assets[3].rate = 0.004; // one lock chamber trending badly
    return {
      assets,
      tick(s) {
        const dtd = 60 / 86400;
        assets.forEach((a) => { const busy = s.os === 'OPERATE' ? 3 : 1; a.hi = Math.max(0.02, a.hi - a.rate * dtd * busy); if (a.cycles != null && s.os === 'OPERATE') a.cycles += 60 / 215; });
      },
      belts(s) { // derived from bay wear + motor-current signature
        const out = [];
        s.lanes.forEach((ln, li) => ln.bays.forEach((b, bi) => {
          const hi = 1 - b.wear, rate = 0.0008 * (1 + b.wear * 3);
          out.push({ id: `BELT-L${li + 1}-B${String(bi + 1).padStart(2, '0')}`, kind: 'Belt + head drum', lane: li, bay: bi, hi, rate, hours: b.hours, sig: 'Motor-current signature, chain elongation', seized: b.seized });
        }));
        return out;
      },
      rul(a) { return a.seized ? 0 : Math.max(0, (a.hi - 0.25) / a.rate); },
    };
  };

  // ---------------------------------------------------------------- advisory copilot (rule-based, local, air-gapped)
  JZ.copilotEval = function (s) {
    const push = (key, o) => { if (s.cpSeen[key]) return; s.cpSeen[key] = true; s.copilot.unshift(Object.assign({ id: key, t: s.t, status: 'PENDING' }, o)); if (s.copilot.length > 40) s.copilot.pop(); };
    if (s.os === 'OPERATE') {
      s.lanes.forEach((ln, li) => {
        if (ln.split < 0.2 && ln.arrRate > 1 && !(s.o2.tail < C.O2_MIN && s.ht.qout > 0.1)) push(`split${li}`, { kind: 'TUNE', lane: li, title: `Lane ${li + 1}: entrance split ${(ln.split * 100).toFixed(0)} → 20 %`,
          why: `Camera counts: η̂ ${ln.etaHat.toFixed(3)}. Virtual-tank trend (07) and safe-BO prior: +0.2 % split ≈ +1.2 % η_r at this sweep. Dewatering ramp returns the surplus; stays in the 15–20 % design band.`, conf: 0.74, apply: { split: 0.2 } });
        const meanBI = ln.bays.reduce((a, b) => a + b.bi, 0) / C.BAYS;
        if (ln.ratioSP < 0.8 && ln.arrRate > 1) push(`ratio${li}`, { kind: 'TUNE', lane: li, title: `Lane ${li + 1}: belt speed ${ln.ratioSP.toFixed(2)}× → 0.80× sweep`,
          why: `Mean blockage index ${(meanBI * 100).toFixed(1)} %. Belt carries bells toward the apex; mechanisms sim (10) shows η≈1.0 for 0.5–1.0× sweep. 0.8× trades ~6 % more belt wear for margin on clogging.`, conf: 0.68, apply: { ratio: 0.8 } });
      });
      const worn = s.lanes.flatMap((ln, li) => ln.bays.map((b, bi) => [li, bi, b])).filter(([, , b]) => b.wear > 0.65);
      worn.forEach(([li, bi]) => push(`wear${li}-${bi}`, { kind: 'MAINT', title: `Belt L${li + 1}-B${bi + 1}: plan inspection at next stow window`,
        why: `Motor-current signature +${(10 + 30 * (s.lanes[li].bays[bi].wear - 0.6)).toFixed(0)} % over baseline at same belt speed; chain elongation trend. RUL estimate < 30 days.`, conf: 0.61, apply: { wo: `BELT-L${li + 1}-B${String(bi + 1).padStart(2, '0')}` } }));
    }
    if (s.o2.tail < C.O2_MIN && s.ht.qout > 0.1 && s.os === 'OPERATE') {
      const rn = s.outlet.risk ? s.outlet.risk.NEAR : 1;
      push('o2route', { kind: 'ADVICE', title: 'Pipe O₂ below target: trade-off for operator decision',
        why: `Outlet O₂ ${s.o2.tail.toFixed(1)} mg/L at ${s.pipe.km} km. Near route halves transit (O₂ ≈ ${Math.max(0, s.o2.head - s.o2.rate * s.pipe.transit / 3600 * C.PIPE_NEAR_KM / s.pipe.km).toFixed(1)} mg/L) but near return risk is ${(rn * 100).toFixed(0)} %. Beyond the 0.3/m³ design density. Documented response, in order: (1) near route if the forecast allows (return risk ≤ 10 %), (2) bring extra O₂ lines / standby dissolver online, (3) throttle entrance flow toward 15 % to cut pipe biomass. Copilot does not choose; each step needs operator action.`, conf: 0.5, apply: { note: true } });
      s.lanes.forEach((ln, li) => { if (ln.split > 0.15) push(`throttle${li}`, { kind: 'ADVICE', lane: li, title: `Lane ${li + 1}: throttle entrance split ${(ln.split * 100).toFixed(0)} → 15 % (O₂ welfare)`,
        why: `Pipe O₂ ${s.o2.tail.toFixed(1)} mg/L beyond design density. Lower entrance flow reduces biomass into the pipe; costs some η_r (more bells meet the plant screens). Operator decides the trade-off.`, conf: 0.55, apply: { split: 0.15 } }); });
    }
    if (s.outlet.pending) push(`out${s.outlet.pending.t}`, { kind: 'OUTLET', title: `Twin recommends Release-${s.outlet.pending.to === 'FAR' ? 'Far' : 'Near'}`,
      why: s.outlet.pending.basis + '. Accepting records YOUR approval in the decision log.', conf: 0.8, apply: { outlet: true } });
    s.alarms.list().filter((a) => a.chatter && a.pri >= 3 && a.st !== 'SHELVED').forEach((a) => push(`shelve${a.tag}${Math.floor(s.t / 3600)}`, { kind: 'ALARM', title: `Shelve chattering ${a.tag} for 30 min`,
      why: `${a.hist.length} annunciations in the last hour (bad actor). Shelving is logged and auto-expires. Urgent alarms are never offered.`, conf: 0.7, apply: { shelve: a.tag } }));
  };
  JZ.copilotAccept = function (s, id, by = 'Operator') {
    const c = s.copilot.find((x) => x.id === id); if (!c || c.status !== 'PENDING') return;
    const ap = c.apply || {};
    if (ap.split != null) s.lanes[c.lane].split = ap.split;
    if (ap.ratio != null) s.lanes[c.lane].ratioSP = ap.ratio;
    if (ap.wo) s.logs.wo.push({ t: s.t, id: ap.wo, text: 'Inspect belt & head drum (copilot, approved)', by, status: 'PLANNED' });
    if (ap.outlet) s.approveOutlet(by + ' (via copilot)');
    if (ap.shelve) s.alarms.shelve(ap.shelve, 30, 'Chattering (copilot, approved)', by);
    c.status = 'ACCEPTED'; c.by = by; c.tA = s.t;
    s.logs.ai.push({ t: s.t, id, title: c.title, decision: 'ACCEPTED', by });
  };
  JZ.copilotDismiss = function (s, id, by = 'Operator') {
    const c = s.copilot.find((x) => x.id === id); if (!c || c.status !== 'PENDING') return;
    c.status = 'DISMISSED'; c.by = by; s.logs.ai.push({ t: s.t, id, title: c.title, decision: 'DISMISSED', by });
  };
})();
