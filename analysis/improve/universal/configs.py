# Configurations replayed by rep.py.  Frozen values: c_T 3e-6, c_R 5e-6 (Multi Floor), ref 0.156, n_min 200 (Multi Floor).
def _seg(fc4, **k):
    a = dict(ref=0.156, stat="scale", rule="gate", avg=None, n_min=200); a.update(k); return fc4.VioConsistency(**a)
CFG = {
 "G17": lambda fc4: dict(),
 "G18": lambda fc4: dict(adapt=_seg(fc4)),
 "G19": lambda fc4: dict(adapt=_seg(fc4), vio_scale_T=10.0),
}
# --- candidates for a universal fix (24 Oct).  REF_DB: largest de-biased r on MF-a1..a4 at >= 200 windows (calib_debias.py)
REF_DB = 0.154
GUARD_EX = 0.72      # largest 2 s LiDAR-minus-VINS path excess on MF-a1..a4 (diag_guard.py), metres
CFG.update({
 "U0": lambda fc4: dict(adapt=_seg(fc4), vio_scale_seg=True),                                   # G18 gate + robust segment scale
 "U1": lambda fc4: dict(adapt=_seg(fc4, ref=REF_DB, debias=True), vio_scale_seg=True),          # de-biased gate + robust scale
 "U2": lambda fc4: dict(adapt=_seg(fc4, ref=REF_DB, debias=True), vio_scale_seg=True, lidar_guard_T=2.0, lidar_guard_ex=GUARD_EX),
 "U3": lambda fc4: dict(adapt=_seg(fc4, ref=REF_DB, debias=True, rule="ratio"), vio_scale_seg=True),
})
CFG.update({
 "L10": lambda fc4: dict(adapt=_seg(fc4), vio_scale_seg="local"),                    # G18 gate + local chord scale (10 s windows, last 10 s)
 "L30": lambda fc4: dict(adapt=_seg(fc4, T_loc=30.0), vio_scale_seg="local"),        # same, windows of the last 30 s
 "G19p": lambda fc4: dict(adapt=_seg(fc4), vio_scale_T=10.0, vio_scale_proj=True),    # G19 with projected path lengths (existing option)
})
CFG.update({
 "A19": lambda fc4: dict(adapt=_seg(fc4), vio_scale_T=10.0, vio_scale_along=True),             # G19, scale only along LiDAR travel
 "A10": lambda fc4: dict(adapt=_seg(fc4), vio_scale_seg="local", vio_scale_along=True),        # local chord scale, along travel
 "A19p": lambda fc4: dict(adapt=_seg(fc4), vio_scale_T=10.0, vio_scale_proj=True, vio_scale_along=True),
})
# fast companion check: RMS of x over windows ending in the last 10 s (5 s), reference = largest such value on MF-a1..a4
R10, R5 = 0.252, 0.278
def _two(fc4, avg=10.0):
    fast = fc4.VioConsistency(ref=R10 if avg == 10.0 else R5, stat="scale", rule="gate", avg=avg, n_min=50 if avg == 10.0 else 25)
    return fc4.VioChecks([_seg(fc4), fast])
CFG.update({
 "F10": lambda fc4: dict(adapt=_two(fc4), vio_scale_T=10.0),
 "F5":  lambda fc4: dict(adapt=_two(fc4, 5.0), vio_scale_T=10.0),
 "K2":  lambda fc4: dict(adapt=_seg(fc4), vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=2 * GUARD_EX),
 "K3":  lambda fc4: dict(adapt=_seg(fc4), vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=3 * GUARD_EX),
 "F10K3":  lambda fc4: dict(adapt=_two(fc4), vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=3 * GUARD_EX),
 "F10pK3": lambda fc4: dict(adapt=_two(fc4), vio_scale_T=10.0, vio_scale_proj=True, lidar_guard_T=2.0, lidar_guard_ex=3 * GUARD_EX),
})
CFG.update({
 # G20 = G19 + fast companion check (5 s, MF-calibrated) + LiDAR blow-up guard (2 s, 3 x the largest MF value)
 "G20": lambda fc4: dict(adapt=_two(fc4, 5.0), vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=3 * GUARD_EX),
})
CFG.update({
 "G20f": lambda fc4: dict(adapt=_two(fc4, 5.0), vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=3 * GUARD_EX, gamma_min=1e-3),
})
# --- diagnostics for the Gazebo office (25 Oct): which channel carries the extra error?  W = (cS + gamma I)^-1 cS, so a huge c means the LiDAR is trusted
# in that channel and c = 0 means VINS-Mono only.  Analysis only, none of these is a proposed configuration.
CFG.update({
 "D1": lambda fc4: dict(sah=False),                                   # G17 without SAH
 "D2": lambda fc4: dict(c_R=1e3),                                     # rotation from the LiDAR, T channel + SAH as G17
 "D3": lambda fc4: dict(c_t=1e3),                                     # translation from the LiDAR, R channel + SAH as G17
 "D4": lambda fc4: dict(c_t=1e3, c_R=1e3, sah=False),                 # LiDAR in both channels, no SAH (should reproduce GenZ-LIO)
 "D5": lambda fc4: dict(c_t=1e3, c_R=1e3),                            # LiDAR in both channels + SAH
})
# --- sensitivity of the T-channel scale c_T (analysis only): G20 settings with c_T multiplied (more LiDAR trust for larger values)
_G20 = lambda fc4: dict(adapt=_two(fc4, 5.0), vio_scale_T=10.0, lidar_guard_T=2.0, lidar_guard_ex=3 * GUARD_EX)
for _k, _c in (("S03", 1e-6), ("S3", 1e-5), ("S10", 3e-5), ("S30", 1e-4)):
    CFG[_k] = (lambda c: (lambda fc4: dict(_G20(fc4), c_t=c)))(_c)
CFG["G20b"] = _G20
# --- G23 (26 Oct 2026) = G20 + LiDAR-gap rule (gap_T = 1 s): fusion_core.FusionCore(gap_T=...), developed on the outage logs of 26 Oct
CFG["G23"] = lambda fc4: dict(_G20(fc4), gap_T=1.0)

# --- Switch-SLAM baselines (27 Oct 2026): the detection rule of Lee et al. (RA-L 2024, Sec. III-C) as published (three smallest normalised
# eigenvalues of the 6x6 Hessian against 0.12 / 0.27 / 0.48) as an all-or-nothing switch between GenZ-LIO and VINS-Mono; no SAH, no consistency
# check, no guard.  SW = translation switched, rotation always from the VIO (the project's F12, defined on 13 Oct, so fixed before this test);
# SWR = the whole 6-DoF increment switched (variant; mixes LiDAR rotation with VIO translation increments, which is much worse).
CFG["SW"] = lambda fc4: dict(sah=False, w_mode="switch_ss")
CFG["SWR"] = lambda fc4: dict(sah=False, w_mode="switch_ss", switch_rot=True)
