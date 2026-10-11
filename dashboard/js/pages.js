/* Secondary pages: Screens, Bypass & Lift, Release, Wildlife, Biology, Alarms, Trends & Analytics, Maintenance, Reports. */
(function () {
  'use strict';
  const JZ = window.JZ, U = JZ.ui, C = JZ.C;
  const P = (JZ.pages = JZ.pages || {});
  const S = () => JZ.sim;
  const hist = (n) => { const h = S().hist; return n ? h.slice(-n) : h; };
  const sel = (JZ.sel = { lane: 1, bay: 22, Hs: null, out: 'auto', range: 720 });
  const kpi = (id, l, s) => `<div class="kpi" id="${id}"><div class="l">${l}</div><div class="v">—</div><div class="s">${s || ''}</div></div>`;
  const setK = (id, v, s, abn) => { const e = document.getElementById(id); if (!e) return; e.querySelector('.v').innerHTML = v; if (s != null) e.querySelector('.s').innerHTML = s; e.classList.toggle('abn', !!abn); };
  const rangeSel = (id) => `<select id="${id}" class="rng"><option value="60">1 h</option><option value="360">6 h</option><option value="720" selected>12 h</option><option value="1440">24 h</option><option value="0">all</option></select>`;
  const H = () => hist(sel.range || 0);
  document.addEventListener('change', (e) => { if (e.target.classList && e.target.classList.contains('rng')) { sel.range = +e.target.value; document.querySelectorAll('.rng').forEach((x) => (x.value = e.target.value)); JZ.app.tick(true); } });

  // ======================================================== SCREENS
  P.screens = {
    title: 'Screens', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Inner screens — angled (11°) moving-belt bays</h1><span class="sub">168 bays · per-bay ΔP (2 transmitters + load-cell estimate, 2oo3), tide- and flow-compensated blockage index, wave filter τ 30 s + 20 s persistence</span></div>
      <div class="kpis" style="margin-bottom:10px">${kpi('sk1', 'Bays down', 'of 168')}${kpi('sk2', 'Blockage index max', 'H 35 % · HH 55 %')}${kpi('sk3', 'Belt drives tripped', 'overcurrent')}${kpi('sk4', 'Relief flaps open', 'passive shear-pin')}${kpi('sk5', 'Raising now', 'pulse rule K = 1 / lane')}${kpi('sk6', 'ΔP clean (expected)', 'tide + flow compensation')}</div>
      <div class="grid g3">
        <div class="panel span2"><h3>Blockage index heatmap (compensated) <span class="r">click a cell to select · grey = normal, colour = alarm band</span></h3><div class="chart" id="scHeat" style="height:230px"></div></div>
        <div class="panel"><h3>Selected bay <span class="r" id="scSelL"></span></h3><div id="scSel"></div></div>
        <div class="panel"><h3>Belt speed vs sweep speed per lane</h3><div class="chart" id="scBelt"></div><div class="note">v5: belts run along the face toward the apex at 0.5–1.0× sweep (mechanisms sim: η ≈ 1.0 across that band, SIMULATED).</div></div>
        <div class="panel"><h3>Motor current — selected lane (42 bays)</h3><div class="chart" id="scCur"></div></div>
        <div class="panel"><h3>Wave filter on selected bay ΔP (last 120 s) <span class="r">Hs <input id="scHs" type="range" min="0" max="2" step="0.1" style="width:90px"> <b class="mono" id="scHsV"></b></span></h3><div class="chart" id="scWave"></div><div class="note" id="scWaveN"></div></div>
        <div class="panel span2"><h3>Selected bay trend — BI, current, belt speed <span class="r">${rangeSel('scR')}</span></h3><div class="chart" id="scTr"></div></div>
        <div class="panel"><h3>Lane BI mean / max trend</h3><div class="chart" id="scLane"></div></div>
      </div>`;
      const t = U.theme;
      U.chart(U.$('#scHeat'), () => {
        const s = S(), data = [];
        s.lanes.forEach((ln, l) => ln.bays.forEach((b, i) => data.push([i, 3 - l, b.st === 'FAULT' || b.flap || b.trip ? 101 : b.pos > 0 ? Math.round(b.bi * 100) : -1])));
        const c = t();
        return U.base({ grid: { left: 54, right: 10, top: 8, bottom: 40 }, tooltip: { trigger: 'item', formatter: (p) => `L${4 - p.value[1]}-B${p.value[0] + 1}: ${p.value[2] < 0 ? 'stowed' : p.value[2] > 100 ? 'FAULT / flap' : p.value[2] + ' %'}` },
          xAxis: U.ax({ type: 'category', data: [...Array(42).keys()].map((i) => i + 1), name: 'bay', nameLocation: 'middle', nameGap: 22, splitArea: { show: false } }),
          yAxis: U.ax({ type: 'category', data: ['Lane 4', 'Lane 3', 'Lane 2', 'Lane 1'] }),
          visualMap: { type: 'piecewise', show: true, orient: 'horizontal', bottom: 0, right: 0, itemWidth: 12, itemHeight: 9, textStyle: { color: c.ink3, fontSize: 10 },
            pieces: [{ lt: 0, label: 'stowed', color: c.inset }, { gte: 0, lt: 10, label: '<10', color: c.eqfill }, { gte: 10, lt: 35, label: '10–35', color: c.eq }, { gte: 35, lt: 55, label: 'H', color: c.p3 }, { gte: 55, lte: 100, label: 'HH', color: c.p2 }, { gt: 100, label: 'fault', color: c.p1 }] },
          series: [{ type: 'heatmap', data, itemStyle: { borderColor: c.panel, borderWidth: 1 }, label: { show: false } }] });
      }, 'screens');
      U.charts[U.charts.length - 1].inst.on('click', (p) => { sel.lane = 3 - p.value[1]; sel.bay = p.value[0]; JZ.app.tick(true); });
      U.chart(U.$('#scBelt'), () => { const s = S(), c = t(); return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 24 },
        xAxis: U.ax({ type: 'category', data: s.lanes.map((_, i) => 'Lane ' + (i + 1)) }), yAxis: U.ax({ name: 'm/s' }),
        series: [{ name: 'Sweep', type: 'bar', data: s.lanes.map((l) => +(l.sweep || C.SWEEP).toFixed(3)), itemStyle: { color: c.data3 } },
          { name: 'Belt (mean of down bays)', type: 'bar', data: s.lanes.map((l) => { const d = l.bays.filter((b) => b.st === 'DOWN'); return d.length ? +(d.reduce((a, b) => a + b.v, 0) / d.length).toFixed(3) : 0; }), itemStyle: { color: c.data } }] }); }, 'screens');
      U.chart(U.$('#scCur'), () => { const s = S(), c = t(), ln = s.lanes[sel.lane]; return U.base({ grid: { left: 40, right: 10, top: 20, bottom: 24 }, xAxis: U.ax({ type: 'category', data: ln.bays.map((_, i) => i + 1) }), yAxis: U.ax({ name: 'A', max: 50 }),
        series: [{ type: 'bar', name: 'Motor current', data: ln.bays.map((b, i) => ({ value: +b.I.toFixed(1), itemStyle: { color: b.trip || b.I > 30 ? c.p2 : i === sel.bay ? c.sel : c.eq } })), markLine: { symbol: 'none', data: [{ yAxis: 40, name: 'OC trip' }], lineStyle: { color: c.ink3, type: 'dashed' }, label: { color: c.ink3, formatter: 'OC trip 40 A' } } }] }); }, 'screens');
      const hs = U.$('#scHs'); hs.value = S().sc.Hs; hs.oninput = () => { sel.Hs = +hs.value; JZ.app.tick(true); };
      U.chart(U.$('#scWave'), () => { const s = S(), c = t(), w = s.waveTrace(sel.lane, sel.bay, sel.Hs); U.$('#scHsV').textContent = (sel.Hs != null ? sel.Hs : s.sc.Hs).toFixed(1) + ' m';
        U.$('#scWaveN').textContent = `Naive 200 Pa single-threshold trips in this window: ${w.naive}. Filtered (τ 30 s, 20 s persistence, 2oo3) trips: ${w.filtTrips}. Test 08 D6: 0 false trips up to Hs 2 m vs 52–828 per bay-day for a naive threshold.`;
        return U.base({ grid: { left: 44, right: 10, top: 24, bottom: 24 }, xAxis: U.ax({ name: 's', nameLocation: 'end' }), yAxis: U.ax({ name: 'Pa' }),
          series: [U.line('Raw ΔP (waves)', w.pts.map((p) => [p[0], +p[1].toFixed(1)]), c.data3, { lineStyle: { width: 1, color: c.data3 } }), U.line('Filtered', w.pts.map((p) => [p[0], +p[2].toFixed(1)]), c.data, { lineStyle: { width: 2.2, color: c.data } }),
            { type: 'line', name: '200 Pa naive', data: [[0, 200], [120, 200]], showSymbol: false, lineStyle: { type: 'dashed', color: c.ink3, width: 1 }, itemStyle: { color: c.ink3 } }] }); }, 'screens');
      U.chart(U.$('#scTr'), () => { const s = S(), c = t(), d = s.bayTrend(sel.lane, sel.bay).slice(-(sel.range || 480)); return U.base({ grid: { left: 44, right: 44, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: [U.ax({ name: 'BI %', max: 100 }), U.ax({ name: 'A · m/s×50', splitLine: { show: false } })],
        series: [U.line('Blockage index %', d.map((p) => [p[0], +(p[1] * 100).toFixed(1)]), c.data, { markLine: { symbol: 'none', silent: true, data: [{ yAxis: 35 }, { yAxis: 55 }], lineStyle: { color: c.ink3, type: 'dashed' }, label: { color: c.ink3, formatter: (p) => (p.value == 35 ? 'H' : 'HH') } } }),
          U.line('Motor current A', d.map((p) => [p[0], +p[2].toFixed(1)]), c.data2, { yAxisIndex: 1 }), U.line('Belt speed ×50', d.map((p) => [p[0], +(p[3] * 50).toFixed(1)]), c.data3, { yAxisIndex: 1, lineStyle: { type: 'dotted', color: c.data3, width: 1.5 } })] }); }, 'screens');
      U.chart(U.$('#scLane'), () => { const c = t(), h = H(), cols = [c.data, c.data2, c.data3, c.eq]; return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: U.ax({ name: '%' }),
        series: [0, 1, 2, 3].flatMap((l) => [U.line(`L${l + 1} max`, h.map((x) => [x.t, +(x.laneBImax[l] * 100).toFixed(1)]), cols[l], { lineStyle: { width: 1.2, color: cols[l], type: 'dashed' } }), U.line(`L${l + 1} mean`, h.map((x) => [x.t, +(x.laneBI[l] * 100).toFixed(1)]), cols[l])]) }); }, 'screens');
    },
    update() {
      const s = S(), all = s.lanes.flatMap((l) => l.bays);
      const exp = C.DP_CLEAN * (7 / (7 + JZ.tide(s.t))) ** 2;
      setK('sk1', all.filter((b) => b.st === 'DOWN').length);
      const bim = Math.max(...all.map((b) => b.bi)); setK('sk2', (bim * 100).toFixed(0) + ' %', null, bim >= C.BI_H);
      setK('sk3', all.filter((b) => b.trip).length, null, all.some((b) => b.trip)); setK('sk4', all.filter((b) => b.flap).length, null, all.some((b) => b.flap));
      setK('sk5', all.filter((b) => b.st === 'RAISING').length); setK('sk6', exp.toFixed(0) + ' Pa', `tide ${JZ.tide(s.t).toFixed(2)} m`);
      const b = s.lanes[sel.lane].bays[sel.bay];
      U.$('#scSelL').textContent = `L${sel.lane + 1}-B${String(sel.bay + 1).padStart(2, '0')}`;
      U.$('#scSel').innerHTML = `<div class="kv"><span class="k">State</span><span class="v">${b.st}</span><span class="k">ΔP A / B / load-cell</span><span class="v">${b.ch.map((x) => x.toFixed(0)).join(' / ')} Pa</span>
        <span class="k">2oo3 voted</span><span class="v">${b.dp.toFixed(0)} Pa${b.devT > 60 ? ' · A deviating (masked)' : ''}</span><span class="k">Blockage index</span><span class="v">${(b.bi * 100).toFixed(1)} %</span>
        <span class="k">Persistence ≥ HH</span><span class="v">${b.pers.toFixed(0)} / ${C.PERSIST_S} s</span><span class="k">Belt</span><span class="v">${b.v.toFixed(2)} m/s · ${b.ratio.toFixed(2)}× sweep</span>
        <span class="k">Motor current</span><span class="v">${b.I.toFixed(1)} A${b.trip ? ' TRIP' : ''}</span><span class="k">Shear pin / flap</span><span class="v">${b.pin}${b.flap ? ' · OPEN' : ''}</span>
        <span class="k">Face load</span><span class="v">${b.load.toFixed(0)} kg</span></div><button class="btn sm" style="margin-top:6px" onclick="JZ.main.openBay(${sel.lane},${sel.bay})">Open faceplate</button>`;
    },
  };

  // ======================================================== BYPASS & LIFT
  P.lift = {
    title: 'Bypass & Lift', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Bypass &amp; lift — entrances → flat-plate dewatering → excluder → water-only HydroLift → head tank → O₂ → pipe</h1><span class="sub">no screws, no pump impeller, no free fall, no bubbles</span></div>
      <div class="kpis" style="margin-bottom:10px">${kpi('lk1', 'Entrance flow (all lanes)', '15–20 % of lane flow')}${kpi('lk2', 'Dewatering return', 'surplus back to lanes')}${kpi('lk3', 'Lift throughput', 't/h, 4 locks')}${kpi('lk4', 'Head tank level', 'H 3.2 / L 1.2 m')}${kpi('lk5', 'Pipe transit', '1.6 m ID gravity')}${kpi('lk6', 'Outlet O₂', 'target ≥ 5 mg/L')}${kpi('lk7', 'Diffuser exit velocity', 'limit ≤ 1 m/s')}</div>
      <div class="grid g3">
        <div class="panel"><h3>Entrance flow split per lane</h3><div class="chart" id="lfSplit"></div></div>
        <div class="panel"><h3>HydroLift chamber cycle — lane <select id="lfLane"><option value="0">1</option><option value="1">2</option><option value="2">3</option><option value="3">4</option></select></h3><div class="chart" id="lfLock"></div><div id="lfLockT"></div></div>
        <div class="panel"><h3>O₂ along the pipe <span class="r">side-stream dissolved, no bubbles</span></h3><div class="chart" id="lfO2"></div></div>
        <div class="panel"><h3>Head tank level &amp; pipe flow <span class="r">${rangeSel('lfR')}</span></h3><div class="chart" id="lfHT"></div></div>
        <div class="panel"><h3>O₂ at head tank / outlet, dose</h3><div class="chart" id="lfO2T"></div></div>
        <div class="panel"><h3>Throughput by lane (t/h lifted)</h3><div class="chart" id="lfTp"></div></div>
        <div class="panel full"><h3>Per-lane status</h3><div class="scroll"><table class="t" id="lfTab"></table></div></div>
      </div>`;
      const t = U.theme;
      U.chart(U.$('#lfSplit'), () => { const s = S(), c = t(); return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 24 }, xAxis: U.ax({ type: 'category', data: s.lanes.map((_, i) => 'Lane ' + (i + 1)) }), yAxis: U.ax({ name: '% of lane flow', min: 0, max: 25 }),
        series: [{ type: 'bar', name: 'Entrance split', data: s.lanes.map((l) => +(l.split * 100).toFixed(1)), itemStyle: { color: c.data }, label: { show: true, position: 'top', color: c.ink2, formatter: '{c} %' },
          markArea: { silent: true, itemStyle: { color: c.inset, opacity: 0.8 }, data: [[{ yAxis: 15, name: 'design band 15–20 %' }, { yAxis: 20 }]], label: { color: c.ink3, position: 'insideTopRight' } } }] }); }, 'lift');
      U.$('#lfLane').onchange = () => JZ.app.tick(true);
      U.chart(U.$('#lfLock'), () => { const s = S(), c = t(), ln = s.lanes[+U.$('#lfLane').value], F = ln.fillS, cyc = F + C.LOCK_RISE + C.LOCK_XFER + C.LOCK_DRAIN;
        const prof = (tp) => tp < F ? 0.4 + 0.3 * (tp / F) : tp < F + C.LOCK_RISE ? 0.7 + (C.LOCK_HEAD - 0.7) * ((tp - F) / C.LOCK_RISE) : tp < F + C.LOCK_RISE + C.LOCK_XFER ? C.LOCK_HEAD : C.LOCK_HEAD - (C.LOCK_HEAD - 0.4) * ((tp - F - C.LOCK_RISE - C.LOCK_XFER) / C.LOCK_DRAIN);
        const cols = [c.data, c.data2, c.data3];
        return U.base({ grid: { left: 36, right: 10, top: 26, bottom: 26 }, xAxis: U.ax({ name: 's in cycle', max: cyc }), yAxis: U.ax({ name: 'm', max: 7 }),
          series: ln.lock.map((ch, k) => { const off = (k * cyc) / 3; const d = []; for (let x = 0; x <= cyc; x += 5) d.push([x, +prof((x + off) % cyc).toFixed(2)]); return U.line('C' + (k + 1), d, cols[k], { markPoint: { symbol: 'circle', symbolSize: 10, data: [{ coord: [((ch.tp - off) % cyc + cyc) % cyc, ch.level] }], itemStyle: { color: cols[k] }, label: { show: false } } }); }) }); }, 'lift');
      U.chart(U.$('#lfO2'), () => { const s = S(), c = t(), p = s.o2.prof; return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 26 }, xAxis: U.ax({ name: 'km', max: 10.5 }), yAxis: U.ax({ name: 'mg/L', min: 0, max: 15 }),
        series: [U.line('Dissolved O₂', s.ht.qout > 0.1 ? p.map((x) => [+x[0].toFixed(2), +x[1].toFixed(2)]) : [], c.data, { areaStyle: { color: c.data, opacity: 0.08 } }),
          { type: 'line', name: 'target 5', data: [[0, 5], [10.5, 5]], showSymbol: false, lineStyle: { type: 'dashed', color: c.ink3 }, itemStyle: { color: c.ink3 } },
          { type: 'line', name: 'LL 3', data: [[0, 3], [10.5, 3]], showSymbol: false, lineStyle: { type: 'dotted', color: c.p1 }, itemStyle: { color: c.p1 } },
          { type: 'line', name: 'saturation', data: [[0, s.o2.sat], [10.5, s.o2.sat]], showSymbol: false, lineStyle: { type: 'dotted', color: c.data3 }, itemStyle: { color: c.data3 } }] }); }, 'lift');
      U.chart(U.$('#lfHT'), () => { const c = t(), h = H(); return U.base({ grid: { left: 40, right: 40, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: [U.ax({ name: 'm', min: 0, max: 3.6 }), U.ax({ name: 'h', splitLine: { show: false } })],
        series: [U.line('Level', h.map((x) => [x.t, +x.lvl.toFixed(2)]), c.data), U.line('Transit h', h.map((x) => [x.t, +(x.transit / 3600).toFixed(2)]), c.data3, { yAxisIndex: 1 })] }); }, 'lift');
      U.chart(U.$('#lfO2T'), () => { const c = t(), h = H(); return U.base({ grid: { left: 40, right: 44, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: [U.ax({ name: 'mg/L', min: 0 }), U.ax({ name: 'kg/h', splitLine: { show: false } })],
        series: [U.line('Head tank', h.map((x) => [x.t, +x.o2head.toFixed(2)]), c.data2), U.line('Outlet', h.map((x) => [x.t, +x.o2tail.toFixed(2)]), c.data, { markLine: { symbol: 'none', data: [{ yAxis: 5 }], lineStyle: { color: c.ink3, type: 'dashed' }, label: { color: c.ink3, formatter: '5' } } }), U.line('Dose kg/h', h.map((x) => [x.t, +x.inj.toFixed(0)]), c.data3, { yAxisIndex: 1 })] }); }, 'lift');
      U.chart(U.$('#lfTp'), () => { const c = t(), h = H(), cols = [c.data, c.data2, c.data3, c.eq]; return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: U.ax({ name: 't/h' }),
        series: [0, 1, 2, 3].map((l) => U.line('Lane ' + (l + 1), h.map((x) => [x.t, +x.tput[l].toFixed(1)]), cols[l])) }); }, 'lift');
    },
    update() {
      const s = S(), ent = s.lanes.reduce((a, l) => a + l.split * C.Q_LANE, 0), lift = s.lanes.reduce((a, l) => a + l.liftedRate, 0) * C.MASS * 3.6;
      setK('lk1', U.n(ent, 1) + ' <small>m³/s</small>'); setK('lk2', U.n(Math.max(0, ent - s.ht.qin), 1) + ' <small>m³/s</small>'); setK('lk3', U.n(lift, 1) + ' <small>t/h</small>');
      setK('lk4', s.ht.level.toFixed(2) + ' <small>m</small>', null, s.ht.level < 1.2 && s.ht.valve); setK('lk5', s.pipe ? (s.pipe.transit / 3600).toFixed(2) + ' <small>h · ' + s.pipe.km + ' km</small>' : '—');
      setK('lk6', s.ht.qout > 0.1 ? s.o2.tail.toFixed(1) + ' <small>mg/L</small>' : '—', null, s.ht.qout > 0.1 && s.o2.tail < 5); setK('lk7', s.pipe ? s.pipe.exitV.toFixed(2) + ' <small>m/s</small>' : '—', null, s.pipe && s.pipe.exitV > 1);
      const ln = s.lanes[+U.$('#lfLane').value];
      U.$('#lfLockT').innerHTML = `<div class="note">${ln.lock.map((c, k) => `C${k + 1}: ${c.hold ? 'HOLD' : c.ph} ${c.level.toFixed(1)} m`).join(' · ')} · cycle ${ln.fillS + 150} s · ${ln.lockHold ? 'HELD by wildlife interlock' : ln.running ? 'cycling' : 'stopped'}</div>`;
      U.$('#lfTab').innerHTML = `<tr><th>Lane</th><th class="num">Entrances</th><th class="num">Split</th><th class="num">Entrance m³/s</th><th class="num">Return m³/s</th><th class="num">Collector</th><th>Excluder vote C/S/B</th><th>Lock</th><th class="num">Lifted t/h</th><th class="num">Fish routed</th><th class="num">η_r (sim) / est.</th></tr>` +
        s.lanes.map((l, i) => `<tr><td>${i + 1}</td><td class="num">${l.entrances}</td><td class="num">${(l.split * 100).toFixed(1)} %</td><td class="num">${(l.split * C.Q_LANE).toFixed(1)}</td><td class="num">${Math.max(0, l.split * C.Q_LANE - l.liftQ).toFixed(1)}</td><td class="num">${U.big(l.collector)}</td><td class="mono">${l.votes.join(' / ')}</td><td>${l.lockHold ? '<b>HELD (wildlife)</b>' : l.manualHold ? 'HELD (operator)' : l.running ? 'cycling' : 'stopped'}</td><td class="num">${U.n(l.liftedRate * C.MASS * 3.6, 1)}</td><td class="num">${U.n(l.fish, 0)}</td><td class="num">${l.eta.toFixed(3)} / ${l.etaHat.toFixed(3)}</td></tr>`).join('');
    },
  };

  // ======================================================== RELEASE
  P.release = {
    title: 'Release', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Release-Near / Release-Far (v4.1 no-harm policy)</h1><span class="sub">10-day drift ensemble (48 members) picks the outlet · operator approves · no Recover / kill mode exists</span></div>
      <div class="grid g3">
        <div class="panel span2"><h3>Release map <span class="r">schematic, not to scale, not for navigation · zones illustrative</span> <select id="rlOut"><option value="near">show near tracks</option><option value="far">show far tracks</option></select></h3><svg id="rlMap" viewBox="0 0 900 380" style="width:100%;height:auto" role="img" aria-label="Release map"></svg></div>
        <div class="panel"><h3>Decision</h3><div id="rlDec"></div></div>
        <div class="panel span2"><h3>10-day distance-to-intake fan (P10–P90, P25–P75, median)</h3><div class="chart tall" id="rlFan"></div></div>
        <div class="panel"><h3>Cumulative return risk (within 3 km of intake)</h3><div class="chart tall" id="rlRisk"></div></div>
        <div class="panel span2"><h3>Decision log <button class="btn sm" id="rlCsv">CSV</button></h3><div class="scroll" style="max-height:240px"><table class="t" id="rlLog"></table></div></div>
        <div class="panel"><h3>Twin reference (far release, η_r 0.9, 10-day bloom)</h3><div class="chart" id="rlRef"></div><div class="src">twin/out/v5_far.json</div></div>
      </div>`;
      U.$('#rlOut').onchange = () => P.release.map();
      U.$('#rlCsv').onclick = () => U.csv('jazr_decision_log.csv', S().logs.decisions.map((d) => ({ time: JZ.fmtISO(d.t), kind: d.kind, from: d.from, to: d.to, status: d.status, by: d.by, basis: d.basis })));
      const t = U.theme;
      U.chart(U.$('#rlFan'), () => { const s = S(), c = t(), f = s.fc; if (!f) return {}; const ser = [];
        [['near', c.data2], ['far', c.data]].forEach(([k, col]) => { const d = f[k].dist, x = d.map((_, i) => i / 24);
          ser.push(U.band(k + ' P10–90', d.map((q, i) => [x[i], q[0], q[4]]), col, 0.13)); ser.push(U.band(k + ' P25–75', d.map((q, i) => [x[i], q[1], q[3]]), col, 0.22));
          ser.push(U.line(k.toUpperCase() + ' median', d.map((q, i) => [x[i], +q[2].toFixed(2)]), col, { lineStyle: { width: 2.2, color: col } })); });
        ser.push({ type: 'line', name: 'return zone 3 km', data: [[0, 3], [10, 3]], showSymbol: false, lineStyle: { type: 'dashed', color: c.p2 }, itemStyle: { color: c.p2 } });
        return U.base({ grid: { left: 44, right: 10, top: 30, bottom: 28 }, legend: { top: 0, right: 0, data: ['NEAR median', 'FAR median', 'return zone 3 km'], textStyle: { color: c.ink2, fontSize: 10.5 } }, tooltip: { trigger: 'axis' }, xAxis: U.ax({ name: 'days after release', nameLocation: 'middle', nameGap: 18, max: 10 }), yAxis: U.ax({ name: 'km from intake', min: 0 }), series: ser }); }, 'release');
      U.chart(U.$('#rlRisk'), () => { const s = S(), c = t(), f = s.fc; if (!f) return {}; return U.base({ grid: { left: 40, right: 10, top: 30, bottom: 28 }, xAxis: U.ax({ name: 'days', nameLocation: 'middle', nameGap: 18, max: 10 }), yAxis: U.ax({ name: '%', max: 100 }),
        series: [U.line('Near', f.near.ret.map((r, i) => [i / 24, +(r * 100).toFixed(1)]), c.data2, { lineStyle: { width: 2, color: c.data2 } }), U.line('Far', f.far.ret.map((r, i) => [i / 24, +(r * 100).toFixed(1)]), c.data, { lineStyle: { width: 2, color: c.data } }),
          { type: 'line', name: '10 % policy', data: [[0, 10], [10, 10]], showSymbol: false, lineStyle: { type: 'dashed', color: c.ink3 }, itemStyle: { color: c.ink3 } }] }); }, 'release');
      U.chart(U.$('#rlRef'), () => { const c = t(), E = window.JZ_EVIDENCE; if (!E) return {}; const r = E.far_release.rows; return U.base({ grid: { left: 150, right: 40, top: 24, bottom: 24 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        xAxis: U.ax({ name: '%', max: 60 }), yAxis: U.ax({ type: 'category', data: r.map((x) => `${x.x_km} km along · ${x.y_km} out${x.ur_cm_s ? ' · ur 1' : ''}`), axisLabel: { color: c.ink3, fontSize: 9.5 } }),
        series: [{ type: 'bar', name: 'mean', data: r.map((x) => ({ value: +(x.mean * 100).toFixed(1), itemStyle: { color: x.x_km >= 10 ? c.data : c.data3 } })), label: { show: true, position: 'right', color: c.ink2, fontSize: 10, formatter: '{c}%' } }] }); }, 'release');
      this.map();
    },
    map() {
      const s = S(), svg = U.$('#rlMap'); if (!svg) return; const G = JZ.GEO, X = (x) => 450 + x * 18, Y = (y) => 330 - y * 40;
      const which = U.$('#rlOut').value, f = s.fc;
      let tracks = '';
      if (f) f[which].tracks.slice(0, 48).forEach((tr) => { tracks += `<polyline fill="none" stroke="var(--data)" stroke-opacity=".28" stroke-width="1" points="${tr.map(([x, y]) => `${X(x).toFixed(1)},${Y(Math.max(0, y)).toFixed(1)}`).join(' ')}"/>`; });
      const zones = G.zones.map((z) => `<rect x="${X(z.x0)}" y="${Y(z.y1)}" width="${(z.x1 - z.x0) * 18}" height="${(z.y1 - z.y0) * 40}" fill="${z.kind === 'beach' ? 'var(--inset)' : 'none'}" stroke="var(--ink3)" stroke-dasharray="4 3"/><text x="${X(z.x0) + 3}" y="${Y(z.y1) - 4}" class="tiny">${z.name}</text>`).join('');
      const act = s.outlet.approved;
      const out = (k, lab) => { const [x, y] = G[k.toLowerCase()]; const a = act === k; return `<circle cx="${X(x)}" cy="${Y(y)}" r="${a ? 9 : 6}" fill="${a ? 'var(--eq-on)' : 'var(--panel)'}" stroke="var(--eq-on)" stroke-width="2"/><text x="${X(x) + 12}" y="${Y(y) + 4}" class="lbl">${lab}${a ? ' — ACTIVE' : ''}</text>`; };
      svg.innerHTML = `<rect x="0" y="0" width="900" height="330" fill="var(--water)" opacity=".35"/><rect x="0" y="330" width="900" height="50" fill="var(--inset)"/>
        <path d="M0 330 L900 330" stroke="var(--ink2)" stroke-width="2"/><text x="8" y="350" class="lbl">Coast (trend 070°/250°) — Al Dhafra, schematic</text>
        ${zones}
        <path d="M${X(0)} 330 L${X(0)} ${Y(5)} M${X(0)} ${Y(5.2) + 30} " stroke="none"/>
        <polyline points="${X(0)},330 ${X(0)},${Y(1.2)} ${X(-10)},${Y(1.2)} ${X(-10)},${Y(3)}" fill="none" stroke="var(--pipe)" stroke-width="3" stroke-dasharray="6 3"/>
        <line x1="${X(0)}" y1="${Y(1.2)}" x2="${X(0.6)}" y2="${Y(5)}" stroke="var(--pipe)" stroke-width="3" stroke-dasharray="6 3"/>
        ${tracks}
        <rect x="${X(-0.6)}" y="322" width="22" height="10" fill="var(--eq-on)"/><text x="${X(0) + 14}" y="322" class="lbl">plant intake</text>
        <circle cx="${X(0)}" cy="330" r="${3 * 18}" fill="none" stroke="var(--p2)" stroke-dasharray="3 3"/><text x="${X(-1.4)}" y="${Y(3.25)}" class="tiny" text-anchor="end">3 km return zone</text>
        ${out('NEAR', 'NEAR 5 km offshore')}${out('FAR', 'FAR ~10 km down-drift')}
        <g transform="translate(800,40)"><circle r="26" fill="var(--panel)" stroke="var(--line2)"/><line x1="0" y1="0" x2="${(f ? f.al : 0) * -8}" y2="${(f ? f.on : 0) * 8}" stroke="var(--ink)" stroke-width="3" marker-end="url(#arw2)"/><text y="40" text-anchor="middle" class="tiny">drift ${f ? f.on.toFixed(1) : '—'} cm/s ${f && f.on > 0 ? 'onshore' : 'offshore'}</text></g>
        <defs><marker id="arw2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="var(--ink)"/></marker></defs>
        <g transform="translate(20,20)"><line x1="0" y1="0" x2="${5 * 18}" y2="0" stroke="var(--ink2)" stroke-width="2"/><text x="0" y="14" class="tiny">5 km (alongshore scale)</text></g>`;
    },
    update(full) {
      const s = S(), o = s.outlet;
      if (full || Math.floor(s.t / 60) % 2 === 0) this.map();
      U.$('#rlDec').innerHTML = `<div class="kv"><span class="k">Active outlet</span><span class="v"><b>${o.approved}</b></span><span class="k">Twin recommends</span><span class="v">${o.rec || '—'}</span>
        <span class="k">10-day return risk near</span><span class="v">${o.risk ? U.pct(o.risk.NEAR, 0) : '—'}</span><span class="k">10-day return risk far</span><span class="v">${o.risk ? U.pct(o.risk.FAR, 0) : '—'}</span>
        <span class="k">Forecast mean onshore</span><span class="v">${s.sc.fc.on.toFixed(1)} cm/s</span><span class="k">Forecast age</span><span class="v">${((s.t - s.fcT) / 3600).toFixed(1)} h ${s.fcFresh ? '' : '(STALE)'}</span>
        <span class="k">Released near / far</span><span class="v">${U.big(s.k.relNear)} / ${U.big(s.k.relFar)}</span><span class="k">Diffuser exit</span><span class="v">${s.pipe ? s.pipe.exitV.toFixed(2) : '—'} m/s</span></div>
        ${s.ht.qout > 0.1 && s.o2.tail < 5 ? `<div style="margin-top:8px;padding:6px 8px;border-left:4px solid ${s.o2.tail < 3 ? 'var(--p1)' : 'var(--p2)'};background:var(--inset)"><b>Pipe O₂ ${s.o2.tail.toFixed(1)} mg/L at the ${o.approved} outlet — beyond design density.</b><br><span class="note">Documented response: (1) near route if the forecast allows — near return risk now ${o.risk ? U.pct(o.risk.NEAR, 0) : '—'} ${o.risk && o.risk.NEAR <= 0.1 ? '(allowed)' : '(NOT allowed: stay far)'}; (2) extra O₂ lines / standby dissolver; (3) throttle entrance flow toward 15 %.</span></div>` : ''}
        ${o.pending ? `<div class="msg" style="margin-top:8px;padding:6px 8px;border-left:4px solid var(--p3);background:var(--inset)">Recommendation: <b>${o.pending.from} → ${o.pending.to}</b><br><span class="note">${U.esc(o.pending.basis)}</span><div class="formrow"><button class="btn primary" id="rlA">Approve</button><button class="btn" id="rlJ">Reject</button></div></div>` : '<div class="note" style="margin-top:8px">No pending recommendation. Rule: near if 10-day return risk ≤ 10 %, else far. Both > 10 % → far + alarm (no Recover mode).</div>'}`;
      const a = U.$('#rlA'); if (a) { a.onclick = () => { s.approveOutlet('Operator'); JZ.app.tick(true); }; U.$('#rlJ').onclick = () => { s.rejectOutlet('Operator'); JZ.app.tick(true); }; }
      U.$('#rlLog').innerHTML = '<tr><th>Time</th><th>Kind</th><th>From → To</th><th>Status</th><th>By</th><th>Basis</th></tr>' + s.logs.decisions.slice().reverse().map((d) => `<tr><td class="mono">${JZ.fmtT(d.t)}</td><td>${d.kind}</td><td>${d.from} → <b>${d.to}</b></td><td>${d.status}</td><td>${U.esc(d.by)}</td><td class="note">${U.esc(d.basis)}</td></tr>`).join('');
    },
  };

  // ======================================================== WILDLIFE
  P.wildlife = {
    title: 'Wildlife', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Wildlife protection</h1><span class="sub">Turtle-excluder grid is the primary barrier · camera + imaging sonar + chute break-beam vote (1oo3 holds the lock, 2oo3 confirms) · hard-wired</span></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px"><span class="badge">NO ACOUSTIC DETERRENTS</span><span class="badge">NO BUBBLE CURTAIN (water jets only)</span><span class="badge">NO NETS</span><span class="badge">NO LETHAL STEP</span><span class="badge">NO BUBBLES IN ANIMAL PATH</span><span class="badge">ESCAPE CHUTE ALWAYS OPEN</span></div>
      <div class="kpis" style="margin-bottom:10px">${kpi('wk1', 'Turtles excluded (confirmed)', 'grid → escape chute, alive')}${kpi('wk2', 'Lock auto-holds', 'any 1 of 3 channels')}${kpi('wk3', 'Unconfirmed (1oo3) holds', 'fail-safe; reviewed')}${kpi('wk4', 'Fish routed alive', 'sonar estimate; survival unmeasured')}${kpi('wk5', 'Sightings logged', 'patrol + sensors')}</div>
      <div class="grid g3">
        <div class="panel"><h3>Live 3-channel vote per lane</h3><div id="wlVote"></div></div>
        <div class="panel span2"><h3>Excluder events</h3><div class="scroll" style="max-height:220px"><table class="t" id="wlEx"></table></div></div>
        <div class="panel"><h3>HydroLift auto-holds</h3><div class="scroll" style="max-height:220px"><table class="t" id="wlHold"></table></div></div>
        <div class="panel"><h3>Fish routed (cumulative, by lane)</h3><div class="chart" id="wlFish"></div><div class="note">04 T3: 170–6,900 fish per unit-day depending on density; analogue survival chain median 48 % (with pump). Here: no pump, O₂ held — still to be measured (T09/P02).</div></div>
        <div class="panel"><h3>Turtle / dugong sighting log</h3><div class="scroll" style="max-height:170px"><table class="t" id="wlSig"></table></div>
          <div class="formrow"><select id="wlSp"><option>Green turtle (Chelonia mydas)</option><option>Hawksbill turtle (Eretmochelys imbricata)</option><option>Dugong (Dugong dugon)</option><option>Indo-Pacific humpback dolphin</option></select><input id="wlWh" placeholder="Where (e.g. 1 km N of lane 2)" style="flex:1"><button class="btn primary" id="wlAdd">Log sighting</button></div></div>
      </div>`;
      U.$('#wlAdd').onclick = () => { const s = S(); s.addSighting({ species: U.$('#wlSp').value, where: U.$('#wlWh').value || 'not given', src: 'Operator entry', action: 'Logged; EAD notified (sim)' }); U.$('#wlWh').value = ''; JZ.app.tick(true); };
      const t = U.theme;
      U.chart(U.$('#wlFish'), () => { const c = t(), h = H(), s = S(); const tot = s.lanes.map((l) => l.fish); return U.base({ grid: { left: 40, right: 10, top: 20, bottom: 24 }, xAxis: U.ax({ type: 'category', data: ['Lane 1', 'Lane 2', 'Lane 3', 'Lane 4'] }), yAxis: U.ax({ name: 'fish' }),
        series: [{ type: 'bar', data: tot.map((v) => +v.toFixed(0)), itemStyle: { color: c.data }, label: { show: true, position: 'top', color: c.ink2 } }] }); }, 'wildlife');
    },
    update() {
      const s = S(), k = s.k;
      setK('wk1', k.turtleConfirmed); setK('wk2', k.lockHolds, null, s.lanes.some((l) => l.lockHold)); setK('wk3', s.logs.holds.filter((h) => h.votes.reduce((a, b) => a + b, 0) < 2).length);
      setK('wk4', U.n(k.fish, 0)); setK('wk5', s.logs.sightings.length);
      U.$('#wlVote').innerHTML = `<table class="t"><tr><th>Lane</th><th>Camera</th><th>Sonar</th><th>Chute</th><th>Vote</th><th>Lock</th></tr>${s.lanes.map((l, i) => { const n = l.votes.reduce((a, b) => a + b, 0); return `<tr><td>${i + 1}</td>${l.votes.map((v) => `<td><span class="lamp ${v ? (n >= 2 ? 'warn' : 'warn') : ''}"></span></td>`).join('')}<td class="mono">${n}/3</td><td>${l.lockHold ? '<b>HELD</b>' : l.running ? 'run' : '—'}</td></tr>`; }).join('')}</table><div class="note" style="margin-top:6px">Sensors can only stop/hold the lift (hard-wired), never start it. Restart after 60 s with 0/3.</div>`;
      U.$('#wlEx').innerHTML = '<tr><th>Time</th><th>Lane</th><th>Species</th><th>Votes C/S/B</th><th>Confirmed</th><th>Path</th></tr>' + (s.logs.excluder.length ? s.logs.excluder.slice().reverse().map((e) => `<tr><td class="mono">${JZ.fmtT(e.t)}</td><td>${e.lane + 1}</td><td>${U.esc(e.species)}</td><td class="mono">${e.votes.join('/')}</td><td>${e.confirmed ? 'yes (2oo3)' : 'no (1oo3)'}</td><td>${U.esc(e.path)}</td></tr>`).join('') : '<tr><td colspan="6" class="note">No excluder events in this run (try the “Turtle event” scenario).</td></tr>');
      U.$('#wlHold').innerHTML = '<tr><th>Time</th><th>Lane</th><th>Reason</th></tr>' + (s.logs.holds.length ? s.logs.holds.slice().reverse().map((h) => `<tr><td class="mono">${JZ.fmtT(h.t)}</td><td>${h.lane + 1}</td><td>${U.esc(h.why)}</td></tr>`).join('') : '<tr><td colspan="3" class="note">None.</td></tr>');
      U.$('#wlSig').innerHTML = '<tr><th>Time</th><th>Species</th><th>Where</th><th>Source</th><th>Action</th></tr>' + (s.logs.sightings.length ? s.logs.sightings.slice().reverse().map((x) => `<tr><td class="mono">${JZ.fmtT(x.t)}</td><td>${U.esc(x.species)}</td><td>${U.esc(x.where)}</td><td>${U.esc(x.src)}</td><td class="note">${U.esc(x.action)}</td></tr>`).join('') : '<tr><td colspan="5" class="note">No sightings yet.</td></tr>');
    },
  };

  // ======================================================== BIOLOGY
  const PLATES = [['SP-01', 'Lane 1 cassette (stowed, dry)'], ['SP-02', 'Lane 3 cassette (stowed, dry)'], ['SP-03', 'Training wall underside L2'], ['SP-04', 'Collector roof'], ['SP-05', 'Head tank (shaded side)'], ['SP-06', 'Pipe access port km 2.5'], ['SP-07', 'Near diffuser'], ['SP-08', 'Far diffuser'], ['SP-REF', 'Reference plate, open breakwater']];
  P.biology = {
    title: 'Biology', build(root) {
      const E = window.JZ_EVIDENCE;
      root.innerHTML = `<div class="page-h"><h1>Biology &amp; animal welfare</h1><span class="sub">Rules from 09_biology_behaviour · live checks against the simulated plant · thresholds partly UNKNOWN for rhizostomes</span></div>
      <div class="panel" style="margin-bottom:10px;border-left:4px solid var(--eq-on)"><b>No bubble curtain, because air under the bell kills jellyfish (AZA); Layer 2 uses water jets only.</b> <span class="note">O₂ is added only as fully dissolved O₂ in a side-stream (rules R01/R02).</span></div>
      <div class="kpis" style="margin-bottom:10px">${kpi('bk1', 'Pipe density', 'animals/m³ in pipe (R05)')}${kpi('bk2', 'Outlet O₂', '≥ 75 % sat target (R03)')}${kpi('bk3', 'ΔT release − intake', '≤ 1 °C (R08)')}${kpi('bk4', 'ΔS release − intake', '≤ 1–2 ppt (R09)')}${kpi('bk5', 'Free bubbles in path', 'ZERO (R01)')}${kpi('bk6', 'Polyps on plates', 'settlement plates (R19)')}</div>
      <div class="grid g3">
        <div class="panel span2"><h3>Oxygen budget by biomass — DO at end of 3 h transit, no injection (0.33 kg bells)</h3><div class="chart tall" id="bgO2"></div><div class="src">${E ? E.o2_budget.source : ''}</div></div>
        <div class="panel"><h3>Velocity rule along the path (R10)</h3><div class="chart tall" id="bgVel"></div><div class="note">Velocities must stay ≥ 3× the bells' sustained swim speed (~0.27 m/s for 4–9 cm/s) after the screen face and accelerate monotonically into the entrance; diffuser exit ≤ 1 m/s. Illustrative from the simulated plant.</div></div>
        <div class="panel"><h3>Release temperature / salinity match <span class="r">${rangeSel('bgR')}</span></h3><div class="chart" id="bgTS"></div></div>
        <div class="panel"><h3>Polyp-habitat monitoring — settlement plates <span class="tag">simulated</span></h3><div class="scroll" style="max-height:220px"><table class="t" id="bgPl"></table></div></div>
        <div class="panel"><h3>Plate polyp counts — monthly <span class="tag">simulated</span></h3><div class="chart" id="bgPlC"></div></div>
        <div class="panel full"><h3>Biology design rules (20) and live status</h3><div class="scroll" style="max-height:340px"><table class="t" id="bgRules"></table></div><div class="src">${E ? E.bio_rules.source : ''}</div></div>
      </div>`;
      const t = U.theme;
      U.chart(U.$('#bgO2'), () => { const c = t(), E = window.JZ_EVIDENCE, s = S(); if (!E) return {}; const rows = E.o2_budget.rows.filter((r) => r.mass_case.startsWith('mean 0.33')); const cases = [...new Set(rows.map((r) => r.resp_case))], cols = [c.data3, c.data2, c.data, c.ink2];
        const dens = s.o2.conc ? s.o2.conc / C.MASS : 0;
        return U.base({ grid: { left: 44, right: 14, top: 40, bottom: 30 }, legend: { top: 0, left: 0, textStyle: { color: c.ink2, fontSize: 10 } }, xAxis: U.ax({ type: 'log', name: 'animals per m³ in pipe', nameLocation: 'middle', nameGap: 20, min: 1, max: 100 }), yAxis: U.ax({ name: 'DO end mg/L', min: -2, max: 6 }),
          series: cases.map((rc, i) => U.line(rc.replace(/\(.*?\)/g, '').trim(), rows.filter((r) => r.resp_case === rc).map((r) => [r.density, r.end_mg_L]), cols[i % 4], { showSymbol: true, symbolSize: 5 }))
            .concat([{ type: 'line', name: 'floor 2.6 (fish)', data: [[1, 2.6], [100, 2.6]], showSymbol: false, lineStyle: { color: c.p1, type: 'dotted' }, itemStyle: { color: c.p1 } },
              { type: 'line', name: '≈75 % sat 4.2', data: [[1, 4.2], [100, 4.2]], showSymbol: false, lineStyle: { color: c.ink3, type: 'dashed' }, itemStyle: { color: c.ink3 } },
              { type: 'scatter', name: 'Now: pipe density (sim)', data: dens > 1 ? [[+dens.toFixed(1), +(5.66 - 0.0715 * dens * 0.33 * 3).toFixed(2)]] : [], symbol: 'diamond', symbolSize: 14, itemStyle: { color: c.sel } }]) }); }, 'biology');
      U.chart(U.$('#bgVel'), () => { const c = t(), s = S(), ln = s.lanes[0]; const v = [['Approach (through mesh)', 0.1], ['Sweep along face', ln.sweep || C.SWEEP], ['Belt', (ln.ratioSP || 0.6) * (ln.sweep || C.SWEEP)], ['Entrance mouth', 0.62], ['Flared transition', 0.75], ['Dewater plate', 0.3], ['Lock transfer', 0.35], ['Pipe', s.pipe ? Math.max(0, s.pipe.v) : 1.0], ['Diffuser exit', s.pipe ? s.pipe.exitV : 0.84]];
        return U.base({ grid: { left: 130, right: 30, top: 10, bottom: 26 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, xAxis: U.ax({ name: 'm/s', max: 1.4 }), yAxis: U.ax({ type: 'category', data: v.map((x) => x[0]).reverse(), axisLabel: { color: c.ink3, fontSize: 10 } }),
          series: [{ type: 'bar', data: v.map((x, i) => ({ value: +x[1].toFixed(2), itemStyle: { color: (i === 8 && x[1] > 1) ? c.p2 : c.data } })).reverse(), label: { show: true, position: 'right', color: c.ink2, fontSize: 10 },
            markLine: { symbol: 'none', data: [{ xAxis: 0.27, name: '3× swim' }, { xAxis: 1.0, name: 'exit limit' }], lineStyle: { color: c.ink3, type: 'dashed' }, label: { color: c.ink3, fontSize: 9, formatter: (p) => p.name } } }] }); }, 'biology');
      U.chart(U.$('#bgTS'), () => { const c = t(), h = H(), s = S(); return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: U.ax({ name: 'Δ', min: -2, max: 2 }),
        series: [U.line('ΔT °C (release − intake)', h.map((x, i) => [x.t, x.o2head > 0 && x.os === 'OPERATE' ? +(0.18 + 0.12 * Math.sin(x.t / 9000) + 0.03 * Math.sin(i)).toFixed(2) : null]), c.data),
          U.line('ΔS ppt', h.map((x, i) => [x.t, x.os === 'OPERATE' ? +(0.05 * Math.sin(x.t / 7000)).toFixed(2) : null]), c.data2),
          { type: 'line', name: 'ΔT limit', data: h.length ? [[h[0].t, 1], [h[h.length - 1].t, 1]] : [], showSymbol: false, lineStyle: { type: 'dashed', color: c.ink3 }, itemStyle: { color: c.ink3 } }] }); }, 'biology');
      U.chart(U.$('#bgPlC'), () => { const c = t(); const months = ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']; const r = JZ.rng(77); return U.base({ grid: { left: 36, right: 10, top: 26, bottom: 24 }, xAxis: U.ax({ type: 'category', data: months }), yAxis: U.ax({ name: 'polyps / plate', min: 0 }),
        series: [U.line('Reference plate', months.map((_, i) => Math.round(2 + i * 1.6 + r() * 3)), c.ink3, { showSymbol: true }), U.line('JAZR plates (max)', months.map((_, i) => (i === 4 ? 1 : 0)), c.data, { showSymbol: true })] }); }, 'biology');
      const r = JZ.rng(5);
      U.$('#bgPl').innerHTML = '<tr><th>Plate</th><th>Location</th><th>Last inspected</th><th class="num">Fouling</th><th class="num">Polyps</th><th>Action</th></tr>' + PLATES.map(([id, loc], i) => { const pol = id === 'SP-REF' ? 9 : id === 'SP-05' ? 1 : 0; return `<tr><td class="mono">${id}</td><td>${loc}</td><td class="mono">0${1 + (i % 9)} Oct</td><td class="num">${Math.round(5 + r() * 30)} %</td><td class="num">${pol}</td><td class="note">${pol && id !== 'SP-REF' ? 'Clean surface; check shading (R19)' : '—'}</td></tr>`; }).join('');
    },
    update() {
      const s = S(), E = window.JZ_EVIDENCE, dens = s.o2.conc ? s.o2.conc / C.MASS : 0, op = s.os === 'OPERATE';
      setK('bk1', op ? U.n(dens, 1) : '—'); setK('bk2', s.ht.qout > 0.1 ? `${s.o2.tail.toFixed(1)} <small>mg/L · ${(100 * s.o2.tail / s.o2.sat).toFixed(0)} % sat</small>` : '—', null, s.ht.qout > 0.1 && s.o2.tail < 4.2);
      setK('bk3', op ? '+0.2 <small>°C (trenched pipe)</small>' : '—'); setK('bk4', op ? '0.0 <small>ppt (same seawater)</small>' : '—'); setK('bk5', '0 <small>side-stream O₂</small>'); setK('bk6', '1 <small>of 8 JAZR plates · ref 9</small>');
      if (!E) return;
      const live = { R01: 'MET (design): submerged path, side-stream O₂, Layer 2 water jets (no air)', R02: s.o2.head > 12 ? 'CHECK: dissolved O₂ high; watch TDG' : 'MET (sim): no free gas', R03: s.ht.qout > 0.1 ? (s.o2.tail >= 4.2 ? `MET: ${s.o2.tail.toFixed(1)} mg/L` : `NOT MET: ${s.o2.tail.toFixed(1)} mg/L`) : 'idle',
        R04: 'MET by O₂ injection', R05: op ? `pipe ${dens.toFixed(1)}/m³` : '—', R06: s.pipe ? `${(s.pipe.transit / 3600).toFixed(2)} h` : '—', R07: 'MET (design): water-to-water', R08: 'MET (sim): ΔT ≈ +0.2 °C', R09: 'MET: same seawater', R10: 'MET (illustrative)', R13: 'MET: no acoustic devices', R14: 'MET: none used', R15: 'MET: dark by default', R16: 'Grid self-clearing to chute', R19: 'Plates monitored', R20: 'OPEN: survival to be measured (T09/P02)' };
      const tb = U.$('#bgRules'); if (tb.dataset.n == String(Math.floor(s.t / 60))) return; tb.dataset.n = String(Math.floor(s.t / 60));
      tb.innerHTML = '<tr><th>ID</th><th>Goal</th><th>Rule</th><th>Threshold</th><th>Confidence</th><th>Live status</th></tr>' + E.bio_rules.rows.map((x) => `<tr><td class="mono">${x.rule_id}</td><td>${x.goal}</td><td>${U.esc(x.rule)}</td><td class="note">${U.esc(x.threshold)}</td><td class="note">${U.esc(x.confidence)}</td><td>${U.esc(live[x.rule_id] || '—')}</td></tr>`).join('');
    },
  };

  // ======================================================== ALARMS
  P.alarms = {
    title: 'Alarms', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Alarm management (ISA-18.2)</h1><span class="sub">Rationalised alarms with cause / consequence / response / time-to-respond · shelving with reason and auto-expiry · state-based suppression · flood grouping</span></div>
      <div class="kpis" style="margin-bottom:10px">${kpi('ak1', 'Annunciations / 10 min', 'ISA-18.2: ≤1 very likely acceptable, ≤2 manageable')}${kpi('ak2', 'Standing alarms', 'active, not shelved')}${kpi('ak3', 'Unacknowledged', '')}${kpi('ak4', 'Shelved', 'auto-expire 30 min')}${kpi('ak5', 'Suppressed by design / flood', '')}${kpi('ak6', 'Flood state', '> 10 per 10 min')}</div>
      <div class="grid g3">
        <div class="panel span2"><h3>Alarm list <span class="r"><select id="alF"><option value="all">all non-normal</option><option value="act">active only</option><option value="sh">shelved/suppressed</option></select> <button class="btn sm" id="alAck">Ack page</button></span></h3><div class="scroll" style="max-height:420px"><table class="t" id="alT"><thead><tr><th></th><th>Time</th><th>Description</th><th>Value</th><th>State</th><th></th></tr></thead><tbody></tbody></table></div></div>
        <div class="panel"><h3>Alarm rate per 10 min</h3><div class="chart" id="alRate"></div><h3 style="margin-top:8px">Priority distribution (annunciated)</h3><div class="chart short" id="alPri"></div><div class="note">EEMUA 191 / ISA-18.2 guidance ≈ 5 % urgent · 15 % high · 80 % medium/low.</div></div>
        <div class="panel"><h3>Bad actors (most frequent)</h3><div class="chart" id="alBad"></div></div>
        <div class="panel span2"><h3>Journal <button class="btn sm" id="alCsv">CSV</button></h3><div class="scroll" style="max-height:250px"><table class="t" id="alJ"></table></div></div>
        <div class="panel full"><h3>Selected alarm rationalisation</h3><div id="alRat" class="note">Hover a row in the list for its rationalisation; full text below for the top alarm.</div></div>
      </div>`;
      JZ.main.wireAlarmButtons(U.$('#alT'));
      U.$('#alF').onchange = () => JZ.app.tick(true);
      U.$('#alAck').onclick = () => { S().alarms.ackAll(); JZ.app.tick(true); };
      U.$('#alCsv').onclick = () => U.csv('jazr_alarm_journal.csv', S().alarms.journal.map((j) => ({ time: JZ.fmtISO(j.t), tag: j.tag, priority: j.pri, event: j.ev, description: j.desc, value: j.value })));
      const t = U.theme;
      U.chart(U.$('#alRate'), () => { const c = t(), r = S().alarms.rate10(); return U.base({ grid: { left: 36, right: 10, top: 20, bottom: 24 }, xAxis: U.tax(), yAxis: U.ax({ name: 'per 10 min', min: 0 }),
        series: [{ type: 'bar', name: 'Annunciations', data: r.map((x) => ({ value: [x[0], x[1]], itemStyle: { color: x[1] > 10 ? c.p2 : c.data } })), barMaxWidth: 6 },
          { type: 'line', name: 'flood 10', data: r.length ? [[r[0][0], 10], [r[r.length - 1][0], 10]] : [], showSymbol: false, lineStyle: { color: c.p2, type: 'dashed' }, itemStyle: { color: c.p2 } },
          { type: 'line', name: 'target ≤ 1', data: r.length ? [[r[0][0], 1], [r[r.length - 1][0], 1]] : [], showSymbol: false, lineStyle: { color: c.ink3, type: 'dashed' }, itemStyle: { color: c.ink3 } }] }); }, 'alarms');
      U.chart(U.$('#alPri'), () => { const c = t(), j = S().alarms.journal.filter((x) => x.ev === 'ALARM'), n = [1, 2, 3, 4].map((p) => j.filter((x) => x.pri === p).length), tot = Math.max(1, n.reduce((a, b) => a + b, 0));
        return U.base({ grid: { left: 70, right: 30, top: 6, bottom: 20 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, xAxis: U.ax({ max: 100, name: '%' }), yAxis: U.ax({ type: 'category', data: ['P4 Low', 'P3 Medium', 'P2 High', 'P1 Urgent'] }),
          series: [{ type: 'bar', name: 'This run', data: [n[3], n[2], n[1], n[0]].map((v, i) => ({ value: +((v / tot) * 100).toFixed(0), itemStyle: { color: [c.p4, c.p3, c.p2, c.p1][i] } })), label: { show: true, position: 'right', color: c.ink2, formatter: '{c}%' } }] }); }, 'alarms');
      U.chart(U.$('#alBad'), () => { const c = t(), b = S().alarms.badActors(); return U.base({ grid: { left: 150, right: 30, top: 6, bottom: 20 }, tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, xAxis: U.ax({ name: 'count' }), yAxis: U.ax({ type: 'category', data: b.map((x) => x[0]).reverse(), axisLabel: { color: c.ink3, fontSize: 9.5 } }),
        series: [{ type: 'bar', data: b.map((x) => x[1]).reverse(), itemStyle: { color: c.data }, label: { show: true, position: 'right', color: c.ink2 } }] }); }, 'alarms');
    },
    update() {
      const s = S(), A = s.alarms, c = A.counts(), r = A.rate10(), last = r.length ? r[r.length - 1][1] : 0;
      setK('ak1', last, null, last > 2); setK('ak2', c.standing); setK('ak3', c.unack, null, c.unack > 0); setK('ak4', c.shelved); setK('ak5', c.supp); setK('ak6', A.flood ? 'FLOOD' : 'normal', A.flood ? 'P4 + per-bay BI-H grouped by lane' : null, A.flood);
      const f = U.$('#alF').value; let l = A.list(); if (f === 'act') l = l.filter((a) => a.active && a.st !== 'SHELVED' && a.st !== 'SUPPRESSED'); if (f === 'sh') l = l.filter((a) => a.st === 'SHELVED' || a.st === 'SUPPRESSED');
      U.$('#alT tbody').innerHTML = l.length ? l.map((a) => JZ.main.alarmRow(a)).join('') : '<tr><td colspan="6" class="note" style="padding:14px">No alarms in this view.</td></tr>';
      const top = l[0];
      U.$('#alRat').innerHTML = top ? `<div class="kv" style="grid-template-columns:160px 1fr"><span class="k">Tag</span><span class="v" style="text-align:left">${top.tag} · P${top.pri} ${JZ.PRI[top.pri]}</span><span class="k">Cause</span><span style="text-align:left">${U.esc(top.cause)}</span><span class="k">Consequence</span><span>${U.esc(top.conseq)}</span><span class="k">Operator response</span><span>${U.esc(top.action)}</span><span class="k">Time to respond</span><span>${U.esc(top.ttr)}</span></div>` : 'No alarm selected.';
      U.$('#alJ').innerHTML = '<tr><th>Time</th><th>P</th><th>Tag</th><th>Event</th><th>Description</th><th>Value</th></tr>' + A.journal.slice(-150).reverse().map((j) => `<tr><td class="mono">${JZ.fmtT(j.t)}</td><td>${U.prio(j.pri)}</td><td class="mono">${j.tag}</td><td>${U.esc(j.ev)}</td><td>${U.esc(j.desc)}</td><td class="mono">${U.esc(j.value)}</td></tr>`).join('');
    },
  };

  // ======================================================== TRENDS & ANALYTICS
  P.trends = {
    title: 'Trends & Analytics', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Trends &amp; analytics</h1><span class="sub">η_r self-calibrates from camera counts at entrances and in the leak zone · leak to plant = (1 − η₁)(1 − η₂) with Layer 2, ≈ 1 − η_r without (illustrative)</span><span class="r">${rangeSel('trR')}</span></div>
      <div class="grid g3">
        <div class="panel span2"><h3>η_r estimate (camera counts, Kalman) vs simulated truth <span class="tag">simulated</span></h3><div class="chart" id="trEta"></div></div>
        <div class="panel"><h3>Leak rate — got past JAZR <span class="tag">illustrative</span></h3><div class="chart" id="trLeak"></div></div>
        <div class="panel"><h3>Throughput — arriving / diverted / leaked</h3><div class="chart" id="trTp"></div></div>
        <div class="panel"><h3>Survival chain <span class="tag est">estimate</span></h3><div class="chart" id="trSurv"></div><div class="note" id="trSurvN"></div><div class="src">TESTS/10_mechanisms/survival_budget.csv; TESTS/11_eta_max_sims/results/survival_chain.csv</div></div>
        <div class="panel"><h3>Bloom density at intake &amp; tide</h3><div class="chart" id="trDen"></div></div>
        <div class="panel span2"><h3>Twin what-if <span class="tag">closed-form approximation, calibrated to twin rows — not the twin</span></h3>
          <div class="grid g2"><div>
            <div class="slider"><label>η_r (inner screen)</label><input type="range" id="wiE" min="0.5" max="0.99" step="0.01" value="0.97"><span class="mono" id="wiEv"></span></div>
            <div class="slider"><label>Onshore drift cm/s</label><input type="range" id="wiD" min="-2" max="6" step="0.1" value="2.5"><span class="mono" id="wiDv"></span></div>
            <div class="slider"><label>Bloom days</label><input type="range" id="wiB" min="1" max="10" step="1" value="10"><span class="mono" id="wiBv"></span></div>
            <div class="formrow"><label class="note">Policy</label><select id="wiP"><option value="far">Release-Far (v4.1)</option><option value="near">Release-Near only</option><option value="none">Today (no JAZR)</option></select></div>
            <div style="margin-top:10px"><div class="note">Share of the swarm reaching the plant</div><div class="big-out" id="wiOut">—</div><div class="note" id="wiCmp"></div></div>
            <div class="note" style="margin-top:6px">leak = (1 − η_r) / (1 − η_r·R), R = return fraction from drift and bloom length; with far release R ≈ 0 → leak ≈ 1 − η_r. Checks vs twin (far, 2.5 cm/s, 10 d): η 0.9 → 11 % (twin 10.4 %); η 0.77 → 24.6 % (23.5 %); η 0.99 → 1.1 % (1.15 %); η 0.996 → 0.46 % (0.39 %); near only η 0.9 → 49 % (49.9 %).</div>
          </div><div class="chart" id="wiChart"></div></div></div>
        <div class="panel"><h3>AI closed-loop tuning <span class="tag">advisory mode</span></h3><div id="trTune"></div><div class="note">Safe Bayesian-optimisation style suggestions from camera counts (mechanism G9). TESTS/11: its value is mainly as a backup — η_r 0.81 vs 0.76 with a fouled bay + belt fault; nominal the fixed best setting already gives ≈1.0. The operator accepts per lane. It never touches bays, interlocks, deploy, the HydroLift or the outlet.</div></div>
        <div class="panel span2"><h3>AI copilot — suggestions requiring human approval</h3><div id="trCp" class="scroll" style="max-height:330px"></div></div>
        <div class="panel"><h3>AI governance</h3><ul class="note" style="margin:0;padding-left:16px;line-height:1.6"><li>Runs on-site, air-gapped (FANR-REG-08 / IEC 62443); no cloud calls.</li><li>Reads OS state and counts; writes only suggestions.</li><li>Cannot command: deploy/veto, bay raise/lower, interlocks, E-stop, lock hold/restart, outlet change (operator confirms).</li><li>Every accept/reject is logged with the operator's name.</li><li>Demo: rule-based logic stands in for the model.</li></ul><h3 style="margin-top:10px">AI decision log</h3><div class="scroll" style="max-height:150px"><table class="t" id="trAiLog"></table></div></div>
      </div>`;
      const t = U.theme;
      U.chart(U.$('#trEta'), () => { const c = t(), h = H().filter((x) => x.etaHat != null); return U.base({ grid: { left: 44, right: 10, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: U.ax({ min: 0.9, max: 1, name: 'η_r' }),
        series: [U.band('90 % CI', h.map((x) => [x.t, +(x.etaHat - 1.645 * x.etaSd).toFixed(4), +(x.etaHat + 1.645 * x.etaSd).toFixed(4)]), c.data, 0.18),
          U.line('Estimate (camera)', h.map((x) => [x.t, +x.etaHat.toFixed(4)]), c.data, { lineStyle: { width: 2, color: c.data } }), U.line('Simulated truth', h.map((x) => [x.t, +x.eta.toFixed(4)]), c.ink3, { lineStyle: { type: 'dashed', color: c.ink3, width: 1.2 } }),
          { type: 'line', name: 'v5 band 0.95–0.99', data: h.length ? [[h[0].t, 0.95], [h[h.length - 1].t, 0.95]] : [], showSymbol: false, lineStyle: { color: c.data3, type: 'dotted' }, itemStyle: { color: c.data3 } }] }); }, 'trends');
      U.chart(U.$('#trLeak'), () => { const c = t(), h = H(); return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: U.ax({ name: '%', min: 0 }),
        series: [U.line('Leak %', h.map((x) => [x.t, x.leakPct != null && x.os !== 'IDLE' ? +(x.leakPct * 100).toFixed(2) : null]), c.data, { markArea: { silent: true, itemStyle: { color: c.inset, opacity: 0.7 }, data: [[{ yAxis: 0.04, name: '(1−η₁)(1−η₂) ≈ 0.04–2 % illustrative' }, { yAxis: 2 }]], label: { color: c.ink3, position: 'insideTopRight', fontSize: 10 } } })] }); }, 'trends');
      U.chart(U.$('#trTp'), () => { const c = t(), h = H(); return U.base({ grid: { left: 44, right: 10, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: U.ax({ name: 't/h' }),
        series: [U.line('Arriving', h.map((x) => [x.t, +(x.arr * C.MASS * 3.6).toFixed(1)]), c.ink3), U.line('Diverted', h.map((x) => [x.t, +(x.guided * C.MASS * 3.6).toFixed(1)]), c.data), U.line('Leaked', h.map((x) => [x.t, +(x.leak * C.MASS * 3.6).toFixed(2)]), c.p2)] }); }, 'trends');
      U.chart(U.$('#trSurv'), () => { const c = t(); let cum = 1; const st = JZ.SURV.map((x) => { cum *= x.p; return [x.k, cum]; }); let lo = 1, hi = 1; const L = JZ.SURV.map((x) => (lo *= x.lo)), Hh = JZ.SURV.map((x) => (hi *= x.hi));
        return U.base({ grid: { left: 40, right: 10, top: 10, bottom: 70 }, xAxis: U.ax({ type: 'category', data: st.map((x) => x[0]), axisLabel: { rotate: 35, color: c.ink3, fontSize: 9.5, interval: 0 } }), yAxis: U.ax({ min: 0.6, max: 1, name: 'cum.' }),
          series: [{ type: 'line', name: 'plausible low', data: L.map((v) => +v.toFixed(4)), lineStyle: { type: 'dotted', color: c.ink3 }, itemStyle: { color: c.ink3 }, showSymbol: false }, { type: 'line', name: 'plausible high', data: Hh.map((v) => +v.toFixed(4)), lineStyle: { type: 'dotted', color: c.ink3 }, itemStyle: { color: c.ink3 }, showSymbol: false },
            { type: 'bar', name: 'cumulative estimate', data: st.map((x) => +x[1].toFixed(4)), itemStyle: { color: c.data, decal: { symbol: 'rect', dashArrayX: [1, 0], dashArrayY: [3, 3], rotation: -0.6, color: 'rgba(255,255,255,.18)' } }, barWidth: '55%', markLine: { symbol: 'none', silent: true, data: [{ yAxis: 0.95, name: 'target ≥0.95' }, { yAxis: 0.76, name: 'MC 0.76' }], lineStyle: { color: c.ink3, type: 'dashed' }, label: { color: c.ink3, fontSize: 9.5, formatter: (p) => p.name, position: 'insideStartTop' } } }] }); }, 'trends');
      U.chart(U.$('#trDen'), () => { const c = t(), h = H(); return U.base({ grid: { left: 40, right: 40, top: 26, bottom: 24 }, xAxis: U.tax(), yAxis: [U.ax({ name: '/m³', min: 0 }), U.ax({ name: 'm', splitLine: { show: false } })],
        series: [U.line('Density', h.map((x) => [x.t, +x.dens.toFixed(3)]), c.data, { areaStyle: { color: c.data, opacity: 0.1 } }), U.line('Tide', h.map((x) => [x.t, +x.tide.toFixed(2)]), c.data3, { yAxisIndex: 1 })] }); }, 'trends');
      const wi = () => { const e = +U.$('#wiE').value, d = +U.$('#wiD').value, b = +U.$('#wiB').value, p = U.$('#wiP').value; U.$('#wiEv').textContent = e.toFixed(2); U.$('#wiDv').textContent = d.toFixed(1); U.$('#wiBv').textContent = b + ' d';
        const v = JZ.whatIf(e, d, b, p); U.$('#wiOut').textContent = (v * 100).toFixed(1) + ' %'; U.$('#wiCmp').textContent = `Today: 97–100 % · reduction ${((1 - v) * 100).toFixed(0)} % of the swarm kept off the plant screens`; U.refreshCharts('trends-wi', true); };
      ['wiE', 'wiD', 'wiB', 'wiP'].forEach((id) => (U.$('#' + id).oninput = wi));
      U.chart(U.$('#wiChart'), () => { const c = t(), d = +U.$('#wiD').value, b = +U.$('#wiB').value, xs = []; for (let e = 0.5; e <= 0.995; e += 0.01) xs.push(+e.toFixed(2));
        const pts = (p) => xs.map((e) => [e, +(JZ.whatIf(e, d, b, p) * 100).toFixed(1)]); const twin = [[0.9, 10.4], [0.7, 30.0], [0.5, 50.7]], t11 = [[0.7733, 23.5], [0.9533, 5.1], [0.99, 1.15], [0.9959, 0.39]];
        return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 30 }, xAxis: U.ax({ name: 'η_r', min: 0.5, max: 1, nameLocation: 'middle', nameGap: 18 }), yAxis: U.ax({ name: '% reaching plant', min: 0, max: 100 }),
          series: [U.line('Release-Far', pts('far'), c.data, { lineStyle: { width: 2, color: c.data } }), U.line('Release-Near only', pts('near'), c.data2), { type: 'scatter', name: 'Twin v4.1 (10 d, far)', data: twin, symbol: 'diamond', symbolSize: 10, itemStyle: { color: c.ink } }, { type: 'scatter', name: 'Twin TESTS/11 (240 h, far)', data: t11, symbol: 'triangle', symbolSize: 10, itemStyle: { color: c.ink2 } },
            { type: 'scatter', name: 'Selected', data: [[+U.$('#wiE').value, +(JZ.whatIf(+U.$('#wiE').value, d, b, U.$('#wiP').value) * 100).toFixed(1)]], symbolSize: 12, itemStyle: { color: c.sel } }] }); }, 'trends-wi');
      wi();
      JZ.main.wireCp(U.$('#trCp'));
      U.$('#trTune').addEventListener('click', (e) => { const l = e.target.dataset.tune; if (l == null) return; const s = S(), ln = s.lanes[+l], sug = P.trends.sug(ln); ln.split = sug.split; ln.ratioSP = sug.ratio; s.logs.ai.push({ t: s.t, id: 'tune' + l, title: `Lane ${+l + 1} tuning split ${(sug.split * 100).toFixed(0)} %, belt ${sug.ratio.toFixed(2)}×`, decision: 'ACCEPTED', by: 'Operator' }); U.toast('Tuning accepted for lane ' + (+l + 1)); JZ.app.tick(true); });
    },
    sug(ln) { const meanBI = ln.bays.reduce((a, b) => a + b.bi, 0) / C.BAYS; return { split: 0.2, ratio: Math.min(1, Math.max(0.5, meanBI > 0.15 ? 0.9 : 0.8)) }; },
    update() {
      const s = S();
      const end = JZ.survEnd(); U.$('#trSurvN').innerHTML = `Two independent ESTIMATES, shown together: <b>engineering budget ${end.toFixed(3)}</b> (plausible ${JZ.SURV.reduce((a, x) => a * x.lo, 1).toFixed(2)}–${JZ.SURV.reduce((a, x) => a * x.hi, 1).toFixed(2)}) and <b>conservative Monte Carlo (HydroLift + dissolved O₂) 0.76</b> (5–95 %: 0.68–0.85); without O₂ 0.40–0.56. Design target ≥ 0.95. Applied to ${U.big(s.k.released)} routed animals: ≈ ${U.big(s.k.released * 0.76)}–${U.big(s.k.released * end)} expected alive at 96 h. Decisive test: 3 h pipe loop with 96 h scoring.`;
      U.$('#trTune').innerHTML = `<table class="t"><tr><th>Lane</th><th class="num">Split now → AI</th><th class="num">Belt × now → AI</th><th class="num">η̂</th><th></th></tr>${s.lanes.map((ln, i) => { const g = this.sug(ln), same = Math.abs(g.split - ln.split) < 1e-6 && Math.abs(g.ratio - ln.ratioSP) < 1e-6; const gain = (Math.max(0, g.split - ln.split) * 0.6 + Math.max(0, g.ratio - ln.ratioSP) * 0.02) * ln.etaBase;
        return `<tr><td>${i + 1}</td><td class="num">${(ln.split * 100).toFixed(1)} → <b>${(g.split * 100).toFixed(0)} %</b></td><td class="num">${ln.ratioSP.toFixed(2)} → <b>${g.ratio.toFixed(2)}</b></td><td class="num">${ln.etaHat.toFixed(3)}${gain > 0.0005 ? ` <span class="note">+${(gain * 100).toFixed(1)}%</span>` : ''}</td><td>${same ? '<span class="note">applied</span>' : `<button class="btn sm primary" data-tune="${i}">Accept</button>`}</td></tr>`; }).join('')}</table>`;
      U.$('#trCp').innerHTML = s.copilot.length ? s.copilot.map(JZ.main.cpCard).join('') : '<div class="note">No suggestions yet — they appear once the system is operating.</div>';
      U.$('#trAiLog').innerHTML = '<tr><th>Time</th><th>Suggestion</th><th>Decision</th><th>By</th></tr>' + (s.logs.ai.slice().reverse().map((a) => `<tr><td class="mono">${JZ.fmtT(a.t)}</td><td>${U.esc(a.title)}</td><td>${a.decision}</td><td>${U.esc(a.by)}</td></tr>`).join('') || '<tr><td colspan="4" class="note">Empty.</td></tr>');
    },
  };

  // ======================================================== MAINTENANCE
  P.maint = {
    title: 'Maintenance', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Predictive maintenance</h1><span class="sub">Health index from motor-current signature, ΔP, cycle counts · RUL = (HI − 0.25) / degradation rate · plan work in stow windows <span class="tag">simulated</span></span></div>
      <div class="kpis" style="margin-bottom:10px">${kpi('mk1', 'Assets monitored', 'belts, drums, lock gates, winches')}${kpi('mk2', 'RUL < 30 days', 'plan at next stow')}${kpi('mk3', 'Faulted now', 'latched')}${kpi('mk4', 'Work orders', 'planned')}${kpi('mk5', 'Availability (model)', '04 T7: 0.99')}</div>
      <div class="grid g3">
        <div class="panel span2"><h3>Belt + head-drum health index (4 × 42)</h3><div class="chart" id="mnHeat" style="height:210px"></div></div>
        <div class="panel"><h3>Selected asset trend — <span id="mnSelN"></span></h3><div class="chart" id="mnTr"></div></div>
        <div class="panel span2"><h3>Asset list (sorted by RUL)</h3><div class="scroll" style="max-height:330px"><table class="t" id="mnT"></table></div></div>
        <div class="panel"><h3>Work orders</h3><div class="scroll" style="max-height:330px"><table class="t" id="mnWO"></table></div></div>
      </div>`;
      U.$('#mnT').addEventListener('click', (e) => { const id = e.target.dataset.wo; if (id) { const s = S(); s.logs.wo.push({ t: s.t, id, text: 'Inspect / replace per RUL forecast', by: 'Operator', status: 'PLANNED' }); JZ.app.tick(true); } const r = e.target.closest('tr'); if (r && r.dataset.id) { P.maint.selId = r.dataset.id; JZ.app.tick(true); } });
      const t = U.theme;
      U.chart(U.$('#mnHeat'), () => { const c = t(), s = S(), data = []; s.lanes.forEach((ln, l) => ln.bays.forEach((b, i) => data.push([i, 3 - l, Math.round((1 - b.wear) * 100)])));
        return U.base({ grid: { left: 54, right: 10, top: 8, bottom: 40 }, tooltip: { trigger: 'item', formatter: (p) => `BELT-L${4 - p.value[1]}-B${p.value[0] + 1}: HI ${p.value[2]} %` }, xAxis: U.ax({ type: 'category', data: [...Array(42).keys()].map((i) => i + 1) }), yAxis: U.ax({ type: 'category', data: ['Lane 4', 'Lane 3', 'Lane 2', 'Lane 1'] }),
          visualMap: { type: 'piecewise', orient: 'horizontal', bottom: 0, right: 0, itemWidth: 12, itemHeight: 9, textStyle: { color: c.ink3, fontSize: 10 }, pieces: [{ lt: 25, label: '<25 replace', color: c.p2 }, { gte: 25, lt: 40, label: '25–40 plan', color: c.p3 }, { gte: 40, lt: 70, label: '40–70', color: c.eq }, { gte: 70, label: '≥70', color: c.eqfill }] },
          series: [{ type: 'heatmap', data, itemStyle: { borderColor: c.panel, borderWidth: 1 } }] }); }, 'maint');
      U.chart(U.$('#mnTr'), () => { const c = t(), s = S(), a = P.maint.find(s); if (!a) return {}; U.$('#mnSelN').textContent = a.id; const r = JZ.rng(a.id.length * 31 + (a.lane + 2) * 7), d = [], f = []; for (let k = -90; k <= 0; k++) { const hi = Math.min(1, a.hi + -k * a.rate); d.push([k, +(hi * 100 + r.n() * 1.2).toFixed(1)]); }
        const rul = s.maint.rul(a); for (let k = 0; k <= Math.min(120, rul + 10); k += 5) f.push([k, +Math.max(0, (a.hi - k * a.rate) * 100).toFixed(1)]);
        return U.base({ grid: { left: 40, right: 10, top: 26, bottom: 28 }, xAxis: U.ax({ name: 'days (0 = now)', nameLocation: 'middle', nameGap: 18 }), yAxis: U.ax({ name: 'HI %', min: 0, max: 100 }),
          series: [U.line('Health index', d, c.data), U.line('Forecast', f, c.data2, { lineStyle: { type: 'dashed', color: c.data2 } }), { type: 'line', name: 'replace 25 %', data: [[-90, 25], [120, 25]], showSymbol: false, lineStyle: { color: c.p2, type: 'dotted' }, itemStyle: { color: c.p2 } }] }); }, 'maint');
    },
    all(s) { return s.maint.belts(s).concat(s.maint.assets); },
    find(s) { const all = this.all(s); return all.find((a) => a.id === this.selId) || all.sort((a, b) => s.maint.rul(a) - s.maint.rul(b))[0]; },
    update() {
      const s = S(), all = this.all(s).map((a) => Object.assign({ rul: s.maint.rul(a) }, a)).sort((a, b) => a.rul - b.rul);
      setK('mk1', all.length); setK('mk2', all.filter((a) => a.rul < 30).length, null, all.some((a) => a.rul < 30)); setK('mk3', s.lanes.reduce((n, l) => n + l.bays.filter((b) => b.st === 'FAULT').length, 0)); setK('mk4', s.logs.wo.length); setK('mk5', '0.99');
      U.$('#mnT').innerHTML = '<tr><th>Asset</th><th>Type</th><th class="num">HI</th><th class="num">RUL (days)</th><th>Signal</th><th></th></tr>' + all.slice(0, 40).map((a) => `<tr data-id="${a.id}" class="${a.id === this.selId ? 'sel' : ''}" style="cursor:pointer"><td class="mono">${a.id}</td><td>${a.kind}</td><td class="num">${(a.hi * 100).toFixed(0)} %</td><td class="num ${a.rul < 30 ? 'v-marg' : ''}">${a.seized ? 'FAILED' : a.rul > 999 ? '>999' : a.rul.toFixed(0)}</td><td class="note">${a.sig}${a.cycles ? ` · ${U.n(a.cycles)} cycles` : ''}</td><td>${a.rul < 60 ? `<button class="btn sm" data-wo="${a.id}">Plan WO</button>` : ''}</td></tr>`).join('');
      U.$('#mnWO').innerHTML = '<tr><th>Time</th><th>Asset</th><th>Task</th><th>By</th><th>Status</th></tr>' + (s.logs.wo.slice().reverse().map((w) => `<tr><td class="mono">${JZ.fmtT(w.t)}</td><td class="mono">${w.id}</td><td>${U.esc(w.text)}</td><td>${U.esc(w.by)}</td><td>${w.status}</td></tr>`).join('') || '<tr><td colspan="5" class="note">No work orders yet. Use “Plan WO” or accept a copilot maintenance suggestion.</td></tr>');
    },
  };

  // ======================================================== REPORTS
  P.reports = {
    title: 'Reports', build(root) {
      root.innerHTML = `<div class="page-h"><h1>Reports</h1><span class="sub">Bloom summary · animal ledger (routed alive / dead-on-arrival to reuse) · EAD release log · exports carry the SIMULATED header</span>
        <span style="margin-left:auto;display:flex;gap:6px"><button class="btn" id="rpL">Ledger CSV</button><button class="btn" id="rpE">EAD release log CSV</button><button class="btn" id="rpD">Decision log CSV</button><button class="btn" id="rpO">OS event log CSV</button><button class="btn primary" id="rpP">Print summary</button></span></div>
      <div class="grid g3">
        <div class="panel span2"><h3>Bloom summary <span class="tag">simulated</span></h3><div id="rpSum"></div></div>
        <div class="panel"><h3>Animal ledger (cumulative)</h3><div class="chart" id="rpPie"></div></div>
        <div class="panel span2"><h3>Hourly ledger</h3><div class="scroll" style="max-height:300px"><table class="t" id="rpLed"></table></div></div>
        <div class="panel"><h3>OS event log</h3><div class="scroll" style="max-height:300px"><table class="t" id="rpOs"></table></div></div>
        <div class="panel full"><h3>EAD release log</h3><div class="scroll" style="max-height:260px"><table class="t" id="rpEad"></table></div></div>
      </div>`;
      U.$('#rpL').onclick = () => U.csv('jazr_ledger.csv', S().logs.ledger.map((r) => ({ hour_ending: JZ.fmtISO(r.t), density_per_m3: r.dens, arrived: Math.round(r.arrived), reached_plant: Math.round(r.leak), diverted: Math.round(r.diverted), released_alive_routed: Math.round(r.released), doa_to_reuse: Math.round(r.doa), transit_mortality_model: Math.round(r.transitMort), outlet: r.outlet, os_state: r.os })));
      U.$('#rpE').onclick = () => U.csv('jazr_ead_release_log.csv', S().logs.releases.map((r) => ({ start: JZ.fmtISO(r.t0), end: JZ.fmtISO(r.t1), outlet: r.outlet, animals_est: Math.round(r.n), wet_mass_t: +(r.kg / 1000).toFixed(2), outlet_O2_mg_L: +r.o2.toFixed(2), SST_C: r.sst, diffuser_exit_m_s: +r.exitV.toFixed(2), approval: r.appr })));
      U.$('#rpD').onclick = () => U.csv('jazr_decision_log.csv', S().logs.decisions.map((d) => ({ time: JZ.fmtISO(d.t), kind: d.kind, from: d.from, to: d.to, status: d.status, by: d.by, basis: d.basis })));
      U.$('#rpO').onclick = () => U.csv('jazr_os_log.csv', S().logs.os.map((d) => ({ time: JZ.fmtISO(d.t), from: d.from, to: d.to, why: d.why, by: d.by })));
      U.$('#rpP').onclick = () => { U.$$('.page').forEach((p) => p.classList.remove('print')); root.classList.add('print'); window.print(); };
      const t = U.theme;
      U.chart(U.$('#rpPie'), () => { const c = t(), k = S().k; return U.base({ tooltip: { trigger: 'item', formatter: (p) => `${p.name}: ${U.big(p.value)} (${p.percent}%)` }, legend: { bottom: 0, left: 0, textStyle: { color: c.ink2, fontSize: 10 } },
        series: [{ type: 'pie', radius: ['45%', '70%'], center: ['50%', '45%'], label: { show: false }, data: [{ name: 'Released alive (routed)', value: Math.round(k.released), itemStyle: { color: c.data } }, { name: 'In system / pipe', value: Math.max(0, Math.round(k.diverted - k.released - k.doa - k.transitMort)), itemStyle: { color: c.data3 } }, { name: 'DOA → reuse', value: Math.round(k.doa), itemStyle: { color: c.eq } }, { name: 'Transit mortality (model)', value: Math.round(k.transitMort), itemStyle: { color: c.p2 } }, { name: 'Reached plant', value: Math.round(k.leakSince + k.leakPre), itemStyle: { color: c.ink3 } }] }] }); }, 'reports');
    },
    update() {
      const s = S(), k = s.k, peak = Math.max(0, ...s.hist.map((h) => h.dens)), leak = k.arrivedSince ? k.leakSince / k.arrivedSince : null;
      const rows = [['Scenario', s.sc.name], ['Simulated span', `${JZ.fmtT(0)} → ${JZ.fmtT(s.t)} (${U.dur(s.t)})`], ['Alert', s.logs.os.find((x) => x.to === 'ALERT') ? JZ.fmtT(s.logs.os.find((x) => x.to === 'ALERT').t) : '—'], ['Deploy started', s.deployT != null ? JZ.fmtT(s.deployT) : 'not deployed'],
        ['Peak density at intake', peak.toFixed(2) + ' /m³'], ['Animals arriving at intake', U.big(k.arrived)], ['<span class="tg b">BEFORE</span> would have reached plant screens', `<span class="vb">${U.big(k.arrived)} (100 %)</span>`], ['<span class="tg w">WITH JAZR</span> got past JAZR since deploy', `<span class="vw">${U.big(k.leakSince)} (${leak != null ? U.pct(leak, 2) : '—'})</span>`], ['<span class="tg w">WITH JAZR</span> reached plant during deploy ramp', U.big(k.leakPre)], ['<span class="tg b">BEFORE</span> → <span class="tg w">WITH JAZR</span> saved alive', `<span class="vb">0</span> → <span class="vw">${U.big(k.released + Math.max(0, s.inPipe))}</span>`],
        ['Diverted into bypass (incl. Layer 2)', U.big(k.diverted)], ['Caught by Layer 2 (hydro-jet curtain)', U.big(k.l2caught)], ['RELEASED ALIVE (main path) near / far', `<b>${U.big(k.relNear)} / ${U.big(k.relFar)}</b>`], ['Dead on arrival → beneficial reuse', U.big(k.doa) + ' (' + U.n(k.doa * C.MASS / 1000, 1) + ' t)'], ['Transit mortality (O₂ model)', U.big(k.transitMort)],
        ['Wet biomass released', U.n(k.bioReleasedKg / 1000, 1) + ' t @ 0.33 kg'], ['Turtles excluded alive', k.turtleConfirmed], ['Fish routed', U.n(k.fish, 0)], ['Crew-hours saved (vs 13-person baseline)', U.n(k.crewSaved, 0)], ['Alarms annunciated', s.alarms.journal.filter((j) => j.ev === 'ALARM').length], ['Survival (96 h) ESTIMATE', JZ.survEnd().toFixed(3) + ' end-to-end']];
      U.$('#rpSum').innerHTML = `<div class="kv" style="grid-template-columns:1fr auto 1fr auto">${rows.map(([a, b]) => `<span class="k">${a}</span><span class="v">${b}</span>`).join('')}</div><div class="note" style="margin-top:8px">All figures are from the simulated data generator (illustrative), consistent with JAZR v4.1/v5 design numbers. No physical prototype exists.</div>`;
      U.$('#rpLed').innerHTML = '<tr><th>Hour ending</th><th class="num">Density</th><th class="num">Arrived</th><th class="num">Reached plant</th><th class="num">Diverted</th><th class="num">Released alive</th><th class="num">DOA→reuse</th><th>Outlet</th><th>OS</th></tr>' + s.logs.ledger.slice(-72).reverse().map((r) => `<tr><td class="mono">${JZ.fmtT(r.t)}</td><td class="num">${r.dens.toFixed(2)}</td><td class="num">${U.big(r.arrived)}</td><td class="num">${U.big(r.leak)}</td><td class="num">${U.big(r.diverted)}</td><td class="num">${U.big(r.released)}</td><td class="num">${U.big(r.doa)}</td><td>${r.outlet}</td><td>${r.os}</td></tr>`).join('');
      U.$('#rpOs').innerHTML = '<tr><th>Time</th><th>→</th><th>Why</th><th>By</th></tr>' + s.logs.os.slice().reverse().map((x) => `<tr><td class="mono">${JZ.fmtT(x.t)}</td><td>${x.to}</td><td>${U.esc(x.why)}</td><td>${U.esc(x.by)}</td></tr>`).join('');
      U.$('#rpEad').innerHTML = '<tr><th>Start</th><th>End</th><th>Outlet</th><th class="num">Animals (est.)</th><th class="num">Wet mass t</th><th class="num">Outlet O₂</th><th class="num">SST</th><th class="num">Exit m/s</th><th>Approval</th></tr>' + (s.logs.releases.slice().reverse().map((r) => `<tr><td class="mono">${JZ.fmtT(r.t0)}</td><td class="mono">${JZ.fmtT(r.t1)}</td><td>${r.outlet}</td><td class="num">${U.big(r.n)}</td><td class="num">${(r.kg / 1000).toFixed(1)}</td><td class="num">${r.o2.toFixed(1)}</td><td class="num">${r.sst}</td><td class="num">${r.exitV.toFixed(2)}</td><td class="note">${U.esc(r.appr)}</td></tr>`).join('') || '<tr><td colspan="9" class="note">No releases yet (pipe transit ≈ 1.5–3 h after operation starts).</td></tr>');
    },
  };
})();
