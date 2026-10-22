import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, sheading as sh, sah_replay as sr
rng=np.random.default_rng(0)
def ptm(h): return h.max()/max(h.mean(),1e-12)
# null: isotropic random normals, keep near-vertical ones (as direction_hist does)
print("null peak/mean quantiles (n vertical points used)")
for n in (50,100,200,400,800,1600,3200):
    v=[]
    for _ in range(2000):
        th=rng.uniform(0,np.pi,n); h=np.bincount((th/sh.BIN).astype(int),minlength=sh.NB).astype(float)
        x=np.arange(-12,13); g=np.exp(-0.5*(x/4)**2); h=np.real(np.fft.ifft(np.fft.fft(h)*np.fft.fft(np.roll(np.pad(g,(0,sh.NB-len(g))),-12))))
        v.append(ptm(h))
    print(n, "q99 %.2f q99.9 %.2f max %.2f"%tuple(np.percentile(v,[99,99.9,100])))
KF=sr.kf_normals("/home/claude/data_in4/keyframes_F8_kf_run1.npz")
vals=[]
for t,(nb,pl) in KF.items():
    h,n=sh.direction_hist(nb,pl)   # body frame, not levelled; fine for peakiness
    if n>0: vals.append((n,ptm(h)))
v=np.array(vals); print("MF keyframes: n used median %d; peak/mean quantiles 1/5/50%%: %.2f %.2f %.2f"%(np.median(v[:,0]),*np.percentile(v[:,1],[1,5,50])))
