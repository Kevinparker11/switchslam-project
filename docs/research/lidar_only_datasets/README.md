# Score the LiDAR detector against map-derived labels

**For a LiDAR-only degeneracy-detection thesis, the best public datasets are SubT-MRS (SuperLoc set), GEODE Stairs, and FusionPortable corridor/building, followed by DCReg's parking-lot map and a TLS-mapped control (Newer College or Oxford Spires).** All five have LiDAR, an IMU, public ground-truth (GT) trajectories and a public or linked GT point-cloud map. A GT map is what makes geometry-based, per-direction labels possible: you perturb the GT pose and re-register the scan against the map. Two of the five give a true 16-beam stream for A-LOAM's `scan_line 16`: SubT-MRS (Velodyne puck) and GEODE's α rig (VLP-16). The protocol question has a blunt answer. **Only L3E reports detection precision and recall against per-direction labels, and it did so in Gazebo simulation. No verified paper evaluates a normal or orientation-tensor measure at all.** Every real-data paper scores detection indirectly, through ATE, map error, a "degeneracy ratio" or qualitative timelines. A labelled, real-data, per-direction detection benchmark would therefore be a thesis contribution in itself, not just a test bed. Keep the IMU out of the detector test, because IMU priors can mask degeneracy. Its presence in these datasets still matters, because it lets LIO baselines be added later on the same sequences.

## Five datasets carry LiDAR, IMU, GT trajectory and a GT map on degenerate scenes

Position-only GT (from a total station) cannot score rotation-direction labels, and a missing GT map rules out L3E-style labels entirely. Those two filters remove most "degenerate" datasets. The table ranks what survives.

| Rank | Dataset / sequences | LiDAR (beams) | IMU | GT type | GT map public | Degenerate content | Papers that used it |
|---|---|---|---|---|---|---|---|
| 1 | **SubT-MRS, SuperLoc set**: Cave01–04, Corridor01/02, Floor01 | Velodyne puck, **16**, 10 Hz | Epson M-G365, 200 Hz | 6-DoF TUM, but **map-aided fusion** of map + LiDAR/visual/IMU odometry | **Yes**: FARO S120 maps (Laurel Caverns, Hawkins) | Caves with aggressive motion; long featureless corridors (axial); multi-floor building | DCReg (Cave01/02/04), LP-ICP (Long Corridor), Switch-SLAM (Multi Floor, Long Corridor), SuperLoc |
| 2 | **GEODE Stairs** (α and β rigs) | α VLP-16 (**16**); β OS1-64 | Xsens MTi-30 (100 Hz per arXiv; rate disputed, see list) | Map-based PALoc alignment; GT only for α and β (the Avia rig drifted) | **Yes**: stairs prior map (with/without glass noise), via PALoc README | Narrow stairs with glass noise; Z degenerate going down, roll–pitch going up (DCReg) | DCReg (Stairs, OS1-64) |
| 3 | **FusionPortable v1**: 20220216_corridor_day, building_day, escalator_day | Ouster OS1-128 (decimate to 16) | STIM300, 200 Hz | GT trajectories; PALoc adds generated `fp_gt` trajectories | **Yes**: garden/escalator/building listed; corridor map via PALoc ("corridor with x degeneracy") | Corridor (x-degenerate); building = false-positive control | DCReg (Corridor, Building) |
| 4 | **DCReg / PALoc "MS" parking lot** | Hesai Pandar XT-32 (32) | Unverified (SBG INS inferred from launch name) | RTK-INS | **Yes**: `prior_map.pcd` (DCReg Drive), parkinglot_01 GT map (PALoc) | Open planar lot: x, y, then yaw degenerate | DCReg (range-limited to 10 m) |
| 5 | **Newer College multi-cam** (Stairs, Maths-Easy/Medium/Hard) or **Oxford Spires** | OS0-128; Hesai QT64 | Alphasense 200 Hz + OS-0 100 Hz; Spires MEMS 400 Hz | cm-level 6-DoF from ICP to the TLS/BLK360 map | NC: GT point cloud on site (full prior map unverified); Spires: **yes** (RTC360) | Stairs, narrow quads; mostly well-constrained, so useful as controls | None verified for detection |

