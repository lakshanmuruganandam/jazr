"""T8 / (c) Release-point study and qualitative comparison with a public ~23% drift-back estimate (15 km tow).
 A cloud of 1500 animals (sigma 100 m) is released at a point; Today physics only (no screens), so every
 animal that reaches r < 60 m is a 'return to the intake'. 4 tide phases x 4 seeds, swim 0.036.
 Release points: offshore of the pocket (x=+1200, y=d) and alongshore-downcoast (x=+d, y=1000), d = 0.6..15 km.
 Horizons 72 h and 240 h; residual drift 0, onshore 1 cm/s, onshore 3 cm/s.
 Also: tide-phase ranking at 3 km and 5 km offshore (12 release phases), and an exact regression re-run of
 twin/out/exportstudy.json (seeds 1,2; N=3000)."""
import numpy as np, json, os, time, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from common import J, PH, save, FIGS, OUT, TWIN
from harness import hrun
from multiprocessing import Pool
DS = (600, 1000, 2000, 3000, 5000, 7500, 10000, 15000); SEEDS = (1, 2, 3, 4); NP = 1500

def cloud(cx, cy, seed):
    r = np.random.default_rng(10_000+seed); x = cx + r.normal(0, 100, NP); y = np.abs(cy + r.normal(0, 100, NP)); return (x, y)

if __name__ == "__main__":
    t0 = time.time(); jobs, keys = [], []
    for geom in ("offshore", "alongshore"):
        for d in DS:
            cx, cy = (1200.0, float(d)) if geom == "offshore" else (float(d), 1000.0)
            for vr in (0.0, -0.01, -0.03):
                for hrs in (72, 240):
                    for p in PH:
                        for s in SEEDS:
                            jobs.append(dict(init_xy=cloud(cx, cy, s), hours=hrs, vr=vr, phase0=p, seed=s)); keys.append(("dist", geom, d, vr, hrs))
    PHS12 = np.arange(12)*2*np.pi/12
    for d in (3000, 5000):
        for p in PHS12:
            for s in SEEDS:
                jobs.append(dict(init_xy=cloud(1200.0, float(d), s), hours=72, phase0=float(p), seed=s)); keys.append(("phase", d, float(p)))
    with Pool() as pool: res = pool.map(hrun, jobs, chunksize=4)
    acc = {}
    for k, r in zip(keys, res): acc.setdefault(k, []).append(r["captured_frac"])
    R = {"distance": {}, "phase": {}}; rows = []
    for k, v in acc.items():
        if k[0] == "dist":
            _, g, d, vr, h = k; R["distance"][f"{g}|d={d}|vr={vr}|h={h}"] = dict(mean=float(np.mean(v)), min=float(np.min(v)), max=float(np.max(v)))
            rows.append([g, d, vr, h, np.mean(v), np.min(v), np.max(v)])
        else:
            _, d, p = k; R["phase"][f"d={d}|phase={p:.3f}"] = float(np.mean(v))
    # monotonicity checks (non-increasing with distance, tolerance 1 pct-pt for MC noise)
    mono = {}
    for g in ("offshore", "alongshore"):
        for vr in (0.0, -0.01, -0.03):
            for h in (72, 240):
                m = [R["distance"][f"{g}|d={d}|vr={vr}|h={h}"]["mean"] for d in DS]
                mono[f"{g}|vr={vr}|h={h}"] = dict(values=m, nonincreasing_within_1pp=bool(np.all(np.diff(m) <= 0.01)),
                                                  strictly_nonincreasing=bool(np.all(np.diff(m) <= 0)))
    R["monotonic"] = mono
    for d in (3000, 5000):
        ph = [R["phase"][f"d={d}|phase={p:.3f}"] for p in PHS12]
        R["phase"][f"summary d={d}"] = dict(best_phase_rad=float(PHS12[int(np.argmin(ph))]), worst_phase_rad=float(PHS12[int(np.argmax(ph))]),
                                           best=float(min(ph)), worst=float(max(ph)), spread_pctpts=float((max(ph)-min(ph))*100))
        print("phase", d, R["phase"][f"summary d={d}"])
    for k, v in mono.items(): print(k, [round(x*100, 1) for x in v["values"]], v["nonincreasing_within_1pp"])
    # regression: exportstudy.json reproduced exactly with the twin's own avg protocol
    from ablation import avg  # noqa  (twin/ablation.py, uses its own Pool)
    pub = json.load(open(os.path.join(TWIN, "out", "exportstudy.json")))
    base = dict(system=True, policy="ebb", window=0.25, ratchet=0.07, cap_t=100)
    chk = {}
    for lab, kw in [("pipe 1 km offshore", dict(gate_x=1200, gate_y=1000)), ("pipe 2 km offshore", dict(gate_x=1200, gate_y=2000)),
                    ("pipe 3 km offshore", dict(gate_x=1200, gate_y=3000)), ("passive lane end 2 km", dict(gate_x=2000, gate_y=150))]:
        a = avg(dict(base, **kw)); chk[lab] = dict(published=pub[lab]["captured"], rerun=a["captured"], exact=bool(abs(a["captured"]-pub[lab]["captured"]) < 1e-12))
        print("export regression", lab, chk[lab])
    R["exportstudy_regression"] = chk
    save("t8_release.json", R)
    with open(f"{OUT}/t8_release_distance.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["geometry", "distance_m", "vr_mps", "hours", "return_frac_mean", "min_over_runs", "max_over_runs"]); w.writerows(rows)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
    cols = {0.0: "#2563eb", -0.01: "#f59e0b", -0.03: "#dc2626"}
    for vr in (0.0, -0.01, -0.03):
        for h, ls in ((72, "-"), (240, "--")):
            ax[0].plot(np.array(DS)/1000, [R["distance"][f"offshore|d={d}|vr={vr}|h={h}"]["mean"]*100 for d in DS], ls, marker="o", ms=3, color=cols[vr], label=f"onshore {-vr*100:.0f} cm/s, {h} h")
            ax[1].plot(np.array(DS)/1000, [R["distance"][f"alongshore|d={d}|vr={vr}|h={h}"]["mean"]*100 for d in DS], ls, marker="o", ms=3, color=cols[vr])
    for a, t in zip(ax, ("release offshore of pocket (x=1.2 km, y=d)", "release downcoast (x=d, y=1 km)")):
        a.axhline(23, color="k", lw=.8, ls=":"); a.text(15, 24, "Public estimate: ~23% drift back (15 km, own metric)", ha="right", fontsize=7)
        a.set_xlabel("release distance d (km)"); a.set_ylabel("% of released animals reaching intake"); a.set_title(t, fontsize=10); a.grid(alpha=.3)
    ax[0].legend(fontsize=7, frameon=False)
    fig.suptitle("T8 drift-back vs release distance (twin, Today physics, 4 phases x 4 seeds, 1500 animals)")
    fig.tight_layout(); fig.savefig(f"{FIGS}/t8_release_distance.png", dpi=130)
    print("runtime s", round(time.time()-t0))
