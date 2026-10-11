# 00_data: real data checks for the JAZR twin

All data were accessed on **2026-10-11**. They come from public sources that need no login. Raw downloads are in `raw/<source>/` and total about 15 MB. They are treated as untrusted data: nothing in them is executed, and they are parsed only with `python3 -I`.

Scripts are in `scripts/`. Outputs (CSV, JSON, PNG) are in `out/`. To reproduce:

```
python3 -I scripts/analyse_metocean.py  <this dir>
python3 -I scripts/analyse_bio_extra.py <this dir>
```

Sign convention: **onshore** means the component toward 160° (SSE). This assumes the the plant coast trends about 070/250°. A different coast angle shifts the onshore numbers slightly.

## Datasets

| # | Dataset | URL (as queried) | What it shows | Key numbers |
|---|---|---|---|---|
| 1 | Open-Meteo Marine API: Copernicus SMOC currents (incl. tides + Stokes), CMEMS waves, SST; hourly 2022-01-01 to 2025-12-31 | `https://marine-api.open-meteo.com/v1/marine?latitude=24.04&longitude=52.21&...` (cell 24.042N 52.208E). Also an offshore cell at 24.625N 52.292E | Currents, waves and SST at the cell nearest the intake | 34,968 h of currents. Speed mean 0.086, median 0.083, p90 0.139, p99 0.194, max 0.389 m/s. **The current is reported in km/h to one decimal, so speeds come in 0.028 m/s steps. "Median 0.083" is just the 0.3 km/h step.** Hs median 0.22, p99 0.88, max 1.42 m; offshore max 2.20 m; Tp about 2.5–3 s. SST 19.1–35.9 °C. Daily sea-level range median 1.42 m, max 2.38 m. See `out/metocean_monthly_openmeteo.csv` and `out/metocean_summary.json` |
| 2 | Tidal harmonic fit (my least-squares fit of M2, S2, N2, K2, K1, O1, P1, M4 to dataset 1 u/v) | derived | Tidal ellipses | M2 major axis 0.073 m/s (minor 0.009) toward about 080°, i.e. alongshore. S2 0.035, K1 0.037, O1 0.016, N2 0.019. Tides explain 52% of current variance. Tide-only speed median 0.052, p90 0.109 m/s. Mean flow (0.007, −0.029) m/s. TPXO itself needs registration, so it was **not used** |
| 3 | HYCOM GLBy0.08 expt_93.0 surface u/v (no tides), 3-hourly, Oct–Nov of 2019–2023 | `https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/uv3z?var=water_u&var=water_v&latitude=24.04&longitude=52.21&...&vertCoord=0&accept=csv` | An independent estimate of the sub-tidal (residual) flow | Values are stored packed; scale 0.001 applied (from dataset.xml). Speed median 0.031, p90 0.059 m/s. Mean onshore 2.3 cm/s (by year: 1.8–2.7). p90 of daily means 3.6 cm/s. See `out/hycom_octnov_surface_currents.csv` |
| 4 | ERA5 10 m wind via the Open-Meteo archive, hourly 2015–2025 | `https://archive-api.open-meteo.com/v1/archive?latitude=24.10&longitude=52.20&models=era5&...` (sea cell 24.0N 52.25E) | Monthly wind climate | Oct–Nov mean 4.0–4.3 m/s, p99 8.0–8.7, max 11.1 m/s. Mean onshore wind component 1.9–2.2 m/s. The windiest months are Jan–Mar (max 13.5 m/s). See `out/wind_monthly_era5.csv` |
| 5 | NOAA OISST v2.1 daily SST via ERDDAP (ncdcOisst21Agg_LonPM180), 1995–2025, cell 24.125N 52.125E | `https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv?sst[...][(0.0)][(24.125)][(52.125)]` | Long SST record | 1995–99 has gaps (the server returned only 1,120 days). Oct mean 31.4 °C (range 28.0–35.1); Nov 27.9 °C (24.5–31.3). Absolute range 17.3–36.7 °C. 242 days >35 °C. Oct–Nov trend +0.15 °C/decade. See `out/sst_monthly_oisst.csv` and `out/sst_annual_oisst.csv` |
| 6 | OBIS + GBIF occurrences of Rhizostomeae in a Gulf box (47–57.5E, 23–30.5N) | `https://api.obis.org/v3/occurrence?scientificname=Rhizostomeae&geometry=POLYGON(...)` and `https://api.gbif.org/v1/occurrence/search?scientificName=Rhizostomeae&geometry=...` | Which rhizostomes are recorded in the Gulf, and where | 35 unique *Catostylus* records (OBIS and GBIF overlap; both are iNaturalist research grade, 2001–2025). **33 are *C. perezi*, 2 are *C. mosaicus*.** The nearest is 173 km from the plant, so there are no records near the plant (a sampling gap, not proof of absence). Months: Mar–Apr 13, Sep–Oct 10, Dec 4, others ≤3. Presence only: **no densities.** See `out/catostylus_occurrences_gulf_dedup.csv` and `out/rhizostome_occurrences_gulf.csv` |
| 7 | OBIS-SEAMAP Gulf Green Turtle Project 2016–2019 (Pilcher et al.; doi 10.82144/c55cd1c3; Pilcher et al. 2020, Glob. Ecol. Conserv. e01169), via OBIS, west Abu Dhabi box 51–54.5E, 23.5–25.5N | `https://api.obis.org/v3/occurrence?scientificname=Cheloniidae&geometry=POLYGON((51 23.5,...))` | Turtle presence near the plant and movement speeds | 5,217 satellite fixes from 39 *Chelonia mydas*. 87 fixes within 50 km of the plant; the closest is 6.5 km. Straight-line displacement speed between fixes 1–24 h apart (median gap 11 h; speeds >3 m/s dropped as Argos error): **median 0.075, p90 0.33, p99 0.87 m/s.** These are lower bounds on swim speed. **No body sizes are in the dataset.** See `out/turtle_displacement_speeds.csv` |
| 8 | OBIS *Dugong* in the Gulf | same API | Dugong records | Only 10 records (6 are historical 1776 specimens) and 4 in the west Abu Dhabi box. Not useful. Use EAD's figure of about 3,000 animals (already in 05_fact_check) |
| 9 | Hashemi et al. 2025, *Iranian Fisheries Science Journal* 34(2):57–70, "Population parameters ... banana jellyfish (*Catostylus perezi*) ... northern Oman Sea" | https://ecc.isc.ac/showJournal/603/296418/3744471 | Measured sizes and wet masses of Gulf-region *Catostylus* | n = 503, Jun–Dec 2024. Total length 20 ± 6 cm (8–40 cm). **Wet weight mean 326 g, range 180–1,700 g** (the reported SD of 899 g looks like a typo). Peak occurrence in August |
| 10 | Aravind et al. 2023 (COSE, doi 10.53256/COSE_230102), UAE monthly mean bell diameter (already on file; used for the mass conversion) | — | Bell size by month | Oct 6.5 cm, Nov 11.8 cm, Dec 18.3 cm. Converted with the Panguil fit WW = 1.12·D^1.93 g, this gives **Oct ≈ 0.04 kg and Nov ≈ 0.13 kg** per animal. See `out/uae_bell_size_to_mass.csv` |
| 11 | Thermal tolerance of *C. mosaicus* / *C. perezi* | literature search | — | **No species-specific upper thermal limit was found.** The only congener data is *C. tagi* (strobilation 2–3× faster at 20 °C than at 15 °C). The field evidence is that UAE *Catostylus* are present year-round across the observed 17–37 °C |
| 12 | Daily intake-blockage load time series (Shin Hanul, Hanbit, etc.) | sources in 13_global_incidents.md | — | **NOT AVAILABLE.** Only 202 t in one day and 428 t over 4 days (Shin Hanul 2024), and 10–40 t/day (Hanbit 2009) are public. A bloom-load distribution cannot be fitted honestly from these |

