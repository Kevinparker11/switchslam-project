"""score G-stack replays: python3 gscore.py TAG [TAG...]  -> per-sequence medians/means + per-recording CSV rows"""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0,"/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/clean4/fusion_v4")
import v2_tools as vt
CACHE="g/ate_cache.json"; cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
_g={}
def ate_one(path, gt):
    if gt not in _g: _g[gt]=vt.load_gt(gt)
    L=pd.read_csv(path); L=L[pd.to_numeric(L["time"],errors="coerce").notna()]
    return vt.ate(L["time"].astype(float).values, L[["fused_x","fused_y","fused_z"]].astype(float).values, *_g[gt])
ENT=[l.split("|") for l in open("glogs.txt").read().split("\n") if l]
def table(tag):
    out={}
    for name,seq,log,kf,gt,ext in ENT:
        p="g/%s/switching_log_v2_%s.csv"%(name,tag); h="g/%s/h_%s.txt"%(name,tag)
        if not (os.path.exists(p) and os.path.exists(h) and any(x.startswith("rows") for x in open(h))): out[name]=(seq,np.nan,np.nan); continue
        key="%s|%s|%d"%(tag,name,int(os.path.getmtime(p)))
        if key not in cache: cache[key]=ate_one(p,gt)
        out[name]=(seq,cache[key][0],cache[key][1])
    json.dump(cache,open(CACHE,"w")); return out
if __name__=="__main__":
    for tag in sys.argv[1:]:
        t=table(tag); seqs=[]
        for n,(s,a,m) in t.items():
            if s not in seqs: seqs.append(s)
        line="%-22s"%tag
        for s in seqs:
            v=np.array([a for n,(ss,a,m) in t.items() if ss==s and not n=="MF-b2"])
            line+="| %s n=%d med %.3f mean %.3f "%(s,np.isfinite(v).sum(),np.nanmedian(v) if np.isfinite(v).any() else np.nan,np.nanmean(v) if np.isfinite(v).any() else np.nan)
        print(line)