Sources: SubT-MRS ([SuperLoc page](https://superodometry.com/superloc); [datasets page](https://superodometry.com/datasets); [CVPR 2024 paper](https://openaccess.thecvf.com/content/CVPR2024/papers/Zhao_SubT-MRS_Dataset_Pushing_SLAM_Towards_All-weather_Environments_CVPR_2024_paper.pdf); [arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)). GEODE ([GEODE README](https://github.com/PengYu-Team/GEODE_dataset); [arXiv 2409.04961v1](https://arxiv.org/html/2409.04961v1); [PALoc README](https://github.com/JokerJohn/PALoc)). FusionPortable ([FusionPortable page](https://fusionportable.github.io/dataset/fusionportable/); [PALoc README](https://github.com/JokerJohn/PALoc)). MS parking lot ([DCReg README](https://github.com/JokerJohn/DCReg); [PALoc README](https://github.com/JokerJohn/PALoc)). Controls ([Newer College](https://ori-drs.github.io/newer-college-dataset/); [multi-cam page](https://ori-drs.github.io/newer-college-dataset/multi-cam/); [Oxford Spires](https://dynamic.robots.ox.ac.uk/datasets/oxford-spires/)). DCReg usage ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy v3, Table 2). LP-ICP ([arXiv 2501.02580v3](https://arxiv.org/html/2501.02580v3)). Switch-SLAM (project PDF, [DOI](https://doi.org/10.1109/LRA.2024.3421792)).

**SubT-MRS ranks first** because it is the only set that combines native 16-beam data, a 200 Hz IMU, 6-DoF GT and public survey maps on genuinely degenerate scenes. It also carries the largest published decoupling margin: DCReg reaches **4.57 cm ATE on Cave02, against 565.61 cm for ME-SR** ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy). The weakness is circularity. Its GT trajectories fuse LiDAR odometry with the map ([arXiv 2307.07607v5](https://arxiv.org/html/2307.07607v5)), so GT is least trustworthy in exactly the frames where the scan is degenerate.

**GEODE Stairs ranks second.** It is the only verified indoor degenerate scene with both a VLP-16 run and a GT map, and DCReg's 3.96 cm against ME-SR's 160.75 cm gives a published reference point ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy).

**FusionPortable corridor and building are paired** because they test opposite things. The corridor is a known single-axis case. In the building sequence every method ties at about 8.6 cm while the full condition number flags 99.23% of frames, so it directly measures false positives ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy).

### Useful but excluded from the top five

Several datasets miss the cut on one specific filter:

- **CERBERUS DARPA SubT Final** has a VLP-16, an Alphasense IMU and TUM GT for ANYmal 1–4. It was used by LP-ICP and Switch-SLAM. Its GT was registered to a DARPA reference map, but redistribution of that map from the repo is unconfirmed ([CERBERUS repo](https://github.com/leggedrobotics/cerberus_darpa_subt_datasets); [subt_resources](https://github.com/subtchallenge/subt_resources/blob/main/3-Datasets.md)).
- **GEODE tunnels** (VLP-16 on the mining-method and urban tunnels) and **ENWIDE** (OS0-128, 100 Hz internal IMU; Tunnel, Field, Runway) are degenerate by design. Their total-station GT is **position-only** and there is no map, so they support only translational, drift-based checks ([GEODE homepage](https://thisparticle.github.io/geode/); [ENWIDE](https://projects.asl.ethz.ch/datasets/enwide/)).
- **BotanicGarden** (VLP-16 + Avia, Xsens 400 Hz, cm GT from an RTC360 survey map) is a strong 16-beam outdoor candidate, but public download of its map is unverified ([BotanicGarden README](https://github.com/robot-pesg/BotanicGarden)).
- **Ground-Challenge** has only FAST-LIO2 pseudo-GT ([arXiv 2307.03890](https://arxiv.org/html/2307.03890v1)).
- **M2TD** GT is fused from LiDAR, IMU and UWB, so it is not independent ([M2TD](https://github.com/longlongzxl/M2TD)).

## Real papers support only indirect detection scoring, except L3E in simulation

**L3E is the only verified paper that scores a detector against per-direction labels with classification metrics**, and it did this entirely in Gazebo with a simulated VLP-16. Its labelling procedure:

1. Perturb each child scan with Gaussian offsets per direction (about 0.1 m, 5–10°) and re-raycast it.
2. Register the child back to its parent.
3. Label a direction localizable if the expected error stays below **0.1 m or 2°**.

On a held-out tunnel, the 6-DoF averages were accuracy 0.854, precision 0.398, recall 0.752 and F1 0.517 ([ar5iv 2203.05698](https://ar5iv.labs.arxiv.org/html/2203.05698)).

Every other verified detector paper scores detection indirectly:

- **X-ICP** shows per-direction localizability timelines and APE/RPE against RTC360 maps ([arXiv 2211.16335](https://arxiv.org/html/2211.16335)).
- **Tuna et al.'s field study** explicitly has no GT labels ([arXiv 2408.11809](https://arxiv.org/pdf/2408.11809)).
- **LP-ICP, Hatleskog & Alexis, SuperLoc and LiLi** use trajectory error, qualitative plots or alignment-quality proxies ([LP-ICP](https://ar5iv.labs.arxiv.org/html/2501.02580); [2410.10784](https://arxiv.org/html/2410.10784v2); [SuperLoc](https://arxiv.org/html/2412.02901v1/); [LiLi](https://arxiv.org/html/2609.17145v2)).
- **DCReg** reports a **degeneracy ratio**, the share of frames flagged, which the authors call "an indicator of detection sensitivity rather than an error metric." They argue correctness from ATE and map accuracy ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy §7.1.2).

One partial exception should be stated, not hidden. Switch-SLAM reports detection accuracy and recall on its own Handheld data, but its labels are outcome-based (GNSS against ICP scan-to-scan per keyframe) and not per-direction (project PDF, [DOI](https://doi.org/10.1109/LRA.2024.3421792)).

**No verified paper evaluates a surface-normal or orientation-tensor degeneracy measure against labels.** LP-ICP uses normals only through point-to-plane Jacobians. LF-GICP ("voxel-normal localizability field", arXiv 2608.19522) is the closest title, but its content could not be read ([arXiv 2608.19522](https://arxiv.org/html/2608.19522)). No public dataset ships per-frame, per-direction degeneracy labels either; GEODE gives only scenario-level categories ([arXiv 2409.04961v1](https://arxiv.org/html/2409.04961v1)). The labelled benchmark is therefore genuinely missing, and building it is a contribution.

### Channel T is related to H_tt, not identical to it

A project note states that Channel T "is exactly H_tt/N." That identity holds only when every correspondence has the same normals, weights and correspondence set as the Hessian. **On the real Multi Floor log, the correlation between T and H_tt/N was only 0.74–0.80** (project measurement, user-reported). The correct statement is that **T is closely related to the un-Schur'd translational block H_tt** (the sum of n·nᵀ over point-to-plane correspondences), but it is not equal to it.

Two consequences follow:

- **Coupling.** Because T sits before the Schur correction, it cannot see translation–rotation coupling, which DCReg's S_tt = H_tt − H_tr H_rr⁻¹ H_rt captures. T should be expected to lag on coupling-dominated cases such as Cave02 and Stairs.
- **Where T could add value.** Any added value would have to come from its independence from correspondence weighting, or from the regimes where DCReg's margin collapses. At a 10 m range limit on the parking lot, DCReg (29.56 cm) and ME-TSVD (30.46 cm) are within 1 cm of each other ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy).

Both points are hypotheses, not published findings.

## A defensible protocol: perturb at the GT pose, score per DoF, keep the IMU out

The protocol combines published pieces. The labels come from L3E. The baselines, thresholds and range manipulation come from DCReg. The circularity caveat applies because several GT trajectories are themselves map registrations.

**Labels.** For each frame, place the scan at its GT pose. Monte-Carlo-perturb the pose along each of the 6 DoF (L3E magnitudes), run point-to-plane ICP against the GT map, and label a direction degenerate if the error exceeds 0.1 m or 2°. Also compute an oracle Hessian/Schur at the GT pose, as a second, model-based label. Sweep the thresholds, the downsampling and the range crop, because labels depend on all three: DCReg flags **86.7% of parking-lot frames at 10 m range against 31.1% at 60 m** ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy). Rotation labels need 6-DoF GT, so position-only datasets are excluded from rotation scoring.

**Detectors and metrics.** Run every detector on identical A-LOAM-style features with no IMU prior:

- **Baselines:** ME (minimum eigenvalue), FCN (full condition number) and CN (relative condition number), which are DCReg's detection baselines.
- **DCReg's Schur condition numbers:** threshold κ = 10.
- **Channel T.**

Report per-DoF precision, recall, F1 and AUC against the labels. Also report DCReg's degeneracy ratio, only so the numbers can be compared with its Table 5 ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy §7.1.2, §7.4.1).

**Sanity check.** Before real data, reproduce DCReg's and Tuna et al.'s symmetric-cylinder simulation, where the degenerate directions are known by construction.

**IMU role.** DCReg warns that "strong priors from IMU ... can also redistribute or mask degeneracy patterns," and deliberately evaluates registration LiDAR-only ([arXiv 2509.06285](https://arxiv.org/abs/2509.06285), project copy §9). The detector test must therefore be IMU-free. The IMU still earns its place: every top-five set carries one, so LIO baselines (and an "IMU-on" robustness ablation) can be added later on the same frames without changing datasets.

### Exact first steps

1. **SubT-MRS Floor01.** Download the GT trajectory `1T-p9TgDwD_9us7U94cT0guwPNTvx3KkI` and the Hawkins map `1F46g0wnJVSedTJubFD_Ne1IwgZAGYvsU` ([SuperLoc page](https://superodometry.com/superloc)). Confirm timestamp overlap with the existing Multi Floor bag, then re-score Channel T and the Hessian detectors against L3E-style labels.
2. **SubT-MRS Cave02.** Download the GT trajectory `1_7D70MVcUbaJqlzN_xlDkguF1qiyZCqF` and the cave map `1JYSVgunLJj6Fj-MsDoNIDHRDx51YWsQP`. Generate labels and run the IMU-free detector comparison, with DCReg's κ = 10.
3. **GEODE Stairs.** Fetch the α (VLP-16) and β (OS1-64) stairs bags from the [GEODE README](https://github.com/PengYu-Team/GEODE_dataset) and the stairs prior map from the [PALoc README](https://github.com/JokerJohn/PALoc). Use α with `scan_line 16` unchanged.
4. **FusionPortable.** Get corridor_day and building_day with the PALoc `fp_gt` trajectories and corridor map. Decimate OS1-128 to 16 rings, and record that the vertical FoV differs from a VLP-16.
5. **Range sweep.** Generate 10/20/30/60 m crops of steps 1–4 for the stress regime.

## Not yet verified: do not cite as fact

| Item | Status |
|---|---|
| GEODE IMU rate | One note says "unverified"; the other cites 100 Hz from arXiv HTML. Re-check against the paper |
| GEODE venue and year (IJRR 2025 vs 2026) and DOI 10.1177/02783649251344967; author list | Notes disagree or unverified |
| GEODE per-sequence degeneracy directions (homepage not retrieved); maps other than stairs; metro-tunnel map release; urban-tunnel GT method; whether stairs α and β were recorded simultaneously; license | Unverified |
| GEODE stairs GT being full 6-DoF | Inferred from map-based alignment |
| FusionPortable v1 GT device; license | Unverified |
| FusionPortableV2 per-sequence GT-map list, GT accuracy and exact sequence names | Unverified |
| DCReg's "FP" being FusionPortable/V2; DCReg Fig. 6 caption attributing the parking lot to Wei et al. 2024 while Table 2 says self-collected "MS" | Inference / inconsistency in source |
| MS parking lot: SBG INS (from launch name); whether the bags themselves are public | Unverified |
| Newer College paper IDs; whether the full BLK360 prior map is downloadable; license | Unverified |
| Oxford Spires data format | Unverified |
| BotanicGarden RTC360 map public download | Unverified |
| MCD: which sequences have withheld GT | Unverified |
| HeLiPR Xsens model/rate, GT system/accuracy, absence of a map | Unverified |
| NTU VIRAL IMU rate; M2DGR venue | Unverified |
| Hilti 2022: Alphasense IMU model/rate; whether Exp03/07/11 have public GT; whether TLS maps are public (sources conflict) | Unverified |
| NTNU lidar_degeneracy_datasets having no GT | Unverified |
| CERBERUS GT accuracy; whether the DARPA reference map is redistributed in the repo | Unverified |
| ARL SubT reference data having per-sequence GT trajectories | Unverified |
| ENWIDE license, size and access policy; OS0 vertical FoV of about 90° (general knowledge) | Unverified |
| CAVERS license; little axial degeneracy in its cave rooms | Unverified / inference |
| X-ICP Seemühle and Ulmberg data being public (none found); X-ICP T-RO volume; L3E venue (ICRA 2022) | Unverified |
| SubT-MRS: SP1 = Spot; Floor01 = Multi_Floor, Corridor01 = Long_Corridor, Cave03 = Laurel_Cavern; DCReg cave GT = SuperLoc release; Drive file contents; per-trajectory GT accuracy; license; cave lighting | Inference or unverified |
| Switch-SLAM using challenge-released GT | Inference |
| Evaluation protocols of Zhang & Singh 2016, Hinduja 2019, DARE-SLAM, GenZ-ICP, RELEAD, COIN-LIO's degeneracy analysis (believed from memory to lack labelled precision/recall) | Unverified |
| LF-GICP method and results; LF-GICP and SVN-ICP using GEODE | Unverified (search snippets only) |
| GrandTour having no tunnel mission; SubSurfaceGeoRobo, CTU-CRAS, CSIRO Wildcat, NeBula/JPL, Explorer, ColoRadar details; DiTer/DiTer++; S3E; WHU-Helmet; Railroad dataset | Unverified |
| Exact per-paper numbers taken from fetch-tool summaries (L3E, X-ICP, Tuna et al., LP-ICP) | Check against the PDFs before quoting |
| "Channel T = H_tt/N exactly" (project note) | **Incorrect as stated**: holds only under identical normals, weights and correspondences; real Multi Floor correlation is 0.74–0.80 |

## Conclusion

The dataset choice is less constrained than the label choice. Five public sets already have the map needed for geometry-based labels. What is missing is anyone having scored a detector against such labels on real data, and nobody has tested an orientation-tensor channel at all. The thesis's strongest framing is therefore the benchmark itself: L3E-style per-DoF labels on SubT-MRS, GEODE Stairs and FusionPortable, with range sweeps, an IMU-free detector test and an explicit circularity flag where the GT is itself a map registration. Channel T is then one tested detector among ME, FCN and Schur, rather than the sole claim.

Expect Channel T to trail Schur-based detection wherever translation and rotation are coupled, because T is built from the un-Schur'd block. Its realistic niche is the range-limited regime where DCReg's own advantage shrinks to about 1 cm. A clean negative result there, against independent labels, would still be publishable evidence.
