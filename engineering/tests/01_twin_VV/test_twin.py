"""T1 pytest suite for the JAZR digital twin (twin/jazr_twin.py, imported read-only).
Run:  cd TESTS/01_twin_VV && python3 -m pytest -q test_twin.py
Fast tests only (< ~2 min total); the heavy studies live in vv_*.py."""
import math, os, json
import numpy as np
import pytest
from common import J, patched, V3, V3_BASE, TODAY, PH, TWIN
import harness as HZ

def one_particle(x0, y0, **kw):
    """Run the TWIN itself (not the harness) with a single particle at a known position, by shrinking the band."""
    with patched(BAND_X=(x0, x0+1e-9), BAND_Y=(y0, y0+1e-9), **kw.pop("patch", {})):
        res, capt, occ, frames = J.simulate(N=1, record_every=1, **kw)
    return res, frames

# ---------------------------------------------------------------- 1. kinematics units
def test_sink_velocity_formula_matches_Q_over_pi_r_h():
    for r0 in (700.0, 1500.0, 4000.0):
        _, fr = one_particle(0.0, r0, hours=60/3600, dt=60.0, swim=0.0, patch=dict(U0=0.0))
        y1 = fr[0][2][0]
        expected = r0 - J.Q/(math.pi*r0*J.H)*60.0
        assert y1 == pytest.approx(expected, rel=1e-12)

def test_half_plane_sink_flux_equals_Q():
    # flux through a half circle of radius r = (pi r) * h * |u_r| must equal Q for every r
    for r in (100.0, 440.0, 5000.0):
        assert math.pi*r*J.H*(J.Q/(math.pi*r*J.H)) == pytest.approx(J.Q)

def test_capture_radius_matches_documented_440m():
    # r* = Q/(pi h U) at the median tidal speed 0.083 m/s should be ~440 m (doc: "~440 m sink zone")
    rstar = J.Q/(math.pi*J.H*0.083)
    assert 400 < rstar < 480 and J.R_I > rstar

def test_tidal_excursion_constant():
    assert 2*J.U0/J.W == pytest.approx(1665.2, abs=1.0)

def test_coast_reflection():
    # pure onshore drift 1 m/s for 60 s from y = 600 lands at |600-60*... | -> reflected about y=0
    with patched(Q=0.0, U0=0.0):
        r, fr = one_particle(5000.0, 600.0, hours=11*60/3600, dt=60.0, swim=0.0, vr=-1.0)
    ys = [f[2][0] for f in fr]
    assert ys[9] == pytest.approx(0.0, abs=1e-9) and ys[10] == pytest.approx(60.0)  # 600-660 -> |-60| = 60
    assert min(ys) >= 0.0

@pytest.mark.parametrize("r_end,captured", [(59.0, True), (61.0, False)])
def test_capture_radius_60m(r_end, captured):
    v = (600.0 - r_end)/60.0
    r, fr = one_particle(0.0, 600.0, hours=60/3600, dt=60.0, swim=0.0, vr=-v, patch=dict(Q=0.0, U0=0.0))
    assert bool(fr[0][3][0] == 2) == captured

# ---------------------------------------------------------------- 2. state machine & conservation
CASES = [dict(TODAY), dict(V3), dict(V3_BASE), dict(system=True, policy="ebb", window=0.25, cap_t=100, gate_x=1200, gate_y=3000),
         dict(system=True, policy="hold", hold_h=6), dict(system=True, policy="ebb", ratchet=0.07, cap_t=30)]

@pytest.mark.parametrize("kw", CASES)
def test_state_partition_and_absorbing_capture(kw):
    res, o = HZ.simulate(N=600, hours=48, seed=4, **kw)
    st = o["state"]
    assert set(np.unique(st)) <= {0, 1, 2}                      # every particle in exactly one state
    assert ((st == 0).sum() + (st == 1).sum() + (st == 2).sum()) == 600
    c = o["capt_ts"]; assert np.all(np.diff(c) >= 0)            # CAPT is absorbing (never decreases)
    assert np.all(o["occ"] + c <= 600)                          # FREE >= 0 at every step
    assert res["captured_tonnes"] == pytest.approx(res["captured_frac"]*res["swarm_tonnes"])
    assert res["swarm_tonnes"] == pytest.approx(J.DENS*8000*1450*J.H*J.MASS/1000)   # mass conserved, N-independent

def test_swarm_mass_independent_of_N():
    m = [J.simulate(N=n, hours=1)[0]["swarm_tonnes"] for n in (100, 1000, 3000)]
    assert m[0] == pytest.approx(m[1]) == pytest.approx(m[2]) == pytest.approx(12180.0)

