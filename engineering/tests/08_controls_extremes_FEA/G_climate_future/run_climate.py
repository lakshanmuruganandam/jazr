"""G. Climate / future-scenario test.

1. Incident trend: decade counts from 13_global_incidents.md (power/desal/LNG intake events, dated rows):
   1980s 5, 1990s 8, 2000s 13, 2010s 19, 2020-Oct 2026 21 (6.8 y). Poisson log-linear fit on
   annual rates. CAVEAT (same file, Condon 2013): reporting bias; no robust global bloom increase.
2. Season length: days/yr with near-site SST >= threshold (Open-Meteo marine 2022-2025), shifted by
   +0.3 and +0.5 C/decade warming [ASM scenarios] to 2050 and 2085. Bloom-season threshold unknown,
   so 30/32/34 C are shown as proxies of 'hot-season duty'.
3. Modular headroom: lift lines needed vs density and flow (line = 2 m3/s water [V3], solids <= 5 %
   by volume [audit #9], bells ~1,020 kg/m3, capture 0.9).
"""
import json, sys, pathlib
import numpy as np
from scipy.optimize import minimize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from common import params as P

DEC = [(1985, 10, 5), (1995, 10, 8), (2005, 10, 13), (2015, 10, 19), (2023.4, 6.8, 21)]  # midpoint, years, count
SRC = ROOT.parents[2] / "13_global_incidents.md"


def verify_counts():
    txt = open(SRC).read()
    ok = all(s in txt for s in ("| 1980s | 5 |", "| 1990s | 8 |", "| 2000s | 13 |", "| 2010s | 19 |", "| 2020 – Oct 2026 | **21** |"))
    return ok


def poisson_fit():
    x = np.array([d[0] for d in DEC]); e = np.array([d[1] for d in DEC]); y = np.array([d[2] for d in DEC])
    def nll(b):
        mu = e * np.exp(b[0] + b[1] * (x - 2000))
        return (mu - y * np.log(mu)).sum()
    r = minimize(nll, [0.0, 0.05])
    b = r.x
    H = r.hess_inv
    se = np.sqrt(np.diag(H))
    return b, se


