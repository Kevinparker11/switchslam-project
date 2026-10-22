# Old vs new: comparison test results

**What was tested.** The current switching node (`switching_node_schurbingham.py`, its branch logic copied exactly) against the new methods (D1–D6), on one simulated 30 m drive:
- 300 frames at 10 Hz: open area → 100-frame corridor (degenerate along x) → corridor with doorways.
- **Real nearest-neighbour point-to-plane ICP every frame**, on an A-LOAM-like 0.4 m voxel map with 5-point plane fits.
- **All pipelines see identical sensor data** (paired comparison), over 5 seeds.
- A full 2×2×2 factorial over the three changes (detector × switching × fusion), so each change's own effect is measured.

Scripts: `compare_old_vs_new_pipeline.py` (end to end), `verify_final_methods.py` (component checks). Raw output: `compare_output_cal99.txt` (main), `compare_output_cal95.txt` (sensitivity). CSVs: `compare_results_cal99.csv`, `compare_per_frame_cal99.csv`. Chart: `old_vs_new_comparison.png`.

**This is a synthetic simulation, not real-sensor validation.**

## Headline: trajectory error (ATE, cm, mean ± std of 5 seeds)

| Scenario | Old pipeline | Old + new fusion only | New pipeline | New better in |
|---|---|---|---|---|
| A. Vision fails on 40 of 300 frames | 280.0 ± 7.0 | 15.9 ± 3.3 | **14.4 ± 5.1** | 5/5 seeds |
| B. Vision healthy throughout | 14.5 ± 4.5 | 15.2 ± 5.7 | 16.3 ± 6.2 | 2/5 (a tie) |
| C. B + 5% random false detector flags | 14.5 ± 4.5 | 15.2 ± 5.7 | 16.3 ± 6.2 | 2/5 (a tie) |
| D. LiDAR has a 2 mm/frame z bias | **14.4 ± 5.2** | 42.3 ± 2.8 | 42.9 ± 0.8 | **0/5 (worse)** |
| E. Vision has a 2% scale bias | 32.7 ± 8.2 | 24.9 ± 9.8 | **17.4 ± 10.1** | 4/5 |

## Verdict per change

| Change | Test | Old | New | Verdict |
|---|---|---|---|---|
| **Switch-SLAM χ² value** | χ²₂ quantiles (S2) | 0.103 used as the 95% value | It is the *lower* 5% point (CDF 0.050); the correct 5.991 makes every threshold negative | **Proven error** |
| **Detector** (D1 replaces semicircle + Channel T) | Per-frame verdicts, scenario B | Flags 100% of well-constrained frames and 100% of corridor frames | Flags 0% of well-constrained frames and 96% of corridor frames | **Much better at telling them apart**, but only after calibration (see caveat 2) |
| | Per-frame error, open area (B, with new fusion) | 9.2 mm | 5.2 mm | Better: good LiDAR information is no longer thrown away |
| **Channel T removed** | Identity check (S1) | treated as a separate channel | H_tt = N·T exactly (difference 0); flags 100% of well-constrained frames | **Proven redundant** |
| **Fusion** (scaled LiDAR + projection + covariance intersection; vision failure → IMU fill) | Scenario A | 280.0 cm | 15.9 cm (this change alone) | **Biggest gain.** The old vision-failure branch zeroes real motion along flagged directions: −200 cm in the corridor = exactly 20 frames × 10 cm |
| | Scenarios B / C | 14.5 cm | 15.2 cm | No difference while vision is healthy |
| | Scenario D (biased LiDAR) | 14.4 cm | 42.3 cm | **Worse.** Information weighting trusts LiDAR and inherits its unmodelled bias |
| | Scenario E (biased vision) | 32.7 cm | 24.9 cm | Better |
| | Consistency under correlated errors (S5) | — | BLUE overconfident (ANEES 7.03 > 6.11); covariance intersection consistent (4.47) | Covariance intersection is the safe choice |
| **conf removed** | Scalar weighting (S5) | 1.172 cm RMSE | 0.713 cm with projection | A scalar cannot fix one bad direction |
| **CUSUM replaces 5-frame buffer** | Scenario C, new detector + old fusion | 27.4 mode switches, 29.2% false degenerate, ATE 35.4 cm | 2.0 switches, 1.1% false degenerate, ATE 19.7 cm | **Better when the old fusion is used** |
| | Scenario C, with new fusion | ATE 15.8 cm, 27.4 switches | ATE 16.3 cm, 2.0 switches | Same accuracy, far fewer switches. The new fusion already ignores flags that carry no direction |
| | Detection delay (S6) | 5.99 frames | 2.27 frames | Faster |
| **VO-failure criteria** (D5) | — | — | — | Not testable in simulation; it is a citation fix (20 features is VINS-Mono's keyframe rule, not its failure check) |

## Caveats you must state

1. **Most of the large Scenario A gain comes from one branch.** The old `LIDAR_ONLY_SAFE` code zeroes motion along "degenerate" directions instead of predicting it. With vision healthy (B, C), old and new are statistically tied.
2. **The new detector needs empirical calibration.** Its noise model alone missed **36.5%** of known-degenerate frames on held-out maps; the nominal rate is 5%. The cause: voxel maps produce structured (layered) plane-fit errors, which break the model's independent-Gaussian assumption. Calibrating on held-out maps fixed it:
   - ×2.48 at the 95th percentile: corridor detection 87%.
   - ×3.29 at the 99th percentile: corridor detection 96%, with a 3–6× margin before any false alarm in well-constrained scenes.

   **I chose the 99th percentile after seeing the 95th-percentile results.** The reasoning is principled: missing a degeneracy costs more than a false alarm when vision is available. But it is a post-hoc choice, so both are reported. With the 95th percentile, the new pipeline was worse than the old in Scenario B (25.2 vs 14.5 cm).
3. **Information-weighted fusion assumes unbiased sensors** (Scenario D). If A-LOAM's real z-drift is significant, the new fusion imports it. In this simulation the old pipeline is effectively vision-only, because the unscaled A-LOAM Hessian is tiny next to VINS's, and simulated vision is unbiased, which favours the old pipeline. The real outcome depends on the actual Hessian magnitudes, which have never been logged.
4. All magnitudes (noise, bias, failure windows) are simulation choices. This checks the logic, not the real system. The Gazebo protocol (D9) is still required.

## What the evidence says to do

- **Adopt the new fusion.** It is the dominant gain, and it is never worse except when LiDAR is biased.
- **Adopt the new detector only with the held-out calibration step.**
- **Add a LiDAR bias check** (for example, compare z against IMU/gravity) before trusting LiDAR information.
- **CUSUM**: keep it for stability (14× fewer mode switches), but it adds no accuracy once the new fusion is in place.
