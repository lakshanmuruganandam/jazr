"""T5 Global sensitivity analysis (numpy implementation; SALib is not installed).
 Morris elementary effects (r=20 trajectories, 4 levels) for v3 AND Today (Today doubles as a check: the
 system-only inputs eta_g, eta_r, gate_y must get mu* = 0 exactly).
 Sobol first-order / total indices (Saltelli 2010 A,B,AB_i design; Jansen total, Saltelli first-order) for v3.
 Output = % of swarm reaching intake. N = 1000 particles per run (stated; reduced from 1500 because the shared machine was overloaded), each run = mean of 2 tide phases
 (0, pi/2) for Morris and tide phase 0 for Sobol, with common random numbers (same seed) across a trajectory /
 design row."""
import numpy as np, time, csv, os, sys, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from common import J, V3, TODAY, pmap, save, FIGS, OUT
FACT = [("eta_g", 0.2, 0.8), ("eta_r", 0.3, 0.95), ("swim", 0.02, 0.15), ("vr", -0.04, 0.0),
        ("ur", -0.02, 0.02), ("gate_y", 2000, 6000), ("hours", 72, 240), ("U0", 0.08, 0.15)]
K = len(FACT); NP = 1000; PHS = (0.0, np.pi/2)

def to_jobs(X, base, seeds, PHS=PHS):
    jobs = []
    for x, s in zip(X, seeds):
        kw = dict(base, N=NP, seed=int(s)); patch = {}
        for (n, lo, hi), u in zip(FACT, x):
            v = lo + u*(hi-lo)
            if n == "U0": patch["U0"] = float(v)
            elif n == "hours": kw["hours"] = float(v)
            else: kw[n] = float(v)
        for p in PHS: jobs.append((dict(kw, phase0=p), patch))
    return jobs

def evaluate(X, base, seeds, PHS=PHS):
    r = pmap(to_jobs(X, base, seeds, PHS))
    return np.array([x["captured_frac"] for x in r]).reshape(len(X), len(PHS)).mean(1)*100

def morris_design(r, p=4, rng=None):
    d = p/(2*(p-1)); grid = np.arange(p)/(p-1)
    T = []
    for _ in range(r):
        x0 = rng.choice(grid[grid + d <= 1 + 1e-9], K)
        order = rng.permutation(K); traj = [x0.copy()]; x = x0.copy()
        for i in order: x = x.copy(); x[i] += d; traj.append(x)
        T.append((np.array(traj), order))
    return T, d

