import sys,os,json,numpy as np
exec(open(sys.argv[1]).read())          # logs_all.py -> LOGS
name=sys.argv[2]; out=sys.argv[3]
row=[x for x in LOGS if x[0]==name][0]; _,seq,log,kf,gt,ext=row
if ext!='-': os.environ["EXTRINSIC_YAML"]=ext
sys.path.insert(0,sys.argv[4]); import v2_tools as vt
d=vt.load_v2_log(log); t=np.asarray(d["t"])
gt_t,gt_p=vt.load_gt(gt)
V=np.full((len(t),3),np.nan)
for i,v in enumerate(d["vins"]):
    if v is not None: V[i]=v[1]+v[0]@vt.t_IL
rm,mx=vt.ate(t,V,gt_t,gt_p)
json.dump(dict(log=name,seq=seq,cfg="VI",ate=rm,max=mx,n=len(t),cover=float(np.isfinite(V).all(1).mean())),open(f"{out}/{name}__VI.json","w"))
print(name,round(rm,3),round(mx,3))
