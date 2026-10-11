import json, os, numpy as np
from v4study import avg
import jazr_twin as J
if __name__=="__main__":
    R={}
    base=dict(system=True,eta_r=0.9,gate_x=1200,gate_y=5000,vr=-0.025)
    for lab,kw in (("no outer line, release",dict(base,ring=False,policy="immediate")),
                   ("no outer line, recover",dict(base,ring=False,policy="hold",hold_h=1e9)),
                   ("outer line 0.1, recover",dict(base,ring=True,eta_g=0.1,policy="hold",hold_h=1e9)),
                   ("no outer line, recover, eta_r 0.7",dict(base,ring=False,eta_r=0.7,policy="hold",hold_h=1e9)),
                   ("no outer line, recover, eta_r 0.5",dict(base,ring=False,eta_r=0.5,policy="hold",hold_h=1e9))):
        for h in (72,240):
            m,lo,hi=avg(dict(kw,hours=h)); R[f"{lab}|{h}h"]=[m,lo,hi]
            print(f"{lab:36s} {h:4d}h: {m*100:5.1f}% [{lo*100:.0f}-{hi*100:.0f}]",flush=True)
    json.dump(R,open(os.path.join(J.OUT,"v4b.json"),"w"),indent=1)
