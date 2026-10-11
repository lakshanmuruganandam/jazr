"""make_gif.py - before/after GIF: v4.1 screen vs best combination in the virtual tank (same seed, same bells).
*** SIMULATED virtual tank (1:20) - not physical evidence. *** -> charts/before_after_v41_vs_best.gif"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from dataclasses import replace
from vt_ext import ParamsX, SimX, BYPASS, ACTIVE
from run_vt import V41, BEST_PRACTICAL

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "charts")
SEED, T, REC = 1003, 90.0, 20


def run(kw):
    P = replace(ParamsX(), **dict(V41, **kw))
    s = SimX(P, SEED, record_every=REC)
    s.release_bells(30)
    s.run(T, early_stop=False)
    return s


def draw_geom(ax, s, title):
    P, g = s.P, s.g
    for w in g.walls:
        ax.plot(*np.c_[w.p0, w.p1], color="#444", lw=2)
    for sc in g.screens:
        ax.plot(*np.c_[sc.p0, sc.p1], color="#2b6cb0", lw=2.5, ls="--" if P.belt_frac == 0 else "-")
    for sm in g.mid_slots:
        c = g.S + sm * g.t
        ax.plot(*np.c_[c - P.slot_w / 2 * g.t, c + P.slot_w / 2 * g.t], color="#38a169", lw=5, solid_capstyle="butt")
    x0, x1, y0, y1 = g.pocket
    ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, color="#38a169", alpha=0.25))
    ax.set_xlim(0, 1.05); ax.set_ylim(P.y_lo - 0.01, P.y_up + 0.01); ax.set_aspect("equal")
    ax.set_title(title, fontsize=10, loc="left"); ax.set_xticks([]); ax.set_yticks([])


def main():
    A = run({}); B = run(BEST_PRACTICAL)
    fig, axs = plt.subplots(2, 1, figsize=(9, 5.0), dpi=90)
    labs = ["BEFORE  v4.1: 4 entrances, 20% entrance flow, static mesh, mu 0.4",
            "AFTER  best: belt 0.5x sweep, 35% flow, flared mouths, graded baffles, wall jet, mu 0.1"]
    sims = [A, B]
    nf = min(len(A.frames), len(B.frames))
    fig.text(0.5, 0.01, "SIMULATED virtual tank (1:20 Froude) - model-based, not a physical test", ha="center",
             color="white", backgroundcolor="#c53030", fontsize=9, weight="bold")
    def upd(k):
        for ax, s, lab in zip(axs, sims, labs):
            ax.cla(); draw_geom(ax, s, lab)
            t, pos, st, d, kind, cont, raised = s.frames[k]
            col = np.where(st == BYPASS, "#38a169", np.where(cont, "#e53e3e", "#d69e2e"))
            vis = st == ACTIVE
            ax.scatter(pos[vis, 0], pos[vis, 1], s=(d[vis] * 900) ** 2 / 12, c=col[vis], edgecolors="k", linewidths=0.3)
            nb = int((st == BYPASS).sum()); nst = int((vis & cont).sum())
            ax.text(0.01, 0.04, f"t = {t:4.0f} s   guided {nb}/30   on face {nst}", transform=ax.transAxes, fontsize=9,
                    bbox=dict(fc="white", ec="none", alpha=0.8))
        return []
    idx = list(range(0, nf, 2))
    an = FuncAnimation(fig, upd, frames=idx, interval=80)
    an.save(os.path.join(OUT, "before_after_v41_vs_best.gif"), writer=PillowWriter(fps=12))
    print("frames", len(idx), "A guided", int((A.status == BYPASS).sum()), "B guided", int((B.status == BYPASS).sum()))


if __name__ == "__main__":
    main()
