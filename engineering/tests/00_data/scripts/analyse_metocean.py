"""Met-ocean analysis near the plant from downloaded raw files (data only; run with python3 -I).
Usage: python3 -I analyse_metocean.py <00_data dir>
Outputs CSV + PNG into <00_data>/out
"""
import json, sys, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = sys.argv[1]; R = os.path.join(D, "raw"); O = os.path.join(D, "out"); os.makedirs(O, exist_ok=True)
MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
ONSHORE_DEG = 160.0   # assumed: the plant coast trends ~070/250 deg, so onshore normal points ~160 deg (SSE)

def load_marine(f):
    j = json.load(open(f)); h = j["hourly"]
    df = pd.DataFrame(h); df["time"] = pd.to_datetime(df["time"]); df = df.set_index("time")
    df.attrs["lat"], df.attrs["lon"] = j["latitude"], j["longitude"]
    if "ocean_current_velocity" in df:
        sp = df["ocean_current_velocity"]/3.6          # km/h -> m/s
        th = np.deg2rad(df["ocean_current_direction"])  # direction the current flows TOWARD
        df["spd"] = sp; df["u"] = sp*np.sin(th); df["v"] = sp*np.cos(th)
    return df

res = {}
near = load_marine(os.path.join(R, "openmeteo_marine", "marine_near.json"))
off = load_marine(os.path.join(R, "openmeteo_marine", "marine_off.json"))
res["near_cell"] = [near.attrs["lat"], near.attrs["lon"]]; res["off_cell"] = [off.attrs["lat"], off.attrs["lon"]]
res["n_hours_near"] = int(near["spd"].notna().sum())
res["period"] = [str(near.index.min()), str(near.index.max())]

# ---------- monthly stats ----------
def q(x, p): return float(np.nanpercentile(x, p))
rows = []
for m in range(1, 13):
    s = near[near.index.month == m]; so = off[off.index.month == m]
    on = s["u"]*np.sin(np.deg2rad(ONSHORE_DEG)) + s["v"]*np.cos(np.deg2rad(ONSHORE_DEG))
    um, vm = s["u"].mean(), s["v"].mean()
    rows.append(dict(month=MON[m-1],
        cur_mean=s["spd"].mean(), cur_median=s["spd"].median(), cur_p90=q(s["spd"],90), cur_p99=q(s["spd"],99), cur_max=s["spd"].max(),
        resid_speed=np.hypot(um, vm), resid_toward_deg=(np.rad2deg(np.arctan2(um, vm)) % 360), resid_onshore=on.mean(),
        hs_mean=s["wave_height"].mean(), hs_median=s["wave_height"].median(), hs_p90=q(s["wave_height"],90), hs_p99=q(s["wave_height"],99), hs_max=s["wave_height"].max(),
        tp_mean=s["wave_period"].mean(), hs_off_p99=q(so["wave_height"],99), hs_off_max=so["wave_height"].max(),
        sst_mean=s["sea_surface_temperature"].mean(), sst_min=s["sea_surface_temperature"].min(), sst_max=s["sea_surface_temperature"].max(),
        cur_off_median=so["spd"].median()))
mt = pd.DataFrame(rows); mt.round(4).to_csv(os.path.join(O, "metocean_monthly_openmeteo.csv"), index=False)

