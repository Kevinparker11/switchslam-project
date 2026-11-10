import csv,collections,numpy as np,sys
sys.path.insert(0,'.'); import ate_tool as at
from scipy.spatial.transform import Rotation as Rot
gtp='data/g0_multifloor/ground_truth_path.csv'
G=np.loadtxt(gtp,delimiter=',',skiprows=1); G[:,0]*=1e-9
def stats(f,label):
    r=list(csv.DictReader(open(f)));n=len(r)
    t=np.array([float(x['time']) for x in r])
    def col(k): return np.array([float(x[k]) if x.get(k) not in (None,'','nan') else np.nan for x in r])
    print('==',label,'rows',n)
    for name,c in [('fused',['fused_x','fused_y','fused_z']),('aft',['aft_x','aft_y','aft_z']),('vins',['v_px','v_py','v_pz'])]:
        tt,P=at.log(f,c);print('  ATE %-5s %.2f / %.2f'%(name,*at.ate(tt,P,at.load_gt(gtp))[:2]))
    if 'sw_case' in r[0]:
        print('  case',dict(collections.Counter(x['sw_case'] for x in r)),'mode',dict(collections.Counter(x['mode'] for x in r)))
        for k in ['det_R','det_T','det_TT','sw_degen','sw_vo_fail']: print('  %s %.1f%%'%(k,100*np.nanmean(col(k))))
        if 'vio_gamma' in r[0]: print('  vio gate closed %.1f%%'%(100*np.nanmean(col('vio_gamma')<0.5)))
    # 10 s relative rotation error vs GT
    q=np.stack([col('fused_qx'),col('fused_qy'),col('fused_qz'),col('fused_qw')],1)
    ok=np.isfinite(q).all(1)&(t>=G[0,0])&(t<=G[-1,0]); t2=t[ok]; Re=Rot.from_quat(q[ok])
    from scipy.spatial.transform import Slerp
    Rg=Slerp(G[:,0],Rot.from_quat(G[:,4:8]))(t2)
    errs=[]
    for i in range(0,len(t2)):
        j=np.searchsorted(t2,t2[i]+10)
        if j>=len(t2): break
        de=(Re[i].inv()*Re[j]).magnitude(); dg=(Rg[i].inv()*Rg[j]).magnitude()
        errs.append(abs(np.degrees(de-dg)))
    print('  10 s rotation-angle error: median %.2f deg, p90 %.2f deg'%(np.median(errs),np.percentile(errs,90)))
    # yaw drift: final heading change error relative to start
    yaw_e=np.degrees(np.unwrap(Re.as_euler('zyx')[:,0])); yaw_g=np.degrees(np.unwrap(Rg.as_euler('zyx')[:,0]))
    d=(yaw_e-yaw_e[0])-(yaw_g-yaw_g[0])
    print('  heading drift vs GT (start-referenced): at 100 s %.1f, 200 s %.1f, 300 s %.1f, end %.1f deg'%tuple(d[np.searchsorted(t2,t2[0]+s)] if s<1e9 else d[-1] for s in (100,200,300,1e10)))
stats('f32mf/MF_switching_log_v2_F32_kf_run1.csv','F32 MF')
stats('f24fam/MF_switching_log_v2_F26_kf_run1.csv','F26 MF')
