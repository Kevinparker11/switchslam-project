"""Tests of switch_slam_detect (run: python3 test_switch_slam_detect.py)."""
import numpy as np
import fusion_core as fc
import switch_slam_core as sw
import switch_slam_detect as sd

def H_from_rad(Hr):
    D = np.diag([2.0, 2, 2, 1, 1, 1]); return D @ Hr @ D
H_ISO = H_from_rad(np.diag([400.0] * 6))
H_DEG_X = H_from_rad(np.diag([400.0, 400, 400, 1.0, 400, 400]))
H_DEG_RZ = H_from_rad(np.diag([400.0, 400, 1.0, 400, 400, 400]))
T_ISO = np.eye(3) / 3
T_NOX = np.diag([1e-4, 0.5, 0.5 - 1e-4])            # raw normals have almost nothing along x

def test_isotropic_nothing_fires():
    d = sd.OurDetector()(H_ISO, T_ISO)
    assert not d["degenerate"] and d["remove"].shape[1] == 0, d["chan"]

def test_switch_rule_is_always_included():
    d = sd.OurDetector(("R",))(H_DEG_X, None)
    base = sw.eig_degeneracy(H_DEG_X)
    assert d["degenerate"] and d["chan"]["SW"] and base["degenerate"]
    assert d["remove"].shape[1] >= 1
    assert abs(abs(d["remove"][3, 0]) - 1.0) < 1e-6          # the flagged direction is translation x

def test_T_channel_sees_translation_x():
    d = sd.OurDetector(("T",))(H_DEG_X, None)
    assert d["chan"]["T"] and d["degenerate"]

def test_R_channel_sees_weak_rotation():
    d = sd.OurDetector(("R",))(H_DEG_RZ, None)
    assert d["chan"]["R"] and d["degenerate"]
    Q = d["remove"]
    assert np.allclose(Q @ Q.T @ np.eye(6)[:, 2], np.eye(6)[:, 2], atol=1e-6)    # rotation z is inside the removed span

def test_additional_T_fires_when_solver_is_silent():
    assert not sw.eig_degeneracy(H_ISO)["degenerate"]
    off = sd.OurDetector(("T",))(H_ISO, T_NOX)
    assert not off["degenerate"]                              # plain Schur T does not see it
    on = sd.OurDetector(("TT",))(H_ISO, T_NOX)
    assert on["degenerate"] and on["chan"]["TT"] and not on["chan"]["SW"], on["chan"]
    assert np.allclose(np.abs(on["remove"][:, 0]), np.eye(6)[3], atol=1e-6)            # translation x removed

def test_additional_T_missing_falls_back_to_plain_T():
    d = sd.OurDetector(("TT",))(H_DEG_X, None)
    assert d["chan"]["T_missing"] and d["degenerate"]        # Schur T still sees the corridor

def test_union_is_orthonormal():
    d = sd.OurDetector()(H_from_rad(np.diag([400.0, 400, 1.0, 1.0, 400, 400])), T_ISO)
    Q = d["remove"]
    assert np.allclose(Q.T @ Q, np.eye(Q.shape[1]), atol=1e-8) and Q.shape[1] >= 2

def test_singular_hessian_does_not_raise():
    d = sd.OurDetector()(np.zeros((6, 6)), T_ISO)
    assert d["degenerate"]

def test_core_removes_the_additional_T_direction():
    """Eq. 16 line 2 with the tensor-only flag: the x component of the scan-matching displacement is dropped"""
    det = sd.OurDetector(("TT",))
    core = sw.SwitchSlamCore(np.eye(3), np.zeros(3), n_buf=5, hess_frame="body", detector=det)
    I = np.eye(3)
    o0 = (I, np.zeros(3)); core.init((I, np.zeros(3)), o0, None, (I, np.zeros(3)), t=0.0)
    o1 = (I, np.array([0.1, 0.0, 0.0]))
    dec = core.decide(o1, None, H_ISO, t=0.1, T=T_NOX)
    assert dec["eig"]["chan"]["TT"] and dec["kind"] == "LIDAR"
    g = dec["guess"]
    aft = (I, g[1] + np.array([0.30, 0.20, 0.10]))
    R, p, info = core.finish(aft, H_ISO, dec, g)
    assert info["case"] == 2 and info["nrem"] == 1
    assert np.allclose(p - g[1], [0.0, 0.20, 0.10], atol=1e-9), p - g[1]       # x dropped, y and z kept

def test_default_core_is_unchanged():
    core = sw.SwitchSlamCore()
    assert core.detector is None

# ---------------------------------------------------------------- our detection only (OwnDetector): no Switch-SLAM thresholds
def test_own_isotropic_nothing_fires():
    d = sd.OwnDetector()(H_ISO, T_ISO)
    assert not d["degenerate"] and d["remove"].shape[1] == 0 and abs(d["w_blend"] - 1.0) < 1e-12, d["chan"]

def test_own_T_threshold_is_information_equal_to_vio():
    # c_T = 0.03, unit VIO information: a direction is degenerate where c lambda < 1, i.e. lambda < 33.3
    ok = sd.OwnDetector(("T",))(H_from_rad(np.diag([400.0, 400, 400, 40.0, 400, 400])), None)
    assert not ok["degenerate"]
    bad = sd.OwnDetector(("T",))(H_from_rad(np.diag([400.0, 400, 400, 30.0, 400, 400])), None)
    assert bad["chan"]["T"] and bad["degenerate"]
    assert abs(abs(bad["remove"][3, 0]) - 1.0) < 1e-6

