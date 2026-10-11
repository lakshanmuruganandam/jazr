#!/usr/bin/env node
/* Headless validation: JS twin (twin.worker.js) vs Python twin results (twin/out/*.json).
 * Same protocol as the Python studies: N = 1500, 4 tide phases x 2 seeds, mean reported.
 * Usage: node validate.js   (writes validation.json next to this file) */
const path = require('path'), fs = require('fs');
const J = require('./twin.worker.js');
const OUT = path.resolve(__dirname, '../../../twin/out');
const L = (f) => JSON.parse(fs.readFileSync(path.join(OUT, f), 'utf8'));
const v3 = L('v3study.json'), v4 = L('v4study.json'), v4b = L('v4b.json'), far = L('v5_far.json'), nh = L('v5_noharm.json');
const pv = (x) => Array.isArray(x) ? x[0] : (typeof x === 'object' ? x.captured : x);
const PH = [0, Math.PI / 2, Math.PI, 3 * Math.PI / 2], SEEDS = [1, 2];
const sys = { system: true, ring: false, eta_r: 0.9, vr: -0.025 };
const CASES = [
  ['Today, onshore 2.5 cm/s, 72 h', { system: false, vr: -0.025, hours: 72 }, pv(v4['Today|onshore 2.5 cm/s|72h']), 'v4study'],
  ['Today, no residual, 72 h', { system: false, hours: 72 }, pv(v3['today|median']), 'v3study'],
  ['Today, onshore 3 cm/s, 72 h', { system: false, vr: -0.03, hours: 72 }, pv(v3['today|onshore 3 cm/s']), 'v3study'],
  ['Today, 10-day bloom', { system: false, hours: 240 }, pv(v3['today|10-day bloom']), 'v3study'],
  ['FAR release (10 km, 3 km out), eta_r 0.9, vr -2.5, 240 h', { ...sys, policy: 'far', hours: 240 }, pv(far['outlet x=10000 y=3000 ur=0.0']), 'v5_far'],
  ['FAR release, + ur 1 cm/s, 240 h', { ...sys, policy: 'far', ur: 0.01, hours: 240 }, pv(far['outlet x=10000 y=3000 ur=0.01']), 'v5_far'],
  ['NEAR release-only (5 km), eta_r 0.9, vr -2.5, 240 h', { ...sys, policy: 'near', hours: 240 }, pv(nh['release only']), 'v5_noharm'],
  ['NEAR release-only (5 km), 72 h', { ...sys, policy: 'near', hours: 72 }, pv(v4b['no outer line, release|72h']), 'v4b'],
  ['Offshore 10 km release, 240 h', { ...sys, policy: 'near', gate_x: 1200, gate_y: 10000, hours: 240 }, pv(far['outlet x=1200 y=10000 ur=0.0']), 'v5_far'],
  ['Alongshore 5 km release, 240 h', { ...sys, policy: 'near', gate_x: 5000, gate_y: 3000, hours: 240 }, pv(far['outlet x=5000 y=3000 ur=0.0']), 'v5_far'],
  ['Hold-unlimited (removed recover), eta_r 0.9, 240 h', { ...sys, policy: 'hold', hours: 240 }, pv(nh['hold unlimited (=no release during bloom)']), 'v5_noharm'],
  ['Hold (removed recover), eta_r 0.7, 240 h', { ...sys, eta_r: 0.7, policy: 'hold', hours: 240 }, pv(v4b['no outer line, recover, eta_r 0.7|240h']), 'v4b'],
  ['Outer line 0.4 + near release, vr -2.5, 72 h', { ...sys, ring: true, eta_g: 0.4, policy: 'near', hours: 72 }, pv(v4['v3 release|onshore 2.5 cm/s|72h']), 'v4study'],
  ['Gate 3 km (x 1.2 km), no residual, 72 h', { system: true, ring: false, eta_r: 0.9, policy: 'near', gate_x: 1200, gate_y: 3000, hours: 72 }, pv(v3['Gate (guard 0.9, outlet 3 km)|median']), 'v3study'],
  ['FAR release, eta_r 0.99, vr -2.5, 72 h', { ...sys, eta_r: 0.99, policy: 'far', hours: 72 }, 0.011, 'expected (coordinator, no JSON)'],
  ['FAR release, eta_r 0.996, vr -2.5, 72 h', { ...sys, eta_r: 0.996, policy: 'far', hours: 72 }, 0.0036, 'expected (coordinator, no JSON)'],
];
const rows = []; let worst = 0; const t0 = Date.now();
for (const [name, kw, py, src] of CASES) {
  const c = [];
  for (const ph of PH) for (const sd of SEEDS) c.push(J.runToEnd({ N: 1500, swim: 0.036, ...kw, phase0: ph, seed: sd }).result().captured_frac);
  const js = c.reduce((a, b) => a + b, 0) / c.length, d = (js - py) * 100;
  worst = Math.max(worst, Math.abs(d));
  rows.push({ case: name, source: src, python_pct: +(py * 100).toFixed(1), js_pct: +(js * 100).toFixed(1), diff_pp: +d.toFixed(1), js_range: [+(Math.min(...c) * 100).toFixed(1), +(Math.max(...c) * 100).toFixed(1)], pass: Math.abs(d) <= 3 });
  console.log(`${name.padEnd(58)} py ${(py * 100).toFixed(1).padStart(5)}%  js ${(js * 100).toFixed(1).padStart(5)}%  diff ${d >= 0 ? '+' : ''}${d.toFixed(1)} pp ${Math.abs(d) <= 3 ? 'PASS' : 'FAIL'}`);
}
console.log(`worst |diff| = ${worst.toFixed(1)} pp; ${((Date.now() - t0) / 1000).toFixed(1)} s`);
fs.writeFileSync(path.join(__dirname, 'validation.json'), JSON.stringify({ protocol: 'N=1500, 4 tide phases x 2 seeds', tolerance_pp: 3, worst_pp: +worst.toFixed(2), rows }, null, 1));
process.exit(rows.every((r) => r.pass) ? 0 : 1);
