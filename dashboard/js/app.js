/* Bootstrap: app bar, tabs, scenario engine loop, URL params. */
(function () {
  'use strict';
  const JZ = window.JZ, U = JZ.ui;
  const TABS = [['main', 'Main Dashboard'], ['simulation', 'Simulation'], ['screens', 'Screens'], ['lift', 'Bypass & Lift'], ['release', 'Release'], ['wildlife', 'Wildlife'], ['biology', 'Biology'],
    ['alarms', 'Alarms'], ['trends', 'Trends & Analytics'], ['evidence', 'Evidence'], ['compliance', 'Compliance'], ['maint', 'Maintenance'], ['reports', 'Reports'], ['tour', '3D Simulation']];
  const q = new URLSearchParams(location.search);
  const app = (JZ.app = { cur: null, speed: +(q.get('speed') || 60), paused: q.get('pause') === '1', built: {} });
  JZ.pages.main = { title: 'Main Dashboard', build: (r) => JZ.main.build(r), update: () => JZ.main.update(JZ.sim) };

  function setTheme(th) { if (th === 'auto') document.documentElement.removeAttribute('data-theme'); else document.documentElement.setAttribute('data-theme', th); try { localStorage.setItem('jz-theme', th); } catch (e) {} U.rethemeCharts(); if (JZ.sim) app.tick(true); }

  app.load = function (id, warp) {
    JZ.sim = new JZ.Sim(id, { autopilot: U.$('#autopilot').checked });
    const w = warp != null ? warp : JZ.SCENARIOS[id].warp; if (w) JZ.sim.advance(w);
    U.$('#scDesc').textContent = JZ.SCENARIOS[id].desc;
    U.closeFP();
    // rebuild open pages so charts and tables bind to the new sim
    Object.keys(app.built).forEach((k) => { if (k !== 'main' && k !== 'simulation' && k !== 'tour') { U.charts.filter((c) => c.page === k || c.page === k + '-wi').forEach((c) => c.inst.dispose()); for (let i = U.charts.length - 1; i >= 0; i--) if (U.charts[i].page === k || U.charts[i].page === k + '-wi') U.charts.splice(i, 1); delete app.built[k]; } });
    app.show(app.cur || 'main');
    app.tick(true);
  };

  app.show = function (id) {
    if (!JZ.pages[id]) id = 'main';
    app.cur = id;
    U.$$('.tab').forEach((t) => t.setAttribute('aria-selected', String(t.dataset.tab === id)));
    U.$$('.page').forEach((p) => p.classList.toggle('on', p.id === 'pg-' + id));
    const root = U.$('#pg-' + id);
    if (!app.built[id]) { JZ.pages[id].build(root); app.built[id] = true; }
    if (JZ.pages[id].show) JZ.pages[id].show(root);
    try { history.replaceState(null, '', '#' + id); } catch (e) {}
    app.tick(true);
  };

  let lastFull = 0;
  app.tick = function (force) {
    const s = JZ.sim; if (!s) return;
    U.$('#clock').textContent = JZ.fmtT(s.t).replace(' Oct', ' Oct 2026') + ' GST';
    const c = s.alarms.counts();
    [1, 2, 3, 4].forEach((p) => { const e = U.$('#as' + p); e.textContent = c[p]; e.classList.toggle('on', c[p] > 0); });
    const anyUn = s.alarms.list().some((a) => a.st === 'UNACK');
    U.$('#asUn').textContent = c.unack ? `${c.unack} unack` : ''; U.$('#asUn').classList.toggle('blink', anyUn && !s.alarms.silenced);
    U.$('#sbState').textContent = `OS ${s.os}`; U.$('#sbComms').textContent = s.commsOk ? 'OT network OK' : 'OT network LOST — local mode, values STALE';
    U.$('#sbSpeed').textContent = app.paused ? 'PAUSED' : `×${app.speed}`;
    const tabAl = U.$('.tab[data-tab="alarms"] .dot'); if (tabAl) { const p = c[1] ? 'p1' : c[2] ? 'p2' : c[3] ? 'p3' : c[4] ? 'p4' : ''; tabAl.style.background = p ? `var(--${p})` : 'transparent'; }
    const pg = JZ.pages[app.cur];
    try { pg.update && pg.update(force); } catch (e) { console.error(e); }
    const now = performance.now();
    if (force || now - lastFull > 900) { U.refreshCharts(app.cur, force); lastFull = now; }
    U.renderFP(false);
    document.body.classList.toggle('stale', false);
  };

  function loop() {
    if (!app.paused && JZ.sim) JZ.sim.advance(app.speed * 0.5);
    app.tick(false);
  }

  function init() {
    let th = q.get('theme'); try { th = th || localStorage.getItem('jz-theme'); } catch (e) {}
    if (th && th !== 'auto') document.documentElement.setAttribute('data-theme', th);
    U.$('#theme').value = th || 'auto';
    if (q.get('wall') === '1') document.documentElement.classList.add('wall');
    const nav = U.$('#tabs'); nav.innerHTML = TABS.map(([id, l]) => `<button class="tab" role="tab" data-tab="${id}" aria-selected="false">${l}${id === 'alarms' ? '<span class="dot"></span>' : ''}</button>`).join('');
    U.$('#pages').innerHTML = TABS.map(([id]) => `<section class="page" id="pg-${id}" role="tabpanel"></section>`).join('');
    nav.addEventListener('click', (e) => { const b = e.target.closest('.tab'); if (b) app.show(b.dataset.tab); });
    const sel = U.$('#scen'); sel.innerHTML = Object.entries(JZ.SCENARIOS).map(([k, v]) => `<option value="${k}">${v.name}</option>`).join('');
    const sc = q.get('scenario') || 'typical'; sel.value = JZ.SCENARIOS[sc] ? sc : 'typical';
    sel.onchange = () => app.load(sel.value);
    U.$('#speed').value = String(app.speed); U.$('#speed').onchange = (e) => { app.speed = +e.target.value; };
    U.$('#pause').onclick = () => { app.paused = !app.paused; U.$('#pause').textContent = app.paused ? 'Run' : 'Pause'; app.tick(true); };
    U.$('#pause').textContent = app.paused ? 'Run' : 'Pause';
    U.$('#reset').onclick = () => { if (!U.confirm('RESET: restart "' + JZ.SCENARIOS[sel.value].name + '" from t = 0? Counters, states, alarms and logs are cleared.')) return; app.load(sel.value, 0); U.toast('Scenario reset to t = 0'); };
    U.$('#theme').onchange = (e) => setTheme(e.target.value);
    U.$('#wall').onclick = () => { document.documentElement.classList.toggle('wall'); setTimeout(() => U.charts.forEach((c) => c.inst.resize()), 50); };
    U.$('#fpClose').onclick = U.closeFP; U.$('#fpBack').onclick = U.closeFP;
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') U.closeFP(); });
    U.$('#autopilot').onchange = (e) => { if (JZ.sim) JZ.sim.autopilot = e.target.checked; };
    const tab = q.get('tab') || (location.hash || '').slice(1) || 'main';
    app.cur = tab;
    app.load(sel.value, q.get('t') != null ? +q.get('t') : undefined);
    setInterval(loop, 500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
