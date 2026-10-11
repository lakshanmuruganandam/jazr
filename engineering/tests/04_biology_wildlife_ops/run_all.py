"""Run every T1-T8 analysis, the T9 pytest suite, and write results/verdicts.md + results/summary.json."""
import importlib, json, os, subprocess, sys
from params import RES, save
mods = ["t1_jelly_transport", "t2_wildlife", "t3_fish_bycatch", "t4_release_ecology",
        "t5_fmea_fta", "t6_ops_des", "t7_reliability", "t8_retention"]
allv = {}
for m in mods:
    mod = importlib.import_module(m)
    if hasattr(mod, "main"):
        r = mod.main()
        v = r["verdicts"]
    else:
        v = getattr(mod, "V", None) or getattr(mod, "v", None) or mod.res["verdicts"]
        if not isinstance(v, dict) or not v:
            v = mod.res["verdicts"]
    allv.update(v)
rc = subprocess.call([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                      "test_bloom_os.py", "test_analyses.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
allv["T9_bloom_os_smoke"] = ("PASS" if rc == 0 else "FAIL", "pytest state-machine + analysis sanity suite (exit %d)" % rc)
save("summary.json", allv)
with open(os.path.join(RES, "verdicts.md"), "w") as f:
    f.write("| Test | Verdict | Evidence |\n|---|---|---|\n")
    for k, (v, w) in allv.items():
        f.write(f"| {k} | **{v}** | {w} |\n")
counts = {}
for v, _ in allv.values():
    key = v.split()[0]
    counts[key] = counts.get(key, 0) + 1
print(counts)
