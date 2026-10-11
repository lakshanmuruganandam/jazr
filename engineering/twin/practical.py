"""Practicality study: how much of the full stack's benefit do the cheapest/most buildable subsets keep?"""
import json, os
from ablation import avg
import jazr_twin as J
if __name__ == '__main__':
  R={}
  B=dict(system=True, policy="ebb", window=0.25, cap_t=100, gate_x=1200)
  cases=[
   ("Today",dict(system=False)),
   ("G: guard 0.8, release at channel side",dict(B,ring=False,gate_y=150)),
   ("G+E2: guard 0.8 + pipe 2 km",dict(B,ring=False,gate_y=2000)),
   ("G+E3: guard 0.8 + pipe 3 km",dict(B,ring=False,gate_y=3000)),
   ("G2+E3: two-stage guard 0.9 + pipe 3 km",dict(B,ring=False,gate_y=3000,eta_r=0.9)),
   ("G2+E3, guard 0.7 (pessimistic)",dict(B,ring=False,gate_y=3000,eta_r=0.7)),
   ("G2+E3 + short arms (eta_g 0.4)",dict(B,gate_y=3000,eta_r=0.9,eta_g=0.4)),
   ("Full stack (arms 0.7, guard 0.8, pipe 3 km)",dict(B,gate_y=3000)),
   ("Full stack, guard 0.9",dict(B,gate_y=3000,eta_r=0.9)),
   ("G2+E3, swim 0.10",dict(B,ring=False,gate_y=3000,eta_r=0.9,swim=0.10)),
   ("G2+E3, onshore 1 cm/s",dict(B,ring=False,gate_y=3000,eta_r=0.9,vr=-0.01)),
   ("G2+E3, no timing",dict(B,ring=False,gate_y=3000,eta_r=0.9,policy="immediate")),
  ]
  for lab,kw in cases:
      a=avg(kw); R[lab]=a
      print(f"{lab:45s}: intake {a['captured']*100:5.1f}% [{a['lo']*100:.0f}-{a['hi']*100:.0f}] handled {a['handlings']:.2f}x",flush=True)
  json.dump(R,open(os.path.join(J.OUT,"practical.json"),"w"),indent=1)
