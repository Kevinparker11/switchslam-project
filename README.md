# SwitchSLAM: LiDAR–VIO fusion under LiDAR degeneracy

M.Tech thesis code and records. The question: when LiDAR scan matching is poorly constrained (corridors, caves, stairs), how should a LiDAR–visual–inertial system weight LiDAR against VINS-Mono, and can it be done without hand-tuned thresholds? The answer built here is **VINS-Mono as the primary pose, corrected by a LiDAR scan-to-map registration weighted per direction by the Schur complement of its Hessian** (`W = (c·S + I)⁻¹ c·S`), plus a **structure-anchored heading** (SAH) correction from wall directions and an offline loop-closure back end.

## Where to start

| I want to... | Go to |
|---|---|
| set the environment up on a new PC | [`docs/setup/INSTALL.md`](docs/setup/INSTALL.md) |
| place the bags and ground truth | [`docs/setup/DATASETS.md`](docs/setup/DATASETS.md) |
| repeat a run or a result table | [`docs/setup/REPRODUCE.md`](docs/setup/REPRODUCE.md) |
| see every configuration and every result | [`docs/results/Configurations_Explained_and_Results_To_Date.md`](docs/results/Configurations_Explained_and_Results_To_Date.md) |
| read the documentation index | [`docs/README.md`](docs/README.md) |

## Repository layout

```
fusion_v2/ fusion_v3/ fusion_v4/   the fusion system, three generations (see below); each folder is self-contained
sah/                               structure-anchored-heading development harness (replays, stress tests)
analysis/improve/                  replay, ablation, statistics and held-out diagnostics
threshold_study/, channelT_test/   degeneracy-threshold screening; Bingham channel-T validity tests
patches/aloam_vins/                modifications of third-party A-LOAM / VINS-Mono code
configs/                           per-sequence launch/config files that live inside the containers
tools/                             capture_environment.sh (records the working machine's environment)
scripts/                           one-off batch helpers
switchslam_v1/                     generation 1 (Sep 2026): the original switching nodes, Farm/Multi Floor logs
docs/                              setup guides, results, protocols, planning, research notes
requirements.txt                   host Python packages
```

## The systems

| Folder | System |
|---|---|
| `fusion_v2/` | first Schur-weighted fusion node |
| `fusion_v3/` | **master, config F16**: VINS-Mono + A-LOAM scan-to-map, Schur translation weight (`C_T = 0.03`, no κ gate), rotation from VINS-Mono, SAH, offline loop closure |
| `fusion_v4/` | the same fusion rules with **GenZ-LIO replacing A-LOAM** (`FRONT=genz`; `FRONT=aloam` reproduces the master), plus the GEODE setup. The fusion files are byte-identical to `fusion_v3` |

Configuration names: `F0` VINS only · `F5` A-LOAM only · `F8` soft Schur translation weight · `F12` hard switch · `F14` W = I · `F16` = F8 + SAH. GenZ stack: `G0` GenZ-LIO alone · `G9` Schur on rotation and translation · `G17` = G9 + SAH. Definitions: [`docs/results/Configurations_Explained_and_Results_To_Date.md`](docs/results/Configurations_Explained_and_Results_To_Date.md).

## Results at a glance
Full-sequence ATE RMSE in metres (Umeyama SE(3), no scale), mean over live runs.

| Sequence | Role | VINS-Mono | Master F8 | Master F16 | G17 (GenZ stack) |
|---|---|---|---|---|---|
| Multi Floor | tuning | 1.28 | 0.617 | 0.640 | 0.388 (replay, in-sample); 0.293 (1 live run) |
| Long Corridor | SAH development | 5.81 | 4.53 | 2.27 | not run |
| Corridor02 | held out for F8; SAH development | 4.03 | 2.12 | 1.71 | 5.60 (1 live run, 1.0x) |
| Cave02 | clean control | 10.25 | 4.47 | 4.40 | 12.66 (1 live run, 1.0x) |
| GEODE stairs (alpha) | untouched test | | | pending | pending |

What this does and does not show: the master system clearly improves on VINS-Mono alone and on the published Switch-SLAM numbers on Multi Floor, and SAH helps on the corridors (significant in the run-level tests). The GenZ-LIO variant reaches 0.29–0.39 m on Multi Floor, but its weights were tuned on that sequence, and **the first two held-out runs did not generalise** — live VINS-Mono failed on both. That diagnosis and the planned control are in [`docs/results/GenZ_fusion_v4_HeldOut_Results.md`](docs/results/GenZ_fusion_v4_HeldOut_Results.md). Settings are frozen before each new sequence and never tuned on held-out bags.

Bags, recordings (`.bag`, `.npz`) and run outputs are not stored here (see `.gitignore`).
