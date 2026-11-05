"""F26: the scan-to-map initial guess chosen by Switch-SLAM's degeneracy status (Algorithm 1, lines 1-8), the fusion itself unchanged.

F24 composes the VINS-Mono motion onto the last fused pose for EVERY scan while VINS is healthy.  Switch-SLAM uses the VIO motion as the
guess only when the scan Hessian is degenerate: LiDAR increment when not degenerate (here A-LOAM's own scan-to-scan odometry
increment, i.e. A-LOAM's usual guess), an interpolation (Eq. 13, w = min(1, sqrt(3) lambda_1)) when the status queue holds both, the VIO
increment when the queue is all degenerate.  The final pose (the F24 fusion) is not touched; only what A-LOAM starts from.

The guess is published in the F24 convention (fused pose composed with an increment), so the only change against F24 is the increment.
VINS healthy = F24's own PREDICT_GUARD test (no VO_FAIL step before, step <= jump_max, rotation <= rot_jump_max); a VINS that fails it is
treated as absent (the LiDAR increment is the guess).  Reuses switch_slam_core.SwitchSlamCore.decide.  numpy only."""
import numpy as np

import fusion_core as fc
import switch_slam_core as ssc


class StatusGuess:
    def __init__(self, R_IL, t_IL, hess_frame="body", n_buf=5, jump_max=1.0, rot_jump_max=0.5):
        self.g = ssc.SwitchSlamCore(R_IL, t_IL, n_buf=n_buf, hess_frame=hess_frame)
        self.jump_max, self.rot_jump_max = float(jump_max), float(rot_jump_max)
        self.kind = "INIT"

    def guess(self, core, odom, vins, H):
        """core = the F24 FusionCore (its last fused pose is the base); odom = (R, p) A-LOAM scan-to-scan pose of this scan;
        vins = (R, p) VINS IMU pose at the scan time or None; H = 6x6 scan Hessian or None.  Returns the pose to publish."""
        g = self.g
        g.Rf, g.pf = core.Rf, core.pf
        if g.prev_o is None:
            g.prev_o, g.prev_v = odom, vins
            self.kind = "INIT"
            return core.Rf, core.pf
        v = vins
        if v is not None and g.prev_v is not None:
            dR_I, dt_I = fc.rel_body(g.prev_v[0], g.prev_v[1], v[0], v[1])
            dR, dt = fc.imu_to_lidar_increment(dR_I, dt_I, g.R_IL, g.t_IL)
            if core.prev_mode == "VO_FAIL" or np.linalg.norm(dt) > self.jump_max or np.linalg.norm(fc.so3_log(dR)) > self.rot_jump_max:
                v = None
        dec = g.decide(odom, v, H)
        if dec["eig"] is not None and not dec["vo_fail"]:
            g.buf.append(dec["eig"]["degenerate"])                  # Algorithm 1, line 10
        g.prev_o, g.prev_v = odom, vins
        self.kind = dec["kind"]
        return dec["guess"]


class OdomFallback:
    """F27: F24's guess unchanged while the VINS motion is usable; when it is not (VINS absent, still starting, after a VO_FAIL, a step above
    jump_max / rot_jump_max, or the warm-up before VINS exists) F24 hands A-LOAM the last fused pose with NO motion.  Here the guess is the
    last fused pose composed with A-LOAM's own scan-to-scan increment instead (what plain A-LOAM would start from).  A step above
    3 x jump_max (an odometry blow-up) is not used (no motion, as F24)."""

    def __init__(self, jump_max=1.0):
        self.prev_o, self.jump_max, self.kind = None, float(jump_max), "INIT"

    def guess(self, core, pred, odom):
        prev, self.prev_o = self.prev_o, odom
        if core.Rf is None or pred is None:
            self.kind = "INIT"
            return pred
        if core.guess_used_vins or prev is None:
            self.kind = "VINS"
            return pred
        dR, dt = fc.rel_body(prev[0], prev[1], odom[0], odom[1])
        if np.linalg.norm(dt) > 3.0 * self.jump_max:
            self.kind = "HOLD"
            return pred
        self.kind = "ODOM"
        return fc.compose(core.Rf, core.pf, dR, dt)
