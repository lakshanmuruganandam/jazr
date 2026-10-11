# B. Seismic response-spectrum check of the gantry

**Method.** We use the same FE model as A, 20 modes (95 % mass participation in x and y), CQC modal combination at 5 % damping, 100/30 directional combination plus dead load, elastic (R = 1). Submerged piles carry added mass plus entrained water.

**Spectra** (ASCE 7 / IBC 2009 shape):

| Spectrum | Basis | Criterion | Max utilisation |
|---|---|---|---|
| S1 IBC design | Irfan et al. 2012 (15WCEE paper 5594, Table 4): Abu Dhabi 2475-yr rock **PGA 0.074 g, Ss 0.178 g, S1 0.075 g**. Site Class D assumed (Fa 1.6, Fv 2.4), SDS = 2/3 SMS | σ ≤ 0.8 fy | 0.14 **PASS** |
| S2 MCE (Seismic II/I no-collapse) | same, not reduced | σ ≤ fy | 0.16 **PASS** |
| S3 nuclear envelope | ASCE shape anchored at **PGA 0.3 g**, plateau 0.75 g. This is the APR1400 standard-design level [verify]; the plant's site-specific SSE is not public | σ ≤ fy | 0.39 **PASS** |

The PDF source is saved in this folder. the plant is about 250 km west of Abu Dhabi city. The paper's map shows little variation across the Emirate of Abu Dhabi. We still use the city value with Site D amplification, and S3 bounds it.

**Nuclear classification (INFO, qualitative).**

- The gantry sits in the cooling-water path, near or upstream of safety-related intake structures. It would normally be **Seismic Category II/I**: it must not collapse onto, or block, safety SSCs. Our analysis shows that, with large margin, as long as the real site SSE is within about 2.5x the 0.3 g envelope.
- Still needed:
  - site SSE spectra from the Nawah FSAR;
  - soil-structure interaction and **liquefaction of reclaimed or dredged sand** (not modelled);
  - seismic qualification of drum brakes and drives;
  - a PLC seismic trip that triggers fail-open (tested in D13: about 34 min for staged all-up);
  - debris and tsunami loads.

Run: `python3 run_seismic.py` (~20 s).
