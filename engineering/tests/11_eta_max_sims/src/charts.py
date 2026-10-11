"""charts.py - PNG charts for 11_eta_max_sims (every chart watermarked SIMULATED / model-based)."""
import os, csv, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results"); OUT = os.path.join(HERE, "..", "charts")
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"]
INK, INK2, MUTED, SURF = "#0b0b0b", "#52514e", "#898781", "#fcfcfb"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 9, "axes.titlesize": 10, "axes.titleweight": "bold", "grid.color": "#e6e5e0"})


def mark(fig, txt="SIMULATED - model-based, not a physical test"):
    fig.text(0.995, 0.005, txt, ha="right", va="bottom", fontsize=7.5, color="#c53030", weight="bold")


def rows(name):
    return list(csv.DictReader(open(os.path.join(RES, name))))


def f(r, k):
    return float(r[k])


def lever_chart():
    R = rows("vt_levers.csv")
    groups = ["L1_entrance_flow", "L2_apex_scoop", "L3_conveyor", "L4_series", "L5_friction", "L6_baffles", "L7_walljet",
              "L8_size_swim", "L9_density"]
    titles = ["1 Entrance flow", "2 Apex / scoop / flare", "3 Conveyor belt", "4 Two screens", "5 Friction mu",
              "6 Graded baffles", "7 Wall jet", "8 Bell size / swimming", "9 Density (continuous feed)"]
    fig, axs = plt.subplots(3, 3, figsize=(15, 11))
    for ax, g, tt in zip(axs.flat, groups, titles):
        rr = [r for r in R if r["group"] == g]
        y = np.arange(len(rr))[::-1]
        m = np.array([f(r, "eta_mean") for r in rr]); lo = np.array([f(r, "eta_ci_lo") for r in rr]); hi = np.array([f(r, "eta_ci_hi") for r in rr])
        ax.hlines(y, lo, hi, color=C[0], lw=2)
        ax.plot(m, y, "o", color=C[0], ms=7, mec=SURF, mew=1.5)
        for yy, mm, h in zip(y, m, hi):
            ax.annotate(f"{mm:.2f}", (min(h, 0.985), yy), xytext=(5, 0), textcoords="offset points", va="center", fontsize=7.5, color=INK2)
        ax.set_ylim(-0.6, len(rr) - 0.4)
        ax.axvline(0.76, color=C[1], lw=1, ls="--"); ax.axvline(0.99, color=C[2], lw=1, ls=":")
        ax.set_yticks(y); ax.set_yticklabels([r["config"][:38] for r in rr], fontsize=7.5)
        ax.set_xlim(0.5, 1.03); ax.set_title(tt, loc="left"); ax.grid(axis="x")
    fig.text(0.01, 0.945, "dashed orange = v4.1 tank reference 0.76;  dotted green = 0.99 target", fontsize=9, color=INK2)
    fig.suptitle("Inner-screen guidance efficiency eta_r, one lever at a time (virtual tank 1:20, 10 seeds x 30 bells, mean and 95% CI)",
                 x=0.01, ha="left", fontsize=12, weight="bold")
    for ax in axs[-1]:
        ax.set_xlabel("eta_r (fraction guided to an entrance)")
    plt.tight_layout(rect=(0, 0.02, 1, 0.97)); mark(fig); fig.savefig(os.path.join(OUT, "01_levers_virtual_tank.png"), dpi=130); plt.close()


SHORT = {"v4.1 (4 entr, 20%, mu 0.4)": "v4.1 (20%, mu 0.4)", "+ 35% entrance flow": "+ 35% flow", "+ belt 0.5": "+ belt 0.5x",
         "+ flared mouths": "+ flared mouths", "+ graded baffles": "+ graded baffles", "+ wall jet 0.25": "+ wall jet 0.25x",
         "+ mu 0.1 coating": "+ mu 0.1 coating", "+ apex share 50% (= BEST)": "+ apex share 50% = BEST",
         "35% + flared": "+ flared", "35% + flared + baffles": "+ baffles", "35% + flared + baffles + jet 0.25": "+ wall jet 0.25x",
         "35% + flared + baffles + jet + mu 0.1 (no belt)": "+ mu 0.1", "no-belt best + apex share 50%": "+ apex share 50%"}


