import itertools, json, numpy as np
from scipy import stats
nan=None
# (rmse, max) per live run; max None = per-run value not recorded (only order used for the rank test, see ORD)
D={
 'MF':{'VINS':[(1.29,2.51),(1.29,2.54),(1.25,2.35)],'ALOAM':[(30.69,58.50),(13.20,25.44),(35.43,64.21)],
       'F8':[(0.74,1.65),(0.51,1.24),(0.54,1.20),(0.77,1.62),(0.73,1.61),(0.62,1.24),(0.58,1.24),(0.59,1.24),(0.47,1.04)],
       'F24':[(0.45,0.92),(1.01,1.73),(0.69,1.24)],'F26':[(0.54,1.01)]},
 'LC':{'VINS':[(5.66,15.24),(6.13,16.2),(5.65,15.2)],'ALOAM':[(23.01,56.0),(13.21,30.0),(11.21,21.2)],
       'F8':[(4.76,12.0),(4.87,14.1),(3.97,11.4)],'F24':[(2.12,5.31),(2.15,5.57),(1.75,3.53)],'F26':[(2.10,3.73)]},
 'C02':{'VINS':[(4.03,6.75),(4.02,6.73),(4.03,6.76)],'ALOAM':[(58.57,100.0),(46.53,79.3),(92.95,134.5)],
       'F8':[(2.07,3.69),(2.10,3.72),(2.19,3.88)],'F24':[(1.47,2.51),(104.00,149.20),(1.29,2.68)],'F26':[(1.93,3.46),(2.04,3.46)]},
 'CAVE':{'VINS':[(10.21,None),(10.26,None),(10.26,None)],'F8':[(4.71,6.75),(4.31,7.2),(4.40,7.74)],
       'F24':[(7.55,12.63),(7.08,11.78),(7.11,11.76)],'F26':[(6.23,10.56)]},
 'GEODE':{'VINS':[(186.58,732.50),(153.08,709.40),(270.77,1060.27),(163.71,717.87),(186.15,730.59),(271.63,1064.67),(200.24,645.33)],
       'F24':[(6.15,14.00),(9.15,25.44),(7.05,17.09),(6.56,16.46)],'F26':[(6.36,14.07),(3.26,7.81),(5.51,15.25)]},
 'FARM':{'VINS':[(4.31,6.95),(14.47,26.57)],'ALOAM':[(0.478,0.977)],'F8':[(0.490,0.750)],'F24':[(0.472,1.068)],'F26':[(0.290,0.562)]},
}
# rows whose max values are placeholders with only the order known
APPROX_MAX={('LC','VINS'):'15.54 (mean)',('LC','ALOAM'):'21.2 to 56.0',('LC','F8'):'12.89 (mean)',('C02','ALOAM'):'79.3 to 134.5',('CAVE','F8'):'6.75 to 7.74'}
REALMAXMEAN={('LC','VINS'):15.543,('LC','F8'):12.893,('C02','VINS'):6.747,('MF','VINS'):2.467}
def mw_exact(base, prop):
    allv=list(base)+list(prop); n1=len(base); n2=len(prop)
    def U(b,p): return sum((x>y)+0.5*(x==y) for x in b for y in p)
    u0=U(base,prop); cnt=0; tot=0
    for idx in itertools.combinations(range(n1+n2), n2):
        p=[allv[i] for i in idx]; b=[allv[i] for i in range(n1+n2) if i not in idx]
        tot+=1; cnt+= U(b,p)>=u0-1e-9
    return cnt/tot, u0, n1*n2
out={}
for env,g in D.items():
    prop=g['F26']
    for base in ['VINS','ALOAM','F8','F24']:
        if base not in g: continue
        b=g[base]; r={}
        for k,name in ((0,'ate'),(1,'max')):
            bv=[x[k] for x in b]; pv=[x[k] for x in prop]
            if None in bv: r[name]=None; continue
            p,u,npair=mw_exact(bv,pv)
            r[name]=(p,u,npair)
        if len(b)>1 and len(prop)>1:
            r['welch']=stats.ttest_ind([x[0] for x in b],[x[0] for x in prop],equal_var=False,alternative='greater').pvalue
        else: r['welch']=None
        out[(env,base)]=r
        print(env,base,{k:(None if v is None else (tuple(round(z,4) for z in v) if isinstance(v,tuple) else round(v,4))) for k,v in r.items()})
# table 1 stats
print()
for env,g in D.items():
    pm=np.mean([x[0] for x in g['F26']]); pmx=np.mean([x[1] for x in g['F26']])
    for m,v in g.items():
        a=np.array([x[0] for x in v]); mx=[x[1] for x in v]
        mxm=REALMAXMEAN.get((env,m), np.mean(mx) if None not in mx else None)
        imp=(a.mean()-pm)/a.mean()*100
        impx=(mxm-pmx)/mxm*100 if mxm else None
        succ=np.mean(a<=10)*100
        med_max=np.median(mx) if None not in mx else None
        print(env,m,len(a),'%.3f %.3f %.3f %.3f'%(a.min(),np.median(a),a.max(),a.mean()),'imp %.1f'%imp, 'maxmean',None if mxm is None else round(mxm,3), None if impx is None else round(impx,1),'succ %.0f'%succ,'medmax',med_max, APPROX_MAX.get((env,m),''))
