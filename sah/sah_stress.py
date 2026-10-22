import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,"/home/claude/fusion_v3")
import numpy as np, v2_tools as vt, cand, sah_replay as sr
seq=sys.argv[1]; qd=float(sys.argv[2]); pairs=[a.split(":") for a in sys.argv[3:]]
gt_t,gt_p=vt.load_gt(cand.SEQ[seq][0])
data=[(cand.load(lg),sr.kf_normals(kf)) for lg,kf in pairs]
rng=np.random.default_rng(1)
def rnd(n): v=rng.standard_normal((n,3)); return (v/np.linalg.norm(v,axis=1,keepdims=True)).astype(np.float32)
T0=min(d["t"][0] for d,_ in data); T1=max(d["t"][-1] for d,_ in data)
def unstruct(nb,pl,t): return rnd(len(nb)),pl
def tail_unstruct(nb,pl,t): return (rnd(len(nb)),pl) if t>T0+0.4*(T1-T0) else (nb,pl)
def head_unstruct(nb,pl,t): return (rnd(len(nb)),pl) if t<T0+0.4*(T1-T0) else (nb,pl)
def outl30(nb,pl,t):
    nb=nb.copy(); m=rng.random(len(nb))<0.3; nb[m]=rnd(m.sum()); return nb,pl
def sparse20(nb,pl,t):
    m=rng.random(len(nb))<0.2; return nb[m],pl[m]
def wrongwall(nb,pl,t):   # a strong spurious direction rotating slowly (e.g. a moving vehicle / glass reflections)
    k=int(0.3*len(nb)); a=np.radians(10)*np.sin((t-T0)/20.0)+np.radians(20)
    v=np.tile(np.array([np.cos(a),np.sin(a),0],np.float32),(k,1)); nb=nb.copy(); nb[:k]=v; return nb,pl
kw=dict(v3=6,bound_R=True) if qd<-6.5 else dict(v3=6) if qd<-5.5 else dict(v3=5) if qd<-4.5 else dict(v3=4) if qd<-3.5 else dict(v3=True) if qd<-1.5 else ({} if qd<0 else dict(fixed_q=np.radians(qd)**2, fixed_R=np.radians(2.0)**2))
for name,tr,k in [("F8 no SAH",None,None),("SAH",None,kw),("SAH unstructured (random normals)",unstruct,kw),("SAH structure lost after 40%",tail_unstruct,kw),
                  ("SAH structure only after 40%",head_unstruct,kw),("SAH 30% outlier normals",outl30,kw),("SAH 20% of points",sparse20,kw),("SAH strong spurious direction",wrongwall,kw)]:
    r=[];st=[]
    for d,KF in data:
        p,s=sr.run(d,KF,sah_kw=k,transform=tr); r.append(vt.ate(d["t"],p,gt_t,gt_p)[0]); st.append(s)
    print("%-36s %s mean %.3f | log1 %s"%(name," ".join("%.3f"%x for x in r),np.mean(r),st[0]),flush=True)