def stack_chart():
    R = {r["config"]: r for r in rows("vt_levers.csv")}
    A = ["v4.1 (4 entr, 20%, mu 0.4)", "+ 35% entrance flow", "+ belt 0.5", "+ flared mouths", "+ graded baffles",
         "+ wall jet 0.25", "+ mu 0.1 coating", "+ apex share 50% (= BEST)"]
    B = ["v4.1 (4 entr, 20%, mu 0.4)", "+ 35% entrance flow", "35% + flared", "35% + flared + baffles",
         "35% + flared + baffles + jet 0.25", "35% + flared + baffles + jet + mu 0.1 (no belt)", "no-belt best + apex share 50%"]
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
    for ax, seq, tt, col in ((axs[0], A, "With conveyor belt", C[0]), (axs[1], B, "Without belt (redundancy if the belt fails)", C[1])):
        seq = [s for s in seq if s in R]
        x = np.arange(len(seq))
        m = [f(R[s], "eta_mean") for s in seq]; cp = [f(R[s], "eta_cp_lo") for s in seq]
        lo = [f(R[s], "eta_ci_lo") for s in seq]; hi = [f(R[s], "eta_ci_hi") for s in seq]
        ax.vlines(x, lo, hi, color=col, lw=2); ax.plot(x, m, "o-", color=col, lw=2, ms=8, mec=SURF, mew=1.5, label="mean, 95% CI over seeds")
        ax.plot(x, cp, "v", color=INK2, ms=6, label="pooled 95% lower bound (Clopper-Pearson)")
        for xx, mm in zip(x, m):
            ax.text(xx, mm + 0.012, f"{mm:.3f}", ha="center", fontsize=8, color=INK)
        ax.axhline(0.99, color=C[2], ls=":", lw=1); ax.text(len(seq) - 0.6, 0.992, "0.99 target", color=C[2], fontsize=8, ha="right")
        ax.set_xticks(x); ax.set_xticklabels([SHORT.get(s, s) for s in seq], fontsize=7.5, rotation=30, ha="right")
        ax.set_title(tt, loc="left"); ax.set_ylim(0.7, 1.03); ax.grid(axis="y")
    axs[0].set_ylabel("eta_r"); axs[0].legend(loc="lower right", fontsize=7.5, frameon=False)
    fig.suptitle("Stacking levers: cumulative eta_r (virtual tank, 30 seeds x 30 bells per step)", x=0.01, ha="left", fontsize=12, weight="bold")
    plt.tight_layout(rect=(0, 0.02, 1, 0.95)); mark(fig); fig.savefig(os.path.join(OUT, "02_stacking_combinations.png"), dpi=130); plt.close()


