"""C. Extreme events: operating envelope and survival (stowed) envelope.

Data: Open-Meteo ERA5 hourly wind 2015-2025 (23.75N 52.25E) and Open-Meteo marine hourly
2022-2025 near-site (24.04N 52.21E) / offshore (24.63N 52.29E) from TESTS/00_data/raw.
Literature: see common/params.py SOURCES. Reanalysis smooths extremes (ERA5 gusts and
0.04-0.25 deg wave models under-estimate local peaks) -> data EVA is a LOWER bound; design
uses the larger of data-EVA and literature/code values.
"""
import json, sys, pathlib
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from common import params as P
from common import gantry as GT

RAW = ROOT.parent / "00_data" / "raw"


def load(path, keys):
    d = json.load(open(path))["hourly"]
    t = np.array(d["time"], dtype="datetime64[h]")
    out = {k: np.array([x if x is not None else np.nan for x in d[k]], float) for k in keys}
    return t, out


def gumbel_rl(annual_max, T):
    loc, scale = stats.gumbel_r.fit(annual_max)
    return loc + scale * -np.log(-np.log(1 - 1 / np.asarray(T)))


def pot_gpd(x, t, q=0.99, decl_h=48, T=(10, 50, 100)):
    ok = np.isfinite(x)
    x, t = x[ok], t[ok]
    u = np.quantile(x, q)
    idx = np.where(x > u)[0]
    peaks = []
    last = -10**9
    for i in idx:
        if i - last > decl_h or not peaks:
            peaks.append(i)
        elif x[i] > x[peaks[-1]]:
            peaks[-1] = i
        last = i
    ex = x[peaks] - u
    c, loc, sc = stats.genpareto.fit(ex, floc=0)
    years = (t[-1] - t[0]).astype(float) / 8766.0
    lam = len(peaks) / years
    rl = {Ti: float(u + stats.genpareto.ppf(1 - 1 / (lam * Ti), c, 0, sc)) for Ti in T}
    return rl, dict(threshold=float(u), n_peaks=len(peaks), years=round(years, 2), shape=float(c))


def wave_dp_amp(H, T, d=7.5, obliq=30.0, kmesh=0.78):
    """Peak wave-induced dP on a deployed mesh (depth-mean normal orbital velocity on top of 0.1 m/s through-flow)."""
    k = GT.wave_number(T, d); w = 2 * np.pi / T
    zz = np.linspace(-d, 0, 30)
    u = np.mean(w * H / 2 * np.cosh(k * (zz + d)) / np.sinh(k * d)) * np.sin(np.radians(obliq))
    v0 = P.V_APPROACH_SCREEN
    return kmesh * 0.5 * P.RHO_W * ((v0 + u) ** 2 - v0**2)


