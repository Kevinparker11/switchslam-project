"""Unit tests for the two F25 fixes (run: python3 test_f25.py).
1. handover_trust: the anchored handover is skipped when the VINS consistency checks are closed (GEODE F24 run 1: 60 deg jump).
2. zupt: standstill hold only for IMU-quiet AND LiDAR wander; not for a straight constant-speed run, not when the IMU is not quiet.
3. StillDetector."""
import numpy as np
import fusion_core as fc
import still_detect as sd

R_IL = fc.so3_exp([0.01, -0.02, 0.03]); t_IL = np.array([0.08, 0.03, 0.03])
H = np.diag([50, 50, 50, 500, 500, 500.0])


class Stub:
    """VioConsistency stand-in with a fixed gamma"""
    proj = False
    r = 0.0

    def __init__(self, g):
        self.g = g

    def update(self, *a, **k): pass
    def reset(self): pass
    def restart_windows(self): pass
    def gamma(self): return self.g
    def trusted(self): return self.g > 0.5


def handover_run(gamma, trust, n=400, dt=0.1, t_warm=20.0):
    core = fc.FusionCore(R_IL, t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=t_warm, handover="anchor",
                         vio_adapt=Stub(gamma), handover_trust=trust)
    R_off_true = fc.so3_exp([0.02, -0.01, 1.2])
    # the VINS orientation drifts away from the LiDAR during the warm-up, 60 deg by the switch (a diverging VINS, GEODE F24 run 1):
    # no single step is a jump, but the warm-up mean (30 deg) differs from the value at the switch, so the anchor makes a jump
    k_switch = int(round(t_warm / dt)) + 1
    out = []
    for k in range(n):
        t = k * dt
        yaw = 0.02 * t
        RL = fc.so3_exp([0.0, 0.0, yaw]); pL = np.array([np.cos(0.05 * t), np.sin(0.05 * t), 0.0]) * 10
        bad = fc.so3_exp([0, 0, np.radians(60.0 * min(1.0, k / k_switch))])
        RLv = bad @ R_off_true.T @ RL
        Rv = RLv @ R_IL.T
        pv = R_off_true.T @ pL - Rv @ t_IL
        Rf, pf, info = core.step(t, (RL, pL), (Rv, pv) if k >= 1 else None, H)
        out.append((info, np.degrees(np.linalg.norm(fc.so3_log(RL.T @ Rf)))))
    first = [o for o in out if o[0]["mode"] == "FUSED"][0]
    hd = [o[0].get("handover_deg") for o in out if "handover_deg" in o[0]]
    err = float(np.mean([o[1] for o in out[-50:]]))
    return hd, err, first[0].get("handover_skipped")


hd0, e0, _ = handover_run(0.0, trust=False)       # F24 behaviour with a distrusted VINS: anchor adopts the bad rotation
hd1, e1, sk1 = handover_run(0.0, trust=True)      # F25: skipped
hd2, e2, sk2 = handover_run(1.0, trust=True)      # F25 with a trusted VINS: the anchor works as before
print("handover: F24 rule, VINS distrusted: jump %s deg, heading error %.2f deg" % (np.round(hd0, 1), e0))
print("handover: trust on, VINS distrusted: jumps %s, skipped=%s, heading error %.2f deg" % (hd1, sk1, e1))
print("handover: trust on, VINS trusted   : jump %s deg, skipped=%s, heading error %.2f deg" % (np.round(hd2, 1), sk2, e2))
assert hd0 and hd0[0] > 20.0, "the F24 rule must show the large jump"
assert hd1 == [] and sk1 == 1 and e1 < 1.0, "trust on + distrusted VINS: no jump"
assert sk2 == 0 and len(hd2) == 1, "trust on + trusted VINS: the anchor still runs"


def zupt_run(kind, still, zupt=True, n=400, dt=0.1):
    rng = np.random.default_rng(1)
    core = fc.FusionCore(R_IL, t_IL, c_t=0.03, gate=fc.KappaGate(kth=1e9), t_warm=1e12, zupt=zupt, zupt_T=5.0, zupt_ratio=0.5)
    pA = np.zeros(3); holds = 0; guesses = []
    for k in range(n):
        t = k * dt
        if kind == "wander":                    # random-walk jitter, no net travel
            pA = pA + rng.normal(0, 0.15, 3) * np.array([1, 1, 0.3])
        elif kind == "straight":                # constant speed 0.5 m/s
            pA = np.array([0.5 * t, 0.0, 0.0]) + rng.normal(0, 0.003, 3)
        guesses.append(core.predict(None))
        Rf, pf, info = core.step(t, (np.eye(3), pA), None, None, still=still)
        holds += info.get("zupt", 0)
    return holds, pf, pA, guesses


h, pf, pA, g = zupt_run("wander", True)
print("zupt wander, IMU quiet : held %d of 400 steps, fused moved %.2f m, A-LOAM moved %.2f m" % (h, np.linalg.norm(pf), np.linalg.norm(pA)))
assert h > 300 and np.linalg.norm(pf) < 1.5 and np.linalg.norm(pA) > 0.2, (h, pf)
assert np.allclose(g[-1][1], pf), "while held the mapping guess is the held pose"
h2, pf2, pA2, _ = zupt_run("wander", True, zupt=False)
print("zupt off (F24), same wander: fused moved %.2f m" % np.linalg.norm(pf2))
assert h2 == 0 and np.linalg.norm(pf2) > np.linalg.norm(pf) + 0.5
h3, pf3, pA3, _ = zupt_run("straight", True)
print("zupt straight run, IMU quiet: held %d, fused moved %.2f m (A-LOAM %.2f m)" % (h3, np.linalg.norm(pf3), np.linalg.norm(pA3)))
assert h3 == 0 and abs(np.linalg.norm(pf3) - np.linalg.norm(pA3)) < 0.05, "constant speed must not be held"
h4, pf4, _, _ = zupt_run("wander", False)
assert h4 == 0, "IMU not quiet: no hold"

det = sd.StillDetector(window=1.0, g_thr=0.02, a_thr=0.1)
rng = np.random.default_rng(2)
for k in range(300):
    det.add(k * 0.01, rng.normal(0, 0.003, 3), np.array([0, 0, 9.81]) + rng.normal(0, 0.02, 3))
assert det.still(2.99)
det2 = sd.StillDetector(window=1.0, g_thr=0.02, a_thr=0.1)
for k in range(300):
    det2.add(k * 0.01, rng.normal(0, 0.3, 3), np.array([0, 0, 9.81]) + rng.normal(0, 0.6, 3))
assert not det2.still(2.99)
det3 = sd.StillDetector()
for k in range(5):
    det3.add(k * 0.01, np.zeros(3), np.array([0, 0, 9.81]))
assert not det3.still(0.04), "too few samples: not still"
assert not det.still(10.0), "stale window: not still"
print("ALL F25 TESTS PASSED")