def test_held_never_captured_and_captured_never_released():
    res, o = HZ.simulate(N=500, hours=72, seed=2, system=True, policy="hold", hold_h=1e9, eta_r=1.0, eta_g=1.0)
    # perfect screens + never release -> nothing reaches the intake except particles that jump 120->60 m in one step
    assert res["captured_frac"] < 0.01
    assert res["still_held_frac"] + res["captured_frac"] + (o["state"] == 0).mean() == pytest.approx(1.0)

# ---------------------------------------------------------------- 3. release policies & pocket cap
def test_immediate_policy_never_holds():
    res, o = HZ.simulate(N=500, hours=48, **V3)
    assert res["peak_held_tonnes"] == 0 and res["still_held_frac"] == 0 and res["mean_handlings"] > 0

def test_hold_policy_releases_after_hold_time():
    res, o = HZ.simulate(N=500, hours=48, system=True, policy="hold", hold_h=6.0)
    assert res["peak_held_tonnes"] > 0
    res2, _ = HZ.simulate(N=500, hours=48, system=True, policy="hold", hold_h=1e9)
    assert res2["still_held_frac"] > res["still_held_frac"]

def test_ebb_policy_releases_only_inside_window():
    w = 0.25
    res, o = HZ.simulate(N=800, hours=72, system=True, policy="ebb", window=w, seed=3)
    occ = o["occ"]; t = np.arange(len(occ))*60.0
    ph = (J.W*t) % (2*np.pi); frac = np.where(ph < np.pi, ph/np.pi, (ph-np.pi)/np.pi)
    drops = np.where(np.diff(occ) < 0)[0] + 1
    assert drops.size > 0 and np.all(frac[drops] < w + 1e-9)

@pytest.mark.parametrize("cap", [30, 100, 300])
def test_pocket_cap_respected(cap):
    res, o = HZ.simulate(N=3000, hours=72, system=True, policy="ebb", window=0.25, cap_t=cap, gate_x=1200, gate_y=3000)
    per = J.DENS*8000*1450*J.H/3000*J.MASS/1000                   # tonnes per particle
    cap_n = int(cap*1000/J.MASS/(J.DENS*8000*1450*J.H/3000))
    assert o["occ"].max() <= 2*cap_n                               # two pockets
    assert res["peak_held_tonnes"] <= 2*cap + per

# ---------------------------------------------------------------- 4. determinism & regressions
def test_determinism_fixed_seed():
    a = J.simulate(N=1000, seed=11, **V3)[0]; b = J.simulate(N=1000, seed=11, **V3)[0]; c = J.simulate(N=1000, seed=12, **V3)[0]
    assert a == b and a != c

@pytest.mark.parametrize("kw", CASES)
def test_harness_is_bit_identical_to_twin(kw):
    a = J.simulate(N=700, seed=5, phase0=1.3, hours=48, **kw)[0]; b = HZ.simulate(N=700, seed=5, phase0=1.3, hours=48, **kw)[0]
    assert all(a[k] == b[k] for k in a)

def test_published_v3_headline_reproduced_exactly_one_run():
    # first job of twin/out/v3study.json protocol (phase 0, seed 1) must be deterministic; full table in vv_statistics.py
    r = J.simulate(N=3000, phase0=0.0, seed=1, **V3)[0]["captured_frac"]
    assert r == J.simulate(N=3000, phase0=0.0, seed=1, **V3)[0]["captured_frac"]
    pub = json.load(open(os.path.join(TWIN, "out", "v3study.json")))["Gate + outer guide (0.4) + outlet 5 km|median"]
    assert pub["lo"] <= r <= pub["hi"]

def test_density_does_not_change_fractions_without_cap():
    a = J.simulate(N=800, seed=3, **V3)[0]
    with patched(DENS=1.0): b = J.simulate(N=800, seed=3, **V3)[0]
    assert a["captured_frac"] == b["captured_frac"] and b["swarm_tonnes"] == pytest.approx(10*a["swarm_tonnes"])

def test_density_matters_only_through_pocket_cap():
    kw = dict(system=True, policy="ebb", window=0.25, cap_t=100, gate_x=1200, gate_y=3000)
    a = J.simulate(N=1500, seed=3, **kw)[0]
    with patched(DENS=1.0): b = J.simulate(N=1500, seed=3, **kw)[0]
    assert a["peak_held_tonnes"] <= 200 + 10 and b["peak_held_tonnes"] <= 200 + 100

