import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
P=json.load(open("out/practical.json"))
rows=[("Today","Today"),("Guard only","G: guard 0.8, release at channel side"),("Guard + pipe 3 km","G+E3: guard 0.8 + pipe 3 km"),
 ("JAZR Gate: 2-stage guard + pipe 3 km","G2+E3: two-stage guard 0.9 + pipe 3 km"),("JAZR Gate + short arms (add-on)","G2+E3 + short arms (eta_g 0.4)"),
 ("Full offshore stack","Full stack (arms 0.7, guard 0.8, pipe 3 km)")]
v=[P[k]["captured"]*100 for _,k in rows]; lo=[P[k]["lo"]*100 for _,k in rows]; hi=[P[k]["hi"]*100 for _,k in rows]
col=["#64748b","#94a3b8","#94a3b8","#0e7490","#0891b2","#cbd5e1"]
fig,ax=plt.subplots(figsize=(8.5,3.8)); y=range(len(rows))
ax.barh(list(y),v,color=col,xerr=[[a-b for a,b in zip(v,lo)],[b-a for a,b in zip(v,hi)]],error_kw=dict(lw=0.8))
for i,a in enumerate(v): ax.text(a+3,i,f"{a:.0f}%",va="center",fontsize=9)
ax.set_yticks(list(y)); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis(); ax.set_xlim(0,105)
for s in ("top","right"): ax.spines[s].set_visible(False)
ax.set_xlabel("Share of swarm band reaching the intake in 72 h (%)  (toy twin; bars = range over tide phase)")
ax.set_title("Practical core: no offshore arms needed for most of the benefit",fontsize=10,loc="left")
fig.tight_layout(); fig.savefig("out/fig5_practical_core.png",dpi=180); print("ok")