def test_own_R_is_judged_alone_with_kappa():
    # kappa(S_RR) > 15.7: weak rotation z
    d = sd.OwnDetector(("R",))(H_from_rad(np.diag([400.0, 400, 20.0, 400, 400, 400])), None)
    assert d["chan"]["R"] and not d["chan"]["T"] and d["remove"].shape[1] == 1
    assert abs(abs(d["remove"][2, 0]) - 1.0) < 1e-6
    ok = sd.OwnDetector(("R",))(H_from_rad(np.diag([400.0, 400, 30.0, 400, 400, 400])), None)       # kappa 13.3
    assert not ok["degenerate"]

def test_own_R_and_T_are_independent():
    Hrt = H_from_rad(np.diag([400.0, 400, 400, 1.0, 400, 400]))
    d = sd.OwnDetector(("R", "T"))(Hrt, None)
    assert d["chan"]["T"] and not d["chan"]["R"]
    d = sd.OwnDetector(("R", "T"))(H_DEG_RZ, None)
    assert d["chan"]["R"] and not d["chan"]["T"]

def test_own_does_not_use_the_paper_rule():
    # a Hessian the paper's normalised rule calls degenerate (one weak direction) but whose weak direction is still above our T bar
    H = H_from_rad(np.diag([400.0, 400, 400, 400, 400, 60.0]))
    assert sw.eig_degeneracy(H)["degenerate"]
    assert not sd.OwnDetector()(H, T_ISO)["degenerate"]

def test_own_additional_T():
    off = sd.OwnDetector(("T",))(H_ISO, T_NOX)
    assert not off["degenerate"]
    on = sd.OwnDetector(("TT",))(H_ISO, T_NOX)
    assert on["chan"]["TT"] and on["degenerate"]
    assert np.allclose(np.abs(on["remove"][:, 0]), np.eye(6)[3], atol=1e-6)
    miss = sd.OwnDetector(("TT",))(H_DEG_X, None)
    assert miss["chan"]["T_missing"] and miss["degenerate"]

def test_own_blend_weight_falls_with_information():
    a = sd.OwnDetector()(H_from_rad(np.diag([400.0, 400, 400, 40.0, 400, 400])), T_ISO)["w_blend"]
    b = sd.OwnDetector()(H_from_rad(np.diag([400.0, 400, 400, 10.0, 400, 400])), T_ISO)["w_blend"]
    c = sd.OwnDetector()(H_DEG_X, T_ISO)["w_blend"]
    assert 1.0 >= a > b > c >= 0.0, (a, b, c)

def test_own_core_uses_the_blend_and_the_remap():
    det = sd.OwnDetector()
    core = sw.SwitchSlamCore(np.eye(3), np.zeros(3), n_buf=5, hess_frame="body", detector=det)
    I = np.eye(3)
    core.init((I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), t=0.0)
    core.buf.extend([False, True])                                   # Start/End
    o1 = (I, np.array([0.1, 0, 0])); v1 = (I, np.array([0.3, 0, 0]))
    dec = core.decide(o1, v1, H_DEG_X, t=0.1, T=T_ISO)
    assert dec["kind"] == "INTERP" and 0.0 < dec["w"] < 1.0 and abs(dec["w"] - det(H_DEG_X, T_ISO)["w_blend"]) < 1e-12
    g = dec["guess"]
    aft = (I, g[1] + np.array([0.30, 0.20, 0.10]))
    R, p, info = core.finish(aft, H_DEG_X, dec, g)
    assert info["case"] == 3 and info["nrem"] >= 1                   # Eq. 15 fusion of the LiDAR step (flagged direction removed) and the VINS step

def test_vo_untrusted_counts_as_failure():
    """F32: an outside check that distrusts VINS makes Algorithm 1 take the LiDAR guess and Eq. 16 line 2"""
    core = sw.SwitchSlamCore(np.eye(3), np.zeros(3), n_buf=5, hess_frame="body", detector=sd.OwnDetector(("T",)))
    I = np.eye(3)
    core.init((I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), t=0.0)
    core.buf.extend([True] * 5)
    o1 = (I, np.array([0.1, 0, 0])); v1 = (I, np.array([0.3, 0, 0]))
    d_ok = core.decide(o1, v1, H_DEG_X, t=0.1)
    assert d_ok["kind"] == "VO" and not d_ok["vo_fail"]
    d_no = core.decide(o1, v1, H_DEG_X, t=0.1, vo_trusted=False)
    assert d_no["kind"] == "LIDAR" and d_no["vo_fail"]
    g = d_no["guess"]
    _, _, info = core.finish((I, g[1] + np.array([0.3, 0.2, 0.1])), H_DEG_X, d_no, g)
    assert info["case"] == 2

def test_jump_limits_are_configurable():
    core = sw.SwitchSlamCore(np.eye(3), np.zeros(3), vins_jump_pos=1.0)
    I = np.eye(3)
    core.init((I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), t=0.0)
    assert core.decide((I, np.array([0.1, 0, 0])), (I, np.array([1.5, 0, 0])), H_DEG_X)["vo_fail"]
    core5 = sw.SwitchSlamCore(np.eye(3), np.zeros(3))
    core5.init((I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), (I, np.zeros(3)), t=0.0)
    assert not core5.decide((I, np.array([0.1, 0, 0])), (I, np.array([1.5, 0, 0])), H_DEG_X)["vo_fail"]

if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1; print("ok", k)
    print(n, "tests passed")
