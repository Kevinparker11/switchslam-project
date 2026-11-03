#!/usr/bin/env python3
"""predict_guard: the mapping guess uses the VINS motion only while VINS is trusted (no VO_FAIL, step within jump_max / rot_jump_max).
Off (default): unchanged (VINS steps up to 3 x jump_max are used in any mode)."""
import numpy as np
import fusion_core as fc

def core(guard, mode="WARMUP"):
    c = fc.FusionCore(predict_guard=guard)
    c.Rf, c.pf = np.eye(3), np.zeros(3)
    c.prev_v = (np.eye(3), np.zeros(3)); c.prev_mode = mode
    return c

def vins(dx, yaw=0.0):
    return (fc.so3_exp(np.array([0.0, 0.0, yaw])), np.array([dx, 0.0, 0.0]))

for dx, yaw, mode, used_on in ((0.05, 0.0, "WARMUP", True),     # normal VINS step: used
                                (0.05, 0.0, "FUSED", True),
                                (2.0, 0.0, "WARMUP", False),     # 1-3 m step: the old rule used it, the guard does not
                                (0.05, 0.0, "VO_FAIL", False),   # after a VO_FAIL step: not used
                                (0.05, 0.8, "WARMUP", False),    # rotation step above rot_jump_max: not used
                                (5.0, 0.0, "WARMUP", False)):    # above 3 x jump_max: neither rule uses it
    for guard in (False, True):
        R, p = core(guard, mode).predict(vins(dx, yaw))
        moved = np.linalg.norm(p) > 1e-9 or np.linalg.norm(R - np.eye(3)) > 1e-9
        expect = used_on if guard else (dx <= 3.0)             # off: only the 3 x jump_max rule
        assert moved == expect, (dx, yaw, mode, guard, moved, expect)
assert core(True).predict(None)[1].tolist() == [0.0, 0.0, 0.0]
print("predict_guard: guard on uses VINS only for small steps outside VO_FAIL; guard off is the old rule (VINS steps up to 3 m used)")
print("ALL PREDICT_GUARD TESTS PASSED")
