# Farm/panels generalization check: do Multi Floor's two Hessian-scale disparities hold?

Data: `switching_log_threeway_farm_rawlog.csv` (3284 frames, `switching_node_threeway.py` with the
raw-Hessian logging patch, L-shape route via `waypoint_driver_v4.py`, 80.5m driven, husky reset to
(0,0,0.2) before the drive). Mode distribution: TIGHTLY_COUPLED 3182, LIDAR_ONLY_SAFE 75, TRANSITION 27.

Methodology matches the Multi Floor analysis in `offline_ablation_replay.py` exactly:
- Diagnostic 1: median of all raw (unnormalized) eigenvalues of `H_l`'s rotation block (`H_l[0:3,0:3]`)
  vs translation block (`H_l[3:6,3:6]`), pooled across every frame.
- Diagnostic 2: `trace(H_v)` vs `trace(H_l)`, restricted to TIGHTLY_COUPLED frames.

## Results

| Diagnostic | Multi Floor (real hardware) | Farm (Gazebo sim) |
|---|---|---|
| Rotation-block / translation-block eigenvalue ratio | 30.3x (R=6215.83, T=205.14) | **202.0x** (R=35322.5, T=174.9) |
| trace(H_v) / trace(H_l), TIGHTLY_COUPLED, median | 122,541x | **17,369x** |
| \|\|H_v\|\| / \|\|H_l\|\| (Frobenius norm), TIGHTLY_COUPLED, median | 75,333x | **10,295x** |

(Note: the "~75,000x" figure quoted earlier in this conversation was the Frobenius-norm ratio, not the
trace ratio -- these are different statistics. Both are reported here for a clean comparison.)

## Honest read

Both disparities are **real and same-direction** on Farm data: rotation eigenvalues dominate
translation eigenvalues in `H_l`, and `H_v` dominates `H_l` by several orders of magnitude, exactly as
on Multi Floor. This is not an artifact specific to the SubT Hawkins real-hardware rig -- it's a
property of this Hessian construction method (LOAM's point-to-plane geometric Hessian vs VINS-Mono's
pixel-reprojection Hessian) that generalizes across a materially different environment, sensor rig
(simulated Husky + Velodyne + monocular camera vs real hardware), and dataset.

The *magnitudes* differ meaningfully in opposite directions:
- The R/T eigenvalue disparity is ~6.7x **larger** on Farm (202x vs 30x) -- rotation is even more
  dominant relative to translation here than on Multi Floor.
- The H_v/H_l disparity is ~7x **smaller** on Farm, whether measured by trace (17.4K vs 122.5K) or
  norm (10.3K vs 75.3K) -- VINS-Mono's Hessian, while still enormously larger than LOAM's, is less
  extreme here than in the Multi Floor rig.

Both are consistent with a real, if unexplained, effect: the underlying disparity mechanism (unit
mismatch between geometric and reprojection-error Hessians) generalizes, but its exact magnitude is
sensitive to something that differs between the two datasets/rigs (e.g. camera resolution/intrinsics,
feature count, point cloud density, or Velodyne channel count -- not investigated further here).
