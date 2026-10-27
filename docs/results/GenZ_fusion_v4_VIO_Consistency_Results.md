# fusion_v4: same R / T / additional-T structure, with a VINS consistency check (G18, G19), 22 Oct 2026

Metric everywhere: full-span ATE RMSE (m), Umeyama SE(3), no scale. All numbers on this page are **exact offline replays** of recorded GenZ-stack runs (GenZ-LIO takes no feedback from the fusion, so a replay equals a live run; the unchanged default path reproduces the old core bit for bit, and the replayed G17 reproduces every live G17 value: 0.293/0.287, 1.893/1.881, 3.655/3.655, 19.75/19.75, 24.62/24.62). Key numbers were recomputed with an independent ATE implementation (identical to 3 decimals). Scripts: `analysis/improve/vio_consistency/`.

## 1. The structure (unchanged)

| Part | What it does | Setting |
|---|---|---|
| R channel | rotation increment = W_R · LiDAR + (I - W_R) · VINS, W_R = (c_R S_RR + γI)^-1 c_R S_RR | c_R = 5e-6 (Multi Floor) |
| T channel | translation increment, same form with S_tt | c_T = 3e-6 (Multi Floor) |
| Additional T (SAH) | structure-anchored heading, ≤ 0.25° per scan | StructureHeadingV6, unchanged |
| Front end | GenZ-LIO, one frozen configuration | unchanged |

The only new quantity is γ, the information of the VINS prior. In G17 it is fixed at 1 (the "unit VINS information" against which c_T and c_R were calibrated). Nothing else in the structure changed.

## 2. Results obtained with the structure as it was (G17)

| Sequence | G17 (live) | GenZ-LIO alone | VINS-Mono alone |
|---|---|---|---|
| Multi Floor (calibration) | 0.293 (replays of 4 recordings 0.256-0.551, mean 0.363) | 0.31-0.88 | 1.25-8.9 |
| Corridor02, 0.33x | 1.893 | 2.696 | 4.00 |
| Cave02, 0.5x | 3.655 | 0.283 | 10.06 |
| GEODE stairs α, 0.5x (PC) | 19.75, 24.62 | 0.345-0.489 | 56-80 |
| Long Corridor | not run on the GenZ stack | | |

Why it fails on Cave02 and GEODE: with γ = 1 the VINS translation carries a large share of every step (c_T S_tt is of order 1). VINS-Mono's scale on those sequences is 25 % (Cave02) to 15-170 % (GEODE) off the LiDAR's, and that bias is integrated along the whole path.

## 3. The change: γ from a VINS-LiDAR consistency check (fusion_core.VioConsistency)

Every scan closes a 10 s window inside the current VINS segment. Both relative motions are expressed in the LiDAR body frame at the window start; the statistic is the scale disagreement ln(|Δt_VINS| / |Δt_LiDAR|) (windows with at least 1 m of LiDAR motion). r = RMS over all windows of the segment.

- **G18 = G17 + gate:** γ = 1 while r ≤ 0.156, else γ = 0 (LiDAR carries the step, SAH still runs). γ = 0 until 200 windows exist (the VINS must first show it agrees; with the 20 s warm-up this is 30 s after each VINS start). Restarts at every VINS loss or re-initialisation.
- **G19 = G18 + online VINS scale correction:** VINS translation increments are multiplied by (LiDAR path length / VINS path length) over the last 10 s of the segment before the Schur-weighted fusion (monocular VINS scale is weakly observable; the LiDAR is metric).
- **The one constant, 0.156, comes only from Multi Floor:** the largest r on the four Multi Floor recordings (0.252 at 50 windows, 0.210 at 100, 0.156 at 200). Corridor02 never exceeds 0.076; Cave02 sits at 0.25-0.29; GEODE at 0.18-0.37 with peaks above 1.

Node: `VIO_CHECK=1` (G18), `VIO_CHECK=1 VIO_SCALE_T=10` (G19); defaults off, so G0-G17 and the A-LOAM master are unchanged. Log columns `vio_gamma`, `s_vio` added.

## 4. Results

