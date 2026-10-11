"""T3 - Fish bycatch in the bypass and survival through the return chain.

No fish-density data exist for the plant's intake channel (not public). We therefore express the result
per 1,000 fish entering the bypass and as a scenario range of channel densities [ASSUME].
Survival chain uses published analogue stage survivals (fish, not jellyfish).
"""
import numpy as np
from params import *

rng = np.random.default_rng(4)
n = 200_000
# stage survival ranges (uniform between literature low/high)
stages = {
    "screen+bypass (angled screen, immediate)": (0.85, 1.00, "GCID screen-to-control 0.85-1.0 [15_ file]"),
    "Archimedes screw (rotating tube)":        (0.98, 1.00, "Red Bluff trout 98.3-100% [SRC 7]"),
    "screw-centrifugal pump (96 h)":           (0.87, 0.99, "Hidrostal Tracy: delta smelt 87% .. steelhead 99% [SRC 7]"),
    "5 km pipe in jellyfish slurry, 47 min":   (0.50, 0.98, "[ASSUME] no data: stings at 1-4% solids + O2 to ~3 mg/L at design density (T1)"),
    "release into offshore bloom patch":       (0.60, 0.95, "[ASSUME] predation/disorientation; Hudson angled screen 96 h survival 35% shows delayed loss can dominate"),
}
surv = np.ones(n)
for k, (lo, hi, _) in stages.items():
    surv *= rng.uniform(lo, hi, n)
pct = np.percentile(surv, [5, 50, 95])
no_pump = np.ones(n)
for k, (lo, hi, _) in stages.items():
    if "pump" in k:
        continue
    no_pump *= rng.uniform(lo, hi, n)
pct_np = np.percentile(no_pump, [5, 50, 95])

# Hudson full-scale angled screen (Matousek 1988): initial survival 90.2% but 96 h 35.3% -> delayed mortality reference
hudson = dict(initial=0.902, h96=0.353)

# bycatch volume scenarios: fish density in channel [ASSUME] (fish/1000 m3) entering lane and swept to bypass
dens = [0.1, 1, 10]          # fish per 1000 m3 [ASSUME]
swept_frac = (0.2, 0.8)      # share of fish that do not swim back out of the 0.5 m/s lane [ASSUME]
per_day = {d: [Q_UNIT * 86400 * d / 1000 * s for s in swept_frac] for d in dens}

res = dict(stages={k: v[2] for k, v in stages.items()},
           chain_survival_p5_p50_p95=pct.tolist(), chain_without_pump=pct_np.tolist(),
           hudson_delayed_mortality=hudson, fish_into_bypass_per_unit_day=per_day,
           baseline_note="Without JAZR these fish meet the plant's own travelling/drum screens; the plant's screen survival / fish-return arrangement is not public.")
res["verdicts"] = {
  "T3a_fish_survival_chain": ("UNKNOWN", "analogue chain median %.0f%% (5-95%%: %.0f-%.0f%%); without pump %.0f%%; the two dominant terms (pipe slurry, release) have no data" % (pct[1]*100, pct[0]*100, pct[2]*100, pct_np[1]*100)),
  "T3b_fish_return_claim": ("MARGINAL", "'fish-return benefit' is only a benefit if chain survival exceeds the plant-screen baseline, which is not public; claim as 'measured in pilot', not as benefit"),
  "T3c_bycatch_volume": ("UNKNOWN", "at 0.1-10 fish/1000 m3 [ASSUME] the lane would send %.0f-%.0f fish/unit-day into the bypass; need a channel fish survey (EAD baseline)" % (per_day[0.1][0], per_day[10][1])),
}
save("t3_fish_bycatch.json", res)
if __name__ == "__main__":
    for k, (v, w) in res["verdicts"].items():
        print(f"{k:28s} {v:9s} {w}")
