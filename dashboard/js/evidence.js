/* Evidence and Compliance pages — built from real test outputs (js/evidence_data.js, js/evidence11.js). */
(function () {
  'use strict';
  const JZ = window.JZ, U = JZ.ui, P = JZ.pages;
  const E = () => window.JZ_EVIDENCE || {};
  const src = (s) => `<div class="src">${U.esc(s)}</div>`;
  const vcls = (v) => { v = String(v || '').toUpperCase(); return v.startsWith('PASS') || v.startsWith('OK') || v.startsWith('MET') ? 'v-pass' : v.startsWith('FAIL') || v.startsWith('CHANGE') ? 'v-fail' : v.startsWith('MARG') || v.startsWith('RISK') ? 'v-marg' : ''; };
  const t = () => U.theme();
  const hbar = (cats, vals, o = {}) => { const c = t(); return U.base(Object.assign({ grid: { left: o.left || 170, right: 40, top: 22, bottom: 26 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: U.ax(Object.assign({ name: o.xname || '' }, o.x || {})), yAxis: U.ax({ type: 'category', data: cats, axisLabel: { color: c.ink3, fontSize: 10, width: (o.left || 170) - 12, overflow: 'truncate' } }),
    series: [{ type: 'bar', data: vals, itemStyle: { color: c.data }, label: { show: true, position: 'right', color: c.ink2, fontSize: 10, formatter: o.fmt || '{c}' } }].concat(o.extra || []) }, o.base || {})); };
  // horizontal error bars: data [[lo, hi, catIndex]]
  const errBars = (data) => ({ type: 'custom', name: 'CI', silent: true, data, renderItem: (p, api) => { const lo = api.coord([api.value(0), api.value(2)]), hi = api.coord([api.value(1), api.value(2)]), h = 5, c = t().ink;
    return { type: 'group', children: [{ type: 'line', shape: { x1: lo[0], y1: lo[1], x2: hi[0], y2: hi[1] }, style: { stroke: c, lineWidth: 1.2 } }, { type: 'line', shape: { x1: lo[0], y1: lo[1] - h, x2: lo[0], y2: lo[1] + h }, style: { stroke: c } }, { type: 'line', shape: { x1: hi[0], y1: hi[1] - h, x2: hi[0], y2: hi[1] + h }, style: { stroke: c } }] }; }, z: 5 });

  P.evidence = {
    title: 'Evidence', build(root) {
      const e = E(), sb = e.scoreboard || { rows: [], totals: {} };
      root.innerHTML = `<div class="page-h"><h1>Evidence — what the test programme actually found</h1><span class="sub">Every chart is built from result files in TESTS/ and twin/out/. Everything is computational or model-based; no physical prototype exists yet.</span></div>
      <div class="kpis" style="margin-bottom:10px">
        <div class="kpi"><div class="l">Computational checks</div><div class="v">≈${sb.totals.checks_approx || 600}</div><div class="s">8 test streams + real data</div></div>
        <div class="kpi"><div class="l">Automated tests passing</div><div class="v">${sb.totals.pytest_pass || 112}</div><div class="s">pytest 54 + 23 + 19 + 16</div></div>
        <div class="kpi"><div class="l">Control states model-checked</div><div class="v">26,633</div><div class="s">0 violations, 0 deadlocks</div></div>
        <div class="kpi"><div class="l">Real-current hindcast (292 windows)</div><div class="pair"><span class="tg b">BEFORE</span><span class="vb">71 %</span><span class="arr">→</span><span class="tg w">WITH JAZR v3</span><span class="vw">6.2 %</span></div></div>
        <div class="kpi"><div class="l">η_r best combination (sim)</div><div class="v">1.000</div><div class="s">95 % LB 0.996 · design claim 0.95–0.99</div></div>
        <div class="kpi"><div class="l">Reaching plant, 240 h, far release</div><div class="pair"><span class="tg b">BEFORE</span><span class="vb">100 %</span><span class="arr">→</span><span class="tg w">WITH JAZR v5</span><span class="vw">0.39 %</span></div></div>
      </div>
      <div class="grid g2">
        <div class="panel"><h3>Share of swarm reaching the plant — v5 FINAL (far release, 2.5 cm/s)</h3><div class="chart" id="evFinal"></div>${src('JAZR/JAZR_v5_FINAL.md §3; TESTS/11_eta_max_sims/results/twin_eta.csv (SIMULATED reduced-order twin)')}</div>
        <div class="panel"><h3>η_r by mechanism lever (virtual tank 1:20, 10 seeds, 95 % CI) <select id="evLev"></select></h3><div class="chart" id="evLevC"></div>${src('TESTS/11_eta_max_sims/results/vt_levers.csv — SIMULATED virtual tank')}</div>
        <div class="panel"><h3>Twin results v4.1 (η_r 0.9 unless stated)</h3><div class="chart" id="evTwin"></div>${src((e.twin_results || {}).source || '')}</div>
        <div class="panel"><h3>Real-current hindcast — share reaching intake (P10 / P50 / P90, mean ◆)</h3><div class="chart" id="evHind"></div>${src((e.hindcast || {}).source || '')}</div>
        <div class="panel"><h3>Release location vs share reaching intake (10-day bloom)</h3><div class="chart" id="evFar"></div>${src((e.far_release || {}).source || '')}</div>
        <div class="panel"><h3>No-harm alternatives: hold-alive caps vs release</h3><div class="chart" id="evNoharm"></div>${src((e.noharm || {}).source || '')}</div>
        <div class="panel"><h3>Mechanisms simulation — η by configuration</h3><div class="chart tall" id="evMech"></div>${src((e.mechanisms || {}).source || '')} <span class="note">${U.esc((e.mechanisms || {}).label || '')}</span></div>
        <div class="panel"><h3>Virtual tank: guidance vs entrance (bypass) flow</h3><div class="chart" id="evVT"></div>${src(((e.vt_guidance || {}).bypass_scan || {}).source || '')}</div>
        <div class="panel"><h3>Sensitivity — Morris μ* (95 % CI) and Sobol total index</h3><div class="chart tall" id="evSens"></div>${src((e.sensitivity || {}).source || '')} <span class="note">${U.esc((e.sensitivity || {}).which || '')}</span></div>
        <div class="panel"><h3>Hydraulics &amp; structures — verdicts by test (300 checks)</h3><div class="chart tall" id="evHyd"></div>${src((e.hydraulics || {}).source || '')} <span class="note">Many FAILs are deliberate stress cases and rejected alternatives.</span></div>
        <div class="panel"><h3>Economics — P(payback) vs site event rate</h3><div class="chart" id="evEco"></div>${src((e.economics || {}).source || '')} <span class="note" id="evEcoN"></span></div>
        <div class="panel"><h3>Crew effort per bloom</h3><div class="chart" id="evCrew"></div>${src((e.crew_hours || {}).source || '')}</div>
        <div class="panel"><h3>Survival — engineering budget per stage <span class="tag est">estimate</span></h3><div class="chart" id="evSurv"></div>${src((e.survival_budget || {}).source || '')}</div>
        <div class="panel"><h3>Survival — conservative Monte Carlo (5–95 %) <span class="tag est">model-based</span></h3><div class="chart" id="evSurvMC"></div>${src('TESTS/11_eta_max_sims/results/survival_chain.csv')}</div>
        <div class="panel"><h3>AI closed-loop controller vs fixed settings (η_r by phase)</h3><div class="chart" id="evCtl"></div>${src('TESTS/11_eta_max_sims/results/controller_summary.csv — SIMULATED')}</div>
        <div class="panel"><h3>FEA / seismic / extremes / climate — stream 08 (${(e.fea || {}).n_checks || 81} checks)</h3><div class="chart short" id="evFeaD"></div><div class="scroll" style="max-height:260px"><table class="t" id="evFea"></table></div>${src((e.fea || {}).source || '')}</div>
        <div class="panel"><h3>Test scoreboard</h3><div class="scroll" style="max-height:330px"><table class="t" id="evSB"></table></div>${src(sb.source || '')}</div>
        <div class="panel"><h3>Control-system verification</h3><div class="scroll" style="max-height:330px"><table class="t" id="evCtrl"></table></div>${src((e.controls || {}).source || '')}</div>
        <div class="panel"><h3>Virtual tank T01–T16 (SIMULATED)</h3><div class="scroll" style="max-height:300px"><table class="t" id="evVTt"></table></div>${src((e.virtual_tank || {}).source || '')}</div>
        <div class="panel"><h3>Real-data assumption check</h3><div class="scroll" style="max-height:300px"><table class="t" id="evData"></table></div>${src((e.data_checks || {}).source || '')}</div>
      </div>`;
      // tables
      U.$('#evSB').innerHTML = '<tr><th>#</th><th>Stream</th><th>Checks</th><th>PASS</th><th>MARG</th><th>FAIL</th><th>Info</th><th>pytest</th></tr>' + sb.rows.map((r) => `<tr><td>${r.id}</td><td>${U.esc(r.stream)}</td><td>${U.esc(r.checks)}</td><td>${U.esc(r.pass)}</td><td>${U.esc(r.marginal)}</td><td>${U.esc(r.fail)}</td><td class="note">${U.esc(r.info)}</td><td><b>${U.esc(r.pytest)}</b></td></tr>`).join('');
      U.$('#evFea').innerHTML = '<tr><th>Area</th><th>Check</th><th class="num">Value</th><th>Unit</th><th>Verdict</th></tr>' + ((e.fea || {}).rows || []).map((r) => `<tr title="${U.esc(r.criterion)} — ${U.esc(r.detail || '')}"><td>${U.esc(r.area)}</td><td>${U.esc(r.check)}</td><td class="num">${typeof r.value === 'number' ? r.value.toLocaleString() : U.esc(r.value)}</td><td class="note">${U.esc(r.unit)}</td><td class="${vcls(r.verdict)}">${r.verdict}</td></tr>`).join('');
      U.$('#evCtrl').innerHTML = '<tr><th>Check</th><th>Result</th><th>Verdict</th></tr>' + ((e.controls || {}).rows || []).map((r) => `<tr><td>${U.esc(r.check)}</td><td class="mono" style="white-space:normal">${U.esc(r.value)}</td><td class="${vcls(r.verdict)}">${r.verdict}</td></tr>`).join('');
      U.$('#evVTt').innerHTML = '<tr><th>Test</th><th>Metric</th><th>Value</th><th>Verdict</th><th>Result</th></tr>' + ((e.virtual_tank || {}).rows || []).map((r) => `<tr><td>${r.test} ${U.esc(r.name)}</td><td class="note">${U.esc(r.metric)}</td><td class="mono">${U.esc(r.value)}</td><td class="${vcls(r.verdict)}">${U.esc(r.verdict)}</td><td class="note">${U.esc(r.result)}</td></tr>`).join('');
      U.$('#evData').innerHTML = '<tr><th>Assumption</th><th>JAZR</th><th>Real data</th><th>Verdict</th></tr>' + ((e.data_checks || {}).rows || []).map((r) => `<tr><td>${U.esc(r.assumption)}</td><td class="note">${U.esc(r.jazr)}</td><td class="note">${U.esc(r.real)}</td><td class="${vcls(r.verdict)}">${U.esc(r.verdict)}</td></tr>`).join('');
      // charts
      const e11 = e.eta11 || {};
      U.chart(U.$('#evFinal'), () => { const c = t(), r = e11.final_table || []; return U.base({ grid: { left: 200, right: 50, top: 26, bottom: 30 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        xAxis: U.ax({ type: 'log', min: 0.1, max: 100, name: '% (log scale)', nameLocation: 'middle', nameGap: 18 }), yAxis: U.ax({ type: 'category', data: r.map((x) => x[0]).reverse(), axisLabel: { color: c.ink3, fontSize: 10 } }),
        series: [{ type: 'bar', name: '72 h', data: r.map((x) => x[1]).reverse(), itemStyle: { color: c.data3 }, label: { show: true, position: 'right', color: c.ink2, fontSize: 10, formatter: '{c}%' } }, { type: 'bar', name: '240 h', data: r.map((x) => x[2]).reverse(), itemStyle: { color: c.data }, label: { show: true, position: 'right', color: c.ink2, fontSize: 10, formatter: '{c}%' } }] }); }, 'evidence');
      const groups = [...new Set((e11.levers || []).map((x) => x.group))];
      U.$('#evLev').innerHTML = groups.map((g) => `<option${g === 'COMBO' ? ' selected' : ''}>${g}</option>`).join('');
      U.$('#evLev').onchange = () => U.refreshCharts('evidence', true);
      U.chart(U.$('#evLevC'), () => { const c = t(), g = U.$('#evLev').value, r = (e11.levers || []).filter((x) => x.group === g).reverse();
        return hbar(r.map((x) => x.config), r.map((x) => ({ value: +x.eta_mean.toFixed(3), itemStyle: { color: x.eta_mean >= 0.95 ? c.data : c.data3 } })), { left: 230, xname: 'η_r', x: { min: 0, max: 1.05 }, extra: [errBars(r.map((x, i) => [x.eta_ci_lo, x.eta_ci_hi, i]))] }); }, 'evidence');
      U.chart(U.$('#evTwin'), () => { const c = t(), r = (e.twin_results || {}).rows || []; const cat = r.map((x) => x.scenario.replace(/\(.*?\)/g, '').slice(0, 42));
        return U.base({ grid: { left: 40, right: 10, top: 30, bottom: 70 }, xAxis: U.ax({ type: 'category', data: cat, axisLabel: { color: c.ink3, fontSize: 9.5, interval: 0, rotate: 18, width: 110, overflow: 'truncate' } }), yAxis: U.ax({ name: '%', max: 100 }),
          series: [['Today', 'today', c.ink3], ['Release only', 'release_only', c.data3], ['v4.1 Release-Near/Far', 'v41', c.data]].map(([n, k, col]) => ({ type: 'bar', name: n, data: r.map((x) => (x[k] == null ? null : +(x[k] * 100).toFixed(1))), itemStyle: { color: col } })) }); }, 'evidence');
      U.chart(U.$('#evHind'), () => { const c = t(), h = e.hindcast || {}, cs = (h.cases || {})['current only'] || {}, cw = (h.cases || {})['current+wind2%'] || {}, keys = Object.keys(cs);
        const mk = (o, off, col, name) => [{ type: 'custom', name, data: keys.map((k, i) => [i, o[k].P10 * 100, o[k].P90 * 100, o[k].P50 * 100]), renderItem: (p, api) => { const i = api.value(0), a = api.coord([i, api.value(1)]), b = api.coord([i, api.value(2)]), m = api.coord([i, api.value(3)]), w = 16, x = a[0] + off;
          return { type: 'group', children: [{ type: 'rect', shape: { x: x - w / 2, y: b[1], width: w, height: a[1] - b[1] }, style: { fill: col, opacity: 0.35 } }, { type: 'line', shape: { x1: x - w / 2, y1: m[1], x2: x + w / 2, y2: m[1] }, style: { stroke: c.ink, lineWidth: 2 } }] }; } },
          { type: 'scatter', name: name + ' mean', data: keys.map((k, i) => [i, +(o[k].mean * 100).toFixed(1)]), symbol: 'diamond', symbolSize: 9, symbolOffset: [off, 0], itemStyle: { color: col } }];
        return U.base({ grid: { left: 40, right: 10, top: 30, bottom: 26 }, tooltip: { trigger: 'item' }, xAxis: U.ax({ type: 'category', data: keys }), yAxis: U.ax({ name: '%', max: 100, min: 0 }), series: mk(cs, -12, c.data, 'current only').concat(mk(cw, 12, c.data3, 'current + 2 % wind')) }); }, 'evidence');
      U.chart(U.$('#evFar'), () => { const c = t(), r = (e.far_release || {}).rows || []; return hbar(r.map((x) => `${x.x_km} km along · ${x.y_km} km out · ur ${x.ur_cm_s} cm/s`), r.map((x) => ({ value: +(x.mean * 100).toFixed(1), itemStyle: { color: x.x_km >= 10 ? c.data : c.data3 } })), { left: 210, xname: '% reaching intake', fmt: '{c}%', extra: [errBars(r.map((x, i) => [x.lo * 100, x.hi * 100, i]))] }); }, 'evidence');
      U.chart(U.$('#evNoharm'), () => { const c = t(), r = (e.noharm || {}).rows || []; return hbar(r.map((x) => x.label), r.map((x) => ({ value: +(x.mean * 100).toFixed(1), itemStyle: { color: c.data3 } })), { left: 230, xname: '% reaching intake', fmt: '{c}%' }); }, 'evidence');
      U.chart(U.$('#evMech'), () => { const c = t(), r = ((e.mechanisms || {}).rows || []).slice().reverse(); return hbar(r.map((x) => x.config), r.map((x) => ({ value: x.eta_mean, itemStyle: { color: x.eta_mean >= 0.95 ? c.data : c.data3 } })), { left: 250, xname: 'η', x: { max: 1.05 }, extra: [errBars(r.map((x, i) => [x.eta_mean - 1.96 * x.eta_se, Math.min(1, x.eta_mean + 1.96 * x.eta_se), i]))] }); }, 'evidence');
      U.chart(U.$('#evVT'), () => { const c = t(), r = ((e.vt_guidance || {}).bypass_scan || {}).rows || []; const l11 = (e11.levers || []).filter((x) => x.group === 'L1_entrance_flow');
        return U.base({ grid: { left: 40, right: 10, top: 30, bottom: 30 }, xAxis: U.ax({ name: 'entrance flow % of lane', nameLocation: 'middle', nameGap: 18 }), yAxis: U.ax({ name: 'η', min: 0, max: 1 }),
          series: [U.line('07 virtual tank (v4)', r.map((x) => [x.bypass_pct, +x.eta_mean.toFixed(3)]), c.data3, { showSymbol: true }), U.line('11 virtual tank (with dewatering)', l11.map((x) => [parseFloat(x.config), +x.eta_mean.toFixed(3)]), c.data, { showSymbol: true })] }); }, 'evidence');
      U.chart(U.$('#evSens'), () => { const c = t(), s = e.sensitivity || {}, m = (s.morris || []).slice().sort((a, b) => a.mu_star - b.mu_star), so = s.sobol || [];
        return U.base({ grid: [{ left: 70, right: '54%', top: 30, bottom: 26 }, { left: '58%', right: 10, top: 30, bottom: 26 }], tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, legend: { show: false },
          title: [{ text: 'Morris μ*', left: 70, top: 4, textStyle: { fontSize: 11, color: c.ink2 } }, { text: 'Sobol S1 / ST', left: '58%', top: 4, textStyle: { fontSize: 11, color: c.ink2 } }],
          xAxis: [U.ax({ gridIndex: 0 }), U.ax({ gridIndex: 1, max: 0.6 })], yAxis: [U.ax({ gridIndex: 0, type: 'category', data: m.map((x) => x.param) }), U.ax({ gridIndex: 1, type: 'category', data: m.map((x) => x.param), axisLabel: { show: false } })],
          series: [{ type: 'bar', xAxisIndex: 0, yAxisIndex: 0, data: m.map((x) => ({ value: +x.mu_star.toFixed(1), itemStyle: { color: x.param === 'eta_r' ? c.data : c.data3 } })) },
            Object.assign(errBars(m.map((x, i) => [x.ci_lo, x.ci_hi, i])), { xAxisIndex: 0, yAxisIndex: 0 }),
            { type: 'bar', name: 'S1', xAxisIndex: 1, yAxisIndex: 1, data: m.map((x) => { const q = so.find((z) => z.param === x.param); return q ? +q.S1.toFixed(3) : 0; }), itemStyle: { color: c.data3 } },
            { type: 'bar', name: 'ST', xAxisIndex: 1, yAxisIndex: 1, data: m.map((x) => { const q = so.find((z) => z.param === x.param); return q ? +q.ST.toFixed(3) : 0; }), itemStyle: { color: c.data } }] }); }, 'evidence');
      U.chart(U.$('#evHyd'), () => { const c = t(), r = (e.hydraulics || {}).by_test || []; return U.base({ grid: { left: 150, right: 20, top: 26, bottom: 26 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, xAxis: U.ax({ name: 'checks' }), yAxis: U.ax({ type: 'category', data: r.map((x) => `${x.test} ${x.title || ''}`).reverse(), axisLabel: { color: c.ink3, fontSize: 10 } }),
        series: [['PASS', c.eq], ['MARGINAL', c.p3], ['FAIL', c.p2]].map(([k, col]) => ({ type: 'bar', name: k, stack: 'v', data: r.map((x) => x[k]).reverse(), itemStyle: { color: col } })) }); }, 'evidence');
      U.chart(U.$('#evEco'), () => { const c = t(), ec = e.economics || {}; U.$('#evEcoN').textContent = `Break-even ≈ ${ec.breakeven_unit_days} lost unit-days per unit-year (${ec.breakeven_note || ''}).`;
        return U.base({ grid: { left: 44, right: 10, top: 30, bottom: 32 }, xAxis: U.ax({ type: 'log', name: 'bloom shutdown events per site-year', nameLocation: 'middle', nameGap: 20, min: 0.005 }), yAxis: U.ax({ name: 'P(payback)', min: 0, max: 1 }),
          series: [U.line('Case A — JAZR Core', ec.payback_curve || [], c.data, { lineStyle: { width: 2, color: c.data } }), U.line('Case B — full system', ec.payback_curve_caseB || [], c.data3),
            { type: 'scatter', name: 'Site scenarios (A)', data: (ec.payback || []).filter((x) => x.case === 'A').map((x) => ({ value: [x.rate_events_per_site_yr, x.p_payback], name: x.scenario })), symbolSize: 9, itemStyle: { color: c.ink }, label: { show: true, position: 'left', fontSize: 9, color: c.ink3, formatter: (p) => p.name.split(' ')[0] + ' ' + (p.value[1] * 100).toFixed(1) + '%' } }] }); }, 'evidence');
      U.chart(U.$('#evCrew'), () => { const c = t(), k = e.crew_hours || {}; return hbar(['Today (high: + boats)', 'Today (low)', 'JAZR'], [{ value: k.today_high, itemStyle: { color: c.ink3 } }, { value: k.today_low, itemStyle: { color: c.data3 } }, { value: k.jazr, itemStyle: { color: c.data } }], { left: 140, xname: 'person-hours per bloom' }); }, 'evidence');
      U.chart(U.$('#evSurv'), () => { const c = t(), r = ((e.survival_budget || {}).rows || []).slice().reverse(); return hbar(r.map((x) => `${x.stage}. ${String(x.description).slice(0, 34)}`), r.map((x) => ({ value: x.target, itemStyle: { color: x.stage.startsWith('ALL') ? c.data : c.data3 } })), { left: 240, xname: 'survival', x: { min: 0.7, max: 1.0 }, fmt: '{c}', extra: [errBars(r.map((x, i) => [x.lo, x.hi, i]))] }); }, 'evidence');
      U.chart(U.$('#evSurvMC'), () => { const c = t(), r = (e11.survival || []).slice().reverse(); return hbar(r.map((x) => `${x.screen} · ${x.lift} · ${x.pipe}`), r.map((x) => ({ value: x.chain_median, itemStyle: { color: x.lift === 'fish_lock' && x.pipe === 'O2' ? c.data : c.data3 } })), { left: 250, xname: 'chain survival (median)', x: { min: 0, max: 1 }, extra: [errBars(r.map((x, i) => [x.chain_p05, x.chain_p95, i]))] }); }, 'evidence');
      U.chart(U.$('#evCtl'), () => { const c = t(), r = e11.controller || [], phases = [...new Set(r.map((x) => x.phase))], ctls = [...new Set(r.map((x) => x.controller))], cols = [c.data, c.data2, c.data3, c.eq, c.ink3];
        return U.base({ grid: { left: 40, right: 10, top: 40, bottom: 30 }, legend: { top: 0, left: 0, textStyle: { color: c.ink2, fontSize: 9.5 } }, xAxis: U.ax({ type: 'category', data: phases, axisLabel: { color: c.ink3, fontSize: 9.5, interval: 0 } }), yAxis: U.ax({ name: 'η_r', min: 0.6, max: 1 }),
          series: ctls.map((k, i) => ({ type: 'bar', name: k, data: phases.map((p) => { const q = r.find((x) => x.controller === k && x.phase === p); return q ? +q.eta_mean.toFixed(3) : null; }), itemStyle: { color: cols[i % 5] } })) }); }, 'evidence');
      U.chart(U.$('#evFeaD'), () => { const c = t(), tt = (e.fea || {}).totals || {}; return U.base({ tooltip: { trigger: 'item' }, legend: { right: 0, top: 'middle', orient: 'vertical', textStyle: { color: c.ink2, fontSize: 10 } },
        series: [{ type: 'pie', radius: ['45%', '75%'], center: ['35%', '50%'], label: { show: false }, data: [['PASS', c.eq], ['MARGINAL', c.p3], ['FAIL', c.p2], ['INFO', c.data3]].map(([k, col]) => ({ name: `${k} ${tt[k] || 0}`, value: tt[k] || 0, itemStyle: { color: col } })) }] }); }, 'evidence');
    },
    update() {},
  };

  P.compliance = {
    title: 'Compliance', build(root) {
      const e = E();
      root.innerHTML = `<div class="page-h"><h1>Compliance &amp; governance</h1><span class="sub">Permits (FANR / Nawah, EAD, Abu Dhabi Maritime) · cyber (IEC 62443 / FANR-REG-08) · no-harm charter · AI governance</span></div>
      <div class="kpis" style="margin-bottom:10px">${['permits', 'cyber'].map((k) => { const tt = (e[k] || {}).totals || {}; return Object.keys(tt).map((s) => `<div class="kpi ${s === 'RISK' ? 'abn' : ''}"><div class="l">${k === 'permits' ? 'Permit items' : 'Cyber items'} ${s}</div><div class="v">${tt[s]}</div><div class="s">${k === 'permits' ? 'of ' + ((e.permits || {}).n_items || '') : 'of 13'}</div></div>`).join(''); }).join('')}
        <div class="kpi"><div class="l">No-harm rules met (live)</div><div class="v" id="cpNH">—</div><div class="s">simulated plant</div></div></div>
      <div class="grid g2">
        <div class="panel"><h3>No-harm charter — live status</h3><div class="note" style="margin-bottom:6px;color:var(--ink)"><b>No bubble curtain, because air under the bell kills jellyfish (AZA); Layer 2 uses water jets only.</b></div><div id="cpRules"></div></div>
        <div class="panel"><h3>AI governance</h3><table class="t">
          <tr><td>Mode</td><td><b>ADVISORY ONLY</b> — suggestions require a named operator's acceptance; every decision logged</td></tr>
          <tr><td>Never allowed</td><td>Deploy / veto, bay raise/lower, interlock or E-stop changes, HydroLift hold/restart, relief flaps, outlet change without operator confirmation</td></tr>
          <tr><td>Network</td><td>Runs on-site, air-gapped; IT → OT one-way via data diode; no remote control of anything safety-related</td></tr>
          <tr><td>Model-check evidence</td><td>MC4: forecast/twin inputs never change bay commands or OS state (159,798 checks, 0 differing)</td></tr>
          <tr><td>Value</td><td>TESTS/11: closed loop matters mainly as a backup (η_r 0.81 vs 0.76 with fouled bay + belt fault)</td></tr>
          <tr><td>This demo</td><td>Rule-based logic stands in for the model; no network calls</td></tr></table></div>
        <div class="panel full"><h3>Permit checklist</h3><div class="scroll" style="max-height:360px"><table class="t" id="cpPerm"></table></div>${src((e.permits || {}).source || '')}</div>
        <div class="panel full"><h3>Cybersecurity checklist (IEC 62443 / FANR-REG-08)</h3><div class="scroll" style="max-height:360px"><table class="t" id="cpCy"></table></div>${src((e.cyber || {}).source || '')}</div>
      </div>`;
      U.$('#cpPerm').innerHTML = '<tr><th>ID</th><th>Requirement</th><th>Authority</th><th>Status</th><th>Why</th></tr>' + ((e.permits || {}).rows || []).map((r) => `<tr><td class="mono">${r.id}</td><td>${U.esc(r.requirement)}</td><td>${U.esc(r.authority)}</td><td class="${vcls(r.status)}">${r.status}</td><td class="note">${U.esc(r.why)}</td></tr>`).join('');
      U.$('#cpCy').innerHTML = '<tr><th>#</th><th>Item</th><th>Standard</th><th>Requirement</th><th>Status</th><th>Note</th></tr>' + ((e.cyber || {}).rows || []).map((r) => `<tr><td>${r.n}</td><td>${U.esc(r.item)}</td><td class="note">${U.esc(r.standard)}</td><td>${U.esc(r.requirement)}</td><td class="${vcls(r.status)}">${r.status}</td><td class="note">${U.esc(r.note)}</td></tr>`).join('');
    },
    update() {
      const s = JZ.sim, op = s.ht.qout > 0.1;
      const rules = [
        ['No acoustic deterrents', true, 'None installed (bio rule R13)'], ['No nets, no hand handling', true, 'Water-to-water transfer only (R07)'], ['No live killing', true, 'Recover mode removed in v4.1; DOA-only to reuse'],
        ['No bubbles under bells', true, 'O₂ dissolved in side-stream, no free gas (R01/R02)'], ['No bubble curtain', true, 'Air under the bell kills jellyfish (AZA); Layer 2 uses water jets only'], ['No screws / pump impellers in animal path', true, 'Water-only HydroLift (v5)'], ['Turtles never enter the pipe', true, 'Excluder grid + 2oo3 vote + lock hold'],
        ['O₂ at outlet ≥ 5 mg/L', !op || s.o2.tail >= 5, op ? s.o2.tail.toFixed(1) + ' mg/L now' : 'pipe idle'], ['Diffuser exit ≤ 1 m/s', !s.pipe || s.pipe.exitV <= 1, s.pipe ? s.pipe.exitV.toFixed(2) + ' m/s' : '—'],
        ['Release outlet approved by operator', !s.outlet.pending || s.os === 'IDLE', s.outlet.pending ? 'recommendation pending' : 'approved: ' + s.outlet.approved], ['Release away from Ruwais, reefs, beaches', true, 'Outlets sited per EAD screening (illustrative)'],
        ['ΔT ≤ 1 °C, same seawater', true, 'trenched pipe, no thermal outfall routing (R08/R09)'], ['Survival measured, not assumed', false, 'OPEN — 3 h pipe loop + 96 h scoring (T09/P02)']];
      U.$('#cpNH').textContent = `${rules.filter((r) => r[1]).length}/${rules.length}`;
      U.$('#cpRules').innerHTML = '<table class="t">' + rules.map(([n, ok, d]) => `<tr><td><span class="lamp ${ok ? 'ok' : 'warn'}"></span></td><td><b>${n}</b></td><td class="note">${U.esc(d)}</td></tr>`).join('') + '</table>';
    },
  };

  // ---- Simulation (embedded module) and 3D tour
  const embed = (id, path, label, note) => ({ title: label, build(root) {
    root.innerHTML = `<div class="page-h"><h1>${label}</h1><span class="sub">${note}</span><span style="margin-left:auto"><a class="btn" href="${path}" target="_blank" rel="noopener">Open full screen</a></span></div><div id="${id}Wrap"></div>`;
  }, show(root) {
    const w = U.$('#' + id + 'Wrap'); if (w.dataset.on) return; w.dataset.on = '1';
    const f = document.createElement('iframe'); f.className = 'embed'; f.title = label; f.src = path; w.appendChild(f);
    f.addEventListener('load', () => { try { const d = f.contentDocument; if (d && (!d.body || d.body.childElementCount === 0 || /not found|ERR_FILE/i.test(d.title))) throw 'missing'; } catch (e) { if (e === 'missing') w.innerHTML = `<div class="placeholder">The module <code>${path}</code> is not built yet. It will appear here automatically once it exists.</div>`; } });
  }, update() {} });
  P.simulation = embed('sim', 'sim/index.html', 'Simulation', 'Model-based simulation (toy twin, validated against our Python model, not field data) — runs live in your browser');
  P.tour = embed('tour', '../3d/index.html', '3D simulation', 'JAZR v5 cinematic 3D twin: split BEFORE / WITH JAZR, Layer 2, HydroLift, release alive');
})();
