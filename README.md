# SwitchSLAM: LiDAR–VIO fusion under LiDAR degeneracy (M.Tech thesis code)

Two generations of work live in this repository.

| Generation | Folders | What it is |
|---|---|---|
| **1. SwitchSLAM + Bingham channel T** (Sep 2026) | repo root, `farm/`, `multifloor/` | The original switching nodes (A-LOAM + VINS-Mono), Farm/Panels and Multi Floor experiments, the Bingham orientation channel. Left in place, as committed. |
| **2. Schur-weighted fusion** (Oct 2026) | `fusion_v2/`, `fusion_v3/`, `fusion_v4/`, `sah/`, `analysis/`, `threshold_study/`, `channelT_test/` | Fusion with a Schur-complement translation weight, structure-anchored heading (SAH) and an offline loop-closure back end. |

## Fusion versions

| Folder | Role |
|---|---|
| `fusion_v2/` | First fusion node (fusion core + node, early tools). |
| `fusion_v3/` | **Master system, config F16**: VINS-Mono primary + A-LOAM scan-to-map, Schur translation weight `W_t = (c·S_tt + I)^-1 · c·S_tt` (`C_T = 0.03`, no kappa gate), rotation from VINS-Mono only, SAH as the additional translation/heading correction, offline loop closure. |
| `fusion_v4/` | Same fusion with **GenZ-LIO replacing A-LOAM** (`FRONT=genz`); `FRONT=aloam` reproduces the master. Includes GenZ install/config tools, the LiDAR-information patch, `lio_bridge.py`, and `geode/` (GEODE device-alpha setup). The fusion files are byte-identical to `fusion_v3`. |

### Configuration names (run with `run_fusion_study.sh`)

`F0` VINS only · `F5` A-LOAM only · `F8` soft Schur translation weight, rotation from VINS · `F12` hard switch · `F14` W = I · `F16` = F8 + SAH · "+loops" = offline loop closure.
GenZ stack: `G0` GenZ-LIO alone · `GV` VINS control · `G8`/`G16` the F8/F16 rule on GenZ · `G9` rotation and translation both Schur-active · `G17` = G9 + SAH.

## Results at a glance (full-sequence ATE RMSE, metres, Umeyama SE(3))

| Sequence | Role | Master F16 | GenZ-LIO alone | G17 (fusion_v4) |
|---|---|---|---|---|
| Multi Floor | tuning sequence | see `docs/results/` | 0.26 | 0.29 (live) |
| Corridor02 | held out | 1.71 | 3.98 | 5.60 |
| Cave02 | held out | 4.40 | 4.61 | 12.66 |

The GenZ-LIO configuration calibrated on Multi Floor **did not generalise** to the two held-out bags: live VINS-Mono failed or re-initialised on both, and the frozen translation weight let that into the output. This is reported as found, with no re-tuning on the held-out bags. See `docs/results/Front_End_Upgrade_GenZ_fusion_v4.md` and `docs/results/Improvement_Replay_Tests.md`. GEODE (stairs, device alpha) is the untouched test set; its scored runs are still pending.

## Layout

```
fusion_v2/ fusion_v3/ fusion_v4/   fusion code, run scripts, tests, back end (loop closure)
sah/                               structure-anchored-heading development and replay harness
analysis/improve/                  replay / ablation / statistical-test scripts for the fusion study
threshold_study/                   degeneracy-threshold screening
channelT_test/                     Bingham channel-T validity tests
scripts/                           batch helpers for Cave02 and longer runs
docs/research/                     literature, datasets, method proofs
docs/results/                      result records and comparisons
docs/protocols/                    held-out test protocols and setup logs
docs/planning/                     thesis plan, novelty and research gap
```

Bags, recordings (`.bag`, `.npz`), and run outputs are not stored here (see `.gitignore`).
