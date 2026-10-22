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

**Revision (22 Oct, user decision): the machines run different bags, no run is duplicated, to save time.** The price is that the machine effect is no longer measured inside the experiment, so the allocation is chosen so that **no comparison crosses machines**:

- **PC: GEODE only**, every configuration of it (F16, G17, G0, F5). The GEODE comparisons (G17 vs G0 vs F16) are all within one machine. GEODE is new data, so no old laptop number has to be matched.
- **Laptop: the two replay-rate controls** on Corridor02 and Cave02. They are compared with the old laptop results of the master and of the 1.0x run, so they should run on the machine that produced those.
- A **60 s smoke test on both machines** (same code, same bag, same settings) first. It gives a coarse machine check (scans kept, time to first VINS pose) and confirms each stack works before the long runs.

Rules (fixed before the runs):
1. Every result is stored with its machine (`runs_..._L` / `_P`) and the repo commit.
2. A PC number is never placed next to a laptop number as if it were the same measurement. GEODE results are PC results; the controls are laptop results.
3. Scan retention (rows / scans) is reported for every run; runs under the row threshold are reported as failures.
4. The smoke test is the only cross-machine evidence. If the retention differs by more than 5 percentage points or VINS-Mono starts at clearly different times, the GEODE numbers are reported as "PC, 0.5x" and not compared with laptop numbers at all.

## 3. Decisions (configuration to follow)

| Decision | Choice |
|---|---|
| Code | both machines: a fresh clone of branch `fusion-v4-and-results` (commit printed in each log) |
| Environment | the laptop's containers exported once and loaded on the PC (`tools/export_images.sh`, `import_images.sh`) |
| Replay rate | GEODE 0.5x; Corridor02 0.33x; Cave02 0.5x (the master's rates) |
| Settings | all frozen: C_T 0.03 (F16); c_T 3e-6, c_R 5e-6, SAH (G17); GenZ config as on Multi Floor |
| PC runs | GEODE: F16 x3, G17 x3, G0 x3, F5 x1 = 10 runs, about 140 min; optional `STAGES=extra` is not needed (3 replicates already) |
| Laptop runs | Corridor02 G17 at 0.33x (about 47 min), then Cave02 G17 at 0.5x (about 35 min) = about 82 min |
| Bags | PC: local copy of GEODE (`~/bags/GEODE`). Laptop: reads Corridor02 and Cave02 from the external drive, which stays with the laptop except for the short trip below |
| Dropped | F0 live (the VINS-only trajectory is inside every F16 and G17 log) |

Why each run: F16 is the validated master; G17 is the proposed system; G0 is GenZ-LIO alone, the LiDAR-inertial baseline that G17 has to beat; F5 is plain A-LOAM. Published GEODE stairs-alpha numbers (recheck against the paper): FAST-LIO2 4.69 m, DLIO 4.89, R3LIVE 4.54, LIO-SAM 6.30, COIN-LIO 0.45, RELEAD 0.57.

## 4. Time plan (T0 = start)

| Minutes | Laptop | PC |
|---|---|---|
| 0-10 | clone repo; 60 s smoke test (reads GEODE from the drive) | install Docker / git, clone repo, 5 min after the drive arrives |
| 10-35 | export the containers to the drive (laptop idle) | - |
| 35-45 | drive goes to the PC | **copy** images, workspaces and GEODE from the drive to the PC's disk (about 5 min), return the drive |
| 45-60 | drive is back; start the controls | `import_images.sh` from the local copy, smoke test, start GEODE |
| 60-145 | Corridor02 then Cave02 controls (about 82 min), then idle | GEODE, 10 runs, ends at about minute 200 |

Everything fits in 4 hours with about 40 minutes of buffer on the PC.

## 5. After the runs
Bring back the results folders of both machines. Then: score GEODE and compare with the published table; per-machine and pooled statistics; the paired VINS-only / LiDAR-only / own-setting replays from the recorded logs; loop closure on the recorded keyframes (offline, on my side); decide whether G17 is kept as the final system or whether the VINS-failure gate becomes the next piece of work; update the project documents.

## 6. Risks
- Docker or the images fail to load on the PC: fall back to `INSTALL.md` section 2B (about 1-1.5 h, untested); then the PC does only the smoke test and one pass.
- RAM 16 GB: GenZ's voxel map plus VINS-Mono plus recorders; watch `free -g`; Cave02 is the heaviest.
- Laptop thermals: raise the fan profile, keep the lid open, run on mains power.
- VINS-Mono may fail on GEODE again at about 125 s; that is a result (the fusion must then run on LiDAR only), not a reason to change settings.

## 7. Outcome (22 Oct, evening)
Run as planned, with the PC stopped early after two replicates each (F16 x2, G17 x2, G0 x2, F5 x1): the extra repeats added nothing once the failure was consistent. Results and conclusions: `docs/results/GenZ_fusion_v4_RateControl_and_GEODE_Results.md`. The batch scripts needed three fixes found on the way (pre-flight on the laptop, missing GEODE config in the moved container, smoke test that did not notice VINS-Mono never starting); all are in the repository.
