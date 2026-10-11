"""B. Response-spectrum seismic check of one gantry bay (same FE model as A).

Spectra (5 % damping, ASCE 7 / IBC 2009 shape: 0.4SDS->SDS plateau T0..Ts, SD1/T beyond, TL=8 s):
  S1 'IBC design':  Irfan et al. 2012 Table 4, Abu Dhabi 2475-yr rock Ss=0.178 g, S1=0.075 g
                    (the plant is ~250 km W of Abu Dhabi city; western region shows little difference
                    in their PGA map) -> Site Class D (dredged/reclaimed marine sand assumed):
                    Fa=1.6, Fv=2.4 -> SMS, SM1; design SDS=2/3 SMS.
  S2 'MCE (II/I)':  same, not reduced by 2/3 (structure must not collapse onto safety items).
  S3 'Nuclear envelope': ASCE shape anchored at PGA = 0.3 g (APR1400 standard design CSDRS level,
                    plateau 2.5 x PGA). the plant site-specific SSE is not public; this is a bounding case.
Modal combination CQC (5 %), directions combined 100/30, plus dead load. Elastic (R = 1) -> stress
must stay <= fy (II/I no-collapse, conservative) and <= 0.8 fy for the IBC design case.
Hydrodynamic added mass + entrained water on submerged piles included (Ca = 1).
"""
import json, sys, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import params as P
from common import gantry as GT

Ss, S1 = 0.178, 0.075
Fa, Fv = 1.6, 2.4


def asce_spectrum(SDS, SD1, TL=8.0):
    T0, Ts = 0.2 * SD1 / SDS, SD1 / SDS
    def Sa(T):
        T = np.asarray(T, float)
        return np.where(T < T0, SDS * (0.4 + 0.6 * T / T0),
               np.where(T <= Ts, SDS, np.where(T <= TL, SD1 / np.maximum(T, 1e-9), SD1 * TL / T**2)))
    return Sa


SPECTRA = {
    "S1 IBC design (2/3 MCE, Site D)": (asce_spectrum(2 / 3 * Fa * Ss, 2 / 3 * Fv * S1), 0.80),
    "S2 MCE 2475-yr (Seismic II/I no-collapse)": (asce_spectrum(Fa * Ss, Fv * S1), 1.00),
    "S3 nuclear envelope PGA 0.3 g": (asce_spectrum(0.75, 0.75 * 0.6), 1.00),  # Ts=0.6 s (RG1.60-like broad plateau) [ASM]
}


def cqc(R, w, zeta=0.05):
    n = len(w)
    rho = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            r = w[j] / w[i]
            rho[i, j] = 8 * zeta**2 * (1 + r) * r**1.5 / ((1 - r**2) ** 2 + 4 * zeta**2 * r * (1 + r) ** 2)
    return np.sqrt(np.abs(np.einsum("i...,ij,j...->...", R, rho, R)))


