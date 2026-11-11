"""offline_imu_check.py on synthetic files: it runs, finds the filter start, reports errors well below 'repeat the last step' on a varying motion,
and finds an injected IMU time offset.  Run: python3 test_offline_imu_check.py"""
import os, subprocess, sys, tempfile, re
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fusion_core as fc, offline_imu_check as oc

rng = np.random.default_rng(3)
R_IL = oc.T_LI[:3, :3]; U, _, Vt = np.linalg.svd(R_IL); R_IL = U @ Vt; t_IL = oc.T_LI[:3, 3]
G = fc.so3_exp([0.1, -0.15, 0.2]) @ np.array([0, 0, -9.81007]); BG = np.array([0.004, -0.003, 0.006]); BA = np.array([0.04, -0.02, 0.03])
R0 = fc.so3_exp([0.2, 0.1, 0.4]); T0 = 2.0

def truth(t):
    s = max(0.0, t - T0)
    p = np.array([0.5 * s * s + 0.3 * np.sin(2 * s), 0.2 * s * s, 0.1 * np.sin(1.1 * s)]) + np.array([1.0, 2.0, 3.0])
    a = np.array([1.0 - 1.2 * np.sin(2 * s), 0.4, -0.121 * np.sin(1.1 * s)]) if t >= T0 else np.zeros(3)
    wz = 0.5 * np.sin(1.5 * s) if t >= T0 else 0.0
    th = (0.5 / 1.5) * (1 - np.cos(1.5 * s))
    return R0 @ fc.so3_exp([0, 0, th]), p, a, np.array([0.0, 0.0, wz])

d = tempfile.mkdtemp()
def make(shift):
    rows = []
    for t in np.arange(0.0, 20.0, 1 / 400.0):
        R, p, a, w = truth(t)
        rows.append((t + shift, *(w + BG + rng.normal(0, 0.003, 3)), *(R.T @ (a - G) + BA + rng.normal(0, 0.05, 3))))
    pd.DataFrame(rows, columns=["t", "gx", "gy", "gz", "ax", "ay", "az"]).to_csv(os.path.join(d, "imu%+.2f.csv" % shift), index=False)
make(0.0); make(0.04)
rows = []
for t in np.arange(0.5, 20.0, 0.1):
    R, p, a, w = truth(t); RL = R @ R_IL; pL = p + R @ t_IL
    RL = RL @ fc.so3_exp(rng.normal(0, 0.002, 3)); pL = pL + rng.normal(0, 0.005, 3)
    q = fc.R_to_quat(RL); rows.append(dict(time=round(t, 4), fused_x=pL[0], fused_y=pL[1], fused_z=pL[2], fused_qx=q[0], fused_qy=q[1], fused_qz=q[2], fused_qw=q[3]))
pd.DataFrame(rows).to_csv(os.path.join(d, "log.csv"), index=False)
script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "offline_imu_check.py")
out = subprocess.run([sys.executable, script, "--imu", os.path.join(d, "imu+0.00.csv"), "--log", os.path.join(d, "log.csv")], capture_output=True, text=True)
assert out.returncode == 0, out.stderr[-800:] + out.stdout[-800:]
txt = out.stdout
m0 = re.search(r"Filter started at scan (\d+)", txt); assert m0 and 8 <= int(m0.group(1)) <= 12, txt[:600]
m = re.search(r"IMU / repeat-last = ([0-9.]+)", txt); assert m and float(m.group(1)) < 0.5, txt
assert "best offset +0.00 s" in txt or "best offset -0.00 s" in txt, txt[-500:]
out2 = subprocess.run([sys.executable, script, "--imu", os.path.join(d, "imu+0.04.csv"), "--log", os.path.join(d, "log.csv")], capture_output=True, text=True)
assert "best offset -0.04 s" in out2.stdout, out2.stdout[-500:]
# a moving start: never initialises, exit code 2 and a clear message
mv = pd.read_csv(os.path.join(d, "imu+0.00.csv")); mv = mv[mv["t"] > 4.0]; mv.to_csv(os.path.join(d, "imu_late.csv"), index=False)
lg = pd.read_csv(os.path.join(d, "log.csv")); lg = lg[lg["time"] > 4.5]; lg.to_csv(os.path.join(d, "log_late.csv"), index=False)
o3 = subprocess.run([sys.executable, script, "--imu", os.path.join(d, "imu_late.csv"), "--log", os.path.join(d, "log_late.csv")], capture_output=True, text=True)
assert o3.returncode == 2 and "never started" in o3.stdout, o3.stdout[-400:]
print("offline_imu_check tests passed;  median IMU / repeat-last = %s, injected 0.04 s offset found" % m.group(1))