# Oct-Nov block
on_all = near["u"]*np.sin(np.deg2rad(ONSHORE_DEG)) + near["v"]*np.cos(np.deg2rad(ONSHORE_DEG))
on_daily = on_all.resample("D").mean()
for name, mm in [("all", range(1,13)), ("OctNov", [10, 11])]:
    s = near[near.index.month.isin(mm)]; o = on_all[on_all.index.month.isin(mm)]
    od = on_daily[on_daily.index.month.isin(mm)]
    res[name] = dict(cur_median=float(s["spd"].median()), cur_mean=float(s["spd"].mean()), cur_p90=q(s["spd"],90), cur_p99=q(s["spd"],99),
                     cur_max=float(s["spd"].max()), resid_vec=float(np.hypot(s["u"].mean(), s["v"].mean())),
                     resid_toward=float(np.rad2deg(np.arctan2(s["u"].mean(), s["v"].mean())) % 360),
                     onshore_mean=float(o.mean()), onshore_daily_p10=q(od,10), onshore_daily_p50=q(od,50), onshore_daily_p90=q(od,90),
                     frac_days_onshore=float((od > 0).mean()),
                     hs_median=float(s["wave_height"].median()), hs_p90=q(s["wave_height"],90), hs_p99=q(s["wave_height"],99), hs_max=float(s["wave_height"].max()),
                     sst_mean=float(s["sea_surface_temperature"].mean()), sst_min=float(s["sea_surface_temperature"].min()), sst_max=float(s["sea_surface_temperature"].max()))

# ---------- tidal harmonic fit (least squares) on u,v ----------
FREQ = {"M2": 12.4206012, "S2": 12.0, "N2": 12.65834751, "K2": 11.96723606, "K1": 23.93447213, "O1": 25.81933871, "P1": 24.06588766, "M4": 6.210300601}
t = (near.index - near.index[0]).total_seconds().values/3600.0
ok = near["u"].notna().values
cols = [np.ones(ok.sum())]
for k, P in FREQ.items():
    w = 2*np.pi/P; cols += [np.cos(w*t[ok]), np.sin(w*t[ok])]
A = np.column_stack(cols)
tide = {}
fit = {}
for comp in ["u", "v"]:
    c, *_ = np.linalg.lstsq(A, near[comp].values[ok], rcond=None); fit[comp] = c
uu = fit["u"]; vv = fit["v"]
for i, k in enumerate(FREQ):
    au, bu = uu[1+2*i], uu[2+2*i]; av, bv = vv[1+2*i], vv[2+2*i]
    # tidal ellipse: velocity vector over one cycle; major/minor semi-axes
    ph = np.linspace(0, 2*np.pi, 721)
    U = au*np.cos(ph)+bu*np.sin(ph); V = av*np.cos(ph)+bv*np.sin(ph); sp = np.hypot(U, V)
    j = sp.argmax()
    tide[k] = dict(major=float(sp.max()), minor=float(sp.min()), major_axis_toward_deg=float(np.rad2deg(np.arctan2(U[j], V[j])) % 180))
pred_u = A @ uu; pred_v = A @ vv
tid_u = pred_u-uu[0]; tid_v = pred_v-vv[0]
var_tot = np.nanvar(near["u"].values[ok]) + np.nanvar(near["v"].values[ok])
var_tid = np.var(tid_u) + np.var(tid_v)
res["tide"] = tide
res["tidal_variance_fraction"] = float(var_tid/var_tot)
res["tidal_only_speed_median"] = float(np.median(np.hypot(tid_u, tid_v)))
res["tidal_only_speed_p90"] = float(np.percentile(np.hypot(tid_u, tid_v), 90))
res["mean_flow_fit"] = [float(uu[0]), float(vv[0])]
# equivalent single-sinusoid U0 for the twin: U0 such that median|U0 sin| = observed median -> U0 = median/sin(pi/4)
res["U0_equiv_from_median_total"] = float(res["all"]["cur_median"]/np.sin(np.pi/4))
res["U0_equiv_from_median_tidal"] = float(res["tidal_only_speed_median"]/np.sin(np.pi/4))
# sea level tidal range
if "sea_level_height_msl" in near:
    sl = near["sea_level_height_msl"].dropna(); d = sl.resample("D")
    rng = (d.max()-d.min())
    res["sea_level_daily_range"] = dict(median=float(rng.median()), p90=float(rng.quantile(.9)), max=float(rng.max()))

