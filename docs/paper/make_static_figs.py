import sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, sys.argv[1])
import ate_tool as at
S, OUT = sys.argv[1], sys.argv[2]
plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.linewidth": 0.6, "pdf.fonttype": 42})
# Fig 2: Corridor02 top view
gt = at.load_gt(S + "/data/gt/c02_gt.txt")
f = S + "/f24fam/C02_switching_log_v2_F26_kf_run1.csv"
def aligned(cols):
    t, P = at.log(f, cols)
    ok = np.isfinite(P).all(1) & (t >= gt[0, 0]) & (t <= gt[-1, 0]); t, P = t[ok], P[ok]
    G = np.stack([np.interp(t, gt[:, 0], gt[:, k]) for k in (1, 2, 3)], 1)
    R, tt = at.umeyama(P, G); return P @ R.T + tt
Pf = aligned(["fused_x", "fused_y", "fused_z"]); Pv = aligned(["v_px", "v_py", "v_pz"])
fig, ax = plt.subplots(figsize=(3.45, 2.6))
ax.plot(gt[:, 1], gt[:, 2], color="0.55", lw=2.2, label="Ground truth")
ax.plot(Pv[:, 0], Pv[:, 1], color="#c2410c", lw=0.8, ls="--", label="VINS-Mono")
ax.plot(Pf[:, 0], Pf[:, 1], color="#1d4ed8", lw=0.9, label="DualChan-LVIO (ours)")
ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)"); ax.set_aspect("equal", adjustable="datalim")
ax.legend(frameon=False, loc="best", fontsize=7); ax.grid(lw=0.3, color="0.85")
fig.tight_layout(pad=0.3); fig.savefig(OUT + "/corridor02_topview.pdf"); plt.close(fig)
# Fig 3: per-run RMSE
bags = ["Multi\nFloor", "Long\nCorridor", "Corridor02", "Cave02", "GEODE\nstairs"]
f24 = [[0.45, 1.01, 0.69], [2.12, 2.15, 1.75], [1.47, 104.00, 1.29], [7.55, 7.08, 7.11], [6.15, 9.15, 7.05, 6.56]]
f26 = [[0.54], [2.10], [1.93, 2.04], [6.23], [6.36, 3.26, 5.51]]
pub = [1.61, 2.42, None, None, None]
fig, ax = plt.subplots(figsize=(3.45, 2.35))
for i, (a, b) in enumerate(zip(f24, f26)):
    ax.scatter(np.full(len(a), i - 0.13), a, s=14, marker="o", facecolors="none", edgecolors="#6b7280", lw=0.8, label="w/o gated prediction" if i == 0 else None)
    ax.scatter(np.full(len(b), i + 0.13), b, s=16, marker="s", color="#1d4ed8", label="DualChan-LVIO (ours)" if i == 0 else None)
    if pub[i] is not None:
        ax.scatter([i], [pub[i]], s=28, marker="x", color="#c2410c", lw=1.0, label="Switch-SLAM [published]" if i == 0 else None)
ax.set_yscale("log"); ax.set_xticks(range(len(bags))); ax.set_xticklabels(bags, fontsize=7)
ax.set_ylabel("ATE RMSE (m)"); ax.grid(axis="y", lw=0.3, color="0.85", which="both")
ax.set_ylim(0.3, 250); ax.legend(frameon=False, fontsize=6.5, loc="upper left", ncol=1)
fig.tight_layout(pad=0.3); fig.savefig(OUT + "/per_run_rmse.pdf"); plt.close(fig)
print("ok", len(Pf), len(Pv))

# Fig 4: Cave02 error per 120 s block, first run of each variant (from the logged runs)
blocks = ["0-120", "120-240", "240-360", "360-480", "480-600", "600-720", "720-840", "840-960"]
a = [12.0, 12.1, 5.8, 5.1, 5.0, 4.9, 5.3, 5.1]; b = [9.7, 10.1, 5.0, 4.2, 4.2, 4.1, 4.3, 4.3]
fig, ax = plt.subplots(figsize=(3.45, 1.9)); x = np.arange(len(blocks)); w = 0.38
ax.bar(x - w/2, a, w, color="#9ca3af", label="w/o gated prediction")
ax.bar(x + w/2, b, w, color="#1d4ed8", label="DualChan-LVIO (ours)")
ax.set_xticks(x); ax.set_xticklabels(blocks, fontsize=6.5); ax.set_xlabel("time window (s)"); ax.set_ylabel("RMSE in window (m)")
ax.legend(frameon=False, fontsize=6.5); ax.grid(axis="y", lw=0.3, color="0.85")
fig.tight_layout(pad=0.3); fig.savefig(OUT + "/cave02_blocks.pdf"); plt.close(fig)
