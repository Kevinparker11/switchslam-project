# fusion_v4 (GenZ-LIO front end): held-out result on Corridor02 and Cave02 (21-22 Oct 2026)

**Outcome: the configuration calibrated on Multi Floor did not generalise.** The weights (c_T = 3e-6, c_R = 5e-6, SAH on) were frozen on Multi Floor and run live, once each, on two bags that were not used for tuning. Both runs were at 1.0x replay. Nothing was re-tuned on these bags.

## Live results (full-span ATE RMSE, m)

| Sequence | Master F16 (A-LOAM) | GenZ-LIO alone (frozen config) | VINS-Mono alone (this run) | G17 live |
|---|---|---|---|---|
| Corridor02 | 1.71 | 3.98 | 336.7 (diverged) | 5.60 |
| Cave02 | 4.40 | 4.61 | 148.8 (diverged) | 12.66 |

For comparison, the master pipeline's VINS-Mono alone scored 4.03 m (Corridor02) and 10.25 m (Cave02).

## Diagnosis (from the recorded logs, `analysis/improve/heldout_diag.py`, `heldout_diag2.py`)

1. **Live VINS-Mono failed and re-initialised repeatedly.** Corridor02: 56 VO_FAIL episodes (1276 of 8817 rows). Cave02: 221 episodes (832 of 9448 rows). First FUSED output at +95.7 s and +117.9 s after a long stationary start.
2. **The fused output was worse than GenZ-LIO alone.** Replaying the frozen G9 rule reproduced the live fused result (5.67 / 12.64), so the logs are consistent. The median translation weights (0.55-0.97) with the very small c_T = 3e-6 still let a large share of the divergent VINS translation into the fused pose. The c_T was calibrated on Multi Floor, where VINS-Mono was healthy.
3. **GenZ-LIO alone is no better than the master here** with one frozen configuration (3.98 vs 1.71 on Corridor02; 4.61 vs 4.40 on Cave02). The stationary start is not the cause: over the first 60 s GenZ-LIO tracked the ground truth (Corridor02: moved 0.07 m vs 0.00; Cave02: 2.67 m vs 2.64). GenZ-LIO's published numbers used a per-sequence configuration; this study uses one.
4. **Information scale differs between sequences.** The rotation-information trace on Corridor02 was about 3x larger than on Multi Floor, so a fixed c does not mean the same weight.

## Post-hoc observation (not adopted)
Replaying the older G8 rule (c_T = 1e-4, rotation from VINS) on the same logs gives 3.82 m (Corridor02) and 2.61 m (Cave02, below the master's 4.40). This was seen after looking at these two bags, so it is **not** a valid tuned result and the setting was not adopted.

## Update, 22 Oct 2026: the rate control was run
Rerun of G17 at the master's replay rates (laptop, one run each): **Corridor02 1.89 m (0.33x), Cave02 3.65 m (0.5x)**, with VINS-Mono healthy. The failure above was therefore a replay-rate effect, not a fusion failure. The same logs show, however, that GenZ-LIO alone is better than the fused result on Cave02 (0.283 m), and the GEODE test (GenZ alone 0.35-0.49 m, fused 19.8-24.6 m) shows the same pattern. Details: `GenZ_fusion_v4_RateControl_and_GEODE_Results.md`.
