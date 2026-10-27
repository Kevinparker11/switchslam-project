"""iG-LIO information export: convention check without ROS.

iG-LIO builds H from dres/dx = [R*hat(mean_A) | -I] with state order [orientation, position]; the patch reorders it to
[dp_W, dtheta_I] (the convention of lio_bridge.py). This test checks, with numerical differentiation of the GICP residual
    e(R, p) = mean_B - (R mean_A + p)
under the perturbation R <- R exp(hat(dtheta)) (body frame), p <- p + dp (world frame), that
  1. the analytic Jacobian used by iG-LIO equals the numerical one up to the sign of the rotation columns (irrelevant for H);
  2. the reordered 6x6 equals J^T M J of the numerical Jacobian in [dp, dtheta] order;
  3. the C++ block swap used by the patch (4 blocks) is that same reordering.
Run: python3 -I tests_v4/test_iglio_convention.py
"""
import numpy as np


def hat(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])


def expm(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3) + hat(w)
    K = hat(w / th)
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K


rng = np.random.default_rng(3)
R = expm(rng.normal(size=3))
p = rng.normal(size=3)
mA = rng.normal(size=3) * 3
mB = R @ mA + p + rng.normal(size=3) * 0.05
Q = rng.normal(size=(3, 3))
M = Q @ Q.T + np.eye(3)                       # Mahalanobis (positive definite)


def res(dp, dth):
    return mB - ((R @ expm(dth)) @ mA + p + dp)


eps = 1e-6
J_num = np.zeros((3, 6))                      # columns [dp_W, dtheta_I]
for k in range(3):
    e = np.zeros(3); e[k] = eps
    J_num[:, k] = (res(e, np.zeros(3)) - res(-e, np.zeros(3))) / (2 * eps)
    J_num[:, 3 + k] = (res(np.zeros(3), e) - res(np.zeros(3), -e)) / (2 * eps)

J_ig = np.zeros((3, 6))                       # iG-LIO's analytic Jacobian, columns [orientation, position]
J_ig[:, 0:3] = R @ hat(mA)
J_ig[:, 3:6] = -np.eye(3)
# 1. same up to the sign of the rotation columns
assert np.allclose(J_ig[:, 3:6], J_num[:, 0:3], atol=1e-6)
assert np.allclose(-J_ig[:, 0:3], J_num[:, 3:6], atol=1e-5) or np.allclose(J_ig[:, 0:3], J_num[:, 3:6], atol=1e-5)
H_ig = J_ig.T @ M @ J_ig                      # [ori, pos]
H_num = J_num.T @ M @ J_num                   # [pos, ori]
# 3. the patch's block swap
L = H_ig
out = np.zeros((6, 6))
out[0:3, 0:3] = L[3:6, 3:6]
out[0:3, 3:6] = L[3:6, 0:3]
out[3:6, 0:3] = L[0:3, 3:6]
out[3:6, 3:6] = L[0:3, 0:3]
# 2. equals the numerical information in [dp_W, dtheta_I] order
assert np.allclose(out, H_num, atol=1e-4 * np.abs(H_num).max()), np.abs(out - H_num).max()
assert np.allclose(out, out.T)
print("iG-LIO information convention OK: [ori,pos] -> [dp_W,dtheta_I] equals the numerical J^T M J (max diff %.2e)" % np.abs(out - H_num).max())