def proto_chart():
    R = rows("proto_levers.csv")
    pick = [("P2_apex_scoop", "apex + 2 m scoops"), ("P2_apex_scoop", "apex + 4 m scoops"), ("P2_apex_scoop", "apex + 6 m scoops"),
            ("P2_apex_scoop", "NO apex entrance, 2 m"), ("P2_apex_scoop", "NO apex entrance, 4 m"),
            ("P2_apex_scoop", "35% equal split | half flow, rheo 10"), ("P2_apex_scoop", "35% apex share 50% | half flow, rheo 10"),
            ("P8_size_swim", "swim 10.0 cm/s rheotactic, half flow"), ("P9_density", "1.0 /m3"),
            ("COMBO_proto", "v4.1 | nominal"), ("COMBO_proto", "best | nominal"),
            ("COMBO_proto", "v4.1 | half flow, rheo 10, 1 /m3, mu 0.4"), ("COMBO_proto", "best | half flow, rheo 10, 1 /m3, mu 0.4")]
    D = {(r["group"], r["config"]): r for r in R}
    pick = [p for p in pick if p in D]
    fig, axs = plt.subplots(1, 3, figsize=(15, 5.2), sharey=True)
    y = np.arange(len(pick))[::-1]
    for ax, k, lab, col in ((axs[0], "eta_mean", "eta_r", C[0]), (axs[1], "t_face_s", "time on face per bell (s, prototype)", C[1]),
                            (axs[2], "contacts_per_bell", "face contacts per bell", C[2])):
        v = [f(D[p], k) for p in pick]
        ax.barh(y, v, color=col, height=0.6)
        for yy, vv in zip(y, v):
            ax.text(vv, yy, f" {vv:.3g}", va="center", fontsize=7.5, color=INK)
        ax.set_xlabel(lab); ax.grid(axis="x")
        if k == "eta_mean":
            ax.set_xlim(0.6, 1.06)
    axs[0].set_yticks(y); axs[0].set_yticklabels([p[1] for p in pick], fontsize=8)
    fig.suptitle("Prototype scale (28 m lane, 2D CFD + tracker, real 6.5-12 cm bells): an UPPER BOUND on eta_r; damage proxies",
                 x=0.01, ha="left", fontsize=12, weight="bold")
    plt.tight_layout(rect=(0, 0.02, 1, 0.95)); mark(fig); fig.savefig(os.path.join(OUT, "03_prototype_scale.png"), dpi=130); plt.close()


def damage_chart():
    R = {r["config"]: r for r in rows("vt_levers.csv")}
    cfg = ["v4.1 (4 entr, 20%, mu 0.4)", "50% with dewatering", "flared mid mouths x2.0", "belt 0.50 x sweep", "graded baffles (downstream 40%)",
           "mu 0.05", "two screens in series", "+ apex share 50% (= BEST)", "35% + flared + baffles + jet + mu 0.1 (no belt)"]
    cfg = [c for c in cfg if c in R]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6), sharey=True)
    y = np.arange(len(cfg))[::-1]
    for ax, k, lab, col in ((axs[0], "t_face_s_proto", "time on face per bell (s, prototype-equivalent x sqrt 20)", C[1]),
                            (axs[1], "contacts_per_bell", "face contacts per bell", C[2]), (axs[2], "jam_rate", "jam rate (left on face/mouth)", C[3])):
        v = [f(R[c], k) for c in cfg]
        ax.barh(y, v, color=col, height=0.6)
        for yy, vv in zip(y, v):
            ax.text(vv, yy, f" {vv:.2f}" if vv < 10 else f" {vv:.0f}", va="center", fontsize=7.5)
        ax.set_xlabel(lab); ax.grid(axis="x")
    axs[0].set_yticks(y); axs[0].set_yticklabels(cfg, fontsize=8)
    fig.suptitle("Damage proxies in the virtual tank: time on face, contacts, jam rate", x=0.01, ha="left", fontsize=12, weight="bold")
    plt.tight_layout(rect=(0, 0.02, 1, 0.93)); mark(fig); fig.savefig(os.path.join(OUT, "04_damage_proxies.png"), dpi=130); plt.close()


