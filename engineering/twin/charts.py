import json, os, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
O="out"; A=json.load(open(f"{O}/ablation.json")); C=json.load(open(f"{O}/capstudy.json")); E=json.load(open(f"{O}/exportstudy.json"))
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
# 1 stack ablation
names=[k.split("|")[0] for k in A["stack"] if k.endswith("swim=0.036")]
v1=[A["stack"][f"{n}|swim=0.036"]["captured"]*100 for n in names]; v2=[A["stack"][f"{n}|swim=0.1"]["captured"]*100 for n in names]
fig,ax=plt.subplots(figsize=(9,4.6)); y=range(len(names))
ax.barh([i+0.2 for i in y],v1,0.4,color="#0e7490",label="swim 3.6 cm/s"); ax.barh([i-0.2 for i in y],v2,0.4,color="#94a3b8",label="swim 10 cm/s")
for i,(a,b) in enumerate(zip(v1,v2)): ax.text(a+1,i+0.2,f"{a:.0f}%",va="center",fontsize=9)
ax.set_yticks(list(y)); ax.set_yticklabels(names); ax.invert_yaxis(); ax.set_xlim(0,105)
ax.set_xlabel("Share of swarm band reaching the intake in 72 h (%)"); ax.legend(loc="lower right",frameon=False)
ax.set_title("JAZR stack, layer by layer (toy twin, unlimited pockets; relative comparison only)",fontsize=10,loc="left")
fig.tight_layout(); fig.savefig(f"{O}/fig1_stack_ablation.png",dpi=180)
# 2 export distance (realistic 100 t pockets)
lab=["pipe 1 km offshore","pipe 1.5 km offshore","pipe 2 km offshore","pipe 3 km offshore"]; d=[1,1.5,2,3]
fig,ax=plt.subplots(figsize=(6,3.8)); ax.plot(d,[E[l]["captured"]*100 for l in lab],"o-",color="#0e7490",label="floating pipe offshore")
ax.plot([2,3],[E["passive lane end 2 km"]["captured"]*100,E["passive lane end 3 km"]["captured"]*100],"s--",color="#ca8a04",label="passive alongshore lane end")
ax.axhline(C["S5|cap=100"]["captured"]*100,color="#b91c1c",ls=":",label="lane end 1.2 km, timed release")
ax.axhline(A["stack"]["S0 Today (no system)|swim=0.036"]["captured"]*100,color="#64748b",ls="-",lw=0.8,label="today")
ax.set_xlabel("Release distance (km)"); ax.set_ylabel("Swarm reaching intake (%)"); ax.set_ylim(0,100); ax.legend(frameon=False,fontsize=8)
ax.set_title("Export distance is the lever (pockets capped at 100 t)",fontsize=10,loc="left"); fig.tight_layout(); fig.savefig(f"{O}/fig2_export_distance.png",dpi=180)
# 3 pocket cap
caps=["None","1000","300","100","30"]; xl=["no cap","1000","300","100","30"]
fig,ax=plt.subplots(figsize=(6,3.8))
ax.plot(xl,[C[f"S5|cap={c}"]["captured"]*100 for c in caps],"o-",color="#b91c1c",label="passive release at 1.2 km")
ax.plot(xl,[C[f"S7|cap={c}"]["captured"]*100 for c in caps],"o-",color="#0e7490",label="export 3 km offshore")
ax.set_xlabel("Pocket capacity (t per pocket)"); ax.set_ylabel("Swarm reaching intake (%)"); ax.set_ylim(0,45); ax.legend(frameon=False)
ax.set_title("Small pockets only work with export",fontsize=10,loc="left"); fig.tight_layout(); fig.savefig(f"{O}/fig3_pocket_cap.png",dpi=180)
# 4 tornado on final design
base=E["pipe 3 km offshore"]["captured"]*100
S=[("guide eff. 0.5 (vs 0.7)",E["pipe 3 km, eta_g 0.5"]["captured"]*100),("guide 0.5 + guard 0.5",E["pipe 3 km, eta_g 0.5, eta_r 0.5"]["captured"]*100),
   ("onshore residual 1 cm/s",E["pipe 3 km, onshore 1 cm/s"]["captured"]*100),("no release timing",E["pipe 3 km, immediate (no timing)"]["captured"]*100),
   ("swim 10 cm/s",E["pipe 3 km, swim 0.10"]["captured"]*100)]
fig,ax=plt.subplots(figsize=(6.4,3.4)); 
for i,(n,v) in enumerate(S): ax.barh(i,v-base,left=base,color="#b91c1c" if v>base else "#16a34a"); ax.text(max(v,base)+0.5,i,f"{v:.0f}%",va="center",fontsize=9)
ax.axvline(base,color="k",lw=0.8); ax.set_yticks(range(len(S))); ax.set_yticklabels([s[0] for s in S]); ax.invert_yaxis()
ax.set_xlabel(f"Swarm reaching intake (%), final design base = {base:.1f}%"); ax.set_title("What breaks it: sensitivity of the final design",fontsize=10,loc="left")
fig.tight_layout(); fig.savefig(f"{O}/fig4_sensitivity.png",dpi=180)
print("ok")
