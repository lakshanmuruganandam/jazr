"""Biology / wildlife / HYCOM / drift-persistence analysis (data only; run with python3 -I).
Usage: python3 -I analyse_bio_extra.py <00_data dir>
"""
import json, sys, os, glob, collections
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = sys.argv[1]; R = os.path.join(D, "raw"); O = os.path.join(D, "out")
BLAT, BLON = 23.96, 52.26
MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
ONSHORE_DEG = 160.0
res = {}

def hav(lat1, lon1, lat2, lon2):
    p = np.pi/180; a = np.sin((lat2-lat1)*p/2)**2 + np.cos(lat1*p)*np.cos(lat2*p)*np.sin((lon2-lon1)*p/2)**2
    return 2*6371.0*np.arcsin(np.sqrt(a))

# ---------- jellyfish occurrences (OBIS + GBIF, Gulf box 47-57.5E, 23-30.5N) ----------
rows = []
for f, src in [("obis/obis_Rhizostomeae.json", "OBIS"), ("gbif/gbif_Rhizostomeae.json", "GBIF")]:
    j = json.load(open(os.path.join(R, f)))
    for r in j["results"]:
        lat, lon = r.get("decimalLatitude"), r.get("decimalLongitude")
        d = r.get("eventDate") or ""
        rows.append(dict(source=src, species=r.get("scientificName") or r.get("species"), lat=lat, lon=lon, date=str(d)[:10],
                         dataset=r.get("datasetName") or r.get("datasetKey"), id=r.get("occurrenceID") or r.get("key")))
jf = pd.DataFrame(rows).dropna(subset=["lat", "lon"])
jf["month"] = pd.to_datetime(jf["date"].str[:10], errors="coerce").dt.month
jf["dist_site_km"] = hav(BLAT, BLON, jf["lat"].astype(float), jf["lon"].astype(float))
jf["genus"] = jf["species"].astype(str).str.split().str[0]
jf.sort_values("dist_site_km").to_csv(os.path.join(O, "rhizostome_occurrences_gulf.csv"), index=False)
jf["lat3"] = jf["lat"].astype(float).round(2); jf["lon3"] = jf["lon"].astype(float).round(2)
cat = jf[jf.genus == "Catostylus"].drop_duplicates(subset=["lat3", "lon3", "date"])
cat.to_csv(os.path.join(O, "catostylus_occurrences_gulf_dedup.csv"), index=False)
res["catostylus_records_unique"] = int(len(cat))
res["catostylus_species"] = cat["species"].value_counts().to_dict()
res["catostylus_by_month"] = {MON[int(k)-1]: int(v) for k, v in cat["month"].dropna().value_counts().sort_index().items()}
res["catostylus_within_100km"] = int((cat.dist_site_km < 100).sum())
res["catostylus_nearest_km"] = float(cat.dist_site_km.min())

# ---------- turtle telemetry (OBIS-SEAMAP, west Abu Dhabi box 51-54.5E, 23.5-25.5N) ----------
tj = json.load(open(os.path.join(R, "obis/obis_Cheloniidae_westAD.json")))["results"]
t = pd.DataFrame(tj)
t["time"] = pd.to_datetime(t["eventDate"], errors="coerce")
t = t.dropna(subset=["time", "decimalLatitude", "decimalLongitude"])
t["dist_site_km"] = hav(BLAT, BLON, t.decimalLatitude, t.decimalLongitude)
res["turtle_records"] = int(len(t)); res["turtle_species"] = t.scientificName.value_counts().to_dict()
res["turtle_datasets"] = t.datasetName.value_counts().to_dict()
res["turtle_records_within_20km_site"] = int((t.dist_site_km < 20).sum())
res["turtle_records_within_50km_site"] = int((t.dist_site_km < 50).sum())
res["turtle_min_dist_site_km"] = float(t.dist_site_km.min())
sp = []
if "organismID" in t:
    for oid, g in t.dropna(subset=["organismID"]).sort_values("time").groupby("organismID"):
        g = g.drop_duplicates("time")
        dt = g.time.diff().dt.total_seconds().values[1:]
        dd = hav(g.decimalLatitude.values[:-1], g.decimalLongitude.values[:-1], g.decimalLatitude.values[1:], g.decimalLongitude.values[1:])*1000
        m = (dt >= 3600) & (dt <= 24*3600)
        for a, b in zip(dd[m], dt[m]): sp.append(dict(organismID=oid, dt_h=b/3600, dist_m=a, speed=a/b))
