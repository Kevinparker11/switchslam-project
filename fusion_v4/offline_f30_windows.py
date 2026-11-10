import csv,sys,numpy as np
GT=np.loadtxt('data/geode/gt_stairs_alpha.txt'); 
def load(f):
    r=list(csv.DictReader(open(f))); 
    g=lambda k:np.array([float(x[k]) if x[k] not in('','nan') else np.nan for x in r])
    return r,g
def umeyama(A,B):  # find R,t: B ~ R A + t
    ma,mb=A.mean(0),B.mean(0); H=(A-ma).T@(B-mb); U,S,Vt=np.linalg.svd(H); D=np.diag([1,1,np.sign(np.linalg.det(Vt.T@U.T))]); R=Vt.T@D@U.T; return R,mb-R@ma
for run in (1,2):
    r,g=load(f'f30files/switching_log_v2_F30_kf_run{run}.csv')
    t=g('time'); F=np.stack([g('fused_x'),g('fused_y'),g('fused_z')],1); A=np.stack([g('aft_x'),g('aft_y'),g('aft_z')],1)
    idx=np.searchsorted(GT[:,0],t); idx=np.clip(idx,1,len(GT)-1); 
    ok=np.abs(GT[idx,0]-t)<0.2
    P=GT[idx,1:4]
    t0=t[ok][0]; w=ok&(t<t0+40)
    Rf,tf=umeyama(F[w],P[w]); Ra,ta=umeyama(A[w],P[w])
    ef=np.linalg.norm((F@Rf.T+tf)-P,axis=1); ea=np.linalg.norm((A@Ra.T+ta)-P,axis=1)
    case=np.array([int(x['sw_case']) for x in r]); mode=np.array([x['mode'] for x in r]); vof=np.array([int(x['sw_vo_fail']) for x in r]); dtv=g('dtv'); dtl=g('dta')
    print('RUN',run,'first 40 s alignment')
    print(' win(s)   err_fused  err_aloam  case1 case2 case3  VO%  INTERP% LIDAR%  vofail%  medVINSstep medLiDARstep')
    for a in range(0,int(t[-1]-t0)+1,20):
        m=(t>=t0+a)&(t<t0+a+20)&ok
        if m.sum()<5: continue
        print('%4d-%-4d %8.2f %9.2f   %4.0f%% %4.0f%% %4.0f%%  %4.0f %6.0f %6.0f %7.0f   %8.3f %8.3f'%(a,a+20,np.nanmean(ef[m]),np.nanmean(ea[m]),*(100*np.mean(case[m]==c) for c in (1,2,3)),*(100*np.mean(mode[m]==k) for k in('SW_VO','SW_INTERP','SW_LIDAR')),100*vof[m].mean(),np.nanmedian(dtv[m]),np.nanmedian(dtl[m])))
