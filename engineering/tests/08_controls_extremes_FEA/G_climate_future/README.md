# G. Climate and future scenarios

**1. Incident trend.** We use the decade counts from `13_global_incidents.md`, checked string-for-string by the script: 1980s 5, 1990s 8, 2000s 13, 2010s 19, and 21 for 2020 to Oct 2026. A Poisson log-linear fit gives about **x1.6 per decade (doubling in about 15 years)**.

This is **INFO only**. The same file warns that the rise is partly reporting bias, and Condon 2013 found no robust global bloom increase. So size the system by design density, not by this trend.

**2. Warmer water and longer hot season.** Near-site daily SST (Open-Meteo 2022-25) is shifted by +0.3 or +0.5 °C per decade, which is our assumption. Days per year at or above 32 °C go from **about 120 now to 140-150 by 2050 and 154-174 by 2085**.

- G2 **MARGINAL**: if blooms track the hot season, the system will be deployed for more than v3's ~60 days per year. Effects:
  - fatigue (A6) has a large margin;
  - energy (F) scales linearly;
  - drum wrap cycles (A8c) and wetted-metal corrosion get worse.
- G3 **FAIL**: peak SST of about 39 °C by 2085 reinforces C7. Wetted parts must be titanium or polymer.

**3. Modular headroom.** One lift line is 2 m³/s of water [V3], with solids at no more than 5 % by volume [audit #9], which gives about **367 t/h per line**.

- At 0.3/m³: 1 line at 100 m³/s, but **2 lines at 172.5 m³/s**.
- At 1/m³: 3-5 lines.
- At 2/m³: up to 10 lines.

G4 **MARGINAL**: the v3 pilot has one line per unit. Reserve civil space and a manifold for 2-3 lines per lane. The screen and gantry scale with flow, and the lift lines scale with density.

Run: `python3 run_climate.py`.
