# fusion_v4: replay-rate controls (Corridor02, Cave02) and the GEODE stairs test (22 Oct 2026)

Metric everywhere: full-span ATE RMSE (m), Umeyama SE(3), no scale. Settings frozen as on Multi Floor (G17: c_T 3e-6, c_R 5e-6, SAH; F16: C_T 0.03, SAH). Nothing was tuned on any of these runs. Raw results: `results_data/2026-10-22/`.

## Summary
1. **The held-out failure of 21 Oct was a replay-rate effect.** At the master's rates G17 scores 1.89 m (Corridor02, 0.33x) and 3.65 m (Cave02, 0.5x), against 5.60 and 12.66 m at 1.0x. VINS-Mono stayed healthy.
2. **GEODE stairs (untouched test set): the fusion as designed fails.** F16 17.5-19.8 m and G17 19.8-24.6 m, against **GenZ-LIO alone 0.35-0.49 m**. A-LOAM alone: 7.98 m.
3. **GenZ-LIO alone is the strongest system on Cave02 and GEODE.** The fused G17 is 13x (Cave02) and 40-70x (GEODE) worse than its own LiDAR input. It is better than GenZ alone only on Multi Floor (the tuning sequence) and Corridor02.
4. **Cause:** the VINS-Mono translation share. VINS-Mono is scale-inconsistent with the LiDAR on Cave02 and GEODE, and the fusion weights (LiDAR information only, one constant frozen on Multi Floor) do not look at that.
5. **SAH on its own** (GenZ + SAH, no VINS translation fill) is never worse than GenZ alone by more than 0.01 m and helps on Multi Floor (-0.10) and Corridor02 (-0.41), by replay. This is a post-hoc observation (see section 4).

## 1. Replay-rate controls (laptop, one run each)

| Sequence | G17 at 1.0x (21 Oct) | G17 at master rate | Master F16 | VINS-Mono alone (same log) | GenZ alone (same log) |
|---|---|---|---|---|---|
| Corridor02, 0.33x | 5.60 | **1.89** (max 3.59; 8856 rows) | 1.708 ± 0.069 | 4.00 | 2.70 |
| Cave02, 0.5x | 12.66 | **3.65** (max 8.63; 9468 rows) | 4.40 ± 0.61 | 10.06 | 0.283 |

VINS-Mono health: Corridor02 modes FUSED 7906 / WARMUP 949 / VO_FAIL 0 (at 1.0x there were 56 failure episodes); Cave02 FUSED 7794 / WARMUP 1426 / VO_FAIL 247. VINS-Mono alone on Corridor02 (4.00) reproduces the master's own VINS-only value (4.03 ± 0.01). One run each: G17 against the master F16 is a tie on both bags (1.89 vs 1.71; 3.65 vs 4.40, within about 1.2 sd of the master).

## 2. GEODE stairs, device alpha (PC, i7-12700, 0.5x, ground truth stairs_alpha.txt)

| Config | Runs (ATE m) | Rows (of 3456 scans) | Note |
|---|---|---|---|
| F16 (VINS-Mono + A-LOAM, master) | 19.77, 17.54 | 3444, 3451 | |
| G17 (VINS-Mono + GenZ-LIO, fusion_v4) | 19.75, 24.62 | 3452, 3453 | |
| G0 (GenZ-LIO alone, live) | 0.489, 0.345 | 3452, 3452 | mean 0.417 |
| GenZ-LIO inside the G17 logs (exact replay) | 0.345, 0.467 | | |
| F5 (A-LOAM alone) | 7.98 | 3446 | one run |
| VINS-Mono alone (replays) | 56-80 | | VO_FAIL 18-35 % of the time |

Published stairs-alpha numbers (GEODE paper v2, from a garbled extraction: recheck): FAST-LIO2 4.69, DLIO 4.89, R3LIVE 4.54, LIO-SAM 6.30, COIN-LIO 0.45, RELEAD 0.57. GenZ-LIO alone with the Multi Floor configuration (0.35-0.49) is in the range of the best published values; this is the published front end, not a result of this project.