def test_system_always_reduces_capture_vs_today():
    for p in PH:
        assert J.simulate(N=1500, phase0=p, **V3)[0]["captured_frac"] < J.simulate(N=1500, phase0=p, **TODAY)[0]["captured_frac"]

# ---------------------------------------------------------------- 5. analytic verification (quick versions)
def test_capture_band_width_steady_current():
    from vv_analytic import band_edge
    r = band_edge(0.117, dt=60.0, n=400)
    assert abs(r["rel_err"]) < 0.02             # vs exact streamline from x0 = -8 km
    assert abs(r["rel_err_vs_W"]) < 0.06        # vs far-field W = Q/(U h)

def test_stagnation_point_r_star():
    from vv_analytic import stagnation
    assert abs(stagnation(0.083)["rel_err"]) < 0.01

def test_zero_flow_capture_radius():
    from vv_analytic import zero_flow
    assert abs(zero_flow(24)["rel_err"]) < 0.01

# ---------------------------------------------------------------- 6. (a) alert-to-arrival timing
@pytest.mark.parametrize("U,d", [(0.05, 3000.0), (0.117, 4000.0), (0.15, 8000.0)])
def test_alert_arrival_time_matches_current_speed(U, d):
    from vv_analytic import arrival
    r = arrival(U, d, 60.0)
    assert abs(r["rel_err"]) < 0.01
    assert r["t_twin_h"] == pytest.approx((d-J.R_I)/U/3600, rel=0.35)   # same order as distance/current

def test_offshore_only_alert_never_arrives():
    # swarm 8-10 km offshore, tide + swimming, no onshore drift: nothing reaches the ring in 72 h
    rng = np.random.default_rng(0); x0 = rng.uniform(-3000, 3000, 500); y0 = rng.uniform(8000, 10000, 500)
    res, o = HZ.simulate(init_xy=(x0, y0), hours=72, swim=0.036)
    assert np.isnan(o["t_arr"]).all() and res["captured_frac"] == 0.0

def test_bearing_matters_upstream_vs_downstream():
    # same distance, steady current toward +x: an upstream (-x) alert arrives, a downstream (+x) one does not
    with patched(U0=0.0):
        up = HZ.simulate(init_xy=(np.full(50, -4000.0), np.linspace(10, 300, 50)), swim=0.0, ur=0.1, hours=48)[0]
        dn = HZ.simulate(init_xy=(np.full(50, 4000.0), np.linspace(10, 300, 50)), swim=0.0, ur=0.1, hours=48)[0]
    assert up["captured_frac"] == 1.0 and dn["captured_frac"] == 0.0

# ---------------------------------------------------------------- 7. (b) wind drift (harness option)
def test_wind_leeway_moves_particles_downwind_exactly():
    with patched(Q=0.0, U0=0.0):
        _, o = HZ.simulate(init_xy=(np.zeros(5), np.full(5, 5000.0)), swim=0.0, hours=10, wind_fn=lambda t: (10.0, 0.0), windage=0.03)
    assert np.allclose(o["x"], 0.03*10.0*10*3600) and np.allclose(o["y"], 5000.0)

def test_onshore_wind_increases_arrivals():
    on = lambda t: (0.0, -5.0); off = lambda t: (0.0, 5.0)
    base = HZ.simulate(N=1500, seed=2, **V3)[0]["captured_frac"]
    a = HZ.simulate(N=1500, seed=2, wind_fn=on, windage=0.02, **V3)[0]["captured_frac"]
    b = HZ.simulate(N=1500, seed=2, wind_fn=off, windage=0.02, **V3)[0]["captured_frac"]
    assert a > base > b

def test_wind_off_by_default_is_identical():
    a = HZ.simulate(N=500, seed=2, **V3)[0]; b = HZ.simulate(N=500, seed=2, wind_fn=lambda t: (9.0, 9.0), windage=0.0, **V3)[0]
    assert a == b

# ---------------------------------------------------------------- 8. (c) release-point ranking
def _returns(x, y, phase=0.0, vr=0.0, hours=72):
    vals = []
    for s in (1, 2):
        r = np.random.default_rng(s); x0 = x + r.normal(0, 100, 600); y0 = np.abs(y + r.normal(0, 100, 600))
        vals.append(HZ.simulate(init_xy=(x0, y0), hours=hours, phase0=phase, vr=vr, seed=s)[0]["captured_frac"])
    return float(np.mean(vals))

