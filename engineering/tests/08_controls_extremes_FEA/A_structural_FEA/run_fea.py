"""A. Structural FEA of one JAZR gantry bay (2 piles + box girder + drum frame).

Runs: static load combinations (operating / accidental stuck-drum / stowed survival),
deflections, stresses vs allowable, modal analysis vs wave periods, VIV screen,
linear buckling, 60-year wave fatigue (Open-Meteo hourly Hs/Tm 2022-2025), and sensitivity
to pile fixity depth and membrane sag. Output: out/fea_results.json, figs/*.png
"""
import json, sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from common import params as P
from common import gantry as GT

DATA = ROOT.parent / "00_data" / "raw" / "openmeteo_marine" / "marine_near.json"
OUT, FIG = HERE / "out", HERE / "figs"


def verdict(util, lim_marg=0.9):
    return "PASS" if util <= lim_marg else ("MARGINAL" if util <= 1.0 else "FAIL")


def run_static(fixity_D=P.PILE_FIXITY_DEPTH_D, sag=P.MEMBRANE_SAG_RATIO, verbose=True):
    f, g, secs, info = GT.build(fixity_D=fixity_D)
    grp = GT.elem_group(f, g)
    D = GT.load_dead(f, g)
    L = GT.load_live(f, g)
    dp_op = 1.5 * P.DP_TRIP
    RU = GT.load_rollup(f, g, dp_op)
    HYD_op = GT.load_screen_dp(f, g, dp_op, sag=sag)
    HYD_acc = GT.load_screen_dp(f, g, P.DP_ACCIDENT, sag=sag)
    # operating sea: Hs 1.0 m (data p99 0.88 m nearshore), Hmax = 1.86 Hs, T 5 s, lane current 0.5 m/s along x
    W_op_x, _ = GT.load_wave_current(f, g, 1.86 * 1.0, 5.0, P.HAT_Z, P.V_LANE, 0.0, info["D_eff"])
    WIND_op = GT.load_wind(f, g, P.WIND_OPERATE_GUST, 90.0, mesh_exposed_h=P.DRUM_Z - P.HAT_Z - 1.5)
    # survival (stowed): 100-yr Hs at SWL = HAT + surge + SLR(2085 SSP5-8.5 median)
    wl_s = P.HAT_Z + P.SURGE100 + P.SLR_2085["SSP5-8.5 median"]
    d_s = wl_s - P.SEABED_Z
    Hmax = min(1.86 * P.HS100, 0.78 * d_s)
    surv = {}
    for th in (0.0, 45.0, 90.0):
        Fw, Vb = GT.load_wave_current(f, g, Hmax, P.TP100, wl_s, P.CURRENT_SURV, th, info["D_eff"])
        surv[th] = (Fw + GT.load_wind(f, g, P.WIND_SURVIVAL_GUST, th), Vb)
    combos = {
        "OP1 operating: D+L+rollup+dP(1.5xtrip)+Hs1.0 wave+0.5 m/s current+20 m/s wind": (D + L + RU + HYD_op + W_op_x + WIND_op, 0.60),
        "ACC1 stuck drum, blinded bay dP=3 kPa: D+dP_acc+current": (D + HYD_acc + W_op_x, 0.91),
        "SURV0 stowed 100-yr wave+surge+SLR2085, wave along x (channel axis)": (D + surv[0.0][0], 0.80),
        "SURV45 stowed 100-yr, 45 deg": (D + surv[45.0][0], 0.80),
        "SURV90 stowed 100-yr, normal to gantry": (D + surv[90.0][0], 0.80),
    }
    res = {}
    for name, (F, allow) in combos.items():
        u = f.solve(F)
        s, _ = f.stresses(u)
        row = {}
        for gn in sorted(set(grp)):
            idx = [i for i, x in enumerate(grp) if x == gn]
            fy = f.elems[idx[0]]["sec"].mat["fy"]
            smax = float(s[idx].max())
            row[gn] = dict(sigma_MPa=round(smax / 1e6, 1), allow_MPa=round(allow * fy / 1e6, 1),
                           util=round(smax / (allow * fy), 3))
        top = g["pile1"][-1]
        drum_mid = g["drum"][len(g["drum"]) // 2]
        row["pile_head_drift_mm"] = round(1e3 * float(np.hypot(u[6 * top], u[6 * top + 1])), 1)
        # max lateral pile deflection along wetted length (rail alignment)
        lat = [np.hypot(u[6 * i], u[6 * i + 1]) for i in g["pile1"] + g["pile2"]]
        row["max_pile_lateral_mm"] = round(1e3 * float(max(lat)), 1)
        row["drum_mid_defl_mm"] = round(1e3 * float(np.linalg.norm(u[6 * drum_mid:6 * drum_mid + 3])), 1)
        Rbase = [F_ for F_ in ()]
        row["util_max"] = max(v["util"] for k, v in row.items() if isinstance(v, dict))
        row["allowable_rule"] = f"{allow:.2f} fy"
        res[name] = row
    extra = dict(survival_SWL_mMSL=round(wl_s, 2), survival_depth_m=round(d_s, 2), Hmax_m=round(Hmax, 2),
                 base_shear_kN={str(k): round(v[1] / 1e3, 1) for k, v in surv.items()},
                 rollup_tension_kN=round(GT.rollup_tension(dp_op) / 1e3, 1),
                 membrane_pull_op_kN_per_m=round(dp_op * P.BAY_W / (8 * sag) / 1e3, 1),
                 membrane_pull_acc_kN_per_m=round(P.DP_ACCIDENT * P.BAY_W / (8 * sag) / 1e3, 1))
    return f, g, res, extra, (D + L + RU)


def run_modal(f, g):
    fr, Phi, M, free = f.modal(8)
    shapes = []
    for k in range(len(fr)):
        ph = Phi[:, k]
        ux, uy, uz = np.abs(ph[0::6]).max(), np.abs(ph[1::6]).max(), np.abs(ph[2::6]).max()
        dom = ["x (along gantry)", "y (normal)", "z (vertical)"][int(np.argmax([ux, uy, uz]))]
        shapes.append(dom)
    return fr, shapes, Phi


def fatigue(f, g, f1, kt=1.0, deployed_dp=True):
    """Pile-at-fixity (seawater+CP, curve D) and pile-top/girder joint (in air, curve D, SCF 2).
    Stress range per wave height found by FE over 24 phases. Waves along x (channel axis) +
    deployed-mesh wave dP normal (y) with 30 deg effective obliquity [ASM]."""
    d = json.load(open(DATA))["hourly"]
    Hs = np.array([x if x is not None else np.nan for x in d["wave_height"]], float) * kt
    Tm = np.array([x if x is not None else np.nan for x in d["wave_period"]], float)
    ok = np.isfinite(Hs) & np.isfinite(Tm)
    Hs, Tm = Hs[ok], Tm[ok]
    years = len(Hs) / 8766.0
    info_D = P.PILE_D + 2 * P.MARINE_GROWTH
    K = f.K(); free = f.free()
    import scipy.linalg as sla
    lu = sla.lu_factor(K[np.ix_(free, free)])
    grp = GT.elem_group(f, g)
    e_fix = 0  # first pile-1 element (at fixity)
    e_top = [i for i, x in enumerate(grp) if x == "pile"][len(g["pile1"]) - 2]  # last pile-1 element

    def stress_hist(H, T, deployed):
        wl = 0.0
        dd = wl - P.SEABED_Z
        k = GT.wave_number(T, dd)
        w = 2 * np.pi / T
        sig = []
        for ph in np.linspace(0, 2 * np.pi, 24, endpoint=False):
            zs, fz = GT.morison_profile(H, T, dd, 0.0, ph, info_D)
            F = np.zeros(f.ndof)
            for gn in ("pile1", "pile2"):
                GT._add_line_load(f, F, g[gn], lambda p, zs=zs, fz=fz: (np.interp(p[2], zs, fz), 0, 0)
                                  if P.SEABED_Z <= p[2] <= zs[-1] else (0, 0, 0))
            if deployed:
                # depth-mean orbital velocity normal to mesh (30 deg obliquity)
                zz = np.linspace(-dd, 0, 20)
                un = np.mean(w * H / 2 * np.cosh(k * (zz + dd)) / np.sinh(k * dd)) * np.cos(ph) * np.sin(np.radians(30))
                v = P.V_APPROACH_SCREEN + un
                kmesh = 0.78  # Idelchik woven screen, porosity 0.64 [ENG]
                dp = kmesh * 0.5 * P.RHO_W * v * abs(v) - kmesh * 0.5 * P.RHO_W * P.V_APPROACH_SCREEN**2
                F += GT.load_screen_dp(f, g, dp, wl=0.0)
            u = np.zeros(f.ndof); u[free] = sla.lu_solve(lu, F[free])
            fl = f.member_forces(u)
            out = []
            for e in (e_fix, e_top):
                fe = fl[e]; sec = f.elems[e]["sec"]
                o = 0 if e == e_fix else 6
                # extreme fibre stress: moment resultant along the dominant plane, signed by the larger component
                My, Mz = fe[o + 4], fe[o + 5]
                M = np.hypot(My, Mz) * np.sign(My if abs(My) > abs(Mz) else Mz)
                out.append(M / sec.Wy)
            sig.append(out)
        sig = np.array(sig)
        return sig.max(0) - sig.min(0)

    Tb = np.array([2.0, 3.0, 4.0, 5.0, 6.0, 7.0])
    Hb = np.array([0.05, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.6])
    tables = {}
    for dep in (False, True):
        tab = np.zeros((len(Tb), len(Hb), 2))
        for i, T in enumerate(Tb):
            r = 1.0 / T / f1
            daf = 1 / np.sqrt((1 - r**2) ** 2 + (2 * 0.02 * r) ** 2)
            for j, H in enumerate(Hb):
                tab[i, j] = stress_hist(H, T, dep) * daf
        tables[dep] = tab

    def N_cp(S):  # seawater + CP, curve D
        S = max(S / 1e6, 1e-9)
        return np.where(S > 10 ** ((11.764 - 6) / 3), 10 ** (11.764 - 3 * np.log10(S)), 10 ** (15.606 - 5 * np.log10(S)))

    def N_air(S):
        S = max(S / 1e6, 1e-9)
        return np.where(S > 52.63, 10 ** (12.164 - 3 * np.log10(S)), 10 ** (15.606 - 5 * np.log10(S)))

    def N_fc(S):  # free corrosion, curve D, single slope
        S = max(S / 1e6, 1e-9)
        return 10 ** (11.687 - 3 * np.log10(S))

    # damage per hour on (Hs, Tm) grid, Rayleigh individual waves
    Hrel = np.linspace(0.05, 2.0, 40)
    pdf = 4 * Hrel * np.exp(-2 * Hrel**2) * 2  # Rayleigh in H/Hs (Hrms = Hs/sqrt2)
    pdf = pdf / pdf.sum()
    Hs_grid = np.linspace(0, 3.0, 61)
    keys = ("fixity_CP", "fixity_freecorr", "top_air_SCF2")
    rate = {k_: np.zeros((len(Tb), len(Hs_grid))) for k_ in keys}  # damage per hour
    for i, t in enumerate(Tb):
        nw = 3600.0 / t
        for jh, h in enumerate(Hs_grid):
            for dep, wfrac in ((False, 1 - P.DEPLOYED_FRACTION), (True, P.DEPLOYED_FRACTION)):
                tab = tables[dep][i]
                for hr, pr in zip(Hrel, pdf):
                    H = hr * h
                    S_fix = np.interp(H, Hb, tab[:, 0]); S_top = np.interp(H, Hb, tab[:, 1]) * 2.0
                    n = nw * pr * wfrac
                    rate["fixity_CP"][i, jh] += n / N_cp(S_fix)
                    rate["fixity_freecorr"][i, jh] += n / N_fc(S_fix)
                    rate["top_air_SCF2"][i, jh] += n / N_air(S_top)
    ti = np.clip(np.searchsorted(Tb, Tm), 0, len(Tb) - 1)  # conservative: next-longer period bin
    dmg = {k_: float(sum(np.interp(Hs[ti == i], Hs_grid, rate[k_][i]).sum() for i in range(len(Tb)))) for k_ in keys}
    life = {}
    for k_, v in dmg.items():
        per_year = v / years
        D60 = per_year * P.LIFE_YEARS
        dff = 3.0 if k_.startswith("fixity") else 1.0
        life[k_] = dict(D_60y=float(D60), DFF=dff, D_x_DFF=float(D60 * dff),
                        fatigue_life_years=float(1 / per_year / dff) if per_year > 0 else float("inf"))
    return life, Tb, Hb, tables


def main():
    f, g, res, extra, Fgrav = run_static()
    fr, shapes, Phi = run_modal(f, g)
    wave_band = (1 / 8.0, 1 / 2.0)
    data_band = (1 / 6.25, 1 / 1.5)
    in_band = [float(x) for x in fr if wave_band[0] <= x <= wave_band[1]]
    # VIV (current) screen: reduced velocity Vr = U/(f D)
    viv = {}
    for U in (0.5, 1.0, 1.4 / 3.6 * 3.6):
        Vr = U / (fr[0] * (P.PILE_D + 2 * P.MARINE_GROWTH))
        viv[f"U={U:.1f} m/s"] = round(float(Vr), 2)
    # buckling under gravity set (D+L+rollup)
    u_ref = f.solve(Fgrav)
    lam = f.buckling(u_ref, 3)
    # sensitivity
    sens = {}
    for fd in (3.0, 5.0, 7.0):
        _, _, r, _, _ = run_static(fixity_D=fd)
        sens[f"fixity {fd:.0f}D"] = {k.split(":")[0].split(" ")[0]: v["util_max"] for k, v in r.items()}
    for sg in (0.02, 0.05, 0.08):
        _, _, r, ex, _ = run_static(sag=sg)
        sens[f"sag {int(sg*100)}%"] = {k.split(":")[0].split(" ")[0]: v["util_max"] for k, v in r.items()}
    life, Tb, Hb, tables = fatigue(f, g, fr[0])
    life_sheltered, *_ = fatigue(f, g, fr[0], kt=0.5)

    verdicts = []
    for name, row in res.items():
        verdicts.append(dict(test="A1 stress " + name.split(":")[0].split(" ")[0], value=row["util_max"],
                             criterion=f"util <= 1 ({row['allowable_rule']}); MARGINAL > 0.9", verdict=verdict(row["util_max"]),
                             detail=name))
    op = res[[k for k in res if k.startswith("OP1")][0]]
    verdicts.append(dict(test="A2 pile lateral deflection, operating (rail alignment)", value=op["max_pile_lateral_mm"],
                         criterion="<= 25 mm [ASM: guide-rail/mesh-edge retention]",
                         verdict="PASS" if op["max_pile_lateral_mm"] <= 25 else ("MARGINAL" if op["max_pile_lateral_mm"] <= 50 else "FAIL")))
    acc = res[[k for k in res if k.startswith("ACC1")][0]]
    verdicts.append(dict(test="A2b pile lateral deflection, stuck-drum accident", value=acc["max_pile_lateral_mm"],
                         criterion="<= 75 mm (mesh stays in rails) [ASM]",
                         verdict="PASS" if acc["max_pile_lateral_mm"] <= 75 else "FAIL"))
    verdicts.append(dict(test="A3 modal: f1 vs wave band 0.125-0.5 Hz (2-8 s)", value=round(float(fr[0]), 3),
                         criterion="no mode within 2-8 s wave band; f1 > 0.5 Hz (T1 < 2 s)",
                         verdict="PASS" if not in_band and fr[0] > 0.5 else ("MARGINAL" if fr[0] > 0.4 else "FAIL"),
                         detail=f"T1={1/fr[0]:.2f} s; data waves 1.5-6.25 s (mean period); modes in band: {in_band}"))
    verdicts.append(dict(test="A4 current VIV (in-line onset Vr>1)", value=max(viv.values()),
                         criterion="Vr < 1 (DNV-RP-C205 in-line onset)", verdict="PASS" if max(viv.values()) < 1 else "MARGINAL",
                         detail=str(viv)))
    verdicts.append(dict(test="A5 linear buckling (gravity + roll-up)", value=round(float(lam[0]), 1),
                         criterion="load factor >= 10 (sway/global) [ENG]", verdict="PASS" if lam[0] >= 10 else "FAIL"))
    for k, v in life.items():
        verdicts.append(dict(test=f"A6 fatigue 60 y {k} (unsheltered Kt=1)", value=round(v["D_x_DFF"], 3),
                             criterion="Miner D x DFF <= 1 (DNV-RP-C203)", verdict=verdict(v["D_x_DFF"], 0.5),
                             detail=f"life ~{v['fatigue_life_years']:.3g} y"))
    for tag, crit in (("fixity", "pile fixity 3-7 D"), ("sag", "membrane sag 2-8 % of span")):
        sub = {k: v for k, v in sens.items() if k.startswith(tag)}
        worst = max(max(v.values()) for v in sub.values())
        verdicts.append(dict(test=f"A7 sensitivity: {crit}", value=worst, criterion="worst util <= 1",
                             verdict=verdict(worst), detail=json.dumps(sub)))
    results = dict(static=res, extra=extra, modal_Hz=[float(x) for x in fr], modal_periods_s=[float(1 / x) for x in fr],
                   mode_dirs=shapes, viv_Vr=viv, buckling_factors=[float(x) for x in lam], sensitivity=sens,
                   fatigue_unsheltered=life, fatigue_sheltered_Kt0p5=life_sheltered, verdicts=verdicts)
    OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
    json.dump(results, open(OUT / "fea_results.json", "w"), indent=2, default=float)

    # ---- figures ----
    fig, ax = plt.subplots(figsize=(7, 3.6))
    T = 1 / np.array(fr)
    ax.axvspan(2, 8, color="#f4c7a1", alpha=0.6, label="wave periods 2-8 s (brief)")
    ax.axvspan(1.5, 6.25, color="#9ec5e8", alpha=0.4, label="data mean periods 2022-25")
    for i, t in enumerate(T):
        ax.axvline(t, color="#333", lw=1.5)
        ax.text(t, 0.9 - 0.1 * (i % 4), f"m{i+1}\n{shapes[i].split()[0]}", fontsize=7, ha="center")
    ax.set_xscale("log"); ax.set_xlim(0.05, 20); ax.set_yticks([])
    ax.set_xlabel("period (s)"); ax.set_title("Gantry bay natural periods vs wave band")
    ax.legend(loc="lower right", fontsize=7)
    fig.tight_layout(); fig.savefig(FIG / "modal_vs_waves.png", dpi=150); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.8))
    names = list(res.keys()); short = [n.split(":")[0].split(" ")[0] for n in names]
    groups = ["pile", "girder", "post", "drum"]
    w = 0.2
    for i, gname in enumerate(groups):
        ax.bar(np.arange(len(names)) + (i - 1.5) * w, [res[n][gname]["util"] for n in names], w, label=gname)
    ax.axhline(1.0, color="k", lw=1); ax.axhline(0.9, color="k", lw=0.8, ls="--")
    ax.set_xticks(range(len(names))); ax.set_xticklabels(short)
    ax.set_ylabel("stress / allowable"); ax.set_title("Utilisation by member group and load case")
    ax.legend(fontsize=8, ncol=4); fig.tight_layout(); fig.savefig(FIG / "utilisation.png", dpi=150); plt.close(fig)

    # deformed shape for ACC1
    f2, g2, *_ = GT.build()
    Fa = GT.load_dead(f2, g2) + GT.load_screen_dp(f2, g2, P.DP_ACCIDENT)
    u = f2.solve(Fa)
    fig, ax = plt.subplots(1, 2, figsize=(8, 4.5))
    sc = 50
    for e in f2.elems:
        a, b = f2.nodes[e["n1"]], f2.nodes[e["n2"]]
        ua, ub = u[6 * e["n1"]:6 * e["n1"] + 3], u[6 * e["n2"]:6 * e["n2"] + 3]
        ax[0].plot([a[0], b[0]], [a[2], b[2]], color="#bbb"); ax[0].plot([a[0] + sc * ua[0], b[0] + sc * ub[0]], [a[2] + sc * ua[2], b[2] + sc * ub[2]], color="#c33")
        ax[1].plot([a[1], b[1]], [a[2], b[2]], color="#bbb"); ax[1].plot([a[1] + sc * ua[1], b[1] + sc * ub[1]], [a[2] + sc * ua[2], b[2] + sc * ub[2]], color="#c33")
    for a_ in ax:
        a_.axhline(0, color="#39f", lw=0.8); a_.axhline(P.SEABED_Z, color="#a87", lw=0.8)
    ax[0].set_title("x-z (along gantry) x50"); ax[1].set_title("y-z (normal) x50")
    ax[0].set_xlabel("x (m)"); ax[1].set_xlabel("y (m)"); ax[0].set_ylabel("z (m MSL)")
    fig.suptitle("ACC1 stuck-drum blinded bay (3 kPa) deformed shape")
    fig.tight_layout(); fig.savefig(FIG / "deformed_ACC1.png", dpi=150); plt.close(fig)

    for v in verdicts:
        print(f"{v['verdict']:9s} {v['test']}: {v['value']}  [{v['criterion']}]")
    print("modes Hz", np.round(fr, 3), shapes)
    print(json.dumps(extra))


if __name__ == "__main__":
    main()
