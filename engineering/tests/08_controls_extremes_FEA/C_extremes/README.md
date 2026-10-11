# C. Extreme events: operating and survival envelopes

**Data.**

- Open-Meteo ERA5 hourly wind 2015-2025.
- Open-Meteo marine hourly 2022-2025, near-site and offshore.

All files are in `../../00_data/raw`. Reanalysis smooths peaks, so data-based extreme-value results are a **lower bound**. Design uses the larger of data and literature.

**Literature** (full citations in `common/params.py` SOURCES):

- Neelamani et al. (WAM hindcast): 100-yr Hs 3.0-4.5 m at 9-16 m depth.
- Varghese et al. 2016: Jebel Ali 1:100 water level 2.71 mCD, including sea-level rise to 2058.
- IPCC AR6: sea-level rise to 2100 is 0.63-1.01 m under SSP5-8.5.
- Dubai basic wind: 38-45 m/s 3-s gust. The Abu Dhabi municipal value was not found.
- NORSOK M-001 via TWI: 25Cr duplex seawater limit of 20 °C with crevices.
- ENEC 2012: the plant is a "dry site".

| # | Check | Result |
|---|---|---|
| C1 | Survival wind 45 m/s vs ERA5 Gumbel 100-yr gust 23.5 m/s | **PASS** (FEA SURV cases pass at 45 m/s) |
| C2 | Motion interlock at 20 m/s gust | **PASS**: never exceeded in 11 years of ERA5 (reanalysis under-reads gusts) |
| C3 | Design Hs100 4.0 m vs data POT (near 1.8 m, offshore 4.0 m from 4 years) | **PASS** (literature governs) |
| C4 | Wave dP on a deployed mesh | **INFO**: Hs 1.7 m gives a wave dP peak of half the trip level; the hard limit is reached at about Hs 4 m. A filter is required (see D6) |
| C5 | Deck air gap in 2085 (soffit +5.6 m MSL) | Inner gantry, sheltered Kt 0.5 [ASM], SSP5-8.5: 0.4 m, **MARGINAL**. Low-confidence high-end: **FAIL**. **Outer guide line (exposed): FAIL by 2.4 m.** Raise the soffit to about +7 m (inner) or +9 m (outer), or design the outer trestle to be overtopped |
| C6 | Low tide (LAT -1.2 m) screen approach velocity | 0.128 m/s at 100 m³/s on a -5.5 m bed: **MARGINAL**. At 172.5 m³/s it is 0.22 m/s: **FAIL** vs the NMFS 0.12 m/s limit. Size the area at LAT and max flow (about 1,900 m²) |
| C7 | Duplex mesh and crevices at SST 36-38 °C (data max 36.3 °C) | **FAIL** vs the 20 °C crevice limit. Use titanium, Cu-Ni 90/10 or polymer for wetted parts |
| C8 | Drives and electronics vs air temperature (ERA5 grid max 41.2 °C; inland UAE is hotter) | **MARGINAL** vs a 40 °C rating: derate, shade and cool the panels |
| C9 | HDPE pipe at 38 °C | **PASS** (low-pressure duty) |
| C10 | Dust and sandstorm | **INFO**: 4.9 % of hours have 10-m wind above 8 m/s (dust-lifting proxy). Need IP66, a drum shroud, brushing on lowering and lens wash |
| C11 | Storm vs bloom policy | **MARGINAL**: block motion above 20 m/s but keep deployed bays down (onshore wind drives blooms). The deployed-storm load case is still to be designed |

Run: `python3 run_extremes.py` (~3 s). Figure: `figs/extremes.png`.