Front end = the fused output; + loops = the same output through the offline loop-closure back end (iso loop weights, 1 round, odometry noise 1.46°, 0.054 m as used for all earlier loop results).

| Sequence (recordings) | GenZ alone | G17 | **G18** | **G19** | SAH only (W = I) | G17 + loops | G18 + loops | **G19 + loops** | SAH only + loops |
|---|---|---|---|---|---|---|---|---|---|
| Multi Floor (4) | 0.584 | 0.363 | 0.367 | 0.388 | 0.523 | 0.324 | 0.374 | **0.330** | 0.683 |
| Corridor02 (1) | 2.696 | 1.881 | 1.967 | 2.484 | 2.284 | 1.024 | **1.005** | 2.345 | 1.859 |
| Cave02 (1) | 0.283 | 3.655 | 0.457 | 0.294 | 0.283 | 3.683 | 0.415 | **0.270** | 0.273 |
| GEODE α (4) | 0.412 | 22.11 | 0.987 | 0.526 | 0.385 | 22.11 | 0.802 | **0.393** | 0.308 |

Per recording:

| Recording | GenZ | G17 | G18 | G19 | SAH only | G17 + L | G18 + L | G19 + L | SAH only + L |
|---|---|---|---|---|---|---|---|---|---|
| MF G17 run 1 | 0.626 | 0.287 | 0.289 | 0.361 | 0.529 | 0.284 | 0.276 | 0.250 | 0.238 |
| MF G0 run 1 | 0.876 | 0.551 | 0.554 | 0.487 | 0.808 | 0.353 | 0.515 | 0.341 | 1.144 |
| MF G0 run 2 | 0.525 | 0.359 | 0.366 | 0.346 | 0.512 | 0.449 | 0.487 | 0.441 | 1.009 |
| MF G0 run 3 | 0.307 | 0.256 | 0.258 | 0.357 | 0.242 | 0.209 | 0.218 | 0.287 | 0.343 |
| Corridor02 G17 | 2.696 | 1.881 | 1.967 | 2.484 | 2.284 | 1.024 | 1.005 | 2.345 | 1.859 |
| Cave02 G17 | 0.283 | 3.655 | 0.457 | 0.294 | 0.283 | 3.683 | 0.415 | 0.270 | 0.273 |
| GEODE G17 run 1 | 0.345 | 19.75 | 1.172 | 0.555 | 0.354 | 19.75 | 0.763 | 0.360 | 0.267 |
| GEODE G17 run 2 | 0.467 | 24.62 | 0.487 | 0.439 | 0.390 | 24.62 | 0.539 | 0.509 | 0.453 |
| GEODE G0 run 1 | 0.489 | 18.49 | 1.147 | 0.584 | 0.461 | 18.49 | 1.147 | 0.345 | 0.244 |
| GEODE G0 run 2 | 0.345 | 25.60 | 1.143 | 0.526 | 0.336 | 25.60 | 0.761 | 0.359 | 0.267 |

## 5. Against the published values

| Sequence | Best published (method, source) | Other references | G19 front end | G19 + loops | Below the best? |
|---|---|---|---|---|---|
| Multi Floor | 0.25 iG-LIO, 0.26 GenZ-LIO (GenZ-LIO Table 4, no loops) | SuperLoc 0.315; challenge Liu 0.401 (loops); Switch-SLAM 1.61 | 0.388 (0.346-0.487) | 0.330 (0.250-0.441) | **No.** Below Switch-SLAM and every challenge entry; above SuperLoc, GenZ-LIO and iG-LIO |
| Corridor02 | 0.69 GenZ-LIO (Table 4; "Corridor 02" of the SuperLoc release, identity with our bag unconfirmed) | PV-LIO 0.73, DLIO 1.39 | 2.484 | 2.345 | **No** (best of ours: G18 + loops 1.005) |
| Cave02 | 0.43 iG-LIO / PV-LIO, 0.44 GenZ-LIO (Table 4) | DLIO 0.57 | 0.294 | **0.270** | **Yes**, by 0.16 m (one recording) |
| GEODE stairs α (VLP-16) | 0.57 RELEAD (GEODE Table 6) | R3LIVE 4.54, FAST-LIO2 4.69, DLIO 4.89, LIO-SAM 6.30; COIN-LIO not run on α | 0.526 (0.439-0.584) | **0.393** (0.345-0.509) | **Yes**: all 4 recordings with loops, 3 of 4 without |
| Long Corridor | 0.817 SuperLoc; 1.55 iG-LIO (Table 4) | Switch-SLAM 2.42 | not run | not run | open |