Mechanism (G17 run 1, fused vs the LiDAR path): both agree for the first 33 s; the fused path leaves the LiDAR path only inside the FUSED stretches (0 to 13 m during 34-66 s, 13 to 50 m during 210-251 s); in WARMUP and VO_FAIL it follows the LiDAR increments. Scale: over 10 s windows VINS-Mono moved 2.7x (run 1) and 1.5x (run 2) the distance the LiDAR moved (median |ln ratio| 1.01 and 0.43).

Cross-machine check: the 60 s smoke test on both machines (1.0x, same code and images) kept 598/597 (laptop) and 599/596 (PC) of about 600 scans and started VINS-Mono at 14.1/13.7 s and 13.9/13.6 s. All runs of this document kept at least 99 % of the scans. GEODE is a PC result and Corridor02/Cave02 are laptop results; no cell mixes machines and no PC number is compared with a laptop number.

## 3. GenZ-LIO alone against the fused G17, same logs

| Sequence | GenZ alone | G17 fused | Effect of the fusion |
|---|---|---|---|
| Multi Floor (tuned) | 0.626 | 0.293 (live) | helps (in-sample) |
| Corridor02, 0.33x | 2.696 | 1.893 | helps |
| Cave02, 0.5x | 0.283 | 3.655 | hurts 13x |
| GEODE, 0.5x | 0.345 / 0.467 | 19.75 / 24.62 | hurts 40-70x |

## 4. Post-hoc diagnostics (computed after seeing the held-out logs; not tests)
Scripts: `analysis/improve/lidar_trust_sweep.py`, `sah_only_sweep.py`, `scale_consistency.py`. All are exact replays of the recorded GenZ-stack logs.

**LiDAR-trust sweep** (G9 weights multiplied by a scale; x1 = frozen G9, no SAH):

| Log | GenZ alone | x0.1 | x1 | x10 | x100 | x1000 |
|---|---|---|---|---|---|---|
| Multi Floor | 0.626 | 0.598 | 0.337 | 0.541 | 0.614 | 0.624 |
| Corridor02 | 2.696 | 3.214 | 2.398 | 2.615 | 2.687 | 2.695 |
| Cave02 | 0.283 | 8.828 | 3.655 | 0.723 | 0.308 | 0.285 |
| GEODE run 1 | 0.345 | 48.7 | 19.7 | 3.06 | 0.527 | 0.356 |

**SAH only** (LiDAR fully trusted, VINS-Mono used only for the gravity direction): Multi Floor 0.529 (GenZ 0.626), Corridor02 2.284 (2.696), Cave02 0.283 (0.283), GEODE 0.354 (0.345) and 0.390 (0.467). With the VINS-Mono fill added: 0.287, 1.881, 3.655, 19.7.

**Scale consistency** (VINS-Mono vs LiDAR displacement over 10 s windows, no ground truth needed): Multi Floor 0.030, Corridor02 0.027, Cave02 0.247, GEODE 1.01 and 0.43. The fusion helps exactly where this is small.

**Status:** these were found on held-out logs of the GenZ stack, so Cave02 and GEODE are no longer clean tests for any rule derived from them. A consistency rule is a candidate for the thesis only if it is fixed from first principles (not from these four numbers) and then run once on a new untouched sequence.

## 5. Consequences
- Do not claim that G17 improves on GenZ-LIO. The defensible statements are: SAH is a small, VINS-independent gain on structured sequences; the VINS-Mono fill helps only while VINS-Mono is scale-consistent with the LiDAR; the weights used so far do not check this.
- Next step (planned, not done): a consistency check between VINS-Mono and LiDAR increments (item B5 of the methodology plan), fixed a priori, then one run on an untouched sequence (SuperLoc Cave01/Cave03/Cave04 are candidates; they have to be downloaded).
- Long Corridor with the GenZ stack is still unscored.

## 6. Files
`results_data/2026-10-22/`: `geode_pc_F`, `geode_pc_G` (index, summaries, ATE, gzipped logs), `corridor02_laptop_rate033`, `cave02_laptop_rate05`, `geode_pc_batch.log`. Keyframe files (`*.npz`) are not in git. Plan and scripts: `docs/planning/Two_Machine_Plan_2026-10-22.md`, `fusion_v4/batches/`.
