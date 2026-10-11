/* Main Dashboard — single-screen operator HMI (ISA-101): command bar, live process mimic, alarms + advisory, mini-trends. */
(function () {
  'use strict';
  const JZ = window.JZ, U = JZ.ui, C = JZ.C;
  const NS = 'http://www.w3.org/2000/svg';
  const LANE_H = 130, LY0 = 14, BX0 = 74, BW = 17.2, BG = 1, BH = 36;
  const KM_X = (km) => 1290 - (km / 10.5) * 1190;
  const STATES = [['WATCH', ['IDLE', 'ALERT']], ['READY', ['READY']], ['DEPLOY', ['DEPLOYING']], ['OPERATE', ['OPERATE']], ['STAND-DOWN', ['STANDDOWN']]];

  const M = (JZ.main = {});

  M.build = function (root) {
    root.innerHTML = `
    <div class="md">
      <div class="cmdbar">
        <div class="panel">
          <div class="ph">Incident state <span class="r" id="mdOsWhy"></span></div>
          <div class="fsm" id="mdFsm">${STATES.map(([n]) => `<div class="s" data-s="${n}">${n}</div>`).join('')}<div class="s" data-s="SAFE" style="flex:.7">SAFE</div></div>
          <div class="cmds">
            <button class="btn big" id="cTrig" title="Raise a manual bloom alert (patrol / camera sighting)">Trigger alert</button>
            <button class="btn big primary" id="cDeploy">Approve deploy</button>
            <button class="btn big warn" id="cVeto">Veto auto-deploy</button>
            <button class="btn big" id="cStand">Stand-down</button>
            <button class="btn big danger" id="cRaise" title="Staged raise of all bays (pulse rule kept). Hard-wired E-stop is on the desk, not on this screen.">Emergency raise-all</button>
            <span id="mdCount"></span>
          </div>
        </div>
        <div class="panel" style="min-width:250px">
          <div class="ph">Alert</div>
          <div class="kv" id="mdAlert"></div>
        </div>
        <div class="panel">
          <div class="ph">Hard-wired interlocks · comms / cyber <span class="r">grey = normal</span></div>
          <div class="ilk" id="mdIlk"></div>
        </div>
        <div class="panel" style="display:flex;gap:8px;align-items:center">
          <svg id="mdTide" width="86" height="86" viewBox="0 0 100 100" role="img" aria-label="Tide clock"></svg>
          <div class="kv" id="mdTideKV" style="min-width:150px"></div>
        </div>
      </div>
      <div class="mdmid">
        <div class="panel mimicwrap">
          <div class="ph">Process mimic — 4 lanes × 42 belt bays + Layer-2 water jets → entrances → dewatering → excluder → HydroLift → head tank → O₂ → pipe → outlets
            <span class="r">click any element for its faceplate · schematic, not to scale</span></div>
          <svg id="mimic" viewBox="0 0 1400 668" role="img" aria-label="JAZR process mimic"></svg>
        </div>
        <div class="rcol">
          <div class="panel">
            <div class="ph">Alarms (ISA-18.2) <span class="r"><span id="mdAlCount"></span> <button class="btn sm" id="mdAckAll">Ack page</button> <button class="btn sm" id="mdSil">Silence</button></span></div>
            <div class="scroll"><table class="t" id="mdAl"><thead><tr><th></th><th>Time</th><th>Description</th><th>Value</th><th>State</th><th></th></tr></thead><tbody></tbody></table></div>
          </div>
          <div class="panel">
            <div class="ph">AI advisory <span class="tag">advisory only</span><span class="r">never takes safety actions · local, air-gapped</span></div>
            <div class="scroll" id="mdCp"></div>
          </div>
        </div>
      </div>
      <div class="strip" id="mdStrip"></div>
    </div>`;
    buildMimic(U.$('#mimic', root));
    buildStrip(U.$('#mdStrip', root));
    U.$('#cTrig', root).onclick = () => { const s = JZ.sim; if (s.os !== 'IDLE') return U.toast('Alert already active'); const lead = prompt('Manual alert — lead time to arrival (hours). < 1 h + RED = pre-authorised auto-deploy:', '2'); if (lead == null) return; const ok = s.manualAlert(Math.max(0.1, +lead || 2)); U.toast(ok ? 'Manual alert raised' : 'Not allowed'); JZ.app.tick(true); };
    U.$('#cDeploy', root).onclick = () => { const s = JZ.sim; if (s.os !== 'READY') return U.toast('Deploy only from READY'); if (!U.confirm('Approve DEPLOY: lower all cassettes (6 at a time per lane, ~10 min)?')) return; s.approveDeploy('Operator'); JZ.app.tick(true); };
    U.$('#cVeto', root).onclick = () => { const s = JZ.sim; if (s.countdown == null) return U.toast('No auto-deploy pending'); const why = prompt('Veto reason (logged):', 'Divers in the water at lane 2'); if (why == null) return; s.veto('Operator: ' + why); JZ.app.tick(true); };
    U.$('#cStand', root).onclick = () => { const s = JZ.sim; if (!(s.os === 'OPERATE' || s.os === 'DEPLOYING')) return U.toast('Stand-down only from DEPLOY/OPERATE'); if (!U.confirm('Approve STAND-DOWN: staged raise, faces clear first, pipe flushed?')) return; s.approveStanddown('Operator'); JZ.app.tick(true); };
    U.$('#cRaise', root).onclick = () => { const s = JZ.sim; if (s.os === 'SAFE') { if (s.resetSafe('Operator')) U.toast('SAFE reset → WATCH'); else U.toast('Reset needs all bays up'); return JZ.app.tick(true); } if (!U.confirm('EMERGENCY RAISE-ALL: all bays raise in stages, lowering blocked, locks stop. Continue?')) return; s.emergencyRaise('Operator'); JZ.app.tick(true); };
    U.$('#mdAckAll', root).onclick = () => { JZ.sim.alarms.ackAll('Operator'); JZ.app.tick(true); };
    U.$('#mdSil', root).onclick = () => { JZ.sim.alarms.silenced = true; U.toast('Horn silenced (alarms remain unacknowledged)'); };
  };

  // ---------------------------------------------------------------- mimic construction
  function el(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  function txt(parent, x, y, s, cls = 'lbl', extra = {}) { const t = el('text', Object.assign({ x, y, class: cls }, extra), parent); t.textContent = s; return t; }
  function hot(parent, label, onclick) { const g = el('g', { class: 'hot', tabindex: 0, role: 'button', 'aria-label': label }, parent); g.addEventListener('click', onclick); g.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onclick(); } }); return g; }
  const R = (M.refs = { lanes: [] });

  function buildMimic(svg) {
    svg.innerHTML = `<defs>
      <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink3)"/></marker>
      <pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="var(--eq)" stroke-width="2"/></pattern>
      <pattern id="perf" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1.1" fill="var(--eq)"/></pattern></defs>`;
    txt(svg, 6, 10, 'SEA →', 'tiny');
    // manifold to head tank
    el('line', { x1: 1236, y1: LY0 + 60, x2: 1236, y2: LY0 + 3 * LANE_H + 60, stroke: 'var(--pipe)', 'stroke-width': 5 }, svg);
    for (let l = 0; l < 4; l++) {
      const y0 = LY0 + l * LANE_H, L = { bays: [] }; R.lanes.push(L);
      const g = el('g', {}, svg);
      el('rect', { x: 48, y: y0 + 4, width: 820, height: LANE_H - 14, fill: 'var(--water)', opacity: 0.35, rx: 2 }, g);
      L.flowLn = el('line', { x1: 20, y1: y0 + 117, x2: 860, y2: y0 + 117, stroke: 'var(--water2)', 'stroke-width': 3, class: 'flow' }, g);
      txt(g, 6, y0 + 40, `U${l + 1}`, 'lbl', { style: 'font-size:20px;font-weight:800;fill:var(--ink)' });
      txt(g, 6, y0 + 56, `LANE ${l + 1}`, 'tiny');
      L.q = txt(g, 6, y0 + 72, '', 'val');
      txt(g, 6, y0 + 84, 'm³/s', 'tiny');
      // belt direction + value
      el('line', { x1: BX0, y1: y0 + 13, x2: BX0 + 42 * (BW + BG) - 4, y2: y0 + 13, stroke: 'var(--ink3)', 'stroke-width': 1.2, 'marker-end': 'url(#arw)' }, g);
      L.belt = txt(g, BX0 + 4, y0 + 10, '', 'tiny');
      L.biMax = txt(g, BX0 + 560, y0 + 10, '', 'tiny');
      // bays
      for (let b = 0; b < C.BAYS; b++) {
        const x = BX0 + b * (BW + BG);
        const hg = hot(g, `Lane ${l + 1} bay ${b + 1}`, () => M.openBay(l, b));
        const frame = el('rect', { class: 'frame', x, y: y0 + 16, width: BW, height: BH, fill: 'none', stroke: 'var(--eq)', 'stroke-width': 1 }, hg);
        const fill = el('rect', { x: x + 1, y: y0 + 17, width: BW - 2, height: BH - 2, fill: 'var(--eq-fill)' }, hg);
        const mark = txt(hg, x + BW / 2, y0 + 39, '', 'val', { 'text-anchor': 'middle', style: 'font-size:12px' });
        L.bays.push({ frame, fill, mark, y: y0 + 17 });
      }
      // entrances
      const eg = hot(g, `Lane ${l + 1} entrances`, () => M.openEntr(l));
      el('rect', { class: 'frame', x: BX0 - 2, y: y0 + 52, width: 42 * (BW + BG) + 4, height: 30, fill: 'transparent', stroke: 'none' }, eg);
      L.entr = el('g', {}, eg);
      L.split = txt(eg, BX0, y0 + 78, '', 'tiny');
      // Layer 2: hydro-jet curtain (water only) between the JAZR screen and the plant's own screens
      const l2 = hot(g, `Lane ${l + 1} Layer 2 hydro-jet curtain`, () => M.openL2(l));
      const W2 = 42 * (BW + BG);
      el('rect', { class: 'frame', x: BX0 - 2, y: y0 + 82, width: W2 + 4, height: 13, fill: 'transparent', stroke: 'var(--eq)', 'stroke-dasharray': '4 2' }, l2);
      L.jets = el('g', {}, l2);
      for (let k = 0; k < 42; k += 2) el('path', { d: `M${BX0 + k * (BW + BG) + 8} ${y0 + 94} l0 -9 m-2.5 3 l2.5 -3 l2.5 3`, stroke: 'var(--eq-on)', fill: 'none', 'stroke-width': 1 }, L.jets);
      L.l2txt = txt(l2, BX0 + 420, y0 + 79, '', 'tiny');
      el('path', { d: `M${BX0 + W2 + 2} ${y0 + 88} L850 ${y0 + 88} L850 ${y0 + 62}`, stroke: 'var(--pipe)', fill: 'none', 'stroke-width': 2, 'stroke-dasharray': '3 2' }, l2);
      el('rect', { x: BX0 - 2, y: y0 + 99, width: W2 + 4, height: 5, fill: 'var(--eq-on)' }, g);
      L.plant = txt(g, BX0, y0 + 112, '', 'tiny');
      // collector to dewatering
      el('line', { x1: 832, y1: y0 + 60, x2: 880, y2: y0 + 60, stroke: 'var(--pipe)', 'stroke-width': 4 }, g);
      L.flowA = el('line', { x1: 832, y1: y0 + 60, x2: 880, y2: y0 + 60, stroke: 'var(--panel)', 'stroke-width': 1.5, class: 'flow' }, g);
      // dewatering ramp
      const dg = hot(g, `Lane ${l + 1} dewatering`, () => M.openDew(l));
      el('polygon', { class: 'frame', points: `880,${y0 + 46} 958,${y0 + 54} 958,${y0 + 72} 880,${y0 + 72}`, fill: 'url(#perf)', stroke: 'var(--eq-on)', 'stroke-width': 1.2 }, dg);
      txt(dg, 880, y0 + 40, 'flat-plate dewater', 'tiny');
      L.dew = txt(dg, 880, y0 + 86, '', 'tiny');
      el('path', { d: `M920 ${y0 + 74} q0 20 -24 32`, stroke: 'var(--water2)', fill: 'none', 'stroke-width': 2, 'marker-end': 'url(#arw)' }, dg);
      // excluder
      const xg = hot(g, `Lane ${l + 1} excluder and wildlife vote`, () => M.openWild(l));
      el('rect', { class: 'frame', x: 970, y: y0 + 34, width: 42, height: 50, fill: 'transparent', stroke: 'var(--line)' }, xg);
      for (let k = 0; k < 6; k++) el('line', { x1: 975 + k * 7, y1: y0 + 80, x2: 983 + k * 7, y2: y0 + 38, stroke: 'var(--eq-on)', 'stroke-width': 2 }, xg);
      txt(xg, 966, y0 + 28, 'excluder 15 cm', 'tiny');
      el('path', { d: `M990 ${y0 + 84} l0 22 l-30 0`, stroke: 'var(--eq)', fill: 'none', 'stroke-width': 1.5, 'stroke-dasharray': '3 2', 'marker-end': 'url(#arw)' }, xg);
      txt(xg, 936, y0 + 104, 'turtle chute', 'tiny');
      L.votes = [0, 1, 2].map((k) => el('rect', { x: 970 + k * 15, y: y0 + 110, width: 12, height: 9, fill: 'none', stroke: 'var(--eq)' }, xg));
      txt(xg, 1018, y0 + 118, 'C S B', 'tiny', { style: 'font-size:8px' });
      el('line', { x1: 1012, y1: y0 + 60, x2: 1034, y2: y0 + 60, stroke: 'var(--pipe)', 'stroke-width': 4 }, g);
      // HydroLift
      const lg = hot(g, `Lane ${l + 1} HydroLift`, () => M.openLock(l));
      el('rect', { class: 'frame', x: 1034, y: y0 + 24, width: 112, height: 84, fill: 'transparent', stroke: 'var(--line)' }, lg);
      txt(lg, 1036, y0 + 18, 'HydroLift (water-only)', 'tiny');
      L.ch = [0, 1, 2].map((k) => {
        const x = 1040 + k * 35;
        el('rect', { x, y: y0 + 30, width: 28, height: 62, fill: 'none', stroke: 'var(--eq-on)', 'stroke-width': 1.2 }, lg);
        const w = el('rect', { x: x + 1, y: y0 + 60, width: 26, height: 31, fill: 'var(--water2)' }, lg);
        const t = txt(lg, x + 14, y0 + 104, '', 'tiny', { 'text-anchor': 'middle' });
        return { w, t, x, y: y0 + 31 };
      });
      L.lockHold = txt(lg, 1036, y0 + 122, '', 'val');
      L.toTank = el('line', { x1: 1146, y1: y0 + 60, x2: 1236, y2: y0 + 60, stroke: 'var(--pipe)', 'stroke-width': 4 }, g);
      L.toTankF = el('line', { x1: 1146, y1: y0 + 60, x2: 1236, y2: y0 + 60, stroke: 'var(--panel)', 'stroke-width': 1.5, class: 'flow' }, g);
      L.lift = txt(g, 1150, y0 + 52, '', 'tiny');
    }
    // O2 dissolver
    const og = hot(svg, 'O2 side-stream dissolver', () => M.openO2());
    el('rect', { class: 'frame', x: 1252, y: 22, width: 130, height: 104, fill: 'transparent', stroke: 'var(--line)' }, og);
    txt(og, 1258, 36, 'O₂ side-stream', 'lbl'); txt(og, 1258, 48, 'dissolved, no bubbles', 'tiny');
    el('path', { d: 'M1275 60 h30 l-6 40 h-18 z', fill: 'none', stroke: 'var(--eq-on)', 'stroke-width': 1.4 }, og);
    R.o2sp = txt(og, 1312, 72, '', 'val'); R.o2inj = txt(og, 1312, 88, '', 'val'); R.o2head = txt(og, 1312, 104, '', 'val');
    el('line', { x1: 1290, y1: 126, x2: 1290, y2: 210, stroke: 'var(--pipe)', 'stroke-width': 2, 'stroke-dasharray': '4 3' }, svg);
    // head tank
    const tg = hot(svg, 'Head tank', () => M.openTank());
    el('rect', { class: 'frame', x: 1250, y: 210, width: 80, height: 170, fill: 'none', stroke: 'var(--eq-on)', 'stroke-width': 1.6 }, tg);
    R.htFill = el('rect', { x: 1251, y: 300, width: 78, height: 79, fill: 'var(--water2)' }, tg);
    R.htH = el('line', { x1: 1246, x2: 1334, y1: 0, y2: 0, stroke: 'var(--ink3)', 'stroke-dasharray': '3 2' }, tg);
    R.htL = el('line', { x1: 1246, x2: 1334, y1: 0, y2: 0, stroke: 'var(--ink3)', 'stroke-dasharray': '3 2' }, tg);
    txt(tg, 1250, 204, 'gravity head tank', 'tiny');
    R.htV = txt(tg, 1338, 300, '', 'val'); txt(tg, 1338, 312, 'level', 'tiny');
    R.htQ = txt(tg, 1338, 340, '', 'val'); txt(tg, 1338, 352, 'to pipe', 'tiny');
    // pipe
    el('path', { d: `M1290 380 L1290 615 L${KM_X(10.5)} 615`, fill: 'none', stroke: 'var(--pipe)', 'stroke-width': 8 }, svg);
    R.pipeF = el('path', { d: `M1290 380 L1290 615 L${KM_X(10.5)} 615`, fill: 'none', stroke: 'var(--panel)', 'stroke-width': 2, class: 'flow' }, svg);
    R.pipeTxt = txt(svg, 820, 600, '', 'tiny');
    R.o2s = [0, 2.5, 5.2, 7.5, 10.5].map((km) => {
      const x = KM_X(km), g = hot(svg, `O2 sensor km ${km}`, () => M.openO2());
      const c = el('circle', { class: 'frame', cx: x, cy: 615, r: 9, fill: 'var(--panel)', stroke: 'var(--eq-on)', 'stroke-width': 1.5 }, g);
      txt(g, x, 619, 'O₂', 'tiny', { 'text-anchor': 'middle', style: 'font-size:7.5px' });
      const v = txt(g, x, 640, '', 'val', { 'text-anchor': 'middle' }); txt(g, x, 652, `km ${km}`, 'tiny', { 'text-anchor': 'middle' });
      return { km, c, v };
    });
    // outlets
    const mk = (key, km, label) => {
      const x = KM_X(km), g = hot(svg, label, () => M.openOutlet());
      const valve = el('path', { d: `M${x - 9} 579 L${x + 9} 593 L${x + 9} 579 L${x - 9} 593 Z`, fill: 'var(--panel)', stroke: 'var(--eq-on)', 'stroke-width': 1.5 }, g);
      el('line', { x1: x, y1: 593, x2: x, y2: 607, stroke: 'var(--pipe)', 'stroke-width': 4 }, g);
      const frame = el('rect', { class: 'frame', x: x - 14, y: 538, width: 230, height: 34, fill: 'transparent', stroke: 'var(--line)', rx: 2 }, g);
      el('path', { d: `M${x} 579 l0 -6 m-8 0 l16 0`, stroke: 'var(--eq-on)', 'stroke-width': 1.5 }, g);
      txt(g, x - 8, 552, label, 'lbl');
      const st = txt(g, x - 8, 566, '', 'tiny');
      return { valve, frame, st, key };
    };
    R.outN = mk('NEAR', 5.2, 'NEAR outlet · 5 km offshore');
    R.outF = mk('FAR', 10.5, 'FAR outlet · ~10 km alongshore');
    txt(svg, KM_X(10.5), 668 - 2, 'Diffuser exit ≤ 1 m/s · pipe 1.6 m ID gravity, no pump · O₂ held ≥ 5 mg/L', 'tiny');
  }

  function buildStrip(root) {
    const W = '<span class="tg w">WITH JAZR</span>', B = '<span class="tg b">BEFORE</span>';
    const tiles = [['hero', W + 'Jellyfish saved alive'], ['tvj', 'Reached plant screens'], ['got', W + 'Got past JAZR since deploy'], ['div', W + 'Diverted (t/h)'], ['eta', W + 'η_r estimate (camera)'],
      ['o2', W + 'O₂ min along pipe'], ['bi', W + 'Blockage index max'], ['tur', W + 'Turtle events'], ['crew', 'Crew on shift']];
    root.innerHTML = tiles.map(([k, l]) => `<div class="mt" id="mt-${k}"><div class="l">${l}</div><div class="v"></div>${k === 'tvj' || k === 'crew' ? '<div class="tvj"></div>' : '<svg class="spark"></svg>'}</div>`).join('');
  }

  // ---------------------------------------------------------------- per-tick update
  M.update = function (s) {
    // FSM
    const map = { IDLE: 0, ALERT: 0, READY: 1, DEPLOYING: 2, OPERATE: 3, STANDDOWN: 4, SAFE: 5 };
    const cur = map[s.os];
    U.$$('#mdFsm .s').forEach((e, i) => { e.className = 's' + (i === cur ? ' cur' + (i === 5 ? ' safe' : '') : i < cur && cur < 5 ? ' done' : ''); });
    const last = s.logs.os[s.logs.os.length - 1];
    U.$('#mdOsWhy').textContent = last ? `${JZ.fmtT(last.t)} · ${last.why} (${last.by})` : '';
    U.$('#cDeploy').disabled = s.os !== 'READY';
    U.$('#cVeto').disabled = s.countdown == null;
    U.$('#cStand').disabled = !(s.os === 'OPERATE' || s.os === 'DEPLOYING');
    U.$('#cTrig').disabled = s.os !== 'IDLE';
    U.$('#cRaise').textContent = s.os === 'SAFE' ? 'Reset SAFE → Watch' : 'Emergency raise-all';
    const cd = U.$('#mdCount');
    if (s.countdown != null) cd.innerHTML = `<span class="countdown"><span>AUTO-DEPLOY IN</span><span class="n">${U.dur(s.countdown - s.t)}</span><span class="note">pre-authorised close RED alert</span></span>`;
    else cd.innerHTML = s.vetoed && s.os === 'READY' ? '<span class="note">Auto-deploy vetoed — manual approval required</span>' : '';
    // alert
    const a = s.alert;
    U.$('#mdAlert').innerHTML = a ? `
      <span class="k">Source</span><span class="v">${a.manual ? 'Operator (manual)' : 'Regional early-warning (sim)'}</span>
      <span class="k">Severity</span><span class="v"><b>${a.level}</b>${a.close ? ' · CLOSE' : ''}</span>
      <span class="k">Lead / ETA</span><span class="v">${a.lead} h · ${JZ.fmtT(a.eta).slice(7)}</span>
      <span class="k">Since deploy</span><span class="v">${s.deployT != null ? U.dur(s.t - s.deployT) : '—'}</span>
      <span class="k">Density at intake</span><span class="v">${s.dens().toFixed(2)} /m³</span>` :
      `<span class="k">Source</span><span class="v">—</span><span class="k">Severity</span><span class="v">none</span><span class="k">Since deploy</span><span class="v">${s.deployT != null ? U.dur(s.t - s.deployT) : '—'}</span><span class="k">Density</span><span class="v">${s.dens().toFixed(2)} /m³</span>`;
    // interlocks (grey/ok = normal; colour only when abnormal)
    const flaps = s.lanes.reduce((n, l) => n + l.bays.filter((b) => !b.flap).length, 0);
    const camOK = true;
    const il = [
      ['E-stop chain', true], ['Seismic (< 0.05 g)', !s.seismic], ['Wind < 15 m/s', !s.windHigh], ['Busy loop (hard-wired)', true],
      ['Pulse rule K=1/lane', s.lanes.every((l) => l.bays.filter((b) => b.st === 'RAISING' && !b.manualUp).length <= 1) || s.os === 'STANDDOWN' || s.os === 'SAFE'],
      [`Relief flaps armed ${flaps}/168`, flaps === 168], ['Camera+sonar health', camOK], ['Lock wildlife permissive', !s.lanes.some((l) => l.lockHold)],
      ['OT network', s.commsOk], ['IT→OT data diode', true], ['Air gap (no remote ctl)', true], ['Forecast feed', s.fcFresh],
    ];
    U.$('#mdIlk').innerHTML = il.map(([n, ok]) => `<span class="i"><span class="lamp ${ok ? 'ok' : 'bad'}"></span>${n}</span>`).join('');
    // tide
    tideClock(U.$('#mdTide'), s);
    const h = JZ.tide(s.t), dh = JZ.tide(s.t + 600) - h;
    U.$('#mdTideKV').innerHTML = `<span class="k">Tide</span><span class="v">${h >= 0 ? '+' : ''}${h.toFixed(2)} m ${dh > 0 ? '▲' : '▼'}</span>
      <span class="k">Hs</span><span class="v">${s.sc.Hs.toFixed(2)} m</span><span class="k">SST</span><span class="v">${s.sc.sst.toFixed(1)} °C</span>
      <span class="k">Wind</span><span class="v">${s.sc.wind.toFixed(1)} m/s</span>`;
    updMimic(s);
    updAlarms(s);
    updCopilot(s);
    updStrip(s);
  };

  function tideClock(svg, s) {
    const ph = JZ.tidePhase(s.t), x = 50 + 34 * Math.sin(ph), y = 50 - 34 * Math.cos(ph);
    svg.innerHTML = `<circle cx="50" cy="50" r="44" fill="var(--panel2)" stroke="var(--line2)"/>
      <text x="50" y="16" text-anchor="middle" class="tiny" style="font-size:9px">HW</text><text x="50" y="92" text-anchor="middle" class="tiny" style="font-size:9px">LW</text>
      <text x="88" y="53" text-anchor="end" class="tiny" style="font-size:8px">ebb</text><text x="12" y="53" class="tiny" style="font-size:8px">flood</text>
      <line x1="50" y1="50" x2="${x}" y2="${y}" stroke="var(--ink)" stroke-width="3" stroke-linecap="round"/><circle cx="50" cy="50" r="3.5" fill="var(--ink)"/>`;
  }

  function bayColor(b) {
    if (b.st === 'FAULT' || b.flap || b.trip) return ['var(--p1)', b.flap ? '◇' : '×'];
    if (b.bi >= C.BI_HH) return ['var(--p2)', '!'];
    if (b.bi >= C.BI_H) return ['var(--p3)', ''];
    return [null, ''];
  }
  function updMimic(s) {
    const stale = !s.commsOk;
    s.lanes.forEach((ln, l) => {
      const L = R.lanes[l];
      L.q.textContent = U.n(ln.arrRate ? C.Q_LANE : C.Q_LANE, 0);
      ln.bays.forEach((b, i) => {
        const B = L.bays[i], [col, m] = bayColor(b);
        const hh = Math.max(0, (BH - 2) * b.pos);
        B.fill.setAttribute('y', B.y + (BH - 2) - hh); B.fill.setAttribute('height', hh);
        // grey depth encodes BI (normal range); colour only above alarm limits
        B.fill.setAttribute('fill', col || (b.st === 'DOWN' ? 'var(--eq-fill)' : 'url(#hatch)'));
        B.fill.setAttribute('opacity', col ? 1 : 0.55 + Math.min(0.45, b.bi * 1.6));
        B.frame.setAttribute('stroke-dasharray', b.st === 'UP' ? '2 2' : '');
        B.frame.setAttribute('stroke', col || 'var(--eq)');
        B.mark.textContent = m;
        B.mark.setAttribute('style', `font-size:12px;fill:${col ? '#fff' : 'var(--ink)'}`);
      });
      const maxBI = Math.max(...ln.bays.map((b) => b.bi));
      L.belt.textContent = `belt → apex  ${ln.ratioSP.toFixed(2)}× sweep (${(ln.ratioSP * (ln.sweep || C.SWEEP)).toFixed(2)} m/s vs sweep ${(ln.sweep || C.SWEEP).toFixed(2)} m/s)${stale ? '  · STALE' : ''}`;
      L.biMax.textContent = `BI max ${(maxBI * 100).toFixed(0)} % · η ${ln.eta ? ln.eta.toFixed(3) : '—'}`;
      const ne = ln.entrances || 4, pos = ne === 8 ? [5, 10, 16, 21, 26, 31, 37, 42] : [11, 21, 32, 42];
      L.entr.innerHTML = pos.map((p) => { const x = BX0 + p * (BW + BG) - BW / 2 - 1; return `<path d="M${x - 6} ${LY0 + l * LANE_H + 67} l6 -14 l6 14 z" fill="${ln.eta ? 'var(--eq-on)' : 'none'}" stroke="var(--eq-on)"/>`; }).join('');
      L.l2txt.textContent = `Layer 2 · hydro-jet curtain (water only) → skimmer · η₂ ${ln.l2.eta2 ? ln.l2.eta2.toFixed(2) : 'off'} · caught ${U.big(ln.l2.caught)}`;
      L.jets.style.opacity = ln.l2.eta2 ? 1 : 0.3;
      L.plant.textContent = `plant's own screens (untouched) · reaching plant ${ln.leakRate != null ? ln.leakRate.toFixed(2) : '0'} /s = (1−η₁)(1−η₂) · 1st-layer leak ${(ln.leak1 || 0).toFixed(2)} /s`;
      L.split.textContent = `${ne} entrances${ne === 8 ? ' (high-flux)' : ''} · split ${(ln.split * 100).toFixed(0)} % = ${(ln.split * C.Q_LANE).toFixed(1)} m³/s`;
      L.flowLn.style.animationPlayState = 'running';
      const run = ln.running;
      [L.flowA, L.toTankF].forEach((e) => (e.style.display = run ? '' : 'none'));
      L.dew.textContent = ln.eta ? `return ${(ln.split * C.Q_LANE - C.Q_LIFT_LANE).toFixed(1)} m³/s → lane` : 'idle';
      const vn = ln.votes.reduce((a, b) => a + b, 0);
      L.votes.forEach((r, k) => { r.setAttribute('fill', ln.votes[k] ? (vn >= 2 ? 'var(--p2)' : 'var(--p3)') : 'none'); });
      ln.lock.forEach((ch, k) => {
        const H = 60 * Math.min(1, ch.level / C.LOCK_HEAD); const c = L.ch[k];
        c.w.setAttribute('y', c.y + 60 - H); c.w.setAttribute('height', H);
        c.t.textContent = ch.hold ? 'HOLD' : { FILL: 'fill', RISE: 'rise', TRANSFER: 'xfer', DRAIN: 'drain' }[ch.ph] || '';
      });
      L.lockHold.textContent = ln.lockHold ? 'HELD — wildlife' : ln.manualHold ? 'HELD — operator' : run ? `cycle ${ln.cycle || 220} s` : 'stopped';
      L.lockHold.setAttribute('style', ln.lockHold ? 'fill:var(--p2)' : '');
      L.lift.textContent = run ? `${U.n(ln.liftedRate * C.MASS * 3.6, 1)} t/h` : '';
    });
    const o2 = s.o2, ht = s.ht;
    R.o2sp.textContent = `SP ${o2.sp.toFixed(1)} mg/L`; R.o2inj.textContent = `${o2.inj.toFixed(0)} kg O₂/h`; R.o2head.textContent = `head ${o2.head.toFixed(1)}`;
    const ly = (lv) => 379 - (lv / 3.6) * 168;
    R.htFill.setAttribute('y', ly(ht.level)); R.htFill.setAttribute('height', 379 - ly(ht.level));
    R.htH.setAttribute('y1', ly(3.2)); R.htH.setAttribute('y2', ly(3.2)); R.htL.setAttribute('y1', ly(1.2)); R.htL.setAttribute('y2', ly(1.2));
    R.htV.textContent = ht.level.toFixed(2) + ' m'; R.htQ.textContent = ht.qout.toFixed(2) + ' m³/s';
    const flowing = ht.qout > 0.1;
    R.pipeF.style.display = flowing ? '' : 'none';
    R.pipeTxt.textContent = flowing ? `v ${s.pipe.v.toFixed(2)} m/s · transit ${(s.pipe.transit / 3600).toFixed(2)} h to ${s.outlet.approved} · in pipe ${U.big(s.inPipe)} animals` : 'pipe isolated (standby, full)';
    R.o2s.forEach((o) => {
      const active = flowing && o.km <= s.pipe.km + 0.01;
      const v = active ? interpO2(o2.prof, o.km) : null;
      o.v.textContent = v == null ? '—' : v.toFixed(1);
      o.c.setAttribute('fill', v != null && v < C.O2_LL ? 'var(--p1)' : v != null && v < C.O2_MIN ? 'var(--p2)' : 'var(--panel)');
    });
    [R.outN, R.outF].forEach((o) => {
      const act = s.outlet.approved === o.key;
      o.valve.setAttribute('fill', act ? 'var(--eq-on)' : 'var(--panel)');
      o.frame.setAttribute('stroke-width', act ? 2.5 : 1); o.frame.setAttribute('stroke', act ? 'var(--eq-on)' : 'var(--line)');
      const risk = s.outlet.risk ? s.outlet.risk[o.key] : null;
      o.st.textContent = `${act ? 'ACTIVE · open' : 'closed'} · return risk ${risk != null ? (risk * 100).toFixed(0) + ' %' : '—'}${s.outlet.pending && s.outlet.pending.to === o.key ? ' · RECOMMENDED' : ''}`;
    });
  }
  function interpO2(prof, km) { if (!prof.length) return null; const last = prof[prof.length - 1][0]; if (km > last + 0.01) return null; for (let i = 1; i < prof.length; i++) if (prof[i][0] >= km) { const [x0, y0] = prof[i - 1], [x1, y1] = prof[i]; return y0 + ((y1 - y0) * (km - x0)) / Math.max(1e-6, x1 - x0); } return prof[prof.length - 1][1]; }

  M.alarmRow = function (a, compact) {
    const cls = a.st === 'UNACK' ? 'unack' : a.st === 'RTN-UNACK' ? 'rtn' : a.st === 'SHELVED' ? 'shelved' : a.st === 'SUPPRESSED' ? 'supp' : '';
    const blink = a.st === 'UNACK' ? ' blink' : '';
    return `<tr class="alrow ${cls}" data-tag="${a.tag}"><td><span class="${blink}">${U.prio(a.pri, a.st === 'SHELVED' || a.st === 'SUPPRESSED')}</span></td>
      <td class="mono">${JZ.fmtTs(a.tOn || 0).slice(0, 5)}</td><td class="desc" title="${U.esc(a.tag)} — Cause: ${U.esc(a.cause)} · Consequence: ${U.esc(a.conseq)} · Response: ${U.esc(a.action)} (${U.esc(a.ttr)})">${U.esc(a.desc)}${a.chatter ? ' <span class="tag">chatter</span>' : ''}</td>
      <td class="mono">${U.esc(a.value || '')}</td><td><span class="st">${a.st}</span></td>
      <td>${a.st === 'UNACK' || a.st === 'RTN-UNACK' ? `<button class="btn sm" data-ack="${a.tag}">Ack</button>` : ''}${a.st === 'SHELVED' ? `<button class="btn sm" data-unshelve="${a.tag}">Unshelve</button>` : a.pri > 1 && a.active ? ` <button class="btn sm" data-shelve="${a.tag}">Shelve</button>` : ''}</td></tr>`;
  };
  M.wireAlarmButtons = function (root) {
    root.addEventListener('click', (e) => {
      const t = e.target, s = JZ.sim;
      if (t.dataset.ack) { s.alarms.ack(t.dataset.ack); JZ.app.tick(true); }
      if (t.dataset.unshelve) { s.alarms.unshelve(t.dataset.unshelve); JZ.app.tick(true); }
      if (t.dataset.shelve) { const r = prompt('Shelve for 30 min — reason (logged, auto-expires):', 'Known fault, WO raised'); if (r) { s.alarms.shelve(t.dataset.shelve, 30, r); JZ.app.tick(true); } }
    });
  };
  let alWired = false;
  function updAlarms(s) {
    const tb = U.$('#mdAl tbody'); if (!alWired) { M.wireAlarmButtons(U.$('#mdAl')); alWired = true; }
    const list = s.alarms.list(); const c = s.alarms.counts();
    U.$('#mdAlCount').textContent = `${c.standing} standing · ${c.unack} unack · ${c.shelved} shelved${s.alarms.flood ? ' · FLOOD' : ''}`;
    tb.innerHTML = list.length ? list.slice(0, 40).map((a) => M.alarmRow(a)).join('') : '<tr><td colspan="6" class="note" style="padding:14px">No active alarms. (A quiet screen is the goal of ISA-18.2.)</td></tr>';
  }
  let cpWired = false;
  M.cpCard = (c) => `<div class="cp ${c.status !== 'PENDING' ? 'done' : ''}"><div class="h"><span class="tag">${c.kind}</span>${U.esc(c.title)}<span class="r note" style="margin-left:auto">${JZ.fmtT(c.t).slice(7)} · conf ${(c.conf * 100).toFixed(0)}%</span></div>
    <div class="w">${U.esc(c.why)}</div>${c.status === 'PENDING' ? `<button class="btn sm primary" data-acc="${c.id}">Accept</button> <button class="btn sm" data-rej="${c.id}">Reject</button>` : `<span class="note">${c.status} by ${U.esc(c.by)}</span>`}</div>`;
  M.wireCp = function (root) { root.addEventListener('click', (e) => { const t = e.target; if (t.dataset.acc) { JZ.copilotAccept(JZ.sim, t.dataset.acc); JZ.app.tick(true); } if (t.dataset.rej) { JZ.copilotDismiss(JZ.sim, t.dataset.rej); JZ.app.tick(true); } }); };
  function updCopilot(s) {
    const r = U.$('#mdCp'); if (!cpWired) { M.wireCp(r); cpWired = true; }
    const l = s.copilot.slice(0, 12);
    r.innerHTML = l.length ? l.map(M.cpCard).join('') : '<div class="note" style="padding:8px">No suggestions. The advisor reads OS state and camera counts; it can propose entrance split, belt speed, maintenance, outlet approval and alarm shelving. It cannot deploy, veto, move bays, change interlocks or hold/release the HydroLift.</div>';
  }

  function updStrip(s) {
    const H = s.hist.slice(-240), k = s.k;
    const set = (id, v, vals, o = {}, abn = false) => { const e = U.$('#mt-' + id); e.querySelector('.v').innerHTML = v; const sp = e.querySelector('.spark'); if (sp) U.spark(sp, vals, o); e.classList.toggle('abn', abn); };
    const leakPct = k.arrivedSince > 0 ? k.leakSince / k.arrivedSince : null;
    set('got', `${U.big(k.leakSince)} <small>${leakPct != null ? U.pct(leakPct, 1) + ' of arrivals' : ''}</small>`, H.map((x) => x.leakPct));
    const div = s.lanes.reduce((a, l) => a + l.guidedRate, 0) * C.MASS * 3.6;
    set('div', `${U.n(div, 1)} <small>t/h</small>`, H.map((x) => x.guided * C.MASS * 3.6));
    const saved = k.released + Math.max(0, s.inPipe);
    set('hero', `${U.big(saved)} <small style="color:var(--ink3)">animals · ${U.n(saved * C.MASS / 1000, 0)} t</small>
      <div class="pair" style="font-size:12px;margin-top:2px"><span class="tg b">BEFORE</span><span class="vb">0</span><span class="arr">→</span><span class="tg w">WITH JAZR</span><span class="vw">${U.big(saved)}</span></div>
      <div class="note" style="font-size:9.5px;font-weight:400;margin-top:1px">released ${U.big(k.released)} + alive in pipe ${U.big(Math.max(0, s.inPipe))} · secondary: dead-on-arrival → reuse ${U.big(k.doa)}</div>`, H.map((x) => x.tput.reduce((a, b) => a + b, 0)));
    const eh = s.lanes.reduce((a, l) => a + l.etaHat, 0) / 4, sd = Math.sqrt(s.lanes.reduce((a, l) => a + l.etaVar, 0) / 16);
    set('eta', s.deployT != null ? `${eh.toFixed(3)} <small>±${(1.645 * sd).toFixed(3)}</small>` : '— <small>not deployed</small>', H.map((x) => x.etaHat), { min: 0.9, max: 1 });
    const o2min = s.ht.qout > 0.1 ? Math.min(...s.o2.prof.map((p) => p[1])) : null;
    set('o2', o2min != null ? `${o2min.toFixed(1)} <small>mg/L (≥5)</small>` : '— <small>pipe idle</small>', H.map((x) => x.o2tail), { lim: 5 }, o2min != null && o2min < 5);
    const bim = Math.max(...s.lanes.map((l) => Math.max(...l.bays.map((b) => b.bi))));
    set('bi', `${(bim * 100).toFixed(0)} <small>% (H 35 / HH 55)</small>`, H.map((x) => Math.max(...x.laneBImax) * 100), { lim: 35, min: 0 }, bim >= C.BI_H);
    set('tur', `${k.turtleConfirmed} <small>excluded alive · ${k.lockHolds} holds</small>`, H.map((x) => x.lockQ.filter((q) => q === 0).length));
    const j = leakPct;
    U.$('#mt-tvj .v').innerHTML = `<div class="pair"><span class="tg b">BEFORE</span><span class="vb">100 %</span><span class="arr">→</span><span class="tg w">WITH JAZR</span><span class="vw">${j != null ? U.pct(j, 1) : '—'}</span></div>`;
    U.$('#mt-tvj .tvj').innerHTML = `<div style="display:grid;grid-template-columns:62px 1fr;gap:2px 6px;font-size:9.5px;align-items:center;margin-top:4px">
      <span class="vb">BEFORE</span><div class="bar"><i style="width:100%;background:var(--before)"></i></div>
      <span class="vw">WITH JAZR</span><div class="bar"><i style="width:${j != null ? Math.max(0.5, j * 100) : 0}%;background:var(--with)"></i></div></div>
      <div class="note" style="font-size:9px">share of arriving bells reaching the plant's own screens (twin: before 97–100 %)</div>`;
    U.$('#mt-crew .v').innerHTML = `<div class="pair" style="font-size:15px"><span class="tg b">BEFORE</span><span class="vb">13+</span><span class="arr">→</span><span class="tg w">WITH JAZR</span><span class="vw">${s.crewOnShift()}</span></div>`;
    U.$('#mt-crew .tvj').innerHTML = '<div class="note" style="font-size:9px;margin-top:3px">extra persons per bloom shift (04 T6: −60 to −90 % crew-hours)</div>';
  }

  // ---------------------------------------------------------------- faceplates
  const kv = (rows) => `<div class="kv">${rows.map(([k, v]) => `<span class="k">${k}</span><span class="v">${v}</span>`).join('')}</div>`;
  M.openBay = function (l, b) {
    U.openFP(`Bay L${l + 1}-B${String(b + 1).padStart(2, '0')}`, (body, first) => {
      const s = JZ.sim, bay = s.lanes[l].bays[b];
      const html = kv([['State', bay.st + (bay.manualHold ? ' (operator hold)' : '')], ['Position', (bay.pos * 100).toFixed(0) + ' % down'], ['Blockage index (comp.)', (bay.bi * 100).toFixed(1) + ' %'],
        ['ΔP A / B / C (filt.)', bay.ch.map((x) => x.toFixed(0)).join(' / ') + ' Pa'], ['2oo3 voted ΔP', bay.dp.toFixed(0) + ' Pa'], ['Belt speed', `${bay.v.toFixed(2)} m/s (${bay.ratio.toFixed(2)}× sweep)`],
        ['Motor current', bay.I.toFixed(1) + ' A' + (bay.trip ? ' — TRIPPED' : '')], ['Shear-pin / relief flap', bay.pin + (bay.flap ? ' · FLAP OPEN' : ' · closed')], ['Face load', bay.load.toFixed(0) + ' kg'], ['Belt wear (PdM)', (bay.wear * 100).toFixed(0) + ' %']]) +
        `<div class="row"><button class="btn" id="fpRaise">Raise (staged)</button><button class="btn" id="fpLower">Lower</button></div>
        <div class="note">Raise is queued under the pulse rule (K = 1 raising per lane) and dumps the face load (pulse) to the plant. Lowering is interlocked: DEPLOY/OPERATE only, comms OK, wind OK, no FAULT/flap.</div><div id="fpMsg"></div>`;
      body.innerHTML = html;
      body.querySelector('#fpRaise').onclick = () => { if (!U.confirm('Raise this bay? Its face load goes to the plant screens.')) return; const r = s.bayCmd(l, b, 'RAISE'); body.querySelector('#fpMsg').innerHTML = `<div class="msg ${r === 'OK' ? '' : 'bad'}">${U.esc(r === 'OK' ? 'Raise requested — waiting for permit (pulse rule)' : r)}</div>`; };
      body.querySelector('#fpLower').onclick = () => { const r = s.bayCmd(l, b, 'LOWER'); body.querySelector('#fpMsg').innerHTML = `<div class="msg ${r === 'OK' ? '' : 'bad'}">${U.esc(r === 'OK' ? 'Lower accepted' : r)}</div>`; };
    }, 'Angled moving-belt screen bay ≤ 4.8 m');
  };
  M.openEntr = function (l) {
    U.openFP(`Lane ${l + 1} entrances & belt speed`, (body, first) => {
      const s = JZ.sim, ln = s.lanes[l];
      if (!first) { const k = body.querySelector('#fpLive'); if (k) k.innerHTML = live(); return; }
      function live() { return kv([['Lane flow', C.Q_LANE + ' m³/s'], ['Entrance flow', (ln.split * C.Q_LANE).toFixed(1) + ' m³/s'], ['Entrances', ln.entrances + (ln.entrances === 8 ? ' (high-flux)' : '')], ['Sweep velocity', (ln.sweep || C.SWEEP).toFixed(2) + ' m/s'], ['Belt speed SP', `${ln.ratioSP.toFixed(2)}× = ${(ln.ratioSP * (ln.sweep || C.SWEEP)).toFixed(2)} m/s`], ['η_r true (sim) / camera est.', `${ln.eta.toFixed(3)} / ${ln.etaHat.toFixed(3)}`]]); }
      body.innerHTML = `<div id="fpLive">${live()}</div>
        <div class="row"><label style="width:150px">Entrance valve (split)</label><input type="range" id="fpSplit" min="15" max="20" step="0.5" value="${ln.split * 100}"><span class="mono" id="fpSplitV">${(ln.split * 100).toFixed(1)} %</span></div>
        <div class="row"><label style="width:150px">Belt / sweep ratio</label><input type="range" id="fpRatio" min="0.5" max="1" step="0.05" value="${ln.ratioSP}"><span class="mono" id="fpRatioV">${ln.ratioSP.toFixed(2)}×</span></div>
        <div class="row"><button class="btn primary" id="fpApply">Apply setpoints</button></div>
        <div class="note">Design band: split 15–20 % of lane flow (virtual tank: η rises with entrance flow); belt 0.5–1.0× sweep (mechanisms sim). Process setpoints only — not safety functions.</div>`;
      const sp = body.querySelector('#fpSplit'), rt = body.querySelector('#fpRatio');
      sp.oninput = () => (body.querySelector('#fpSplitV').textContent = (+sp.value).toFixed(1) + ' %');
      rt.oninput = () => (body.querySelector('#fpRatioV').textContent = (+rt.value).toFixed(2) + '×');
      body.querySelector('#fpApply').onclick = () => { ln.split = +sp.value / 100; ln.ratioSP = +rt.value; s.logOS(s.os, `Lane ${l + 1} setpoints: split ${(ln.split * 100).toFixed(1)} %, belt ${ln.ratioSP.toFixed(2)}× sweep`, 'Operator'); U.toast('Setpoints applied'); };
    }, 'Apex + intermediate entrances');
  };
  M.openL2 = function (l) {
    U.openFP(`Lane ${l + 1} Layer 2 — hydro-jet curtain`, (body, first) => {
      const s = JZ.sim, ln = s.lanes[l], q = ln.l2;
      const live = () => kv([['Status', q.eta2 ? 'RUNNING' : q.on ? 'standby (runs in DEPLOY/OPERATE)' : 'OFF'], ['Jet header pressure', q.eta2 ? q.p.toFixed(1) + ' bar' : '—'], ['Jet flow (water only)', q.jetQ.toFixed(2) + ' m³/s'], ['Skimmer intake flow', q.skimQ.toFixed(2) + ' m³/s'],
        ['Layer-2 catch η₂ (illustrative)', q.eta2 ? q.eta2.toFixed(2) : '—'], ['Caught by Layer 2 (cum.)', U.big(q.caught)], ['Catch rate', (q.rate || 0).toFixed(2) + ' /s'],
        ['1st-layer leak (1−η₁)', `${(ln.leak1 || 0).toFixed(2)} /s · η₁ ${ln.eta.toFixed(3)}`], ['Reaching plant (1−η₁)(1−η₂)', `${(ln.leakRate || 0).toFixed(3)} /s · ${ln.arrRate ? U.pct(ln.leakRate / ln.arrRate, 2) : '—'}`]]);
      if (!first) { body.querySelector('#fpLive').innerHTML = live(); return; }
      body.innerHTML = `<div id="fpLive">${live()}</div>
        <div class="row"><label style="width:150px">Jet header pressure SP</label><input type="range" id="fpJP" min="1" max="3" step="0.1" value="${q.p}"><span class="mono" id="fpJPV">${q.p.toFixed(1)} bar</span></div>
        <div class="row"><button class="btn primary" id="fpJA">Apply</button><button class="btn" id="fpJO">${q.on ? 'Switch Layer 2 off' : 'Switch Layer 2 on'}</button></div>
        <div class="note">Layer 2 sits between the JAZR belt screen and the plant's own screens. Low-velocity water jets (no air) lift leakers to a surface skimmer that feeds the same collector, then dewatering → excluder → HydroLift. No bubble curtain: air under the bell kills jellyfish (AZA). η₂ 0.5–0.9 is illustrative; with η₁ 0.95–0.99 the plant sees (1−η₁)(1−η₂).</div>`;
      const r = body.querySelector('#fpJP'); r.oninput = () => (body.querySelector('#fpJPV').textContent = (+r.value).toFixed(1) + ' bar');
      body.querySelector('#fpJA').onclick = () => { q.p = +r.value; s.logOS(s.os, `Lane ${l + 1} Layer-2 jet pressure ${q.p.toFixed(1)} bar`, 'Operator'); U.toast('Jet pressure applied'); };
      body.querySelector('#fpJO').onclick = (e) => { q.on = !q.on; e.target.textContent = q.on ? 'Switch Layer 2 off' : 'Switch Layer 2 on'; s.logOS(s.os, `Lane ${l + 1} Layer 2 ${q.on ? 'ON' : 'OFF'}`, 'Operator'); };
    }, 'Water jets + surface skimmer → same collector');
  };
  M.openDew = function (l) {
    U.openFP(`Lane ${l + 1} flat-plate dewatering`, (body) => {
      const ln = JZ.sim.lanes[l];
      body.innerHTML = kv([['Inflow (entrance)', (ln.split * C.Q_LANE).toFixed(1) + ' m³/s'], ['Returned to lane', Math.max(0, ln.split * C.Q_LANE - C.Q_LIFT_LANE).toFixed(1) + ' m³/s'], ['To excluder / lock', C.Q_LIFT_LANE.toFixed(2) + ' m³/s'],
        ['Plate', 'horizontal smooth perforated, ≥ 0.3 m depth'], ['Animals in collector', U.big(ln.collector)], ['Survival (ESTIMATE)', '0.997 (0.985–0.999)']]) +
        '<div class="note">Water drains down through the plate while bells stay in ≥ 0.3 m of water: no wedge-wire edges facing the flow, no air contact (bio rule R01, R07).</div>';
    }, 'S-DEWATER (10_mechanisms)');
  };
  M.openWild = function (l) {
    U.openFP(`Lane ${l + 1} excluder & wildlife vote`, (body) => {
      const s = JZ.sim, ln = s.lanes[l], n = ln.votes.reduce((a, b) => a + b, 0);
      body.innerHTML = kv([['Camera', ln.votes[0] ? 'DETECT' : 'clear'], ['Imaging sonar', ln.votes[1] ? 'DETECT' : 'clear'], ['Chute break-beam', ln.votes[2] ? 'DETECT' : 'clear'], ['Vote', `${n}/3 ${n >= 2 ? '(confirmed 2oo3)' : n === 1 ? '(1oo3 — fail-safe hold)' : ''}`],
        ['HydroLift', ln.lockHold ? 'HELD by wildlife interlock' : 'permitted'], ['Grid', 'round bars 15 cm, 30–55° → open escape chute']]) +
        '<div class="note">The grid is the primary barrier. Sensors are backup and can only HOLD the lift (hard-wired); restart needs 60 s with 0/3 votes. No acoustic deterrents are installed.</div>';
    }, 'Turtle excluder grid + camera/sonar/chute 2oo3');
  };
  M.openLock = function (l) {
    U.openFP(`Lane ${l + 1} HydroLift`, (body, first) => {
      const s = JZ.sim, ln = s.lanes[l];
      const live = () => `<table class="t"><tr><th>Chamber</th><th>Phase</th><th>Level</th><th>Animals</th></tr>${ln.lock.map((c, k) => `<tr><td>C${k + 1}</td><td>${c.hold ? 'HOLD' : c.ph}</td><td class="num">${c.level.toFixed(2)} m</td><td class="num">${U.big(c.n)}</td></tr>`).join('')}</table>` +
        kv([['Cycle time', `${ln.fillS + C.LOCK_RISE + C.LOCK_XFER + C.LOCK_DRAIN} s (fill ${ln.fillS} · rise ${C.LOCK_RISE} · transfer ${C.LOCK_XFER} · drain ${C.LOCK_DRAIN})`], ['Lift', C.LOCK_HEAD + ' m to head tank'], ['Throughput', U.n(ln.liftedRate * C.MASS * 3.6, 1) + ' t/h'], ['Status', ln.lockHold ? 'HELD (wildlife)' : ln.manualHold ? 'HELD (operator)' : ln.running ? 'cycling' : 'stopped']]);
      if (!first) { body.querySelector('#fpLive').innerHTML = live(); return; }
      body.innerHTML = `<div id="fpLive">${live()}</div>
        <div class="row"><label style="width:120px">Fill time</label><input type="range" id="fpFill" min="40" max="120" step="5" value="${ln.fillS}"><span class="mono" id="fpFillV">${ln.fillS} s</span></div>
        <div class="row"><button class="btn primary" id="fpFillA">Apply</button><button class="btn" id="fpHold">${ln.manualHold ? 'Release operator hold' : 'Operator hold'}</button></div><div id="fpMsg"></div>
        <div class="note">Water-only lock: animals float up with the water, no screw, no pump impeller, no air (10_mechanisms S-LOCK). Restart from a wildlife hold is interlocked.</div>`;
      const f = body.querySelector('#fpFill'); f.oninput = () => (body.querySelector('#fpFillV').textContent = f.value + ' s');
      body.querySelector('#fpFillA').onclick = () => { ln.fillS = +f.value; U.toast('Lock fill time ' + ln.fillS + ' s'); };
      body.querySelector('#fpHold').onclick = (e) => {
        if (ln.manualHold) { if (ln.lockHold) { body.querySelector('#fpMsg').innerHTML = '<div class="msg bad">Interlock: wildlife vote active — cannot release.</div>'; return; } ln.manualHold = false; } else ln.manualHold = true;
        e.target.textContent = ln.manualHold ? 'Release operator hold' : 'Operator hold';
      };
    }, '2–3 chambers: fill → rise → transfer → drain');
  };
  M.openTank = function () {
    U.openFP('Gravity head tank', (body) => {
      const s = JZ.sim, ht = s.ht;
      body.innerHTML = kv([['Level', ht.level.toFixed(2) + ' m (H 3.2 / L 1.2)'], ['Inflow from locks', ht.qin.toFixed(2) + ' m³/s'], ['Outflow to pipe', ht.qout.toFixed(2) + ' m³/s'], ['Outlet valve', ht.valve ? 'OPEN' : 'CLOSED'], ['Head', '≈ 6 m (gravity, no pump)'], ['Down-leg', 'no free fall, no air (R01)']]);
    }, 'Overflow weir returns surplus to lane');
  };
  M.openO2 = function () {
    U.openFP('O₂ side-stream dissolver', (body, first) => {
      const s = JZ.sim, o = s.o2;
      const live = () => kv([['Setpoint at outlet', o.sp.toFixed(1) + ' mg/L'], ['Saturation (SST ' + s.sc.sst + ' °C)', o.sat.toFixed(2) + ' mg/L'], ['Dissolved at head tank', o.head.toFixed(1) + ' mg/L'], ['O₂ dose', o.inj.toFixed(0) + ' kg/h'],
        ['Biomass in pipe', (o.conc || 0).toFixed(1) + ' kg/m³'], ['Demand', (o.rate || 0).toFixed(2) + ' mg/L/h'], ['Outlet O₂', o.tail.toFixed(1) + ' mg/L'], ['Transit', s.pipe ? (s.pipe.transit / 3600).toFixed(2) + ' h' : '—']]) +
        `<table class="t" style="margin-top:6px"><tr><th>km</th>${o.prof.filter((_, i) => i % 2 === 0).map((p) => `<th class="num">${p[0].toFixed(1)}</th>`).join('')}</tr><tr><td>mg/L</td>${o.prof.filter((_, i) => i % 2 === 0).map((p) => `<td class="num">${p[1].toFixed(1)}</td>`).join('')}</tr></table>`;
      if (!first) { body.querySelector('#fpLive').innerHTML = live(); return; }
      body.innerHTML = `<div id="fpLive">${live()}</div>
        <div class="row"><label style="width:150px">Outlet O₂ setpoint</label><input type="range" id="fpO2" min="4.5" max="7" step="0.1" value="${o.sp}"><span class="mono" id="fpO2V">${o.sp.toFixed(1)}</span></div>
        <div class="row"><button class="btn primary" id="fpO2A">Apply</button></div>
        <div class="note">O₂ is dissolved in a screened water-only side-stream and blended at the head tank — animals never meet bubbles (bio rules R01–R03). Max dissolved ${C.O2_MAX_DISSOLVED} mg/L (assumed equipment limit).</div>`;
      const r = body.querySelector('#fpO2'); r.oninput = () => (body.querySelector('#fpO2V').textContent = (+r.value).toFixed(1));
      body.querySelector('#fpO2A').onclick = () => { o.sp = +r.value; s.logOS(s.os, `O₂ outlet setpoint ${o.sp.toFixed(1)} mg/L`, 'Operator'); U.toast('O₂ setpoint applied'); };
    }, 'S-O2: bubble-free oxygenation');
  };
  M.openOutlet = function () {
    U.openFP('Release outlet selection', (body, first) => {
      const s = JZ.sim, o = s.outlet;
      const live = () => kv([['Active (approved)', o.approved], ['Twin recommends', o.rec || '—'], ['Return risk 10 d — near', o.risk ? U.pct(o.risk.NEAR, 0) : '—'], ['Return risk 10 d — far', o.risk ? U.pct(o.risk.FAR, 0) : '—'], ['Forecast age', ((s.t - s.fcT) / 3600).toFixed(1) + ' h'], ['Diffuser exit velocity', s.pipe ? s.pipe.exitV.toFixed(2) + ' m/s (≤ 1)' : '—']]) +
        (o.pending ? `<div class="msg">Pending: switch ${o.pending.from} → <b>${o.pending.to}</b>. ${U.esc(o.pending.basis)}</div>` : '');
      if (!first) { body.querySelector('#fpLive').innerHTML = live(); return; }
      body.innerHTML = `<div id="fpLive">${live()}</div><div class="row"><button class="btn primary" id="fpApp">Approve recommendation</button><button class="btn" id="fpRej">Reject</button>
        <button class="btn" id="fpMan">Manual select…</button></div>
        <div class="note">v4.1 no-harm policy: Release-Near (5 km offshore) when the 10-day ensemble shows offshore transport, Release-Far (~10 km alongshore, down-drift, away from Ruwais, reefs and beaches) when onshore. There is no Recover/kill mode. Every change needs operator confirmation and is logged for EAD.</div>`;
      body.querySelector('#fpApp').onclick = () => { if (!o.pending) return U.toast('Nothing pending'); s.approveOutlet('Operator'); U.toast('Outlet approved'); U.renderFP(true); };
      body.querySelector('#fpRej').onclick = () => { if (!o.pending) return U.toast('Nothing pending'); s.rejectOutlet('Operator'); U.renderFP(true); };
      body.querySelector('#fpMan').onclick = () => { const to = o.approved === 'NEAR' ? 'FAR' : 'NEAR'; if (!U.confirm(`Switch active outlet ${o.approved} → ${to}? Return risk ${o.risk ? U.pct(o.risk[to], 0) : '?'}. This is logged for EAD.`)) return;
        s.logs.decisions.push({ t: s.t, kind: 'Outlet', from: o.approved, to, basis: 'Manual operator selection', by: 'Operator', status: 'APPROVED' }); o.approved = to; o.pending = null; U.renderFP(true); };
    }, 'Release-Near / Release-Far (v4.1)');
  };
})();