# ---------- ERA5 winds ----------
j = json.load(open(os.path.join(R, "openmeteo_era5", "era5_wind.json"))); w = pd.DataFrame(j["hourly"])
w["time"] = pd.to_datetime(w["time"]); w = w.set_index("time")
wrows = []
for m in range(1, 13):
    s = w[w.index.month == m]
    th = np.deg2rad(s["wind_direction_10m"]+180)  # toward
    wrows.append(dict(month=MON[m-1], ws_mean=s["wind_speed_10m"].mean(), ws_p90=q(s["wind_speed_10m"],90), ws_p99=q(s["wind_speed_10m"],99),
        ws_max=s["wind_speed_10m"].max(), gust_max=s["wind_gusts_10m"].max(), frac_gt10ms=(s["wind_speed_10m"]>10).mean(),
        mean_wind_toward_deg=(np.rad2deg(np.arctan2((s["wind_speed_10m"]*np.sin(th)).mean(), (s["wind_speed_10m"]*np.cos(th)).mean())) % 360),
        onshore_wind_mean=(s["wind_speed_10m"]*np.cos(th-np.deg2rad(ONSHORE_DEG))).mean()))
wt = pd.DataFrame(wrows); wt.round(4).to_csv(os.path.join(O, "wind_monthly_era5.csv"), index=False)
res["era5_period"] = [str(w.index.min()), str(w.index.max())]
res["era5_windage_3pct_onshore_OctNov"] = float(0.03*wt.loc[wt.month.isin(["Oct","Nov"]), "onshore_wind_mean"].mean())

# ---------- NOAA OISST ----------
import glob
fos = sorted(f for f in glob.glob(os.path.join(R, "noaa_oisst", "oisst_*.csv")) if os.path.getsize(f) > 1000)
if fos:
    s = pd.concat([pd.read_csv(f, skiprows=[1]) for f in fos]); s["time"] = pd.to_datetime(s["time"]); s = s.set_index("time").sort_index()["sst"].dropna()
    s = s[~s.index.duplicated()]; s.index = s.index.tz_localize(None)
    om = s.groupby(s.index.month).agg(["mean", "min", "max"]); om.index = MON
    ann = s.groupby(s.index.year).agg(["mean","max"])
    om.round(3).to_csv(os.path.join(O, "sst_monthly_oisst.csv")); ann.round(3).to_csv(os.path.join(O, "sst_annual_oisst.csv"))
    on_ = s[s.index.month.isin([10, 11])]
    yr = on_.groupby(on_.index.year).mean()
    trend = np.polyfit(yr.index.values, yr.values, 1)[0]*10
    res["oisst"] = dict(period=[str(s.index.min()), str(s.index.max())], OctNov_mean=float(on_.mean()), OctNov_min=float(on_.min()), OctNov_max=float(on_.max()),
                        annual_max=float(s.max()), annual_min=float(s.min()), days_above_35=int((s>35).sum()), OctNov_trend_C_per_decade=float(trend),
                        Oct_mean=float(s[s.index.month==10].mean()), Nov_mean=float(s[s.index.month==11].mean()))
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].fill_between(range(12), om["min"], om["max"], color="#9ecae1", label="daily min–max")
    ax[0].plot(range(12), om["mean"], "o-", color="#08519c", label="OISST mean")
    ax[0].plot(range(12), mt["sst_mean"], "s--", color="#e6550d", label="Open-Meteo/CMEMS 2022–25")
    ax[0].axvspan(8.5, 10.5, color="#fdd0a2", alpha=.4, label="bloom season Oct–Nov")
    ax[0].set_xticks(range(12)); ax[0].set_xticklabels(MON, fontsize=8); ax[0].set_ylabel("SST (°C)"); ax[0].legend(fontsize=7); ax[0].set_title("SST near the plant, monthly")
    ax[1].plot(yr.index, yr.values, "o-", color="#08519c"); ax[1].set_title(f"Oct–Nov mean SST by year (trend {trend:+.2f} °C/decade)"); ax[1].set_ylabel("°C")
    fig.tight_layout(); fig.savefig(os.path.join(O, "fig_sst.png"), dpi=140); plt.close(fig)
else:
    res["oisst"] = "NOT AVAILABLE (download failed)"

