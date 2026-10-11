"""T2 Analytic verification of the twin's flow kinematics (swim = 0, deterministic drifters).
 (a) steady uniform current U + half-plane sink: capture band width W = Q/(U h) far upstream
 (b) downstream stagnation point on the coast at r* = Q/(pi h U)
 (c) zero ambient flow: capture radius after time t, r0 = sqrt(R_CAP^2 + 2 Q t/(pi h))
 (d) tidal excursion, no sink: peak-to-peak 2 U0/omega
 (e) alongshore arrival time at the ring vs exact ODE solution
Uses harness.simulate (proven bit-identical to jazr_twin.simulate) with module constants patched."""
import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from common import J, patched, save, FIGS
from harness import simulate as HS

def band_edge(U, dt=60.0, n=600, ymax=None, x0=-8000.0):
    Wth = J.Q/(U*J.H); ymax = ymax or 2.0*Wth
    y0 = np.linspace(1.0, ymax, n); x0a = np.full(n, x0)
    hours = (abs(x0)+3000)/U/3600 + 12
    with patched(U0=0.0):
        _, o = HS(init_xy=(x0a, y0), swim=0.0, ur=U, hours=hours, dt=dt)
    c = o["state"] == 2
    edge = 0.5*(y0[c].max() + y0[~c & (y0 > y0[c].max())].min())
    # exact dividing streamline of psi = U h y - (Q/pi) theta through the stagnation point, evaluated at the
    # finite start x0: y = (Q/(pi U h)) * (pi - atan(y/|x0|))  (-> W = Q/(U h) as x0 -> -inf)
    yex = Wth
    for _ in range(100): yex = Wth*(1 - np.arctan(yex/abs(x0))/np.pi)
    return dict(U=U, dt=dt, W_theory=Wth, W_exact_at_x0=float(yex), W_twin=float(edge), rel_err_vs_W=float(edge/Wth-1),
                rel_err=float(edge/yex-1),
                monotone=bool(np.all(c[y0 < y0[c].max()])), dy=float(y0[1]-y0[0]))

def stagnation(U, dt=60.0, n=400):
    rs = J.Q/(np.pi*J.H*U)
    x0 = np.linspace(J.R_CAP+5, 2.0*rs, n)
    with patched(U0=0.0):
        _, o = HS(init_xy=(x0, np.full(n, 0.5)), swim=0.0, ur=U, hours=48, dt=dt)
    c = o["state"] == 2
    edge = 0.5*(x0[c].max() + x0[~c & (x0 > x0[c].max())].min())
    return dict(U=U, dt=dt, rstar_theory=rs, rstar_twin=float(edge), rel_err=float(edge/rs-1), dx=float(x0[1]-x0[0]))

def zero_flow(hours=72, dt=60.0, n=600):
    rth = np.sqrt(J.R_CAP**2 + 2*J.Q*hours*3600/(np.pi*J.H))
    th = np.linspace(0.05, np.pi-0.05, n); r0 = np.linspace(600, 2*rth, n)
    with patched(U0=0.0):
        _, o = HS(init_xy=(r0*np.cos(th), r0*np.sin(th)), swim=0.0, hours=hours, dt=dt)
    c = o["state"] == 2
    edge = 0.5*(r0[c].max() + r0[~c & (r0 > r0[c].max())].min())
    return dict(hours=hours, dt=dt, r_theory=float(rth), r_twin=float(edge), rel_err=float(edge/rth-1))

def excursion(dt=60.0):
    with patched(Q=0.0):
        _, o = HS(init_xy=(np.array([0.0]), np.array([5000.0])), swim=0.0, hours=12.42, dt=dt, phase0=0.0)
    # rerun recording positions every step
    xs = []
    with patched(Q=0.0):
        for h in np.arange(dt, 12.42*3600+dt, dt*10)/3600:
            xs.append(HS(init_xy=(np.array([0.0]), np.array([5000.0])), swim=0.0, hours=h, dt=dt)[1]["x"][0])
    xs = np.array(xs + [0.0])
    th = 2*J.U0/J.W
    return dict(dt=dt, excursion_theory=float(th), excursion_twin=float(xs.max()-xs.min()), rel_err=float((xs.max()-xs.min())/th-1))

def arrival(U=0.1, d=4000.0, dt=60.0):
    a = J.Q/(np.pi*J.H); R = J.R_I
    t_th = (d-R)/U - a/U**2*np.log((U*d+a)/(U*R+a))
    with patched(U0=0.0):
        _, o = HS(init_xy=(np.array([-d]), np.array([0.5])), swim=0.0, ur=U, hours=t_th/3600*1.5, dt=dt)
    return dict(U=U, d=d, dt=dt, t_theory_h=float(t_th/3600), t_twin_h=float(o["t_arr"][0]/3600),
                rel_err=float(o["t_arr"][0]/t_th-1))

if __name__ == "__main__":
    R = {"band": [], "stag": [], "zero": [], "exc": [], "arrival": []}
    for U in (0.05, 0.083, 0.117, 0.15):
        for dt in (30.0, 60.0, 120.0):
            R["band"].append(band_edge(U, dt)); R["stag"].append(stagnation(U, dt))
            R["arrival"].append(arrival(U, 4000.0, dt))
            print("band", R["band"][-1]); print("stag", R["stag"][-1]); print("arr", R["arrival"][-1], flush=True)
    for dt in (30.0, 60.0, 120.0):
        R["zero"].append(zero_flow(72, dt)); R["exc"].append(excursion(dt))
        print("zero", R["zero"][-1]); print("exc", R["exc"][-1], flush=True)
    save("t2_analytic.json", R)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for dt, m in ((30.0, "o"), (60.0, "s"), (120.0, "^")):
        b = [r for r in R["band"] if r["dt"] == dt]; s = [r for r in R["stag"] if r["dt"] == dt]
        ax[0].plot([r["U"] for r in b], [r["W_twin"] for r in b], m, label=f"twin dt={dt:.0f}s")
        ax[1].plot([r["U"] for r in s], [r["rstar_twin"] for r in s], m, label=f"twin dt={dt:.0f}s")
    Us = np.linspace(0.045, 0.155, 100)
    ax[0].plot(Us, J.Q/(Us*J.H), "k-", label="W = Q/(U h) (x0 -> -inf)")
    ax[0].plot([r["U"] for r in R["band"] if r["dt"] == 60.0], [r["W_exact_at_x0"] for r in R["band"] if r["dt"] == 60.0], "k--", label="exact streamline at x0 = -8 km"); ax[0].set_xlabel("steady current U (m/s)"); ax[0].set_ylabel("capture band width (m)")
    ax[1].plot(Us, J.Q/(np.pi*J.H*Us), "k-", label="r* = Q/(pi h U)"); ax[1].set_xlabel("steady current U (m/s)"); ax[1].set_ylabel("stagnation distance (m)")
    for a in ax: a.legend(frameon=False); a.grid(alpha=.3)
    fig.suptitle("T2 analytic verification: twin vs closed-form sink-in-current solution")
    fig.tight_layout(); fig.savefig(f"{FIGS}/t2_analytic.png", dpi=130)
