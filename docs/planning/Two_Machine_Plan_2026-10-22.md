# Status and two-machine test plan (22 Oct 2026)

Purpose: decide what to run in the 4 hours on two computers (laptop Ryzen 5 5600H, PC i7-12700, 16 GB RAM each), after the failed overnight batch, without breaking the rules of the study (settings frozen, no tuning on held-out bags, every result reported as found).

## 1. Where the project stands

### What is finished
| Item | Result | Evidence |
|---|---|---|
| Master system fusion_v3 (F16: VINS-Mono + A-LOAM, Schur translation weight C_T 0.03, SAH, offline loops) | Multi Floor 0.640 ± 0.115 (F8 0.617 ± 0.107; with loops 0.347); Long Corridor 2.27 / 1.54 with loops; Corridor02 1.71 / 1.25 with loops; Cave02 4.40 | `results/Configurations_Explained_and_Results_To_Date.md` |
| Against published | beats Switch-SLAM clearly on Multi Floor (1.61), ties it on Long Corridor (2.42), weak on Cave02; not better than tuned LIO methods (GenZ-LIO 0.26, iG-LIO 0.25 on Multi Floor) | `results/Published_Comparison_All_Datasets.md` |
| fusion_v4 (GenZ-LIO front end, rule G9/G17 with R and T both from Schur + SAH) | Multi Floor 0.420 / 0.388 (replay, in-sample), live G17 0.293 | `results/GenZ_fusion_v4_MultiFloor_Results.md` |
| fusion_v4 on held-out bags, 1.0x replay, frozen weights | **did not generalise**: Corridor02 G17 5.60 (master 1.71, GenZ alone 3.98); Cave02 12.66 (master 4.40, GenZ alone 4.61). Live VINS-Mono failed and re-initialised hundreds of times | `results/GenZ_fusion_v4_HeldOut_Results.md` |
| Statistics, SAH, yaw-drift, replay studies, loop closure | done and documented | `results/` |
| Repository, setup guides, environment capture, image export tools | done 22 Oct (`docs/setup/`) | commits up to c455933 |

### What is open
1. **GEODE stairs (alpha), the untouched test set: no scored run exists.** Setup and a 160 s smoke test (1.0x, A-LOAM stack) worked: 1516 rows, 95 % of scans kept, clocks aligned, camera republished. In that smoke test VINS-Mono initialised early, fused for about 105 s, then reported tracking failure at about +125 s ("unstable features tracking", `VO_FAIL`) while the ground truth shows the carrier still moving. Whether this is the dataset (stairs, 10 Hz images) or the 1.0x replay rate is not known.
2. **The overnight batch never ran.** It stopped silently seconds after its first run started (only the container-restart log existed afterwards; no error line; containers were up; the laptop had not slept). Cause not confirmed; the most likely cause is that the process was tied to the terminal. It is not a GEODE failure. The new batch script logs any signal it receives.
3. **Replay-rate control.** Held-out failures of the GenZ stack were at 1.0x, the master used 0.33x (Corridor02) and 0.5x (Cave02). If live VINS-Mono stays healthy at those rates the failure was a rate effect; if not, the fusion needs a principled VINS-failure gate (to be validated on Multi Floor first).
4. Loop closure for G17 on the held-out bags, the project-document updates, and the thesis text.

## 2. Does the computer change the results?

**Not negligible a priori. The earlier results already show it.**

- Corridor02 protocol: on the laptop at 1.0x the mapping node saturated one core at 93 °C and **about 40 % of scans were dropped** (8 runs discarded below the row threshold). At 0.33x F8 **still lost about 20 % of scans in minutes 8-11**.
- VINS-Mono's optimiser is limited by wall-clock time (`max_solver_time 0.04 s`, 8 iterations): a faster CPU completes more iterations per frame, the replay clock does not compensate.
- GenZ-LIO is multithreaded (`max_threads 0` = all cores) and varies by 0.3-0.6 m between identical runs on the same machine (G0 Multi Floor 0.88 / 0.53 / 0.31).
- The i7-12700 (8 performance + 4 efficiency cores, 20 threads, up to about 4.9 GHz) is roughly 1.2x faster per thread and about 1.8x in total than the 5600H (6 cores, 12 threads, up to about 4.2 GHz, thermally limited in the laptop). Expected effect: fewer dropped scans and more optimiser iterations on the PC, so equal or better numbers, **but a PC number is not the same measurement as a laptop number**, and the 16 GB RAM must hold three stacks.

