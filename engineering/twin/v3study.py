"""v3 robustness study: Gate variants under the auditor's bad cases (onshore 3 cm/s, 10-day bloom, low guard efficiency)."""
import json, os
from ablation import avg
import jazr_twin as J
if __name__ == '__main__':
  R={}
  base=dict(system=True, policy="immediate", ring=False, eta_r=0.9, gate_x=1200, gate_y=3000)
  configs={
   "Gate (guard 0.9, outlet 3 km)": {},
   "Gate, outlet 5 km": dict(gate_y=5000),
   "Gate + outer guide line (0.4)": dict(ring=True, eta_g=0.4),
   "Gate + outer guide (0.4) + outlet 5 km": dict(ring=True, eta_g=0.4, gate_y=5000),
   "Gate + outer guide (0.6) + outlet 5 km": dict(ring=True, eta_g=0.6, gate_y=5000),
  }
  conds={"median":{}, "onshore 3 cm/s":dict(vr=-0.03), "10-day bloom":dict(hours=240), "guard 0.5":dict(eta_r=0.5)}
  for cn,ck in configs.items():
    for dn,dk in conds.items():
      a=avg(dict(base,**ck,**dk)); R[f"{cn}|{dn}"]=a
      print(f"{cn:42s} | {dn:15s}: {a['captured']*100:5.1f}%  handled {a['handlings']:.2f}x",flush=True)
  R["today|median"]=avg(dict(system=False)); R["today|10-day bloom"]=avg(dict(system=False,hours=240)); R["today|onshore 3 cm/s"]=avg(dict(system=False,vr=-0.03))
  for k in ("today|median","today|10-day bloom","today|onshore 3 cm/s"): print(k, f"{R[k]['captured']*100:.1f}%")
  json.dump(R,open(os.path.join(J.OUT,"v3study.json"),"w"),indent=1)
