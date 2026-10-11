"""(e) Real-forcing hindcast. The twin's idealised tide + residual is REPLACED by the hourly Open-Meteo marine
surface current at 24.04N 52.21E (2022-2025; a model product, not an in-situ measurement), rotated into twin
axes. 72 h alerts start every 5 days (00:00 UTC); N = 1000 particles, seed 1. Configs: Today, v2 Gate
(guard 0.9, outlet 3 km), v3 (outer guide 0.4 + outlet 5 km). Variant with ERA5 wind leeway 2% added.
Test: ordering Today > v2 > v3 in the mean and in what fraction of windows."""
import numpy as np, time, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from multiprocessing import Pool
from common import V3, V3_BASE, TODAY, save, FIGS, OUT
from harness import hrun
import hindcast as HC
CFG = {"Today": TODAY, "v2 Gate": V3_BASE, "v3": V3}

if __name__ == "__main__":
    t0 = time.time(); F = HC.load()
    if F is None: raise SystemExit("no real forcing data in ../00_data/raw - hindcast skipped")
    t = F["time"]; starts = [i for i in range(0, len(t)-80, 24*5)]
    jobs, keys = [], []
    for wind in ((False, True) if F["wind"] is not None else (False,)):
        for i in starts:
            cf = HC.Series(F["u"], F["v"], i, 72)
            wf = HC.Series(F["wind"][0], F["wind"][1], i, 72) if wind else None
            for name, kw in CFG.items():
                jobs.append(dict(kw, N=1000, seed=1, hours=72, current_fn=cf, wind_fn=wf, windage=0.02 if wind else 0.0)); keys.append((wind, i, name))
    with Pool() as p: res = p.map(hrun, jobs, chunksize=8)
    M = {}
    for (w, i, n), r in zip(keys, res): M.setdefault(w, {}).setdefault(n, {})[i] = r["captured_frac"]
    R = {"n_windows": len(starts), "period": [str(t[0]), str(t[-1])], "n_missing_hours_interpolated": F["n_missing"],
         "mean_u_along": float(F["u"].mean()), "mean_v_offshore": float(F["v"].mean())}
    rows = []
    for w, D in M.items():
        tag = "current+wind2%" if w else "current only"
        a = {n: np.array([D[n][i] for i in starts]) for n in CFG}
        month = np.array([int(str(t[i])[5:7]) for i in starts]); on = np.isin(month, (10, 11))
        R[tag] = {n: dict(mean=float(v.mean()), P10=float(np.percentile(v, 10)), P50=float(np.median(v)), P90=float(np.percentile(v, 90)),
                          mean_OctNov=float(v[on].mean())) for n, v in a.items()}
        R[tag]["frac_windows_Today>v2>v3"] = float(((a["Today"] > a["v2 Gate"]) & (a["v2 Gate"] > a["v3"])).mean())
        R[tag]["frac_windows_Today>v2>=v3"] = float(((a["Today"] > a["v2 Gate"]) & (a["v2 Gate"] >= a["v3"])).mean())
        R[tag]["frac_windows_v3<Today"] = float((a["v3"] < a["Today"]).mean())
        R[tag]["ordering_of_means_holds"] = bool(a["Today"].mean() > a["v2 Gate"].mean() > a["v3"].mean())
        print(tag, {k: v for k, v in R[tag].items()}, flush=True)
        for j, i in enumerate(starts): rows.append([tag, str(t[i]), a["Today"][j], a["v2 Gate"][j], a["v3"][j]])
        if not w:
            fig, ax = plt.subplots(figsize=(11, 3.8)); x = np.array([t[i] for i in starts]).astype("datetime64[D]")
            for n, c in (("Today", "#9ca3af"), ("v2 Gate", "#f59e0b"), ("v3", "#2563eb")): ax.plot(x, a[n]*100, ".", ms=4, color=c, label=f"{n} (mean {a[n].mean()*100:.1f}%)")
            ax.set_ylabel("% reaching intake in 72 h"); ax.set_title("Hindcast: twin forced by Open-Meteo surface current at the plant, one 72 h alert every 5 days")
            ax.legend(frameon=False, fontsize=8); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(f"{FIGS}/t9_hindcast.png", dpi=130)
    save("t9_hindcast.json", R)
    with open(f"{OUT}/t9_hindcast_windows.csv", "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["forcing", "start_utc", "today", "v2_gate", "v3"]); wr.writerows(rows)
    print("runtime s", round(time.time()-t0))