sp = pd.DataFrame(sp)
if len(sp):
    sp = sp[sp.speed < 3.0]   # drop implausible (Argos location error) fixes
    sp.to_csv(os.path.join(O, "turtle_displacement_speeds.csv"), index=False)
    res["turtle_speed_n_pairs"] = int(len(sp)); res["turtle_n_individuals"] = int(sp.organismID.nunique())
    res["turtle_speed_median_ms"] = float(sp.speed.median()); res["turtle_speed_p90_ms"] = float(sp.speed.quantile(.9))
    res["turtle_speed_p99_ms"] = float(sp.speed.quantile(.99))

dg = json.load(open(os.path.join(R, "obis/obis_Dugong.json")))["results"]
res["dugong_obis_records_gulf"] = len(dg)

# ---------- wet mass vs diameter (published relations only) ----------
D_cm = np.linspace(5, 45, 81)
panguil = 1.12*D_cm**1.93/1000      # kg; Catostylus sp. Panguil Bay fit (WW g = 1.12 BD^1.93), as read in agent_enec_science.md
iso = 0.27*(D_cm/17)**3             # isometric from 0.27 kg at 17 cm (same source point)
aravind = {"Jan":14.3,"Feb":13.9,"Mar":11.3,"Apr":12.4,"May":14.1,"Jun":15.9,"Jul":14.9,"Aug":10.7,"Sep":10.1,"Oct":6.5,"Nov":11.8,"Dec":18.3}
mrow = [dict(month=k, bell_cm=v, wetmass_panguil_kg=1.12*v**1.93/1000, wetmass_isometric_kg=0.27*(v/17)**3) for k, v in aravind.items()]
pd.DataFrame(mrow).round(4).to_csv(os.path.join(O, "uae_bell_size_to_mass.csv"), index=False)
res["mass_at_UAE_Oct_Nov_mean_bell_kg"] = {r["month"]: [round(r["wetmass_panguil_kg"], 3), round(r["wetmass_isometric_kg"], 3)] for r in mrow if r["month"] in ("Oct", "Nov")}
fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
ax[0].plot(D_cm, panguil, label="Panguil Bay fit 1.12·D^1.93 g")
ax[0].plot(D_cm, iso, "--", label="isometric from 0.27 kg @17 cm")
ax[0].axhline(3, color="r", ls=":", label="JAZR typical 3 kg"); ax[0].axhline(1.7, color="k", ls="-.", label="Oman Sea C. perezi max 1.7 kg (n=503)")
ax[0].axhline(0.326, color="grey", ls="-.", label="Oman Sea C. perezi mean 0.33 kg")
ax[0].axvspan(30, 45, color="#fdd0a2", alpha=.4, label="ENEC brief 30–45 cm")
ax[0].set_xlabel("bell diameter (cm)"); ax[0].set_ylabel("wet mass (kg)"); ax[0].legend(fontsize=7); ax[0].set_title("Catostylus wet mass vs size")
ax[1].bar(range(12), list(aravind.values()), color=["#e6550d" if k in ("Oct", "Nov") else "#9ecae1" for k in aravind])
ax[1].set_xticks(range(12)); ax[1].set_xticklabels(MON, fontsize=8); ax[1].set_ylabel("mean bell diameter (cm)")
ax[1].set_title("UAE Catostylus mean bell by month (Aravind et al. 2023, n=130)")
fig.tight_layout(); fig.savefig(os.path.join(O, "fig_jellyfish_size_mass.png"), dpi=140); plt.close(fig)

# ---------- load scenarios: Q=100 m3/s per unit ----------
L = []
for dens in (0.01, 0.1, 0.3, 1.0):
    for mname, m in (("JAZR 3 kg", 3.0), ("C. perezi max 1.7 kg", 1.7), ("C. perezi mean 0.33 kg", 0.326)):
        L.append(dict(density_ind_m3=dens, mass_case=mname, t_per_h_per_unit=dens*100*m*3600/1000, t_per_day_4units=dens*100*m*86400*4/1000))
pd.DataFrame(L).round(2).to_csv(os.path.join(O, "intake_load_scenarios.csv"), index=False)
# implied density for real events at 4 x 100 m3/s (the plant-scale) -- illustration only, Shin Hanul flow differs
ev = {"Shin Hanul 17 Jul 2024 (202 t/day)": 202, "Shin Hanul 4-day mean (428 t/4 d)": 107, "Hanbit 2009 upper (40 t/day)": 40, "Hanbit 2009 lower (10 t/day)": 10}
res["implied_density_if_at_400m3s"] = {k: {f"{m} kg": v*1000/(m*400*86400) for m in (3.0, 0.326)} for k, v in ev.items()}

# ---------- HYCOM (no tides) Oct-Nov surface currents ----------
hs = []
for f in sorted(glob.glob(os.path.join(R, "hycom", "hycom_*OctNov.csv"))):
    h = pd.read_csv(f); h.columns = ["time", "lat", "lon", "z", "u", "v"]
    if len(h) < 10: continue
    h["year"] = os.path.basename(f)[6:10]; hs.append(h)