def controller_chart():
    p = os.path.join(RES, "controller.json")
    if not os.path.exists(p):
        return
    R = json.load(open(p))
    fig, axs = plt.subplots(1, 2, figsize=(15, 4.8), gridspec_kw=dict(width_ratios=[2.2, 1]))
    ax = axs[0]
    names = list(R["curve_mean"])
    cols = {names[0]: C[0], names[1]: C[3], names[2]: C[1], names[3]: MUTED, names[4]: C[2]}
    for nm in names:
        c = np.array(R["curve_mean"][nm]); k = 5
        sm = np.convolve(c, np.ones(k) / k, mode="valid")
        ax.plot(np.arange(len(sm)) + k - 1, sm, color=cols[nm], lw=2 if "AI" in nm else 1.5, ls=":" if nm == "oracle" else "-", label=nm)
    for i, (a, b, lab) in enumerate(((0, 30, "nominal 0.3 /m3"), (30, 60, "density -> 1 /m3"), (60, 90, "fouled bay"), (90, 120, "fouled + belt fault"))):
        ax.axvspan(a, b, color="#f0efec" if i % 2 else SURF, zorder=0); ax.text(a + 1, 0.615, lab, fontsize=8, color=INK2)
    ax.set_ylim(0.6, 1.02); ax.set_xlim(0, 120); ax.set_xlabel("epoch (one simulated batch each)"); ax.set_ylabel("eta_r (5-epoch running mean, 200 replays)")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 0.08), fontsize=8, frameon=False); ax.grid(axis="y")
    ax.set_title("AI closed-loop controller vs fixed settings", loc="left")
    ax = axs[1]
    S = R["summary"]; ph = ["nominal", "density 0.3->1", "fouled bay", "fouled + belt fault"]
    w = 0.16
    for i, nm in enumerate(names):
        v = [S[nm][p]["eta"] for p in ph]
        ax.bar(np.arange(4) + (i - 2) * w, v, w * 0.9, color=cols[nm], label=nm)
    ax.set_xticks(np.arange(4)); ax.set_xticklabels(ph, fontsize=7.5, rotation=15); ax.set_ylim(0.6, 1.02); ax.grid(axis="y")
    ax.set_title("Mean eta_r per phase", loc="left")
    plt.tight_layout(rect=(0, 0.02, 1, 1)); mark(fig, "SIMULATED virtual tank + replayed controller - model-based")
    fig.savefig(os.path.join(OUT, "05_ai_controller.png"), dpi=130); plt.close()


def cue_chart():
    vt = rows("vt_levers.csv"); pr = rows("proto_levers.csv")
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for lab, src, key, col in (("tank, v4.1 (jam-limited)", vt, "v4.1 | cue", C[1]), ("tank, best combo (1.000 at every cue; hidden under yellow)", vt, "best | cue", C[0]),
                               ("prototype, half plant flow, rheotactic 10 cm/s", pr, "| half flow, rheo 10", C[2]),
                               ("prototype, full flow, rheotactic 3.6 cm/s", pr, "| full flow, rheo 3.6", C[3])):
        rr = [r for r in src if r["group"] in ("CUE", "CUE_proto") and key in r["config"]]
        x = [float(r["config"].split("cue ")[1].split(" ")[0]) for r in rr]
        o = np.argsort(x); x = np.array(x)[o]
        m = np.array([f(r, "eta_mean") for r in rr])[o]; lo = np.array([f(r, "eta_ci_lo") for r in rr])[o]; hi = np.array([f(r, "eta_ci_hi") for r in rr])[o]
        ax.fill_between(x, lo, hi, color=col, alpha=0.15, lw=0); ax.plot(x, m, "o-", color=col, lw=2, ms=6, label=lab)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_xlabel("HYPOTHETICAL cue-directed swim (cm/s, prototype): - away from apex | + toward apex")
    ax.set_ylabel("eta_r"); ax.set_ylim(0.7, 1.02); ax.grid(axis="y"); ax.legend(fontsize=8, frameon=False, loc="lower right")
    ax.set_title("Behavioural-cue sensitivity (HYPOTHETICAL; no rhizostome phototaxis evidence found, see 09)", loc="left")
    plt.tight_layout(rect=(0, 0.03, 1, 1)); mark(fig, "SIMULATED, HYPOTHETICAL behaviour - model-based")
    fig.savefig(os.path.join(OUT, "06_behaviour_cue_hypothetical.png"), dpi=130); plt.close()


