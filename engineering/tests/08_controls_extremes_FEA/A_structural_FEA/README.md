# A. Structural FEA of one gantry bay + mesh panel check

**What we built.** We wrote a 3D Euler-Bernoulli frame finite-element solver (`common/fe3d.py`, 12 DOF per element). It does linear statics, modal analysis with hydrodynamic added mass and linear buckling. It is checked against closed-form answers in `tests/test_fe3d.py`: cantilever deflection in both planes, axial, torsion, root stress, first frequency, tip-mass frequency, Euler buckling and portal sway (7 tests, all passing).

**Model** (`common/gantry.py`). The model is one 10 m bay with:

- 2 piles: CHS 1016 x 22 mm effective (25 mm minus 3 mm corrosion), S355, fixed at 5D below a -7.5 m MSL bed.
- A box girder (800 x 600 x 20 mm) at +6.0 m.
- 2 duplex 2205 posts and a 610 mm drum at +7.5 m.

The v3 design gives no member sizes, so all sizes are our assumptions [ASM]. Every assumption sits in `common/params.py`.

**Loads.**

- Dead load and live load.
- Roll-up line tension: submerged mesh + bottom bar + 0.3 rail friction x dP, all x1.3.
- Mesh dP. The mesh is modelled as a **membrane spanning between the two pile rails**. It loads the piles normal to the screen (dP x 5 m per metre). It also creates an inward membrane pull of dP·L/(8·sag), which is unbalanced whenever the neighbouring bays are rolled up.
- Morison wave + current with linear theory and Wheeler stretching, scanned over phase.
- Wind at 45 m/s 3-s gust (survival) and 20 m/s (operating).

**Load cases.**

- OP1 operating: 1.5 x the 500 Pa trip, Hs 1 m, 0.5 m/s current, 20 m/s wind. Allowable 0.6 fy.
- ACC1 stuck drum on a blinded bay at 3 kPa. Allowable 0.91 fy.
- SURV stowed 100-yr storm: Hs 4.0 m, Hmax 7.4 m (depth-limited), T 8 s, SWL = HAT + 0.6 m surge + 0.61 m sea-level rise to 2085, 1 m/s current, 45 m/s wind, three directions. Allowable 0.8 fy.

| Run | Result (see `out/fea_results.json`) |
|---|---|
| Stress, all cases (A1) | max utilisation OP1 0.38, ACC1 0.81, SURV 0.32-0.59: **PASS** |
| Pile deflection (A2) | operating 21 mm vs 25 mm rail limit: **PASS (tight)**. Accident 50 mm: **PASS** |
| Modal (A3) | f1 = 1.50 Hz (T1 0.67 s), normal to the gantry; f2 = 2.35 Hz. Nothing in the 2-8 s wave band: **PASS** |
| VIV (A4) | reduced velocity Vr 0.84 at 1.4 m/s current: **PASS** (close to the in-line onset of 1) |
| Buckling (A5) | load factor 103: **PASS** |
| Fatigue, 60 y (A6) | DNV-RP-C203 curve D, Open-Meteo hourly Hs/Tm 2022-25, Rayleigh waves, DAF, DFF 3. D x DFF = 0.06 even in free corrosion: **PASS** |
| Sensitivity (A7) | fixity 3-7D: worst 0.89, **PASS**. Membrane sag 2 %: ACC1 1.08, **FAIL**. Sag 5-8 %: 0.46-0.58 |

**Mesh check** (`mesh_check.py`, `out/mesh_check.json`). Woven 2205 mesh with 2.5 mm wire, 10 mm aperture, porosity 0.64, 6.4 kg/m².

- Wire tension as a membrane is fine at every dP: 0.29-0.78 of allowable, sag 0.21-0.33 m. **PASS.**
- **Wrapping on the 0.61 m drum bends each wire to E·d/D = 820 MPa, above yield.** That is plastic every roll-up, about 56,000 wraps in 60 y. **FAIL.** To fix it you need one of:
  - a drum of at least 2.8 m;
  - wire of at most 0.55 mm;
  - better, a **hinged-link / balanced-weave belt or a polymer mesh**.
- A rigid wedge-wire panel would pass in strength (271 MPa), but it cannot roll up.

**Design implications.**

1. Specify a slack membrane (sag at least 3-5 %) or **shear-release edge clips**. The clips double as passive fail-open above the hard limit. Without them, the end and neighbour piles of a taut, blinded bay are overstressed.
2. Replace the "woven wire on drum" with an articulated or polymer mesh. This also fixes corrosion: see C7.
3. Deflection, not strength, governs the piles in operation (rail alignment).

**Limits.** Static and quasi-static only. There is no p-y soil model (equivalent fixity instead) and no wave-in-deck slam. Both piles are loaded in phase, which is conservative. Section sizes are our own.

Run: `python3 run_fea.py` (~2 min) and `python3 mesh_check.py`.
