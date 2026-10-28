# Additional T in the fusion: one live run on the A-LOAM stack (protocol written 28 Oct 2026, before any run)

## What was built
Until now the orientation tensor T (the "additional T") existed only as a logger and as synthetic tests; the fusion (F8/F16) never used it. This adds it to `fusion_node_v2.py` / `fusion_core.py`, **off by default** (F0-F17 are unchanged bit for bit; checked by `fusion_v4/test_t_cap.py`, `test_fusion_core.py` and a mock-node run).

Rule (`t_cap_info`, "fail-safe", the H+T = min arm of the synthetic test `ChannelT_Mini_Test_Protocol.md`, now applied to the weight):
- T = mean of n nᵀ over k = 12 PCA normals of a 400-point subsample of the scan's planar points (`/laser_cloud_surf_last`), from the raw points alone, paired with the mapped scan by time stamp.
- The Schur translation information S_tt has eigen-directions v_i with eigenvalues λ_i (what the SOLVER believes). T supports N·v_iᵀTv_i along the same direction, with N = tr(H_tt) (same total mass, so there is **no free constant**).
- λ_i' = min(λ_i, N·v_iᵀTv_i); the weight is W_t = (c S' + I)⁻¹ c S' with c = 0.03 as in F8. If the Hessian is itself N·T the cap never binds (S_tt ≤ H_tt); it binds only where the solver claims more information along a direction than the raw normals contain, which is the "solver unreliable" case of the thesis. A scan with no T is weighted exactly as F8.
- Configs: **F18 = F8 + T**, **F19 = F16 + T** (`run_fusion_study.sh`, FRONT=aloam). Log gets 3 extra columns: `T_l1`, `T_ms`, `tcap_ratio` (smallest λ'/λ).

## What is and is not claimed
- Your target "better than the Switch-SLAM paper on the A-LOAM version" is **already met on Multi Floor by F8 without T** (0.617 ± 0.107 m against 1.61 m). A T run therefore cannot prove anything by beating 1.61; the question that means something is **F18 against F8 on the same bag**.
- On Long Corridor the paper (2.42 m) is NOT clearly beaten: F8 4.53, F16 2.27 ± 0.45 (a tie). That is where T could matter for the claim; F19 is defined for it (Test 2, optional).
- The rule is deliberately mild and has no tunable constant. Preview on an old farm log (generation-1 node, 3284 frames): the smallest Schur eigenvalue per unit mass had median 0.163 against T's l1 0.088 (correlation of logs 0.93), so the cap can bind in nearly every frame but by about a factor 2 in the weakest direction. With c = 0.03 that changes the weights only slightly where cλ is already large. **Expected outcome (stated before the run): no detectable difference.** A stronger rule would need a scale for T that I would have to tune on this bag, which I will not do.
- T uses planar points only; edge features (door edges) that really constrain the corridor axis are not in T, so the cap can undercount real constraint. This is a known weakness, not hidden.
- Multi Floor is the sequence on which c = 0.03 was calibrated (development data for F8); it is not a held-out test.

## Test 1 (the one run asked for): Multi Floor, F18, one live run
Settings frozen: F8's (C_T 0.03, no gate) plus TCAP=1, replay at 0.5x (T costs 15-30 ms per scan in numpy; 0.5x leaves headroom; matched baseline at 0.5x: F8 3 runs 0.603 ± 0.112, range 0.52-0.73; 1.0x: 9 runs 0.617 ± 0.107, range 0.47-0.77).
Validity (otherwise the run is reported as invalid and is not a result): at least 3000 log rows, and T present on at least 90 % of FUSED rows.
Verdict (single run, absolute rules, fixed now):
- BETTER: ATE below 0.47 m, the lowest of the 9 F8 runs. Even then it is suggestive only: under "no effect" a run falls below the minimum of 10 about 1 time in 10. Three repeats would be needed before any claim.
- WORSE: ATE above 0.77 m, the highest F8 run. T hurts in this run.
- Otherwise: no difference detectable by one run.
Paper bar reported beside it: ATE < 1.61 m (Switch-SLAM Multi Floor).
Diagnostics reported with no verdict: share of FUSED rows with tcap_ratio < 0.9 and < 0.5, median ratio, T compute time p50/p99.

## Test 2 (optional, only if asked): Long Corridor, F19, one live run
F16 + TCAP=1 at 0.5x, same frozen settings. BETTER: ATE < 1.99 m (lowest of 6 F16 runs); WORSE: > 3.17 m (highest); else no difference. Paper bar 2.42 m. Long Corridor is development data for SAH, so this is not held out either.

## Commands (host terminal; bags stay under "/media/kavinkumar/One Touch1/laptop_bags/")
```
cd ~/switchslam-project && git fetch https://github.com/Kevinparker11/switchslam-project fusion-v4-final && git checkout fusion-v4-final && git merge --ff-only FETCH_HEAD
cd fusion_v4 && python3 test_t_cap.py | tail -1
FRONT=aloam ./run_fusion_study.sh --dry F18 | head -3
# 70 s smoke run (no scoring) to see that T is paired with the scans:
SMOKE=1 PLAY_RATE=0.5 FRONT=aloam ./run_fusion_study.sh F18
python3 tcap_report.py ~/runs_v2/switching_log_v2_SMOKE_F18_run1.csv --seq multifloor --ate 1.0 | head -8
# the single run (about 15 minutes):
PLAY_RATE=0.5 FRONT=aloam ./run_fusion_study.sh F18
python3 tcap_report.py ~/runs_v2/switching_log_v2_F18_run1.csv --seq multifloor
```
Send back the last printout (and `~/runs_v2/switching_log_v2_F18_run1.csv` if you can). The smoke run is checked for the "T present" line only; its ATE is meaningless.

## Superseded (28 Oct 2026, before the full run)
Only the 70 s smoke run of F18 was made (T paired on 99.3 % of fused rows; cap ratio median 0.71; T 8.3 ms p50 / 20.7 ms p99). The single full run was not made: the replay study `OT_Channel_Study.md` showed that a tensor of planar normals only is the wrong source for a cap on A-LOAM (it removes valid edge-constrained information: -0.5 to -0.6 m on the corridors). The orientation-tensor channel now uses the geometric tensor of the keyframe scans (planes and edges) in config F20; F18 / F19 remain in the code for the record.