def twin_chart():
    R = rows("twin_eta.csv")
    fig, axs = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
    for ax, hrs in zip(axs, (72, 240)):
        sw = [r for r in R if r["case"].startswith("sweep") and int(r["hours"]) == hrs]
        x = np.array([f(r, "eta_r") for r in sw]); yv = np.array([f(r, "pct_reaching_plant") for r in sw])
        o = np.argsort(x)
        ax.plot(x[o], yv[o], "-", color=MUTED, lw=1.5, label="eta_r sweep")
        ax.plot(x[o], 100 * (1 - x[o]), ":", color=MUTED, lw=1, label="1 - eta_r")
        keep = ["v4.1 published 0.73", "v4.1 (tank: 4 entrances, 20%, batch)", "v4.1 published 0.82 (35%)",
                "two screens in series (tank)", "best combo (tank, 95% lower bound)"]
        named = [r for k in keep for r in R if r["case"] == k and int(r["hours"]) == hrs]
        for i, r in enumerate(named):
            ax.plot(f(r, "eta_r"), f(r, "pct_reaching_plant"), "o", color=C[i % len(C)], ms=8, mec=SURF, mew=1.5,
                    label=f"{r['case']}: {f(r, 'pct_reaching_plant'):.1f}%")
        today = [r for r in R if r["case"].startswith("Today") and int(r["hours"]) == hrs]
        ax.set_title(f"{hrs} h bloom (today, no JAZR: {f(today[0], 'pct_reaching_plant'):.0f}%)" if today else f"{hrs} h", loc="left")
        ax.set_xlabel("inner-screen eta_r"); ax.set_yscale("log"); ax.set_ylim(0.05, 60); ax.grid(which="both", axis="y")
        ax.legend(fontsize=6.8, frameon=False, loc="lower left")
    axs[0].set_ylabel("% of swarm reaching the plant screens (log)")
    fig.suptitle("Plant-scale twin: share reaching the plant's screens vs eta_r (far alongshore release, onshore drift 2.5 cm/s; eta_r = 1 gives 0%)",
                 x=0.01, ha="left", fontsize=12, weight="bold")
    plt.tight_layout(rect=(0, 0.02, 1, 0.94)); mark(fig, "SIMULATED twin (reduced-order, not validated)")
    fig.savefig(os.path.join(OUT, "07_twin_reaching_plant.png"), dpi=130); plt.close()


def survival_chart():
    R = rows("survival_chain.csv")
    fig, ax = plt.subplots(figsize=(11, 5.2))
    y = np.arange(len(R))[::-1]
    for yy, r in zip(y, R):
        col = C[0] if r["screen"].startswith("best") else C[1]
        ax.hlines(yy, f(r, "chain_p05"), f(r, "chain_p95"), color=col, lw=3)
        ax.plot(f(r, "chain_median"), yy, "o", color=col, ms=8, mec=SURF, mew=1.5)
        ax.text(f(r, "chain_p95") + 0.01, yy, f"{f(r, 'chain_median'):.2f} ({f(r, 'chain_p05'):.2f}-{f(r, 'chain_p95'):.2f})", va="center", fontsize=7.5)
    ax.set_yticks(y); ax.set_yticklabels([f"{r['screen']} | {r['lift'].replace('_', ' ')} | pipe {r['pipe'].replace('_0.3m3', ' (0.3/m3)')}" for r in R], fontsize=8)
    ax.set_xlim(0, 1.12); ax.set_xlabel("end-to-end survival of guided bells (median, 5-95%)"); ax.grid(axis="x")
    ax.set_title("Survival chain Monte Carlo (stage ranges = literature analogues + labelled assumptions)", loc="left")
    plt.tight_layout(rect=(0, 0.03, 1, 1)); mark(fig, "MODEL-BASED: no scyphomedusa survival data exist for screws/pumps/pipes")
    fig.savefig(os.path.join(OUT, "08_survival_chain.png"), dpi=130); plt.close()


if __name__ == "__main__":
    for fn in (lever_chart, stack_chart, proto_chart, damage_chart, controller_chart, cue_chart, twin_chart, survival_chart):
        try:
            fn(); print("ok", fn.__name__)
        except Exception as e:
            print("FAIL", fn.__name__, repr(e))
