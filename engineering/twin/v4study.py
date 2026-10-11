"""v4: release vs RECOVER policy under real-data onshore drift (2.5 cm/s typical, 5.5 stress), 72 h and 10 days."""
import json, os, numpy as np
from multiprocessing import Pool
import jazr_twin as J
PH=(0,np.pi/2,np.pi,3*np.pi/2); SEEDS=(1,2)
def one(a):
    kw,ph,sd=a; return J.simulate(N=1500,phase0=ph,seed=sd,**kw)[0]["captured_frac"]
def avg(kw):
    with Pool() as p: r=p.map(one,[(kw,ph,sd) for ph in PH for sd in SEEDS])
    return float(np.mean(r)),float(min(r)),float(max(r))
if __name__=="__main__":
    base=dict(system=True,ring=True,eta_g=0.4,eta_r=0.9,gate_x=1200,gate_y=5000)
    R={}
    for vr,dn in ((-0.025,"onshore 2.5 cm/s"),(-0.055,"onshore 5.5 cm/s")):
        for hrs in (72,240):
            for lab,kw in (("Today",dict(system=False)),("v3 release",dict(base,policy="immediate")),
                           ("v4 recover",dict(base,policy="hold",hold_h=1e9))):
                m,lo,hi=avg(dict(kw,vr=vr,hours=hrs)); R[f"{lab}|{dn}|{hrs}h"]=[m,lo,hi]
                print(f"{lab:12s} {dn:18s} {hrs:4d}h: {m*100:5.1f}% [{lo*100:.0f}-{hi*100:.0f}]",flush=True)
    json.dump(R,open(os.path.join(J.OUT,"v4study.json"),"w"),indent=1)