if __name__ == "__main__":
    t0 = time.time(); rng = np.random.default_rng(7); R = {}
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    T, d = morris_design(20, rng=rng)
    mfile = f"{OUT}/t5_morris_cache.json"
    if part in ("morris", "all") or not os.path.exists(mfile):
      X = np.vstack([t[0] for t in T]); seeds = np.repeat(np.arange(100, 120), K+1)
      for name, base in (("v3", V3), ("today", TODAY)):
          Y = evaluate(X, base, seeds).reshape(20, K+1)
          EE = np.zeros((20, K))
          for j, (traj, order) in enumerate(T):
              for step, i in enumerate(order): EE[j, i] = (Y[j, step+1]-Y[j, step])/d   # pct-pts per full range
          mu = EE.mean(0); mus = np.abs(EE).mean(0); sig = EE.std(0, ddof=1)
          # bootstrap CI on mu*
          bi = rng.integers(0, 20, (2000, 20)); mus_ci = np.percentile(np.abs(EE)[bi].mean(1), [2.5, 97.5], axis=0)
          R[f"morris_{name}"] = {FACT[i][0]: dict(mu=float(mu[i]), mu_star=float(mus[i]), sigma=float(sig[i]),
                                                 mu_star_ci95=[float(mus_ci[0, i]), float(mus_ci[1, i])]) for i in range(K)}
          R[f"morris_{name}"]["_ranking"] = [FACT[i][0] for i in np.argsort(-mus)]
          print(name, "Morris mu* (pct-pts over full range):", {FACT[i][0]: round(mus[i], 2) for i in np.argsort(-mus)}, flush=True)
      json.dump(R, open(mfile, "w"), indent=1)
    else:
      R.update(json.load(open(mfile)))
    if part == "morris": raise SystemExit(f"morris done {time.time()-t0:.0f} s")
    rng = np.random.default_rng(8)
    # Sobol (Saltelli design), v3 only
    Nb = 128; NPS = 1000
    A = rng.random((Nb, K)); Bm = rng.random((Nb, K))
    mats = [A, Bm] + [np.where(np.arange(K) == i, Bm, A) for i in range(K)]
    Xs = np.vstack(mats); sd = np.tile(np.arange(1000, 1000+Nb), K+2)     # common random numbers per row
    sfile = f"{OUT}/t5_sobol_Y.npz"
    if os.path.exists(sfile): Ys = np.load(sfile)["Y"]
    else:
        NP = NPS; Ys = evaluate(Xs, V3, sd, PHS=(0.0,)).reshape(K+2, Nb); np.savez(sfile, Y=Ys, X=Xs)
    fA, fB, fAB = Ys[0], Ys[1], Ys[2:]
    def indices(ix):
        V = np.var(np.concatenate([fA[ix], fB[ix]]), ddof=1)
        S1 = np.array([np.mean(fB[ix]*(fAB[i][ix]-fA[ix]))/V for i in range(K)])
        ST = np.array([0.5*np.mean((fA[ix]-fAB[i][ix])**2)/V for i in range(K)])
        return S1, ST, V
    S1, ST, V = indices(np.arange(Nb))
    bs = [indices(rng.integers(0, Nb, Nb)) for _ in range(500)]
    S1c = np.percentile([b[0] for b in bs], [2.5, 97.5], axis=0); STc = np.percentile([b[1] for b in bs], [2.5, 97.5], axis=0)
    R["sobol_v3"] = {FACT[i][0]: dict(S1=float(S1[i]), S1_ci95=[float(S1c[0, i]), float(S1c[1, i])],
                                      ST=float(ST[i]), ST_ci95=[float(STc[0, i]), float(STc[1, i])]) for i in range(K)}
    R["sobol_v3"]["_output_mean_pct"] = float(np.mean(np.concatenate([fA, fB]))); R["sobol_v3"]["_output_var"] = float(V)
    R["sobol_v3"]["_ranking_ST"] = [FACT[i][0] for i in np.argsort(-ST)]
    R["sobol_v3"]["_sum_S1"] = float(S1.sum())
    R["_settings"] = dict(N_particles_morris=1000, N_particles_sobol=NPS, phases=list(PHS), morris_r=20, morris_levels=4, sobol_base=Nb,
                          sobol_phases=[0.0], runs=int(20*(K+1)*2*len(PHS) + Nb*(K+2)), ranges={n: [lo, hi] for n, lo, hi in FACT})
    print("Sobol ST:", {FACT[i][0]: round(ST[i], 3) for i in np.argsort(-ST)}, "sum S1", round(float(S1.sum()), 3), flush=True)
    print("Sobol S1:", {FACT[i][0]: round(S1[i], 3) for i in np.argsort(-ST)})
    save("t5_sensitivity.json", R)
    with open(f"{OUT}/t5_sobol_samples.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["matrix_row"] + [n for n, _, _ in FACT] + ["pct_to_intake"])
        for i, (x, y) in enumerate(zip(Xs, Ys.ravel())): w.writerow([i] + [lo+u*(hi-lo) for u, (n, lo, hi) in zip(x, FACT)] + [y])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    m = R["morris_v3"]
    for n, _, _ in FACT:
        ax[0].scatter(m[n]["mu_star"], m[n]["sigma"], color="#2563eb"); ax[0].annotate(n, (m[n]["mu_star"], m[n]["sigma"]), xytext=(4, 3), textcoords="offset points")
    ax[0].set_xlabel("Morris mu* (pct-pts change over full input range)"); ax[0].set_ylabel("sigma (interaction / non-linearity)")
    ax[0].set_title("Morris screening, v3"); ax[0].grid(alpha=.3)
    order = np.argsort(-ST); yy = np.arange(K)
    ax[1].barh(yy-0.2, ST[order], 0.4, xerr=np.abs(STc[:, order]-ST[order]), color="#2563eb", label="total ST")
    ax[1].barh(yy+0.2, S1[order], 0.4, xerr=np.abs(S1c[:, order]-S1[order]), color="#93c5fd", label="first-order S1")
    ax[1].set_yticks(yy); ax[1].set_yticklabels([FACT[i][0] for i in order]); ax[1].invert_yaxis()
    ax[1].set_xlabel("Sobol index (95% bootstrap CI)"); ax[1].set_title(f"Sobol, v3 (Saltelli N={Nb})"); ax[1].legend(frameon=False); ax[1].grid(alpha=.3, axis="x")
    fig.tight_layout(); fig.savefig(f"{FIGS}/t5_sensitivity.png", dpi=130)
    print("runtime s", round(time.time()-t0))