def main():
    V = []
    counts_ok = verify_counts()
    b, se = poisson_fit()
    g = b[1]
    doubling = np.log(2) / g
    proj = {yr: float(np.exp(b[0] + g * (yr - 2000))) for yr in (2030, 2050, 2085)}
    rate_now = float(np.exp(b[0] + g * 26))
    res = dict(source_counts_verified=counts_ok, growth_per_year=float(g), growth_se=float(se[1]),
               doubling_years=float(doubling), rate_2026_per_yr=rate_now, projected_rate_per_yr_if_trend_continues=proj)
    V.append(dict(test="G1 reported intake-incident trend (global catalogue)", value=f"x{np.exp(10*g):.2f} per decade, doubling {doubling:.0f} y",
                  criterion="INFO - reporting-biased; plan capacity on design density, not on trend", verdict="INFO",
                  detail=f"2026 fitted ~{rate_now:.1f}/yr; if trend continued: 2050 ~{proj[2050]:.0f}/yr, 2085 ~{proj[2085]:.0f}/yr (not a forecast)"))

    # SST season
    d = json.load(open(ROOT.parent / "00_data" / "raw" / "openmeteo_marine" / "marine_near.json"))["hourly"]
    t = np.array(d["time"], dtype="datetime64[h]")
    sst = np.array([x if x is not None else np.nan for x in d["sea_surface_temperature"]], float)
    day = t.astype("datetime64[D]")
    ud = np.unique(day)
    dmean = np.array([np.nanmean(sst[day == u]) if np.isfinite(sst[day == u]).any() else np.nan for u in ud])
    valid_days = np.isfinite(dmean).sum()
    season = {}
    for thr in (30.0, 32.0, 34.0):
        row = {}
        for label, dT in (("2022-25", 0.0), ("2050 +0.3C/dec", 0.3 * 2.6), ("2050 +0.5C/dec", 0.5 * 2.6),
                          ("2085 +0.3C/dec", 0.3 * 6.1), ("2085 +0.5C/dec", 0.5 * 6.1)):
            row[label] = float(np.nansum(dmean + dT >= thr) / valid_days * 365.25)
        season[f">={thr:.0f}C"] = row
    res["sst_valid_days"] = int(valid_days)
    res["season_days_per_year"] = season
    r32 = season[">=32C"]
    V.append(dict(test="G2 warmer water -> longer hot season (SST>=32 C proxy)", value=f"{r32['2022-25']:.0f} d/yr now -> {r32['2085 +0.5C/dec']:.0f} d/yr (2085, +0.5 C/dec)",
                  criterion="deployed-days margin: fatigue/energy/wear designed for 60 d/yr [V3 ~2 months]",
                  verdict="MARGINAL" if r32["2085 +0.5C/dec"] > 60 else "PASS",
                  detail="if blooms track hot season, duty rises; fatigue (A6) has large margin, corrosion (C7) and drum-wrap cycles (A8c) get worse"))
    V.append(dict(test="G3 SST 2085 vs material limits", value=f"max data {np.nanmax(sst):.1f} C + {0.5*6.1:.1f} C = {np.nanmax(sst)+0.5*6.1:.1f} C",
                  criterion="mesh/rail materials rated for >= 40 C seawater", verdict="FAIL" if np.nanmax(sst) + 3.05 > 38 else "MARGINAL",
                  detail="reinforces C7: specify titanium or polymer wetted parts"))

    # modular headroom
    line_cap_th = 2.0 * 0.05 * 1020 * 3.6     # t/h of bells per line (5 % solids by volume)
    rows = []
    for dens in (0.1, 0.3, 1.0, 2.0):
        for Q in (P.Q_UNIT, P.Q_UNIT_MAX):
            need = dens * Q * P.BELL_MASS * 0.9 * 3.6   # t/h
            rows.append(dict(density=dens, Q=Q, biomass_t_per_h=round(need, 0), lines=int(np.ceil(need / line_cap_th))))
    res["line_capacity_t_per_h"] = line_cap_th
    res["lines_needed"] = rows
    l03 = max(r["lines"] for r in rows if r["density"] == 0.3)
    l1 = max(r["lines"] for r in rows if r["density"] == 1.0)
    V.append(dict(test="G4 modular lift headroom", value=f"{line_cap_th:.0f} t/h per line; 0.3/m3 needs {l03} lines @172.5 m3/s, 1/m3 needs {l1}",
                  criterion="v3 pilot = 1 line per unit; design density 0.3/m3 at max flow", verdict="MARGINAL" if l03 > 1 else "PASS",
                  detail="gantry/screen scale with flow not density; lines (screw+pump+pipe) are the modular unit; reserve space for 2-3 lines per lane"))
    res["verdicts"] = V
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(res, open(HERE / "out" / "climate_results.json", "w"), indent=2)

    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    x = np.array([dd[0] for dd in DEC]); rate = np.array([dd[2] / dd[1] for dd in DEC])
    xx = np.linspace(1980, 2085, 100)
    ax[0].bar(x, rate, width=6, color="#5b8fc9", label="catalogue (13_)")
    ax[0].plot(xx, np.exp(b[0] + g * (xx - 2000)), "k--", lw=1, label="log-linear fit (not a forecast)")
    ax[0].set_yscale("log"); ax[0].set_ylabel("reported events / yr"); ax[0].legend(fontsize=7)
    ax[0].set_title("Intake jellyfish events (reporting-biased)", fontsize=9)
    for thr, c in ((30, "#5b8fc9"), (32, "#e39a4f"), (34, "#c33")):
        r = season[f">={thr}C"]
        ax[1].plot(list(r.keys()), list(r.values()), "o-", color=c, label=f"SST >= {thr} C")
    ax[1].tick_params(axis="x", labelsize=6, rotation=20); ax[1].set_ylabel("days / yr"); ax[1].legend(fontsize=7)
    ax[1].axhline(60, color="k", lw=0.8); ax[1].set_title("Hot-season length, near-site SST", fontsize=9)
    for Q, m in ((P.Q_UNIT, "o-"), (P.Q_UNIT_MAX, "s--")):
        rr = [r for r in rows if r["Q"] == Q]
        ax[2].plot([r["density"] for r in rr], [r["lines"] for r in rr], m, label=f"Q={Q} m3/s")
    ax[2].set_xlabel("density (ind/m3)"); ax[2].set_ylabel("lift lines per unit"); ax[2].legend(fontsize=7)
    ax[2].set_title(f"Modular lines ({line_cap_th:.0f} t/h each)", fontsize=9)
    fig.tight_layout(); fig.savefig(HERE / "figs" / "climate_future.png", dpi=150)
    for v in V:
        print(v["verdict"], v["test"], v["value"])
    print(json.dumps(season))


if __name__ == "__main__":
    main()