def main():
    V = []
    tw, w = load(RAW / "openmeteo_era5" / "era5_wind.json", ["wind_speed_10m", "wind_gusts_10m", "wind_direction_10m", "temperature_2m"])
    tn, mn = load(RAW / "openmeteo_marine" / "marine_near.json",
                  ["wave_height", "wave_period", "sea_surface_temperature", "ocean_current_velocity", "sea_level_height_msl"])
    to, mo = load(RAW / "openmeteo_marine" / "marine_off.json", ["wave_height", "wave_period", "sea_surface_temperature"])
    res = {}

    # ---- 1. wind ----
    yrs = tw.astype("datetime64[Y]").astype(int) + 1970
    amax_g = np.array([np.nanmax(w["wind_gusts_10m"][yrs == y]) for y in np.unique(yrs)])
    rl_g = gumbel_rl(amax_g, [10, 50, 100])
    nw = (w["wind_direction_10m"] >= 270) | (w["wind_direction_10m"] <= 360)
    shamal = (w["wind_direction_10m"] >= 280) & (w["wind_direction_10m"] <= 360)
    frac_op_exceed = float(np.mean(w["wind_gusts_10m"] > P.WIND_OPERATE_GUST))
    frac_15 = float(np.mean(w["wind_gusts_10m"] > 15.0))
    res["wind"] = dict(era5_gust_annual_max=amax_g.tolist(), gumbel_gust_10_50_100=[round(x, 1) for x in rl_g],
                       code_design_gust=P.WIND_SURVIVAL_GUST, frac_hours_gust_gt_20=frac_op_exceed, frac_hours_gust_gt_15=frac_15,
                       shamal_share_of_gusts_gt_12=float(np.mean(shamal[w["wind_gusts_10m"] > 12])))
    V.append(dict(test="C1 wind survival (stowed): design gust vs data 100-yr",
                  value=f"design {P.WIND_SURVIVAL_GUST} m/s; ERA5 Gumbel 100-yr {rl_g[2]:.1f} m/s",
                  criterion="design >= max(code 38-45 m/s, data EVA); FEA SURV cases pass at 45 m/s (A1)",
                  verdict="PASS" if P.WIND_SURVIVAL_GUST >= rl_g[2] else "FAIL",
                  detail="ERA5 under-estimates gusts; Abu Dhabi municipal basic wind speed not found -> confirm with ADM/DMT"))
    V.append(dict(test="C2 wind operating limit (roll-down/up <= 20 m/s gust)", value=f"{100*frac_op_exceed:.3f} % of hours exceed",
                  criterion="availability >= 99 % of hours", verdict="PASS" if frac_op_exceed < 0.01 else "MARGINAL",
                  detail=f"gust>15 m/s {100*frac_15:.2f} % hours; shamal (280-360 deg) share of gusts>12 m/s {100*res['wind']['shamal_share_of_gusts_gt_12']:.0f} %"))

    # ---- 2. waves ----
    wav = {}
    for nm, t_, m_ in (("near", tn, mn), ("off", to, mo)):
        rl, meta = pot_gpd(m_["wave_height"], t_)
        wav[nm] = dict(rl_Hs=rl, meta=meta, max=float(np.nanmax(m_["wave_height"])))
    res["waves"] = wav
    V.append(dict(test="C3 100-yr Hs: data POT vs design", value=f"design Hs100 {P.HS100} m; data POT near {wav['near']['rl_Hs'][100]:.2f} m, off {wav['off']['rl_Hs'][100]:.2f} m",
                  criterion="design >= literature 3.0-4.5 m (9-16 m depth, Neelamani) and data EVA",
                  verdict="PASS" if P.HS100 >= max(wav['near']['rl_Hs'][100], wav['off']['rl_Hs'][100]) else "FAIL",
                  detail="only 4 years of data -> data EVA is indicative; literature governs"))
    # operating sea state limit from wave dP noise
    Hgrid = np.linspace(0.1, 4, 200)
    dp = np.array([wave_dp_amp(1.86 * h, 4.5) for h in Hgrid])  # Hmax in an hour, T~4.5 s (data p99 4.3 s)
    Hs_noise = float(Hgrid[np.argmax(dp > 0.5 * P.DP_TRIP)]) if (dp > 0.5 * P.DP_TRIP).any() else 4.0
    Hs_hard = float(Hgrid[np.argmax(dp > P.DP_HARD)]) if (dp > P.DP_HARD).any() else 4.0
    exceed_noise = float(np.nanmean(mn["wave_height"] > Hs_noise))
    res["operating_waves"] = dict(Hs_where_wave_dP_peak_reaches_half_trip=Hs_noise, Hs_where_peak_reaches_hard_limit=Hs_hard,
                                  frac_hours_near_exceed=exceed_noise)
    V.append(dict(test="C4 deployed-screen wave dP envelope", value=f"Hs {Hs_noise:.2f} m -> peak wave dP = 0.5 x trip; Hs {Hs_hard:.2f} m -> hard limit",
                  criterion="filter needed if Hs_noise < data p99 Hs (0.88 m); deployed survival Hs > op Hs",
                  verdict="INFO" if Hs_noise > 0.88 else "MARGINAL",
                  detail=f"{100*exceed_noise:.2f} % of hours nearshore exceed Hs {Hs_noise:.2f} m (unsheltered); spikes are periodic 2-6 s -> D filter test"))

    # ---- 3. water level, SLR, air gap, low tide ----
    sl = mn["sea_level_height_msl"]
    res["sea_level_model"] = dict(min=float(np.nanmin(sl)), max=float(np.nanmax(sl)), p001=float(np.nanquantile(sl, 0.001)),
                                  p999=float(np.nanquantile(sl, 0.999)))
    rows = []
    for scen, slr in P.SLR_2085.items():
        swl = P.HAT_Z + P.SURGE100 + slr
        for site, kt in (("inner gantry (sheltered Kt=0.5 ASM)", 0.5), ("outer guide line (exposed)", 1.0)):
            d = swl - P.SEABED_Z
            Hmax = min(1.86 * P.HS100 * kt, 0.78 * d)
            crest = swl + 0.75 * Hmax  # near-breaking crest ~0.7-0.8 H
            gap = P.DECK_SOFFIT_Z - crest
            rows.append(dict(scenario=scen, site=site, SWL=round(swl, 2), Hmax=round(Hmax, 2), crest=round(crest, 2),
                             air_gap=round(gap, 2), needed_deck_soffit=round(crest + 1.0, 2)))
    res["air_gap"] = rows
    for r in rows:
        if r["scenario"] in ("SSP5-8.5 median", "low-confidence high-end"):
            V.append(dict(test=f"C5 air gap 2085 {r['scenario']} - {r['site']}", value=f"{r['air_gap']} m",
                          criterion="crest below deck soffit +5.6 m MSL with >= 1.0 m margin [ENG]",
                          verdict="PASS" if r["air_gap"] >= 1.0 else ("MARGINAL" if r["air_gap"] >= 0 else "FAIL"),
                          detail=f"SWL {r['SWL']} m, Hmax {r['Hmax']} m, crest {r['crest']} m; raise soffit to {r['needed_deck_soffit']} m MSL"))
    # low tide: lane & screen velocities
    lt = []
    for bed in (-5.5, -7.5):
        for q in (P.Q_UNIT, P.Q_UNIT_MAX):
            h = P.LAT_Z - bed
            h0 = 0 - bed
            area = P.SCREEN_AREA * h / h0  # 1000 m2 provided at MSL depth [V3], shrinks with water level
            lt.append(dict(bed=bed, Q=q, depth_LAT=round(h, 2), lane_v=round(q / (P.LANE_W * h), 2),
                           screen_v=round(q / area, 3)))
    res["low_tide"] = lt
    worst = max(x["screen_v"] for x in lt if x["Q"] == P.Q_UNIT)
    worstmax = max(x["screen_v"] for x in lt)
    V.append(dict(test="C6 low tide (LAT) screen approach velocity at nominal 100 m3/s", value=worst,
                  criterion="<= 0.12 m/s (NMFS active screen)", verdict="PASS" if worst <= 0.12 else ("MARGINAL" if worst <= 0.15 else "FAIL"),
                  detail=json.dumps(lt)))
    V.append(dict(test="C6b low tide screen velocity at max 172.5 m3/s", value=worstmax, criterion="<= 0.12 m/s",
                  verdict="PASS" if worstmax <= 0.12 else ("MARGINAL" if worstmax <= 0.15 else "FAIL"),
                  detail="relief: add bays/lengthen line for low-water max-flow, or accept higher approach at LAT"))

    # ---- 4. temperature ----
    sst = np.concatenate([mn["sea_surface_temperature"], mo["sea_surface_temperature"]])
    res["temperature"] = dict(sst_max=float(np.nanmax(sst)), sst_p99=float(np.nanquantile(sst, 0.99)),
                              days_sst_ge_34_per_yr=float(np.nansum(mn["sea_surface_temperature"] >= 34) / 24 / 4),
                              air_max=float(np.nanmax(w["temperature_2m"])), air_hours_gt_45=int(np.nansum(w["temperature_2m"] > 45)))
    V.append(dict(test="C7 duplex 2205/2507 mesh & crevices at SST 36-38 C", value=f"data max {res['temperature']['sst_max']:.1f} C; design {P.SST_MAX_DESIGN} C",
                  criterion="NORSOK M-001 Rev.5: 25Cr duplex <= 20 C in seawater with crevices (via TWI)",
                  verdict="FAIL", detail="woven-mesh knuckles and rail contacts are crevices; immersion is in the hottest months. "
                                         "Use titanium Gr2, Cu-Ni 90/10, or polymer (HDPE/PET/UHMWPE) mesh; keep duplex only above water"))
    V.append(dict(test="C8 electrical/drive equipment vs air temperature (ERA5 grid max; land sites hotter)", value=f"{res['temperature']['air_max']:.1f} C, {res['temperature']['air_hours_gt_45']} h > 45 C",
                  criterion="standard IEC motor/VFD/PLC rating 40 C ambient", verdict="MARGINAL" if res['temperature']['air_max'] > 40 else "PASS",
                  detail="derate motors (~0.9 at 50 C), shaded/air-conditioned panels, solar-load on drums & load cells (temperature-compensated range)"))
    V.append(dict(test="C9 HDPE seabed pipe at 36-38 C", value="PE100 pressure derating ~0.75-0.8 at 35-40 C [ENG]",
                  criterion="pipe is low-pressure (~7 m head) -> derated rating still >> duty", verdict="PASS",
                  detail="check ring stiffness/creep for ballast loads at temperature"))

    # ---- 5. dust ----
    dust_proxy = float(np.mean(w["wind_speed_10m"] > 8.0))
    V.append(dict(test="C10 sandstorm/dust on stowed drums", value=f"{100*dust_proxy:.1f} % hours with 10-m wind > 8 m/s (dust-lifting proxy)",
                  criterion="drums, bearings, brakes, load cells sealed IP66; rolled mesh under a shroud; camera/lens wash",
                  verdict="INFO", detail="the plant already designs penetrations > 6 m above grade for dust (ENEC 2012). "
                                         "Abrasion of rolled mesh by trapped sand on every roll-down -> brush/spray on lowering too"))

    # ---- 6. storm vs bloom coincidence (operating policy) ----
    V.append(dict(test="C11 envelope policy: storm stow vs bloom", value=f"stow wind gust > {P.WIND_OPERATE_GUST} m/s only for motion; stay deployed up to Hs {Hs_hard:.1f} m",
                  criterion="screen must not be forced up in a shamal (onshore drift drives blooms)",
                  verdict="MARGINAL", detail="design rule: roll-down/up blocked above 20 m/s gust but a deployed bay may stay down; "
                                             "hard-limit relief still active. Needs deployed-storm load case in detailed design"))

    res["verdicts"] = V
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(res, open(HERE / "out" / "extremes_results.json", "w"), indent=2, default=float)

    # figures
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.6))
    ax[0].hist(w["wind_gusts_10m"], bins=60, color="#6a9fd4"); ax[0].axvline(P.WIND_OPERATE_GUST, color="#c33")
    ax[0].axvline(P.WIND_SURVIVAL_GUST, color="k"); ax[0].set_yscale("log"); ax[0].set_xlabel("ERA5 hourly gust (m/s)")
    ax[0].set_title("Wind 2015-25: op limit (red), design (black)", fontsize=9)
    ax[1].hist(mn["wave_height"], bins=60, color="#6a9fd4", alpha=0.7, label="near")
    ax[1].hist(mo["wave_height"], bins=60, color="#e39a4f", alpha=0.5, label="off")
    ax[1].axvline(Hs_noise, color="#c33"); ax[1].set_yscale("log"); ax[1].set_xlabel("Hs (m)"); ax[1].legend(fontsize=8)
    ax[1].set_title("Waves 2022-25: red = wave dP at 1/2 trip", fontsize=9)
    ss = [r for r in rows if r["site"].startswith("inner")]
    ax[2].bar(range(len(ss)), [r["crest"] for r in ss], color="#6a9fd4", label="inner crest")
    ax[2].bar(range(len(ss)), [r["crest"] for r in rows if r["site"].startswith("outer")], color="none", edgecolor="#c33", label="outer crest")
    ax[2].axhline(P.DECK_SOFFIT_Z, color="k", label="deck soffit")
    ax[2].set_xticks(range(len(ss))); ax[2].set_xticklabels([r["scenario"].replace(" ", "\n") for r in ss], fontsize=6)
    ax[2].set_ylabel("m MSL"); ax[2].legend(fontsize=7); ax[2].set_title("100-yr crest + SLR 2085 vs deck", fontsize=9)
    fig.tight_layout(); fig.savefig(HERE / "figs" / "extremes.png", dpi=150)
    for v in V:
        print(f"{v['verdict']:9s} {v['test']}: {v['value']} [{v['criterion']}]")
    print(json.dumps({k: res[k] for k in ("wind", "temperature", "sea_level_model")}, default=float)[:1500])


if __name__ == "__main__":
    main()
