# Thesis methodology: action plan after the synthetic comparison

## Corrections to the results summary first

- **Scenario D:** the new pipeline was better in 0/5 seeds, i.e. **worse in 5/5**. Write it that way.
- **Scenario C does not test old vs new.** The two rows are identical to Scenario B for a reason:
  - The old detector already flags 100% of frames, so 5% extra flags change nothing.
  - The new fusion only projects flags that carry a direction, so random flags are harmless there.

  The only informative result in C is the ablation: with the old fusion, CUSUM cut false switching from 27.4 to 2.0 and ATE from 35.4 to 19.7 cm.
- **"CUSUM delay 2.27 vs 5.99 frames" is not a pipeline measurement.** It comes from a separate simulation with *assumed* per-frame rates (false-flag a = 0.05, detection b = 0.90).
- **Scenario B is a tie, not a loss.** 16.3 ± 6.2 vs 14.5 ± 4.5 cm, better in 2/5 seeds.

---

## A. KEEP (do not change)

1. **Schur decoupling (S_RR, S_tt).** The marginal-covariance identity is exact.
2. **Channel T removal.** H_tt = N·T exactly.
3. **Scalar confidence removal.**
4. **Covariance intersection, not BLUE.** The increments share IMU data and the prior, and BLUE was overconfident under correlation.
5. **Projection of degenerate directions plus IMU fill when vision fails.** This produced the dominant gain.
6. **VINS-Mono's own failure criteria.**
7. **CUSUM.** Keep it for switching stability only (see B6).
8. **The paired, factorial evaluation design and held-out calibration.**
9. **The tolerances τ_t = 0.10 m and τ_R = 1°.** They are requirements, so fix them now and do not retune them after seeing results.
10. **Do not return to the semicircle threshold, κ > 10 or λ3 < 0.15.**
11. **Do not add** an aliasing detector, a visual Hessian test or a new fusion scheme.
12. **Keep every negative result in the thesis.**

## B. CHANGE

1. **Restate D1(a) honestly.** It is a *model-derived statistic with an empirically calibrated null*, not a purely derived threshold. The uncalibrated model missed 36.5% of known-degenerate frames (target 5%) because voxel-map plane-fit errors are correlated, not independent. The calibration step (held-out known-degenerate frames, multiplier c) becomes part of the method.
2. **Fix the calibration percentile now, before any Gazebo test data is seen: 99%.** The justification is cost asymmetry: when vision is available, a missed degeneracy imports fake LiDAR information, while a false alarm only discards some good information. State openly that 99% was first chosen after seeing the 95% result.
3. **Correct the methods report.** Its "99.8% corridor detection" came from a simulator artifact: a fixed voxel grid that put a constant 2.4 mm/frame bias into the LiDAR. Replace it with the calibrated figures.
4. **Make LiDAR covariance calibration part of the method, not just validation.** Scale I_l by an inflation factor k estimated from NEES on calibration runs. CI is only consistent if its input covariances are.
5. **LiDAR bias (Scenario D).** Measure first, then act. Do not redesign the fusion.
   - **Step 1:** In Gazebo, measure the real per-frame A-LOAM bias against ground truth, per axis. If it is within the NEES-calibrated noise, document it as a limitation and stop.
   - **Step 2:** Only if the bias is significant, add a *disagreement monitor* built from parts already in the method:
     - a windowed CUSUM on the normalized innovation between LiDAR and VIO increments, along each axis;
     - on alarm, set ω = 0.5 (equal trust) in the disagreeing direction. CI stays consistent for any ω.
   - **Why equal trust:** with only two sensors you can detect a disagreement but not tell which sensor is wrong. Projecting LiDAR out would fix D but break E. Equal trust bounds the damage to about half the bias in either case.
   - **Status:** untested. Treat it as a proposal until the Gazebo bias-injection test.
6. **CUSUM claim.** Claim fewer false switches and lower delay. Do **not** claim an ATE improvement once the new fusion is in place.
7. **Logging (required for every claim in C).** Per frame, log:
   - H_l and H_v scale (trace, eigenvalues);
   - per-direction λ, μ, threshold, and which sub-test (a or b) fired;
   - ω, the CUSUM statistics g, the mode, and the VO-failure flags.

   Also patch A-LOAM to export per-correspondence points, normals and neighbourhood scatter, which D1 needs.
8. **IMU fill horizon.** State how long IMU-only fill is trusted in the vision-failed branch. The synthetic test assumed 1 cm/frame IMU error over 2 s windows, which has not been checked.

## C. VALIDATE (minimum Gazebo experiment)

**Worlds, with ground truth defined by geometry, never by the detector:**

| World | Degenerate directions | Purpose |
|---|---|---|
| W1: long rectangular corridor | 1 translational (along the axis) | Main test |
| W2: room / corridor with doorways | 0 | Control |
| W3: circular tunnel | translation along the axis + roll about it | **The rotation part of D1 has never been exercised with a truly rotation-degenerate scene.** If time is short, this is the one to add. |

Calibration and test must use different instances (different length, width and texture), never random frames from the same run.

**Runs.** One route through W2 → W1 → W2.
- Record the rosbag once, then replay it so every pipeline sees identical data.
- Repeat ≥ 5 runs (5–10 if time allows).
- Vision failure: drop camera messages for 2 s inside W1 and once inside W2 on replay. This covers Scenario A.
- Bias injection on replay: +2 mm/frame z on the LiDAR increment (Scenario D) and 2% scale on the VIO increment (Scenario E).

