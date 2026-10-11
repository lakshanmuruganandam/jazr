"""PNG charts for the virtual tank (SIMULATED virtual tank - not physical evidence)."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES, OUT = os.path.join(HERE, "results"), os.path.join(HERE, "charts")
os.makedirs(OUT, exist_ok=True)
SURF, INK, INK2, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#a3a29c", "#e4e3df"
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
CRIT = "#e34948"
WM = "SIMULATED virtual tank — not physical evidence"

plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 12,
                     "axes.titleweight": "bold", "axes.titlecolor": INK, "axes.titlelocation": "left", "legend.frameon": False})


def load(name):
    p = os.path.join(RES, name)
    return json.load(open(p)) if os.path.exists(p) else None


def finish(fig, name, sub=None):
    fig.text(0.99, 1.0, WM, ha="right", va="bottom", color=CRIT, fontsize=8.5, fontweight="bold")
    if sub:
        fig.text(0.01, -0.03, sub, ha="left", va="top", color=INK2, fontsize=8)
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)


def refline(ax, y, txt, color=CRIT):
    ax.axhline(y, color=color, lw=1.2, ls=(0, (4, 3)))
    ax.text(ax.get_xlim()[1], y, " " + txt, color=color, va="center", fontsize=8.5)


def t03(R):
    c = R["T02"]["conditions"]
    angs = [8, 11, 15, 20]
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    m = [c[f"T03 screen {a} deg"]["eta_r_all"] for a in angs]
    p = [c[f"T03 screen {a} deg"]["eta_r_protocol"] for a in angs]
    x = np.arange(len(angs))
    ax.bar(x, [v["mean"] for v in m], width=0.5, color=S1, label="η_r, mean of 15 seeded runs")
    ax.errorbar(x, [v["mean"] for v in m], yerr=[[v["mean"] - v["min"] for v in m], [v["max"] - v["mean"] for v in m]],
                fmt="none", ecolor=INK2, capsize=4, lw=1)
    ax.scatter(x + 0.32, [v["mean"] for v in p], color=INK, s=28, zorder=3, label="mean of the 3 protocol runs")
    ax.set_xticks(x, [f"{a}°" for a in angs]); ax.set_ylim(0, 1); ax.set_xlim(-0.6, 3.9)
    ax.set_ylabel("fraction of 30 bells to bypass (η_r)"); ax.set_xlabel("screen angle to flow")
    refline(ax, 0.7, "pass ≥0.7 (11°)"); refline(ax, 0.4, "kill <0.4 (all angles)", MUTED)
    b = c["T02 no screen, bypass on (control)"]["eta_r_all"]["mean"]
    ax.axhline(b, color=S3, lw=1.2); ax.text(-0.55, b + 0.02, f"no screen, bypass on: {b:.2f} by chance", color=INK2, fontsize=8.5)
    ax.set_title("T03 · Inner screen guidance at 10% bypass flow — FAIL at 11° (nominal)")
    ax.legend(loc="upper left", fontsize=8.5)
    finish(fig, "T03_eta_vs_angle.png", "Whiskers = min–max over runs. Intake fraction was 0 in every screen run; the loss is bells stuck at the face.")


def bypass_curve(S):
    if not S:
        return
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for th, col in ((11, S1),):
        ks = sorted([k for k in S["bypass"] if k.startswith(f"{th}|")], key=lambda k: float(k.split("|")[1]))
        b = [float(k.split("|")[1]) * 100 for k in ks]
        e = [S["bypass"][k]["eta_mean"] for k in ks]
        se = [S["bypass"][k]["eta_sem"] for k in ks]
        ax.errorbar(b, e, yerr=se, color=col, lw=2, marker="o", ms=6, capsize=3, label=f"screen {th}°, 4–6 cm bells")
    D = S.get("design", {})
    if "bells 1.5-2.5 cm" in D:
        ax.scatter([10], [D["bells 1.5-2.5 cm"]["eta_mean"]], color=S3, s=60, zorder=4, label="1.5–2.5 cm bells (geometric 1:20)")
    if "bells 1.5-2.5 cm, bypass 3%" in D:
        ax.scatter([3], [D["bells 1.5-2.5 cm, bypass 3%"]["eta_mean"]], color=S3, s=60, zorder=4)
    ax.set_ylim(0, 1); ax.set_xlim(0, 42)
    refline(ax, 0.7, "pass 0.7")
    ax.axvspan(1.5, 4, color=MUTED, alpha=0.18, lw=0)
    ax.text(2.7, 0.05, "v3 lift ≈2–4%\nof lane flow", ha="center", fontsize=8, color=INK2)
    ax.set_xlabel("bypass flow, % of lane flow"); ax.set_ylabel("η_r (3 seeds, ±1 s.e.)")
    ax.set_title("Bypass flow is the decisive design variable in the virtual tank")
    ax.legend(loc="lower right")
    finish(fig, "eta_vs_bypass_flow.png", "4–6 cm surrogate bells, 6 cm end entrance + 1 mid-face entrance.")


def tornado(S):
    if not S:
        return
    nom = S["oat"]["nominal|nom|0"]["eta_mean"]
    rows = []
    for p in S["ranges"]:
        lo = [v for k, v in S["oat"].items() if k.startswith(p + "|low")]
        hi = [v for k, v in S["oat"].items() if k.startswith(p + "|high")]
        rows.append((p, lo[0]["eta_mean"] if lo else nom, hi[0]["eta_mean"] if hi else nom))
    rows.sort(key=lambda r: abs(r[2] - r[1]))
    lab = dict(E="bell stiffness E 1–30 kPa", mu_f="friction μ 0.1–1.0", adhesion="mucus adhesion 0–3 Pa",
               cd_mult="drag ×0.6–1.6", turb_I="turbulence 3–25%", ell_s="screen resistance ×0.2–6",
               rho_sd_scale="density scatter ×0.1–2")
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    y = np.arange(len(rows))
    for i, (p, lo, hi) in enumerate(rows):
        ax.barh(i, lo - nom, left=nom, color=S1, height=0.55, label="low end" if i == 0 else None)
        ax.barh(i, hi - nom, left=nom, color=S2, height=0.55, label="high end" if i == 0 else None)
    ax.set_yticks(y, [lab.get(r[0], r[0]) for r in rows])
    ax.axvline(nom, color=INK, lw=1); ax.axvline(0.7, color=CRIT, lw=1.2, ls=(0, (4, 3)))
    ax.text(0.7, len(rows) - 0.4, " pass 0.7", color=CRIT, fontsize=8.5)
    L = S["oat_band"]
    ax.set_xlim(0, 1); ax.set_xlabel("η_r at 11° (3 seeds per bar, 120 s runs)")
    ax.set_title(f"Unknown parameters move η_r(11°) between {L['min']:.2f} and {L['max']:.2f}")
    ax.legend(loc="lower right", fontsize=8.5)
    finish(fig, "sensitivity_tornado.png", f"Nominal η_r = {nom:.2f} (one-at-a-time; seed noise ≈ ±0.05).")


def t05(R):
    ts = load("_T05_timeseries.json")
    if not ts:
        return
    dr = round(R["T05"]["design_rate_per_min"])
    fig, axs = plt.subplots(1, 2, figsize=(10, 4))
    for cyc, col, lab in ((False, S2, "no bay cycling"), (True, S1, "bay cycling (1 bay up 2 s every 20 s)")):
        vv = [np.array(v["ts"]) for v in ts if v["rate"] == dr and v["cycling"] == cyc]
        n = min(len(v) for v in vv)
        A = np.stack([v[:n] for v in vv])
        t = A[0, :, 0]
        for k, ax in ((1, axs[0]), (2, axs[1])):
            ax.plot(t, A[:, :, k].mean(0), color=col, lw=2, label=lab)
            ax.fill_between(t, A[:, :, k].min(0), A[:, :, k].max(0), color=col, alpha=0.15, lw=0)
    axs[0].set_ylabel("screen head difference, mm water"); axs[1].set_ylabel("face covered, %")
    axs[0].axhline(0.5, color=MUTED, ls=(0, (4, 3))); axs[0].text(5, 0.52, "≈ readable on two clear tubes", fontsize=8, color=INK2)
    axs[1].axhline(50, color=CRIT, ls=(0, (4, 3))); axs[1].text(5, 52, "kill: >50% in <1 min", fontsize=8, color=CRIT)
    for ax in axs:
        ax.set_xlabel("time, s")
    axs[1].set_ylim(0, 100)
    axs[0].set_title(f"T05 · Clogging at design rate ≈{dr} bells/min")
    axs[1].legend(loc="upper left", fontsize=8.5)
    finish(fig, "T05_clogging_design_rate.png", "Band = min–max of 3 seeded runs.")


def t08(R):
    if "T08" not in R:
        return
    c = R["T08"]["conditions"]
    fig, ax = plt.subplots(figsize=(7, 4))
    angs = [15, 20, 25]
    x = np.arange(3)
    for j, (d, col) in enumerate((("flood", S1), ("ebb", S2))):
        v = [c[f"{a} deg {d}"]["eta_g"] for a in angs]
        ax.bar(x + (j - 0.5) * 0.36, [q["mean"] for q in v], width=0.34, color=col, label=d)
        ax.errorbar(x + (j - 0.5) * 0.36, [q["mean"] for q in v], yerr=[[q["mean"] - q["min"] for q in v], [q["max"] - q["mean"] for q in v]],
                    fmt="none", ecolor=INK2, capsize=3, lw=1)
    ax.set_xticks(x, [f"{a}°" for a in angs]); ax.set_ylim(0, 1); ax.set_xlim(-0.6, 2.9)
    refline(ax, 0.4, "pass 0.4")
    ax.set_ylabel("fraction deflected (η_g)"); ax.set_xlabel("outer line angle to flow")
    ax.set_title("T08 · Outer guide line (partial-depth curtain)")
    ax.legend(loc="upper left")
    finish(fig, "T08_outer_line.png", "3 runs per bar, 30 bells released in the curtain's shadow.")


def t12(R):
    if "T12" not in R:
        return
    c = R["T12"]["conditions"]
    d = [0.3, 0.6, 1.0]
    fig, ax = plt.subplots(figsize=(6.5, 4))
    for key, col, lab in (("ret_after_1", S2, "after 1 tidal cycle"), ("ret_after_3", S1, "after 3 cycles")):
        ax.plot([x * 100 for x in d], [c[f"{x} m"][key]["mean"] for x in d], color=col, lw=2, marker="o", ms=7, label=lab)
    ax.set_ylim(0, 1); ax.set_xlabel("release distance from intake, cm (model)"); ax.set_ylabel("fraction returned to intake")
    ax.set_title("T12 · Drift-back falls with distance (model)")
    ax.legend()
    finish(fig, "T12_driftback.png", "Mean of flood- and ebb-phase releases, 3 runs each. Tidal excursion ≈ 66 cm.")


def t14():
    E = np.logspace(1.3, 4.6, 100)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for r, col in ((1.5, S3), (2, S1), (4, S2)):
        ax.plot(E, E * (r - 1), color=col, lw=2, label=f"extrusion threshold, fragment = {r}× opening")
    from vtank import K_mesh
    dp = lambda u, b: 0.5 * 1000 * K_mesh(0.5 * (1 - b)) * u ** 2
    bands = [("tank 1:20, clean", dp(0.022, 0)), ("tank, 75% blinded", dp(0.022, 0.75)),
             ("prototype 0.1 m/s, clean", dp(0.10, 0)), ("prototype, 75% blinded", dp(0.10, 0.75))]
    bands = [(l, v / 1.4, v * 1.4) for l, v in bands]
    for lab, lo, hi in bands:
        ax.axhspan(lo, hi, color=MUTED, alpha=0.25, lw=0)
        ax.text(22, np.sqrt(lo * hi), lab, fontsize=8, color=INK2, va="center")
    ax.axvspan(50, 300, color=S4, alpha=0.15, lw=0); ax.text(120, 3e4, "assumed\nmesoglea", ha="center", fontsize=8, color=INK2)
    ax.axvspan(3000, 30000, color=S1, alpha=0.08, lw=0); ax.text(9500, 3e4, "gel\nsurrogates", ha="center", fontsize=8, color=INK2)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(20, 4e4); ax.set_ylim(0.1, 1e5)
    ax.set_xlabel("fragment stiffness E, Pa"); ax.set_ylabel("pressure across mesh, Pa")
    ax.set_title("T14 · Gel surrogates cannot reproduce prototype extrusion")
    ax.legend(loc="lower right", fontsize=8)
    finish(fig, "T14_extrusion_scaling.png", "Extrusion when operating ΔP (grey bands) exceeds the threshold line. Threshold law and E of mesoglea are assumptions.")


def t15(R):
    c = R["T15"]["conditions"]
    b = [0, 25, 50, 75]
    fig, ax = plt.subplots(figsize=(6.8, 4))
    for U, col in ((11.0, S1), (5.5, S2)):
        sim = [c[f"U={U:.1f}cm/s b={x/100}"]["F_sim"] for x in b]
        calc = [c[f"U={U:.1f}cm/s b={x/100}"]["F_calc"] for x in b]
        ax.plot(b, [s["mean"] for s in sim], color=col, lw=2, marker="o", ms=7, label=f"virtual tank, {U} cm/s")
        ax.fill_between(b, [s["min"] for s in sim], [s["max"] for s in sim], color=col, alpha=0.15, lw=0)
        ax.plot(b, calc, color=col, lw=1.2, ls=(0, (4, 3)), label=f"hand calc (uniform), {U} cm/s")
    ax.set_yscale("log"); ax.set_xlabel("face blinded, %"); ax.set_ylabel("force on strip, N (model scale)")
    ax.axhline(0.5, color=MUTED, lw=1); ax.text(1, 0.55, "≈ luggage-scale resolution", fontsize=8, color=INK2)
    ax.set_title("T15 · Strip load scales with blinding")
    ax.legend(fontsize=8)
    finish(fig, "T15_bay_load.png", "Band = uniform and patchy blinding. Prototype force ≈ model × 8000 (λ³).")


def t01(R):
    s = R["T01"]["scan"]
    k = sorted(s, key=float)
    sd = [s[x]["sd_drho"] for x in k]
    fig, ax = plt.subplots(figsize=(6.8, 4))
    for key, col, lab in (("hover_3mm", S2, "|w_s| ≤ 3 mm/s"), ("hover_5mm", S1, "|w_s| ≤ 5 mm/s (used)"), ("hover_10mm", S3, "|w_s| ≤ 10 mm/s")):
        ax.plot(sd, [s[x][key] for x in k], color=col, lw=2, marker="o", ms=6, label=lab)
    ax.set_xscale("log"); ax.set_ylim(0, 1.02)
    nom = s["1.0"]["sd_drho"]
    ax.axvline(nom, color=INK, lw=1); ax.text(nom, 0.95, " nominal kitchen scatter", fontsize=8)
    ax.axhline(0.8, color=CRIT, lw=1.2, ls=(0, (4, 3))); ax.text(sd[0], 0.82, "pass 80%", color=CRIT, fontsize=8.5)
    ax.set_xlabel("bell density scatter (s.d.), kg/m³"); ax.set_ylabel("fraction of bells that 'hover'")
    ax.set_title("T01 · Hovering needs density control to ~0.03 kg/m³")
    ax.legend(loc="lower left", fontsize=8.5)
    finish(fig, "T01_hover_vs_scatter.png", "4–6 cm gelatin domes; drag-limited settling velocity.")


def grid():
    V = load("SIM_verification.json")
    if not V:
        return
    fig, ax = plt.subplots(figsize=(6.8, 4))
    for (k, v), col in zip(V["grid_flow"].items(), (S2, S1, S3)):
        s = np.linspace(0.1, 0.9, len(v["un_profile"]))
        ax.plot(s, np.array(v["un_profile"]) * 100, color=col, lw=2, marker="o", ms=4, label=k)
    ax.set_xlabel("position along the face (0 = toe, 1 = bypass end)"); ax.set_ylabel("through-screen velocity, cm/s")
    ax.set_title("Grid check · through-velocity along the 11° face")
    ax.legend()
    finish(fig, "verification_grid.png")


if __name__ == "__main__":
    R = load("sim_results.json")
    S = load("SIM_sensitivity.json")
    for f in (lambda: t03(R), lambda: bypass_curve(S), lambda: tornado(S), lambda: t05(R), lambda: t08(R), lambda: t12(R),
              t14, lambda: t15(R), lambda: t01(R), grid):
        try:
            f()
        except Exception as e:
            print("chart skipped:", repr(e))
    print(sorted(os.listdir(OUT)))