Correction: the earlier "COIN-LIO 0.45 on stairs α" was wrong; that value is on device β (Ouster OS1-64). On α the best published is RELEAD 0.57.

Metric caveat (unchanged): papers rarely state alignment and span; differences under about 0.1 m are ties. Our GenZ-LIO alone already reaches 0.283 (Cave02) and 0.41 (GEODE) with one frozen configuration, so on those two sequences the published bar is reached by the front end; the contribution of G19 there is that the fusion no longer destroys it (G17: 3.65 and 22 m).

## 6. Which configuration, and what is honest to claim

- **Recommended single configuration: G19** (with loops for the final numbers). It is the only fused setting that is never clearly worse than its own LiDAR input: better on Multi Floor (0.388 vs 0.584) and Corridor02 (2.48 vs 2.70), tied on Cave02 (0.294 vs 0.283), +0.11 on GEODE (within GenZ-LIO's own run-to-run spread of 0.35-0.49); with loops it is the best fused setting on Cave02 and GEODE and within 0.01 of the best on Multi Floor (G17 + loops 0.324).
- **Its weak point is Corridor02.** The scale correction removes VINS information that is genuinely useful in a corridor, where the LiDAR is degenerate along the axis and its path length is not a reliable scale reference (projecting the scale estimate through W_t did not fix it: 2.45). G18 keeps the gain there (1.005 with loops) but fails on GEODE (0.99). No single rule tried here wins on all four sequences.
- **Development, not test.** The check was designed after the Cave02 and GEODE failures were seen, and several variants were compared on those logs (variance-ratio weighting, 10 s gates, a fast 2-5 s gate, scale correction with and without projection: see `analysis/improve/vio_consistency/`). The threshold comes from Multi Floor only, but the choice of statistic and of n_min = 200 was made with the held-out logs in view. Cave02, GEODE and Corridor02 are therefore development sequences for G18/G19. **The clean test is Long Corridor, which has never been run on the GenZ stack.**
- **Sample size.** Corridor02 and Cave02 have one recording each; Multi Floor and GEODE four each, replayed. Live G19 runs are needed to confirm replay = live for the new options.
- **SAH only with loops** is lowest on GEODE (0.308) and ties on Cave02, but is unstable on Multi Floor (1.14 and 1.01 with loops on two recordings) and does not use VINS at all; it is a baseline, not the fusion.

## 7. Next runs (live)

Laptop, Long Corridor (the untouched test), one recording gives every configuration by replay:
```
cd ~/switchslam-project && git pull && cd fusion_v4
sed 's|^OUT_DIR=.*|OUT_DIR=/home/kavinkumar/runs_corridor_test_L|' ~/runs_corridor/seq.env > ~/runs_corridor/seq_L.env
SEQ_ENV=~/runs_corridor/seq_L.env REPEAT=2 RECORD_KF=1 PLAY_RATE=0.5 FRONT=genz setsid nohup systemd-inhibit --what=sleep:idle --why=slam ./run_fusion_study.sh G19 > ~/batch_LC_G19.log 2>&1 < /dev/null & disown
```
PC, confirmation that the live node matches the replay (GEODE, 0.5x):
```
cd ~/switchslam-project && git pull && cd fusion_v4
SEQ_ENV=~/runs_geode_P/seq.env REPEAT=1 RECORD_KF=1 PLAY_RATE=0.5 FRONT=genz setsid nohup systemd-inhibit --what=sleep:idle --why=slam ./run_fusion_study.sh G19 G18 > ~/batch_geode_G19.log 2>&1 < /dev/null & disown
```
Score Long Corridor once, with G19 frozen exactly as above; do not change the threshold or the window after seeing it.
