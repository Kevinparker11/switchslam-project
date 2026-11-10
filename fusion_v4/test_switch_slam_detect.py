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

if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1; print("ok", k)
    print(n, "tests passed")