def main():
    f, g, secs, info = GT.build()
    grp = GT.elem_group(f, g)
    nm = 20
    fr, Phi, M, free = f.modal(nm)
    w = 2 * np.pi * fr
    Mfull = f.M()
    total_mass = sum(Mfull[i, i] for i in range(0, f.ndof, 6) if i in set(free))
    K = f.K()
    Fd = GT.load_dead(f, g)
    ud = f.solve(Fd)
    sd, fld = f.stresses(ud)
    results, verdicts = {}, []
    for name, (Sa, allow) in SPECTRA.items():
        dir_resp = {}
        mass_part = {}
        for k_dir, dname in ((0, "x"), (1, "y")):
            r = np.zeros(f.ndof); r[k_dir::6] = 1.0
            # modal responses (member end forces) per mode
            Fm, Um = [], []
            eff = 0
            for m in range(nm):
                ph = Phi[:, m]
                Mn = ph @ Mfull @ ph
                Gam = (ph @ Mfull @ r) / Mn
                eff += Gam**2 * Mn
                A = Sa(1 / fr[m]) * P.G
                u = ph * Gam * A / w[m] ** 2
                Um.append(u)
                Fm.append(np.array(f.member_forces(u)))
            mass_part[dname] = float(eff / total_mass)
            Fm = np.array(Fm)            # modes x elems x 12
            Um = np.array(Um)
            dir_resp[dname] = (cqc(Fm, w), cqc(Um, w))
        # 100/30 combination, add dead load, compute stress per element
        smax = np.zeros(len(f.elems))
        for a, b in (("x", "y"), ("y", "x")):
            Fc = dir_resp[a][0] + 0.3 * dir_resp[b][0]
            for i, e in enumerate(f.elems):
                sec = e["sec"]
                for o in (0, 6):
                    N = abs(fld[i][o]) + Fc[i][o]
                    s = N / sec.A + (abs(fld[i][o + 4]) + Fc[i][o + 4]) / sec.Wy + (abs(fld[i][o + 5]) + Fc[i][o + 5]) / sec.Wz
                    smax[i] = max(smax[i], s)
        row = {}
        for gn in sorted(set(grp)):
            idx = [i for i, x in enumerate(grp) if x == gn]
            fy = f.elems[idx[0]]["sec"].mat["fy"]
            row[gn] = dict(sigma_MPa=round(float(smax[idx].max()) / 1e6, 1), util=round(float(smax[idx].max()) / (allow * fy), 3))
        top = g["pile1"][-1]
        ux = dir_resp["x"][1][6 * top]; uy = dir_resp["y"][1][6 * top + 1]
        row["pile_head_disp_mm"] = dict(x=round(1e3 * float(ux), 1), y=round(1e3 * float(uy), 1))
        row["mass_participation_20_modes"] = mass_part
        row["Sa_at_T1_g"] = round(float(Sa(1 / fr[0])), 3)
        um = max(v["util"] for v in row.values() if isinstance(v, dict) and "util" in v)
        row["util_max"] = um
        results[name] = row
        verdicts.append(dict(test=f"B1 seismic RSA {name.split(' ')[0]}", value=um,
                             criterion=f"stress <= {allow:.2f} fy (elastic, R=1)",
                             verdict="PASS" if um <= 0.9 else ("MARGINAL" if um <= 1 else "FAIL"),
                             detail=f"{name}; Sa(T1)={row['Sa_at_T1_g']} g; head disp {row['pile_head_disp_mm']}"))
    # qualitative nuclear classification item
    verdicts.append(dict(test="B2 nuclear seismic classification", value="Seismic II/I (assumed)",
                         criterion="Structure in UHS/CW path near safety SSCs must not collapse onto them or block the intake; "
                                   "the plant site SSE & intake layout not public",
                         verdict="INFO",
                         detail="Needs: site-specific SSE spectra from Nawah FSAR Ch.2/3; II/I interaction analysis; "
                                "post-quake fail-open (all bays up) on PLC seismic trip; seismic qualification of drum brakes"))
    out = dict(spectra_params=dict(Ss=Ss, S1=S1, Fa=Fa, Fv=Fv, SDS=2 / 3 * Fa * Ss, SD1=2 / 3 * Fv * S1,
                                   source="Irfan et al. 2012 15WCEE Table 4 (ABD)"),
               periods_s=[float(1 / x) for x in fr[:8]], results=results, verdicts=verdicts)
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(out, open(HERE / "out" / "seismic_results.json", "w"), indent=2)

    T = np.linspace(0.01, 4, 400)
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for name, (Sa, _) in SPECTRA.items():
        ax.plot(T, Sa(T), label=name)
    for t in 1 / fr[:4]:
        ax.axvline(t, color="#888", lw=0.7, ls="--")
    ax.text(1 / fr[0], 0.05, " T1", fontsize=8)
    ax.set_xlabel("period (s)"); ax.set_ylabel("Sa (g), 5 % damping"); ax.set_title("Spectra used and gantry modal periods")
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(HERE / "figs" / "spectra.png", dpi=150)
    for v in verdicts:
        print(f"{v['verdict']:9s} {v['test']}: {v['value']} [{v['criterion']}] {v.get('detail','')}")


if __name__ == "__main__":
    main()