def test_release_further_offshore_gives_fewer_returns():
    r = [np.mean([_returns(1200.0, d, p, vr=-0.01) for p in PH]) for d in (600.0, 2000.0, 5000.0, 15000.0)]
    assert all(b <= a + 0.01 for a, b in zip(r, r[1:])) and r[0] > r[-1]

def test_release_timing_matters_and_ebb_phase_is_best():
    # release 3 km offshore of the +x pocket (x=1.2 km): releasing as the tide turns toward +x (phase 0, away
    # from the intake) must return fewer animals than releasing as it turns toward the intake (phase pi).
    # NOTE (finding): at the collector mouth (x=600, y=150) and at 1-2 km, 100% return within 72 h at every
    # phase, so timing cannot help there - only export distance can.
    good = _returns(1200.0, 3000.0, phase=0.0); bad = _returns(1200.0, 3000.0, phase=np.pi)
    assert good < bad - 0.03
    assert _returns(600.0, 150.0, phase=0.0) == 1.0

# ---------------------------------------------------------------- 9. (d) stranding / beaching (harness option)
def test_stranded_particles_never_count_as_arriving():
    res, o = HZ.simulate(N=1500, seed=3, vr=-0.05, beach=True, **TODAY)
    s = o["state"] == HZ.STRAND
    assert s.sum() > 0 and np.isnan(o["t_cap"][s]).all()
    no = HZ.simulate(N=1500, seed=3, vr=-0.05, beach=False, **TODAY)[0]
    assert res["captured_frac"] < no["captured_frac"]
    assert res["captured_frac"] + res["stranded_frac"] + res["still_held_frac"] + ((o["state"] == 0).mean()) == pytest.approx(1.0)

def test_twin_itself_has_no_stranding():
    # documented behaviour: the twin reflects at y = 0 (no beaching state); only states 0/1/2 exist
    res, o = HZ.simulate(N=500, seed=3, vr=-0.05)
    assert res["stranded_frac"] == 0.0 and set(np.unique(o["state"])) <= {0, 1, 2}

# ---------------------------------------------------------------- 10. (e) real-data hindcast
def test_hindcast_ordering_with_real_forcing():
    import hindcast as HC
    F = HC.load()
    if F is None:
        pytest.skip("No real current time series in TESTS/00_data/raw/openmeteo_marine yet - hindcast skipped")
    starts = list(range(24*150, len(F["time"])-80, 24*60))[:12]        # 12 windows, every 60 days
    tot = {"Today": [], "v2": [], "v3": []}
    for i in starts:
        cf = HC.Series(F["u"], F["v"], i, 72)
        for n, kw in (("Today", TODAY), ("v2", V3_BASE), ("v3", V3)):
            tot[n].append(HZ.simulate(N=600, hours=72, current_fn=cf, **kw)[0]["captured_frac"])
    m = {k: np.mean(v) for k, v in tot.items()}
    assert m["Today"] > m["v2"] > m["v3"], m

# ---------------------------------------------------------------- 11. (f) v3 sizing regression numbers
RHO, G = 1025.0, 9.81
def test_screen_area_1000m2_at_0p10():
    q_unit = J.Q/4                       # 4 units share the twin's 400 m3/s
    assert q_unit/0.10 == pytest.approx(1000.0)

def test_screen_angle_sweep_ratio_and_length():
    th = math.radians(11.0)
    assert 1/math.tan(th) == pytest.approx(5.14, abs=0.01)          # sweep/through ~5
    assert 0.5*math.cos(th) == pytest.approx(0.49, abs=0.01)         # sweep ~0.5 m/s
    assert 1000/7 == pytest.approx(143, abs=0.5) and 1000/5 == pytest.approx(200)   # 143-200 m screen at 7/5 m depth

def test_lane_width_28_to_40m():
    assert 100/(0.5*7) == pytest.approx(28.6, abs=0.1) and 100/(0.5*5) == pytest.approx(40.0)

@pytest.mark.parametrize("L,kw_doc", [(3000, 195), (5000, 286)])
def test_pipe_power(L, kw_doc):
    Qp, D, f, eta, minor = 2.0, 1.2, 0.012, 0.7, 2.0
    v = Qp/(math.pi*D**2/4); hf = f*L/D*v**2/(2*G)
    P = RHO*G*Qp*(hf+minor)/eta/1000
    assert P == pytest.approx(kw_doc, abs=2.0)

def test_stress_load_108_t_per_h():
    assert 0.1*100*3*3600/1000 == pytest.approx(108.0)