Not obtained: CMEMS direct downloads (need a login), TPXO (needs registration), and EAD turtle and dugong reports with body sizes or speeds (none found as open data).

## Charts (`out/`)

- `fig_metocean_monthly.png`: monthly current percentiles against the twin's U0 and median; monthly onshore residual against the twin's 1–3 cm/s band; Hs; ERA5 wind.
- `fig_current_distribution.png`: hourly speed histogram against the twin's |0.117 sin ωt|, and a 1–15 Oct 2024 trace with the harmonic fit.
- `fig_onshore_persistence.png`: Oct–Nov 1-, 3- and 10-day running-mean onshore drift.
- `fig_sst.png`: OISST monthly climatology and the Oct–Nov trend.
- `fig_jellyfish_size_mass.png`: published mass–diameter relations against the 3 kg assumption, and UAE bell size by month.
- `fig_occurrence_map.png`: Gulf rhizostome records and turtle telemetry around the plant.
- `intake_load_scenarios.csv`: t/h per unit for densities 0.01–1 ind/m³ at 3 kg, 1.7 kg and 0.33 kg.

## Assumption check

The machine-readable version is `out/assumption_check.csv`.

| Assumption in JAZR | JAZR value | Real data value | Verdict |
|---|---|---|---|
| Tidal amplitude U0 (alongshore) | 0.117 m/s | M2 0.073 m/s alongshore (~080°); spring M2+S2 ≈ 0.108; equivalent U0 from total-current median = 0.118 | **OK.** It matches total current and spring tide. Tide alone is weaker, so the twin is slightly conservative |
| Median current | 0.083 m/s | median 0.083 (quantised value), mean 0.086; p99 0.19; max 0.39 m/s | **OK.** Add the quantisation caveat: quote the mean, 0.086 |
| Onshore residual drift | 1–3 cm/s, with 3 cm/s as the "worst case" | Oct–Nov mean 2.5 cm/s (CMEMS), 2.3 cm/s (HYCOM); 3-day mean p90 6.2, p99 9.5 cm/s; 10-day p90 4.7 cm/s; onshore on 76% of days | **CHANGE.** 3 cm/s is the *typical* case. Run the stress case at 5–6 cm/s (the flaw audit's 5 cm/s run gave 33%) |
| Wind drift | not modelled | Oct–Nov onshore wind 1.9–2.2 m/s mean, p99 8–8.7 m/s | **CHANGE.** Add a windage term, or state the exclusion |
| SST (survival, welfare, fouling) | 31 → 23 °C Oct → Dec; 35 °C summer | Oct 31.4, Nov 27.9 °C; Oct–Nov max 35.1; all-time 17.3–36.7 °C; +0.15 °C/decade | **OK** |
| Wave height (ops/structures) | Hs max 1.4 m nearshore; <0.6 m 90% Oct–Nov | Hs p90 Oct–Nov 0.52 m, max 1.02; all-year max 1.42 nearshore, 2.20 offshore | **OK for operations.** For structural design, 4 years is not an extreme-value basis: get 50/100-year Hs |
| Wet mass per animal | 3 kg typical, 5 kg upper | *C. perezi* (Oman Sea, n = 503) mean 0.33 kg, max 1.7 kg; UAE Oct–Nov mean bells 6.5–11.8 cm → 0.04–0.13 kg | **CHANGE.** Use about 0.3 kg typical and 1.7 kg upper (or 1–2 kg for the brief's 30–45 cm animals). At 0.1/m³ the stress load falls from 108 to about 12 t/h per unit at 0.33 kg, or about 61 t/h at 1.7 kg |
| Bloom density for sizing | 0.3 ind/m³ design (0.1–1) | No Gulf density data exist (presence-only records). Shin Hanul's 202 t/day at plant-scale flow implies only ~0.002–0.02 ind/m³ | **OK as conservative.** It cannot be validated |
| Species | *C. mosaicus* | 33 of 35 Gulf records are *C. perezi* | **CHANGE.** Say "*Catostylus* sp. (likely *C. perezi*)" |
| Jellyfish swim speed | 3.6 / 10 cm/s | no new data | Unchanged (no data) |
| Turtles near the intake | camera diverter; turtles bell-sized | 39 green turtles tracked; fixes within 6.5 km of the plant; displacement p90 0.33 m/s, p99 0.87 m/s | **OK.** Turtles are present, and many move faster than the 0.10 m/s approach velocity. No sizes are in the open data |
| Bloom-load distribution | Shin Hanul 200 t/day pilot load | no public daily series | **NOT AVAILABLE** |

## Caveats

- Datasets 1–3 are **model** products at roughly 8–9 km resolution, not in-situ measurements. The intake channels sit inside breakwaters and are not resolved.
- The current residual depends on the assumed coast angle.
- OBIS and GBIF records are opportunistic: absence near the plant does not mean the animals are absent.
- Turtle displacement speeds are straight-line speeds between Argos fixes. They underestimate true swim speed, and Argos error inflates some pairs.
