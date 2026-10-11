"""Run every test in order and compile out/results_summary.csv + verdict counts."""
import subprocess, sys, os, json, csv, glob
HERE = os.path.dirname(os.path.abspath(__file__))
scripts = sorted(glob.glob(os.path.join(HERE, "t[0-9][0-9]_*.py")))
for s in scripts:
    print("==>", os.path.basename(s), flush=True)
    r = subprocess.run([sys.executable, s], cwd=HERE, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr); sys.exit(1)
rows = []
for j in sorted(glob.glob(os.path.join(HERE, "out", "T??_results.json"))):
    rows += json.load(open(j))["checks"]
with open(os.path.join(HERE, "out", "results_summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
from collections import Counter
c = Counter((r["test"], r["verdict"]) for r in rows)
for t in sorted({r["test"] for r in rows}):
    print(t, {v: c[(t, v)] for v in ("PASS", "MARGINAL", "FAIL")})
print("TOTAL", Counter(r["verdict"] for r in rows))