# ---------- figures ----------
x = range(12)
fig, ax = plt.subplots(2, 2, figsize=(12, 7.5))
a = ax[0, 0]
a.plot(x, mt["cur_median"], "o-", label="median |u|"); a.plot(x, mt["cur_p90"], "^-", label="p90"); a.plot(x, mt["cur_p99"], "v-", label="p99")
a.axhline(0.083, color="k", ls="--", lw=1, label="twin median 0.083"); a.axhline(0.117, color="r", ls=":", lw=1.2, label="twin U0 0.117")
a.set_xticks(x); a.set_xticklabels(MON, fontsize=8); a.set_ylabel("m/s"); a.set_title("Surface current speed (CMEMS SMOC via Open-Meteo)"); a.legend(fontsize=7)
a = ax[0, 1]
a.bar(x, mt["resid_onshore"]*100, color=["#e6550d" if v > 0 else "#3182bd" for v in mt["resid_onshore"]])
a.axhspan(1, 3, color="grey", alpha=.25, label="twin onshore drift 1–3 cm/s"); a.axhline(0, color="k", lw=.8)
a.set_xticks(x); a.set_xticklabels(MON, fontsize=8); a.set_ylabel("cm/s toward 160° (onshore)"); a.set_title("Monthly mean onshore residual"); a.legend(fontsize=7)
a = ax[1, 0]
a.plot(x, mt["hs_median"], "o-", label="Hs median"); a.plot(x, mt["hs_p99"], "v-", label="Hs p99"); a.plot(x, mt["hs_max"], "k^", label="Hs max (nearshore)")
a.plot(x, mt["hs_off_max"], "r^", label="Hs max (24.6°N offshore)")
a.set_xticks(x); a.set_xticklabels(MON, fontsize=8); a.set_ylabel("m"); a.set_title("Significant wave height"); a.legend(fontsize=7)
a = ax[1, 1]
a.plot(x, wt["ws_mean"], "o-", label="mean"); a.plot(x, wt["ws_p99"], "v-", label="p99"); a.plot(x, wt["ws_max"], "k^", label="max")
a.set_xticks(x); a.set_xticklabels(MON, fontsize=8); a.set_ylabel("m/s at 10 m"); a.set_title("ERA5 wind 2015–2025"); a.legend(fontsize=7)
fig.tight_layout(); fig.savefig(os.path.join(O, "fig_metocean_monthly.png"), dpi=140); plt.close(fig)

cf = [np.ones(len(t))]
for k, P in FREQ.items():
    w_ = 2*np.pi/P; cf += [np.cos(w_*t), np.sin(w_*t)]
full_u = np.column_stack(cf) @ uu
# current speed distribution vs twin sinusoid
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
sp = near["spd"].dropna().values
ax[0].hist(sp, bins=60, density=True, alpha=.6, label="observed (model) hourly speed")
ph = np.random.default_rng(0).uniform(0, 2*np.pi, 200000)
ax[0].hist(np.abs(0.117*np.sin(ph)), bins=60, density=True, histtype="step", color="r", label="twin |0.117 sin ωt|")
ax[0].set_xlabel("m/s"); ax[0].legend(fontsize=7); ax[0].set_title("Current speed distribution")
wk = near.loc["2024-10-01":"2024-10-15"]
ax[1].plot(wk.index, wk["u"], lw=.8, label="u (east)"); ax[1].plot(wk.index, wk["v"], lw=.8, label="v (north)")
ax[1].plot(wk.index, full_u[(near.index >= "2024-10-01") & (near.index < "2024-10-16")], "k--", lw=.6, label="harmonic fit u")
ax[1].set_title("1–15 Oct 2024 components"); ax[1].legend(fontsize=7); ax[1].tick_params(axis="x", labelsize=7, rotation=30)
fig.tight_layout(); fig.savefig(os.path.join(O, "fig_current_distribution.png"), dpi=140); plt.close(fig)

json.dump(res, open(os.path.join(O, "metocean_summary.json"), "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
print(mt.round(3).to_string()); print(wt.round(2).to_string())
