# G20 + OT (orientation-tensor channel on the GenZ-LIO stack): pre-registration, written before any OT candidate is replayed
Written: 2026-10-29. Reason: the A-LOAM stack (F20 / F21) gives no margin over Switch-SLAM on Long Corridor live (F20 2.80 m vs 2.42 m); the GenZ-LIO stack (G20: R, T, SAH) has it (Long Corridor 1.65-1.75, Multi Floor 0.26-0.38). The request: keep R, T and OT, and try OT on G20.

## What is replayed
The 47 recorded GenZ-stack runs of `analysis/improve/universal/logs_all.py` (MF 13 incl. 4 live G20, C02 1, CV 4, LC 10, GEO 14, GZ 4), through the real `fusion_node_v2` callbacks (`node_harness.py`, SAH_SYNC=1). GenZ-LIO and VINS-Mono take no feedback from the fusion, so a replay equals a live run (except the asynchronous live SAH worker).
Baseline G20 = `FUSION_MODE=fused C_T=3e-6 C_R=5e-6 KAPPA_TH=1e9 SAH=1 VIO_CHECK=1 VIO_SCALE_T=10 VIO_CHECK_FAST=5 LIDAR_GUARD_T=2`. Check done before this file: this harness reproduces the earlier G20 replay on 33 recordings with max difference 0.038 m (medians MF 0.350, LC 1.707, CV 0.296, GEO 0.474, C02 2.476, GZ 0.455).

## Candidates (everything else = G20; C_T, C_R, all check constants frozen at G20 values; OT adds no constant)
Each adds `OT_SRC=geom` and one rule for the translation weight (definitions in OT_Channel_Study.md and OT_Channel_Round2.md):
1. `OT_MODE=min`  (fail-safe cap by the geometric tensor, F20's rule)
2. `OT_MODE=smin` (scale-free shape cap, fail-safe)
3. `OT_MODE=gmax` (F21's rule: can also raise the LiDAR information)
4. `OT_MODE=agm`  (Ando geometric mean)
Order for ties: min, smin, gmax, agm.

## Conditions (cells)
Clean: MF, LC, CV, C02, GEO, GZ. Faults on MF, LC, CV (the three with several recordings): FL = LiDAR solver slide (FAULT=1: 0.2 m/s along the weakest direction, H_tt replaced by tr/3 I, 3 windows of 20 s at 25/50/75 %), FV = VINS translation increments x2.5 in the same windows (FAULT=1 FAULT_KIND=vio). 12 cells.
Cell value = median ATE (m, Umeyama SE(3), full span) over the recordings of the cell; MF-b2 (the run in which GenZ-LIO itself diverged) is left out of the clean MF median and reported on its own, as in the G20 write-up.

## Selection
Score = mean over the 12 cells of ln(cell value of candidate / cell value of G20) (negative = better than G20).
Admissible only if on each clean cell (MF, LC, CV, C02, GEO, GZ) the candidate's median is at most 0.05 m above G20's.
The candidate with the lowest score among the admissible is "G20 + OT". If its score is not below -0.01, the conclusion is that OT does not change G20 on these recordings, and that is reported; the structure is then still run with OT as a safeguard (no performance claim).
Reported whatever the outcome: per-recording table; MF-b2; counts of recordings better / worse than G20 by more than 0.05 m and 10 %; the comparison with Switch-SLAM (MF 1.61, LC 2.42): cell median and the number of recordings above the paper value.

## Limits stated in advance
All 47 recordings were used when G20 was designed (development data); no new recording is used here. A claim beyond "replay on development data" needs a live run on new recordings (the live run is the held-out step). The fault cells are injected, not real failures. Replay is not live: live SAH is asynchronous.