**Pipelines (minimum set):**
1. OLD
2. NEW
3. OLD + new fusion only
4. NEW with the 5-frame buffer instead of CUSUM
5. LiDAR-only
6. VIO-only

**Sample size.** ≥ 1068 labelled frames per class gives ±0.03 (Wilson, 95%). At 10 Hz that is about 107 s of corridor and 107 s of non-degenerate driving in the test set.

**Metrics to report:**

| Metric | Detail |
|---|---|
| ATE | evo, SE(3) Umeyama alignment; mean ± std over runs, plus each run |
| RPE | translation and rotation, over 1 m and per frame, **per segment** (open / corridor / doors) |
| Final drift | % of distance travelled |
| Degeneracy detection | Precision, recall, F1 and false-alarm rate per frame, each with a Wilson 95% CI |
| Direction correctness | Angle between the detected degenerate eigenvector and the true axis |
| CUSUM | Entry and exit delay (frames from geometric boundary to mode change); false switches per minute (≈ ARL0); measured a and b |
| Consistency | NEES/ANEES with the χ² band, for the LiDAR registration covariance (before and after inflation k) and for the fused covariance |
| Calibration | c with a bootstrap CI; spread of c across calibration worlds |
| Diagnostics | Which D1 sub-test fired; CI weight ω distribution; mode occupancy |
| Real-time | D1 + fusion compute time per frame |
| Paired statistics | Wilcoxon signed-rank (old vs new) on per-run ATE and per-segment RPE; McNemar on per-frame detector verdicts |

**On c = 3.29:** treat it as a **provisional value** from the synthetic study only. c describes how plane-fit errors behave in a particular map, so it must be recalibrated:
- on the Gazebo calibration worlds, at the pre-fixed 99th percentile;
- with a bootstrap CI;
- with the check that c is reasonably stable across W1 variants.

If c varies strongly between worlds, report that the detector needs per-environment calibration. Do not reuse 3.29 for Gazebo or real data.

## D. FINAL CLAIMS

**Can you claim "The proposed method improves SLAM robustness in GPS-denied environments"?** No.
- All evidence is synthetic.
- Under healthy vision it ties with the old pipeline.
- Under LiDAR bias it is worse.
- No real GPS-denied data has been used.

**Defensible wording now:**
> "In a synthetic point-to-plane ICP simulation, the proposed projected covariance-intersection fusion reduced trajectory error when visual odometry failed during a LiDAR-degenerate corridor (ATE 280 → 14 cm, 5/5 seeds). After calibration on held-out maps, the proposed detector separated degenerate from well-constrained frames (0% false alarms, ≈96% detection). With healthy vision, performance was statistically indistinguishable from the existing pipeline. Under a systematic LiDAR bias, it was worse (14 → 43 cm), because information-weighted fusion assumes unbiased sensors. Validation in Gazebo and on real data is pending."

**After the Gazebo experiment, if it succeeds:**
> "…improves robustness to visual-odometry failure in LiDAR-degenerate simulated environments."

Keep "simulated" until you have real or public-dataset results (for example GEODE or SubT-MRS).

### PROVEN mathematically
- [H⁻¹]_tt = S_tt⁻¹ and [H⁻¹]_RR = S_RR⁻¹ (block inverse).
- H_tt = N·T for point-to-plane residuals, so Channel T is redundant.
- c·H keeps H's eigenvectors and condition number, so no scalar weight can isolate one direction.
- Switch-SLAM's 0.103 is the lower 5% point of χ²₂, not the 95% critical value.
- The Bingham statistic tests uniformity and grows linearly with N for any non-uniform scene.
- CI is consistent for any cross-correlation, *provided its input covariances are consistent*.
- BLUE is optimal only for unbiased, uncorrelated inputs with correctly scaled covariances.
- The projection (Zhang 2016 remapping) is an orthogonal projector onto the well-constrained directions.
- CUSUM is delay-optimal for a given false-alarm rate, *for independent per-frame verdicts with known a and b*.
- **Not proven:** the noise-floor null distribution. It is a Satterthwaite approximation, and it failed uncalibrated.

### SUPPORTED by synthetic experiments only
- The new fusion's large gain when vision fails (A); a tie with healthy vision (B); a gain under vision scale bias (E).
- A loss under LiDAR bias (D).
- The old detector and Channel T flag every frame (0 discrimination); the calibrated D1 separates the scenes.
- An uncalibrated D1 misses 36.5% (vs a nominal 5%), and c = 3.29 at the 99th percentile.
- CUSUM reduces false switching (27.4 → 2.0 switches) and delay (2.27 vs 5.99 frames, at assumed rates).
- CI stays consistent and BLUE becomes overconfident under correlated errors (stylized magnitudes).

### NOT YET VALIDATED
- Everything on Gazebo or real data: c, the inflation k, NEES, a/b, the real delay, the real Hessian magnitudes, the real A-LOAM bias.
- Rotation-degeneracy detection (no rotation-degenerate scene tested).
- How the VINS failure criteria behave in this system.
- IMU-fill accuracy over a realistic outage.
- Extraction of the VINS marginal information I_v (the simulation used a synthetic diagonal H_v).
- The frame dependence of S_tt.
- Real-time feasibility.
- The LiDAR-bias monitor (B5).
- Any claim about GPS-denied environments in general.
