# Handoff: G20 + OT replay study (state at 2026-10-29 ~03:10 UTC)
Pre-registration: PREREG3.md (written 02:29:54Z, before any OT candidate was replayed). Scripts: batchg.sh (one tag = one config over the 47 GenZ-stack recordings), driveG.sh (the full list of runs), gscore.py (ATE, cached), gselect.py (PREREG3 score), glogs.txt (47 logs: name|seq|log|keyframes|GT|extrinsics; the paths point into the session scratchpad, edit them on a new machine), g20.env (baseline G20 settings), node_harness.py (drives the real fusion_node_v2 callbacks; needs fusion_v4 on FUSION_DIR).

## Done (clean cells, medians in m)
| Config | MF | LC | CV | C02 | GEO | GZ |
|---|---|---|---|---|---|---|
| G20 (harness; reproduces the earlier G20 replay on 33 recordings, max diff 0.038 m) | 0.350 | 1.707 | 0.296 | 2.476 | 0.474 | 0.455 |
| G20 + OT_MODE=min | 0.350 | 1.707 | 0.296 | 2.473 | 0.473 | 0.455 |
| G20 + OT_MODE=smin | 0.351 | 1.707 | 0.296 | 2.476 | 0.474 | 0.453 |
| **G20 + OT_MODE=gmax** | 0.347 | **1.461** | 0.288 | 2.227 | **0.379** | **0.213** |
The two fail-safe rules (min, smin) are neutral on G20, as on A-LOAM. gmax lowers Long Corridor (1.707 to 1.461), GEODE (0.474 to 0.379), Gazebo (0.455 to 0.213) and Corridor02 (2.476 to 2.227) and leaves Multi Floor and Cave02 level (clean medians; MF mean 0.390 vs 0.374). Not yet scored: fault cells, agm, the PREREG3 score and the per-recording counts. gmax is not a fail-safe (see OT_Channel_Round2.md), so the FL cells decide.

## Still to run (in driveG.sh order)
Gc_agm_clean; then fault cells Gbase_FL, Gbase_FV and for min, smin, gmax, agm: Gc_<rule>_FL, Gc_<rule>_FV (MF, LC, CV only). Then `python3 gselect.py` applies the PREREG3 rule (score = mean ln ratio over 12 cells; admissible if every clean sequence median is within +0.05 m of G20).
batchg.sh skips recordings that are finished, so re-running driveG.sh resumes. About 9 min per clean candidate and 5-8 min per fault tag on 2 cores.

## Needed from the data (not in the repo)
The 47 recordings (switching logs + keyframes npz) listed in glogs.txt: the GenZ-stack runs in the session scratchpad (g20all, lapres, pcres, lap, g17, g0mf, gz20). On a new session they are available only if the same container/session is kept; otherwise they must be re-supplied.

## After the run
Write docs/results/G20_OT_Results.md (table, score, conclusion, limits from PREREG3), save to the project, then decide on a live G20 + OT run (the held-out step) with criteria written first.
