"""Pitch animation: T03 at 11 deg, NO SCREEN vs SCREEN, same 30 bells, same seed.
SIMULATED virtual tank - not physical evidence.  Writes charts/T03_11deg_noscreen_vs_screen.mp4 and .gif"""
import os, subprocess, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle, Rectangle
from dataclasses import replace
from vtank import Params, Sim, INTAKE, BYPASS, ACTIVE, LABEL

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "charts")
FR = os.path.join(HERE, "results", "_frames")
os.makedirs(OUT, exist_ok=True)
T_SIM, REC, SEED = 45.0, 10, 10000   # 45 s simulated, frame every 0.1 s (2x time-lapse at 20 fps)

SURF, INK, INK2, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#a3a29c"
C_BELL, C_BYP, C_INT, C_SCR = "#2a78d6", "#1baf7a", "#e34948", "#4a3aa7"


def run(screen):
    P = replace(Params(), screen=screen)
    s = Sim(P, SEED, record_every=REC)
    s.release_bells(30)
    s.run(T_SIM, early_stop=False)
    return s


def draw_static(ax, s, title):
    P, g, f = s.P, s.g, s.flow
    sp = np.hypot(f.F[0], f.F[1]).T
    mask = np.ones_like(sp, bool)
    mask[(f.yc > P.y_lo) & (f.yc < P.y_up), :] = False
    sp = np.ma.array(sp, mask=mask)
    ax.imshow(sp, origin="lower", extent=(0, P.Lx, 0, P.Ly), cmap="Blues", vmin=0, vmax=0.2, alpha=0.55,
              interpolation="bilinear")
    for w in g.walls:
        ax.plot(*np.array([w.p0, w.p1]).T, color=INK2, lw=2.5, solid_capstyle="butt")
    x0, x1, y0, y1 = g.pocket
    ax.add_patch(Rectangle((g.E[0], y0), x1 - g.E[0], y1 - y0, color=C_BYP, alpha=0.25, lw=0))
    ax.text(x1 + 0.01, y1 - 0.012, "bypass", color=INK2, fontsize=9, va="top")
    for sm in g.mid_slots:
        p = g.S + sm * g.t
        ax.add_patch(Circle(p + 0.012 * g.n, 0.018, color=C_BYP, alpha=0.3, lw=0))
    if P.screen:
        for sg in g.screens:
            ax.plot(*np.array([sg.p0, sg.p1]).T, color=C_SCR, lw=3)
        ax.text(g.S[0] + 0.30, g.S[1] + 0.02, "roll-down mesh, 11°", color=C_SCR, fontsize=9, rotation=11, rotation_mode="anchor")
    else:
        for sg in g.screens:
            ax.plot(*np.array([sg.p0, sg.p1]).T, color=MUTED, lw=1, ls=(0, (3, 3)))
        ax.text(g.S[0] + 0.30, g.S[1] + 0.02, "screen raised", color=MUTED, fontsize=9, rotation=11, rotation_mode="anchor")
    ax.add_patch(Rectangle((P.Lx - 0.012, P.y_lo), 0.012, P.y_up - P.y_lo, color=C_INT, alpha=0.5, lw=0))
    ax.text(P.Lx - 0.015, P.y_lo - 0.012, "intake pump", color=INK2, fontsize=9, ha="right", va="top")
    ax.annotate("", xy=(0.10, P.y_up + 0.025), xytext=(0.0, P.y_up + 0.025),
                arrowprops=dict(arrowstyle="->", color=INK2, lw=1.2))
    ax.text(0.11, P.y_up + 0.025, "11 cm/s (0.5 m/s at 1:20)", color=INK2, fontsize=9, va="center")
    ax.set_xlim(0, P.Lx); ax.set_ylim(0.09, 0.355)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp_ in ax.spines.values():
        sp_.set_visible(False)
    ax.set_title(title, loc="left", color=INK, fontsize=13, fontweight="bold")


def main():
    sims = [run(False), run(True)]
    nfr = min(len(s.frames) for s in sims)
    if os.path.exists(FR):
        shutil.rmtree(FR)
    os.makedirs(FR)
    fig, axes = plt.subplots(2, 1, figsize=(12.8, 7.2), dpi=100, facecolor=SURF)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.08, hspace=0.25)
    titles = ["A  No screen (baseline, T02)", "B  JAZR roll-down screen at 11° + 2 bypass entrances (T03)"]
    for ax, s, t in zip(axes, sims, titles):
        draw_static(ax, s, t)
    fig.suptitle("JAZR Gate v3 · virtual tank, 1:20 Froude scale · 30 surrogate bells", x=0.02, ha="left",
                 color=INK, fontsize=15, fontweight="bold", y=0.975)
    fig.text(0.02, 0.915, "SIMULATED virtual tank — not physical evidence. Model counts, not video counts.",
             color=C_INT, fontsize=11, fontweight="bold")
    fig.text(0.02, 0.025, "Plan view. Blue discs = surrogate bells; a bell disappears when the bypass (green zones) or the intake pump (red) takes it. "
             "Background shade = flow speed. Time-lapse 2x.", color=INK2, fontsize=9)
    dyn = []
    for k in range(nfr):
        for a in dyn:
            a.remove()
        dyn = []
        for ax, s in zip(axes, sims):
            t, pos, st, d, kind, con, raised = s.frames[k]
            show = (st == ACTIVE)
            pc = PatchCollection([Circle((pos[i, 0], pos[i, 1]), d[i] / 2) for i in np.nonzero(show)[0]],
                                 facecolor=C_BELL, edgecolor=SURF, linewidths=1.0, alpha=0.85)
            dyn.append(ax.add_collection(pc))
            nb, ni = int((st == BYPASS).sum()), int((st == INTAKE).sum())
            na = int(show.sum())
            box = f"t = {t:4.1f} s    bypass {nb:2d}    intake {ni:2d}    still in tank {na:2d}"
            dyn.append(ax.text(0.30, 0.105, box, color=INK, fontsize=11, family="monospace"))
        fig.savefig(os.path.join(FR, f"f{k:04d}.png"), facecolor=SURF)
        if k == nfr - 1:
            fig.savefig(os.path.join(OUT, "T03_11deg_final_frame.png"), facecolor=SURF)
        if k == nfr // 5:
            fig.savefig(os.path.join(OUT, "T03_11deg_early_frame.png"), facecolor=SURF)
    plt.close(fig)
    ff = "/opt/homebrew/bin/ffmpeg"
    mp4 = os.path.join(OUT, "T03_11deg_noscreen_vs_screen.mp4")
    gif = os.path.join(OUT, "T03_11deg_noscreen_vs_screen.gif")
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", "20", "-i", os.path.join(FR, "f%04d.png"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], check=True)
    subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", "20", "-i", os.path.join(FR, "f%04d.png"),
                    "-vf", "fps=10,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse",
                    gif], check=True)
    shutil.rmtree(FR)
    for s, n in zip(sims, ("no screen", "screen")):
        print(n, s.summary())


if __name__ == "__main__":
    main()