if hs:
    h = pd.concat(hs); h["time"] = pd.to_datetime(h["time"])
    sc = 0.001 if h[["u", "v"]].abs().max().max() > 5 else 1.0   # raw packed ints (scale_factor 0.001) if not unpacked
    h["u"] *= sc; h["v"] *= sc; h["spd"] = np.hypot(h.u, h.v)
    h["on"] = h.u*np.sin(np.deg2rad(ONSHORE_DEG)) + h.v*np.cos(np.deg2rad(ONSHORE_DEG))
    h.to_csv(os.path.join(O, "hycom_octnov_surface_currents.csv"), index=False)
    res["hycom_scale_applied"] = sc
    res["hycom_OctNov"] = dict(years=sorted(h.year.unique().tolist()), n=int(len(h)), spd_median=float(h.spd.median()), spd_p90=float(h.spd.quantile(.9)),
        mean_u=float(h.u.mean()), mean_v=float(h.v.mean()), onshore_mean=float(h.on.mean()),
        onshore_daily_p90=float(h.set_index("time").on.resample("D").mean().dropna().quantile(.9)),
        by_year_onshore={y: float(g.on.mean()) for y, g in h.groupby("year")})

# ---------- persistence of onshore drift (Open-Meteo/CMEMS SMOC) ----------
j = json.load(open(os.path.join(R, "openmeteo_marine", "marine_near.json")))["hourly"]
m = pd.DataFrame(j); m["time"] = pd.to_datetime(m["time"]); m = m.set_index("time")
spd = m.ocean_current_velocity/3.6; th = np.deg2rad(m.ocean_current_direction)
on = spd*np.sin(th)*np.sin(np.deg2rad(ONSHORE_DEG)) + spd*np.cos(th)*np.cos(np.deg2rad(ONSHORE_DEG))
on_on = on[on.index.month.isin([10, 11])]
pers = {}
for win in (1, 3, 10):
    r = on.rolling(f"{win*24}h", min_periods=int(win*24*0.9)).mean()
    r = r[r.index.month.isin([10, 11])].dropna()
    pers[f"{win}d"] = dict(p50=float(r.quantile(.5)), p90=float(r.quantile(.9)), p99=float(r.quantile(.99)), max=float(r.max()))
res["onshore_running_mean_OctNov_ms"] = pers
fig, ax = plt.subplots(figsize=(7, 3.6))
for win, c in ((1, "#9ecae1"), (3, "#3182bd"), (10, "#08519c")):
    r = on.rolling(f"{win*24}h", min_periods=int(win*24*0.9)).mean(); r = r[r.index.month.isin([10, 11])].dropna()*100
    ax.hist(r, bins=50, histtype="step", lw=1.6, color=c, density=True, label=f"{win}-day running mean")
ax.axvspan(1, 3, color="grey", alpha=.25, label="twin 1–3 cm/s")
ax.set_xlabel("onshore residual (cm/s, toward 160°), Oct–Nov 2022–25"); ax.legend(fontsize=7); ax.set_title("How strong and persistent is onshore drift?")
fig.tight_layout(); fig.savefig(os.path.join(O, "fig_onshore_persistence.png"), dpi=140); plt.close(fig)

# ---------- occurrence map ----------
fig, ax = plt.subplots(figsize=(7.5, 5.5))
ax.scatter(t.decimalLongitude, t.decimalLatitude, s=2, c="#74c476", alpha=.4, label=f"turtle telemetry fixes (n={len(t)})")
for g, c in (("Catostylus", "#e6550d"), ("Cassiopea", "#756bb1"), ("Cotylorhiza", "#3182bd"), ("Marivagia", "#636363")):
    s = jf[jf.genus == g].drop_duplicates(subset=["lat3", "lon3", "date"]); ax.scatter(s.lon, s.lat, s=18, c=c, edgecolor="k", lw=.3, label=f"{g} (n={len(s)} unique)")
ax.plot(BLON, BLAT, "k*", ms=16, label="the plant")
ax.set_xlim(47, 57.5); ax.set_ylim(23, 30.5); ax.set_xlabel("lon"); ax.set_ylabel("lat"); ax.legend(fontsize=7, loc="upper right")
ax.set_title("Gulf rhizostome records (OBIS/GBIF) + green turtle fixes", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(O, "fig_occurrence_map.png"), dpi=140); plt.close(fig)

json.dump(res, open(os.path.join(O, "bio_extra_summary.json"), "w"), indent=1, default=float)
print(json.dumps(res, indent=1, default=float))
