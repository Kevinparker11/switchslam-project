"""PREREG3 scoring.  python3 gselect.py"""
import sys, numpy as np
sys.argv=["x"]
import gscore
RULES=["min","smin","gmax","agm"]
CELLS=[(s,c) for c in ("clean","FL","FV") for s in ("MF","LC","CV")]+[("C02","clean"),("GEO","clean"),("GZ","clean")]
def tab(tag): return gscore.table(tag)
def cellmed(t,seq):
    v=np.array([a for n,(s,a,m) in t.items() if s==seq and n!="MF-b2"]); return float(np.nanmedian(v)) if np.isfinite(v).any() else np.nan, int(np.isfinite(v).sum())
base={"clean":tab("Gbase"),"FL":tab("Gbase_FL"),"FV":tab("Gbase_FV")}
ref={cl:cellmed(base[cl[1]],cl[0])[0] for cl in CELLS}
print("G20 cells:"," ".join("%s-%s %.3f"%(s,c,ref[(s,c)]) for s,c in CELLS))
res={}
for r in RULES:
    T={"clean":tab("Gc_%s_clean"%r),"FL":tab("Gc_%s_FL"%r),"FV":tab("Gc_%s_FV"%r)}
    v={cl:cellmed(T[cl[1]],cl[0]) for cl in CELLS}
    ok=[cl for cl in CELLS if np.isfinite(v[cl][0]) and np.isfinite(ref[cl])]
    sc=np.mean([np.log(v[cl][0]/ref[cl]) for cl in ok]) if ok else np.nan
    adm=all(v[(s,"clean")][0]<=ref[(s,"clean")]+0.05 for s in ("MF","LC","CV","C02","GEO","GZ") if np.isfinite(v[(s,"clean")][0]))
    # per-recording better/worse (clean)
    b=w=n=0
    for name,(s,a,m) in T["clean"].items():
        r0=base["clean"][name][1]
        if np.isfinite(a) and np.isfinite(r0):
            n+=1
            if a<r0-max(0.05,0.1*r0): b+=1
            elif a>r0+max(0.05,0.1*r0): w+=1
    res[r]=(sc,adm,len(ok))
    print("%-5s score %+.4f (cells %d) admissible %s | better %d worse %d of %d recordings"%(r,sc,len(ok),adm,b,w,n))
    print("      "," ".join("%s-%s %.3f"%(s,c,v[(s,c)][0]) for s,c in CELLS))
    print("      MF-b2 %.2f (G20 %.2f)"%(T["clean"]["MF-b2"][1],base["clean"]["MF-b2"][1]))