**Rules that follow (fixed before the runs):**
1. Never pool a cell of the table from different machines without a record of the machine. Every run is stored under `runs_..._L` or `_P`.
2. The two machines run the **same design** (same configurations, same number of runs, same rate, same code commit, same images). Configurations are then compared within machine and across machines, and the machine effect is measured, not assumed.
3. Retention (rows ÷ scans) is reported for every run as a validity measure. Runs under the row threshold are reported as failures, not hidden.
4. The machine effect is called negligible if, for each of F16, G17, G0, the difference between the machine means is smaller than the pooled within-machine standard deviation and the retention differs by less than 5 percentage points. Otherwise results are reported per machine and conclusions are drawn only from within-machine comparisons.
5. Older master numbers (laptop) stay valid as laptop numbers. No master number is recomputed on the PC.

## 3. Decisions (configuration to follow)

| Decision | Choice | Reason |
|---|---|---|
| Code | both machines run a fresh clone of branch `fusion-v4-and-results` (same commit, printed in each log) | identical code; the old working folder on the laptop is not used |
| Environment | the laptop's containers exported once and loaded on the PC (`tools/export_images.sh`, `import_images.sh`) | identical software; git holds code and configs, not the container images, which are the missing part |
| Replay rate | 0.5x for all GEODE runs on both machines | the master's convention for Long Corridor/Cave02; 1.0x lost scans on the laptop |
| Bag location | **local copy on each machine's internal disk** (`~/bags/GEODE`), not the external drive | same read speed on both, laptop and PC independent of one drive |
| Settings | all frozen: C_T 0.03 (F16); c_T 3e-6, c_R 5e-6, SAH (G17); GenZ config as on Multi Floor | nothing is tuned on GEODE |
| Runs per machine | GEODE: F16 x2, G17 x2, G0 x2, F5 x1 (7 runs); total n = 4 per main configuration, 2 for F5 | 7 x 14 min = 98 min per machine |
| Dropped | F0 live: the VINS-only trajectory is part of every F16 / G17 log and is scored by the paired replay (same data); live F0 would only repeat it | saves 3 runs |
| Control runs | laptop: Corridor02 G17 at 0.33x (47 min); PC: Cave02 G17 at 0.5x (35 min); one run each | answers the replay-rate question for both held-out bags |
| Optional | `STAGES=extra`: third replicate of F16, G17, G0 (42 min) | only if time is left |

Why each run: F16 is the validated master; G17 is the proposed system; G0 is GenZ-LIO alone, the LiDAR-inertial baseline that G17 has to beat; F5 is plain A-LOAM. The published GEODE stairs-alpha numbers (recheck against the paper) are FAST-LIO2 4.69 m, DLIO 4.89, R3LIVE 4.54, LIO-SAM 6.30, COIN-LIO 0.45, RELEAD 0.57.

## 4. Time plan (T0 = the moment you start; both machines about 4 h)

| Minutes | Laptop | PC |
|---|---|---|
| 0-10 | copy GEODE bag to `~/bags`, clone repo | (HDD not yet there) install Docker / git / pip, clone repo |
| 10-35 | export the containers to the external drive (laptop idle) | wait; then plug the drive in |
| 35-60 | start the batch (smoke, then GEODE) | `import_images.sh` (10-15 min), copy GEODE and Cave bags to `~/bags`, start the batch; the drive goes back to the laptop |
| 60-160 | GEODE runs (98 min) | GEODE runs |
| 160-210 | control: Corridor02 G17 at 0.33x | control: Cave02 G17 at 0.5x |
| 210-240 | optional extra replicate / buffer | optional extra replicate / buffer |

If the PC window is tighter than 4 h in total, the PC drops the control and the extra stage; the GEODE block is what matters.

## 5. After the runs
Bring back the results folders of both machines. Then: score GEODE and compare with the published table; per-machine and pooled statistics; the paired VINS-only / LiDAR-only / own-setting replays from the recorded logs; loop closure on the recorded keyframes (offline, on my side); decide whether G17 is kept as the final system or whether the VINS-failure gate becomes the next piece of work; update the project documents.

## 6. Risks
- Docker or the images fail to load on the PC: fall back to `INSTALL.md` section 2B (about 1-1.5 h, untested); then the PC does only the smoke test and one pass.
- RAM 16 GB: GenZ's voxel map plus VINS-Mono plus recorders; watch `free -g`; Cave02 is the heaviest.
- Laptop thermals: raise the fan profile, keep the lid open, run on mains power.
- VINS-Mono may fail on GEODE again at about 125 s; that is a result (the fusion must then run on LiDAR only), not a reason to change settings.
