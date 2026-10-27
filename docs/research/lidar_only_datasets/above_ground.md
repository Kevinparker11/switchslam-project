# Public LiDAR datasets with geometrically degenerate ABOVE-GROUND scenes (for LiDAR-only degeneracy detection evaluation)

Research date: Oct 2026. Method note: arxiv.org was blocked/rate-limited from this environment (WebFetch HTTP 429, curl CONNECT 403), so paper-internal details (exact IMU rates, GT accuracy tables) were taken from official dataset pages / GitHub READMEs where possible; anything not confirmed from a primary page is marked "unverified".

## Master table (verified fields; "unverified" where not confirmed)

| Dataset | Paper (venue, year, ID) | URL | LiDAR(s) | IMU | GT type / accuracy | GT traj public? | GT map public? | Degenerate above-ground sequences | Format | License |
|---|---|---|---|---|---|---|---|---|---|---|
| GEODE | Chen, Qi, Feng, Zhuang, Chen, Hu, Wu, Peng, Lu, "Heterogeneous LiDAR Dataset for Benchmarking Robust Localization in Diverse Degenerate Scenarios", IJRR (accepted 2025-03), arXiv 2409.04961 | github.com/PengYu-Team/GEODE_dataset ; thisparticle.github.io/geode | 3 rigs: alpha = Velodyne VLP-16 (16-beam spinning); beta = Ouster OS1-64 (spinning); gamma = Livox AVIA (solid-state) | Xsens MTi-30 on every rig (rate unverified) | Off-road & inland waterways: GNSS/INS; metro tunnels: Leica MS60 prism (position only); stairs: PALoc map-based alignment to GT map | Yes (Google Drive + Baidu) ; stairs has GT only for alpha & beta (gamma drifted) | Stairs prior map downloadable (via PALoc README links) ; other maps unverified | Stairs (narrow, glass noise), flat ground, off-road, inland waterways, bridges (+ tunnels/metro underground). Per-sequence degeneracy direction listed on homepage (not retrieved) | ROS1 bags + calib yaml | unverified |
| FusionPortable (v1) | Jiao et al., IROS 2022, arXiv 2208.11865 | fusionportable.github.io/dataset/fusionportable/ | Ouster OS1-128 (128x2048, spinning) | STIM300 (200 Hz per dataset abstract) | GT trajectories + GT maps (device not named on page; unverified) | Yes for listed sequences | Page explicitly lists GT maps for garden, escalator, building; PALoc README also links a corridor GT map | 20220216_corridor_day (x-degenerate per PALoc), escalator_day (open stairwell), building_day (indoor hallway, 3 loops) | ROS bag + KITTI-format | unverified |
| FusionPortableV2 | Wei, Jiao, Hu, Yu, Xie, Wu, Zhu, Liu, Wang, Liu, IJRR 2025, DOI 10.1177/02783649241303525, arXiv 2404.08563 | fusionportable.github.io/dataset/fusionportable_v2/ | Ouster OS1-128 (spinning) | STIM300; also 3DM-GQ7 GNSS/INS | GT trajectories & maps (accuracy unverified) | Page says GT trajectories available for all sequences | Page says GT maps downloadable "for sequences spanning diverse environments" (exact per-sequence list unverified) | Corridors, escalators, underground parking lots (exact sequence names unverified) | ROS bag + KITTI | unverified (open access paper) |
| Newer College (2020) + Multi-cam extension (2021) | Ramezani et al. IROS 2020; Zhang et al. (extension) 2021 (IDs unverified) | ori-drs.github.io/newer-college-dataset/ | Stereo set: Ouster OS-1 64; Multi-cam set: Ouster OS-0 128 | Multi-cam: Alphasense IMU 200 Hz + Ouster OS-0 IMU 100 Hz | 6-DoF GT, "centimetre accurate", from Leica BLK360 survey map (290M points, mm precision) | Yes | Site says map/GT point cloud available ("extended ground truth pointcloud"); PALoc supports two maps (parkland, math-institute) | Stairs; Maths-Easy/Medium/Hard; Quad; Cloister; Park | ROS bags | unverified |
| Oxford Spires | Tao et al., IJRR 2025, arXiv 2411.10546 | dynamic.robots.ox.ac.uk/datasets/oxford-spires/ | Hesai QT64 (64-ch, 60 m) | MEMS IMU 400 Hz, HW-synced | TLS (Leica RTC360) mm-accurate map; cm-accurate poses | Yes | Yes (TLS map part of dataset) | 24 seqs in Keble, Observatory Quarter, Blenheim Palace, Bodleian, Christ Church, New College; indoor/corridor segments (degeneracy not labelled) | unverified | CC BY-NC-SA 4.0 |
| BotanicGarden | RA-L 2024, DOI 10.1109/LRA.2024.3359548 | github.com/robot-pesg/BotanicGarden | Velodyne VLP-16 (16-beam spinning) + Livox AVIA (solid-state) on same robot | Xsens MTi-680G 400 Hz; Livox BMI088 200 Hz (accel in g) | Map-based localization inside Leica RTC360 survey map (11 mm std, ~1 cm map) -> cm-level poses (TUM, VLP16 frame) | Yes, all 33 seqs | GT map produced; public download unverified | Thick woods, riversides, narrow trails, bridges, grasslands (unstructured, flat/vegetated) | ROS bags | unverified |
| MCD (Multi-Campus) | Nguyen et al., CVPR 2024, arXiv 2403.11496 | mcdviral.github.io | Ouster OS1-128 (ATV) / OS1-64 (handheld) + Livox Mid-70 | 400 Hz IMUs (Bosch, VectorNav, Ouster) | Continuous-time GT vs survey-grade prior maps | Partly (withheld subset for challenge: unverified) | "High resolution large scale survey-grade prior maps" available | Campus NTU/KTH/TUHH (degeneracy not labelled) | ROS bags | CC BY-NC-SA 4.0 |
| HeLiPR | IJRR 2024, arXiv 2309.14590 | sites.google.com/view/heliprdataset | Ouster OS2-128, Velodyne VLP-16 (spinning), Livox Avia, Aeva Aeries II (solid-state/FMCW) — all on same vehicle | Xsens (model/rate unverified) | Global UTM poses (INS-based; system/accuracy unverified) | Yes | No map (unverified) | Bridge, Riverside, Roundabout, Town, KAIST, DCC (urban; Bridge = candidate degenerate) | HeLiPR file player | unverified |
| NTU VIRAL | Nguyen et al., IJRR 2022, 41(3):270-280, DOI 10.1177/02783649211052312 | ntu-aris.github.io/ntu_viral_dataset | 2x Ouster OS1-16 (horizontal+vertical; per awesome list) | multiple IMUs (VN100, rate unverified) | Leica total station prism, position only (0.4 m prism offset) | Yes | No | eee (carpark), nya (indoor auditorium), sbs, rtp (carpark), tnp (indoor plaza), spms (facade) — aerial | ROS bag | CC BY-NC-SA 4.0 |
| M3DGR | IROS 2025, arXiv 2507.08364 | github.com/sjtuyinjie/M3DGR | Livox Avia + Livox MID-360 (both non-repetitive, solid-state) | Livox IMUs 200 Hz; D435i 200 Hz | Corridor/elevator: ArUco; others RTK (0.8 cm H) / OptiTrack 1 mm | Yes | No | Corridor01, Corridor02 (long corridor), Elevator01 (corridor+elevator) under "LiDAR Degeneracy" | ROS bags | unverified |
| M2DGR | Yin et al., RA-L 2022 (venue from memory, unverified) | github.com/SJTU-ViSYS/M2DGR | Velodyne VLP-32C | Handsfree A9 150 Hz; Xsens MTi-680G 100 Hz | Vicon (1 mm), Leica MS60, RTK (2 cm) | Yes | No | Lifts, halls, rooms (indoor) | ROS bags | MIT (academic) |
| Ground-Challenge | Yin et al., ROBIO 2023, arXiv 2307.03890 | github.com/sjtuyinjie/Ground-Challenge | Velodyne VLP-16 | Xsens MTi-300 400 Hz; D435i 200 Hz | PSEUDO-GT from FAST-LIO2 (3 cm vs mocap in 15x15 m room) | Yes | No | Corridor, Hall, Rotation, Static | ROS bags | MIT badge |
| Hilti 2022 (Hilti-Oxford) | Zhang et al., RA-L 2022 / Hilti challenge (arXiv 2109.11316 is 2021 paper) | hilti-challenge.com/dataset-2022 | Hesai PandarXT-32 | Alphasense IMU (model/rate unverified) | Z+F Imager 5016 TLS, registration sigma < 1 mm | 8 "additional" sequences public; 7 challenge sequences withheld | unverified | Exp07, Exp11 long corridor/gallery; Exp03 construction stairs (whether these are in the public-GT subset: unverified) | ROS bag | CC BY-NC-SA 3.0 |
| ENWIDE | Pfreundschuh et al., COIN-LIO, ICRA 2024, arXiv 2310.01235; data DOI 10.3929/ethz-c-000787551 | projects.asl.ethz.ch/datasets/enwide | Ouster OS0-128 Rev D, 10 Hz | Ouster internal IMU 100 Hz | Leica MS60 total station, position-only, TUM CSV | Yes | No | Tunnel, Field, Intersection, Katzensee, Runway (smooth/dynamic) — explicitly geometrically degenerate | ROS bags | unverified |
| NTNU lidar_degeneracy_datasets | Nissov, Khedekar, Alexis, ICRA 2024, DOI 10.1109/ICRA57147.2024.10611444, arXiv 2403.05332 | github.com/ntnu-arl/lidar_degeneracy_datasets | Ouster OS0-128 | VectorNav VN100 200 Hz | No GT mentioned in README | No (unverified) | No | 500 m bike tunnel (self-similar), fog-filled corridor (aerial) | ROS bag (HuggingFace) | unverified |
| DCReg / PALoc "MS" self-collected | Hu et al., DCReg, IJRR 2026, arXiv 2509.06285; PALoc (Hu et al., GitHub JokerJohn/PALoc) | github.com/JokerJohn/DCReg ; github.com/JokerJohn/PALoc | Hesai Pandar XT-32 | SBG INS (per launch name ms_sbg_pandar32; unverified) | RTK-INS GT (per DCReg paper) | parkinglot_01 GT map + redbird_02/03 GT trajectories public via PALoc | Yes: parking-lot prior_map.pcd (DCReg Google Drive); parkinglot_01 GT map (PALoc gofile) | Open parking lot: x,y translation + yaw degenerate (planar) | pcd + rosbag | unverified |

## Which provide LiDAR + IMU + public GT for degenerate sequences, plus a GT map (for geometry-based oracle labels)?

### Takeaway
Best fits with LiDAR + IMU + public GT trajectory + downloadable GT/prior map on explicitly degenerate above-ground scenes are: GEODE (stairs; map via PALoc), FusionPortable v1 (corridor_day, escalator_day, building_day with GT maps), Newer College multi-cam (stairs, maths institute; BLK360 map), Oxford Spires (TLS map), DCReg/PALoc MS parking lot (prior map + RTK-INS GT), and MCD (survey-grade prior maps). ENWIDE and NTU VIRAL have position-only total-station GT and no map; Ground-Challenge GT is only FAST-LIO2 pseudo-GT.

### Cited Findings
- GEODE: three rigs (VLP-16 / OS1-64 / Livox AVIA), each with Xsens MTi-30; GT via GNSS/INS (off-road, inland waterways), Leica MS60 prism position-only (metro tunnels), PALoc alignment to GT map (stairs); stairs GT not available for gamma (Avia) because odometry drifts; README recommends map-vs-GT-map evaluation for stairs — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- GEODE off-road, inland_waterways and Metro_Tunnels were recorded with all three rigs mounted simultaneously on one rack with one GT system, with scripts (alpha2GT_gnss.py, gamma2gt_gnss.py, beta2gt_leica.py) to transform trajectories — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- GEODE accepted by IJRR (2025-03-09); arXiv 2409.04961; download via Google Drive and Baidu; ROS1 bags only — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- GEODE stairs prior map (with and without glass noise) downloadable; "Stairs scenes with different types of lidar and glass noise ... narrow stairs" — [PALoc README](https://github.com/JokerJohn/PALoc)
- FusionPortable 20220216_corridor_day has a GT map described as "corridor with x degeneracy"; escalator_day "open stairwell"; building_day "three loops of indoor hallway"; GT maps linked for these — [PALoc README](https://github.com/JokerJohn/PALoc)
- PALoc added generated GT trajectories of the FP dataset in `fp_gt` folder (2026-01-20) — [PALoc README](https://github.com/JokerJohn/PALoc)
- FusionPortable v1: OS1-128, STIM300; GT trajectories for canteen, garden, corridor_day, escalator_day, building_day, MCR, campus_road; GT maps explicitly for garden, escalator, building — [FusionPortable page](https://fusionportable.github.io/dataset/fusionportable/)
- FusionPortableV2: OS1-128, STIM300 + 3DM-GQ7; corridors, escalators, underground parking; GT trajectories & maps provided — [FusionPortableV2 page](https://fusionportable.github.io/dataset/fusionportable_v2/); IJRR 2025, DOI 10.1177/02783649241303525 — [SAGE](https://journals.sagepub.com/doi/10.1177/02783649241303525)
- Newer College: centimetre-accurate 6-DoF GT from Leica BLK360 map (290M points) — [Newer College site](https://ori-drs.github.io/newer-college-dataset/); multi-cam collections include Stairs, Quad-*, Cloister, Park, Maths-Easy/Medium/Hard; Alphasense IMU 200 Hz + OS-0 IMU 100 Hz — [Multi-cam page](https://ori-drs.github.io/newer-college-dataset/multi-cam/)
- Oxford Spires: Hesai QT64, 400 Hz MEMS IMU, Leica RTC360 TLS GT map, CC BY-NC-SA 4.0, arXiv 2411.10546 — [Oxford Spires page](https://dynamic.robots.ox.ac.uk/datasets/oxford-spires/)
- MCD: OS1-128/OS1-64 + Livox Mid-70, 400 Hz IMUs, continuous-time GT, survey-grade prior maps, CVPR 2024, CC BY-NC-SA 4.0 — [MCD site](https://mcdviral.github.io/), [MCD user manual](https://mcdviral.github.io/UserManual.html), [arXiv 2403.11496](https://arxiv.org/abs/2403.11496)
- BotanicGarden: VLP-16 + Livox AVIA, Xsens MTi-680G 400 Hz, Livox BMI088 200 Hz; Leica RTC360 survey map (11 mm std, 900+ scans); GT trajectories for all 33 sequences via map-based localization; woods, riversides, bridges, grasslands — [BotanicGarden README](https://github.com/robot-pesg/BotanicGarden)
- M3DGR "LiDAR Degeneracy" group: Corridor01 (403 s), Corridor02 (293 s), Elevator01 (699 s) with ArUco-based GT; sensors Livox Avia + MID-360 — [M3DGR README](https://github.com/sjtuyinjie/M3DGR)
- Hilti 2022: GT from Z+F Imager 5016 TLS (sigma < 1 mm); 8 additional sequences have public GT, 7 challenge sequences withheld; Exp07/Exp11 long corridor, Exp03 stairs; CC BY-NC-SA 3.0 — [Hilti 2022 page](https://hilti-challenge.com/dataset-2022)
- ENWIDE: OS0-128, internal IMU 100 Hz, Leica MS60 position-only GT in TUM CSV; Tunnel/Field/Intersection/Katzensee/Runway — [ENWIDE page](https://projects.asl.ethz.ch/datasets/enwide); paper targets "geometrically degenerate scenarios, like tunnels or flat fields" — [COIN-LIO README](https://github.com/ethz-asl/COIN-LIO)
- NTU VIRAL: Leica total station GT, position only, 0.4 m prism offset; 18 sequences incl. carparks, indoor auditorium, plaza, facade; CC BY-NC-SA 4.0; IJRR 2022 DOI 10.1177/02783649211052312 — [NTU VIRAL](https://ntu-aris.github.io/ntu_viral_dataset/)
- Ground-Challenge GT is pseudo-GT from FAST-LIO2 (3 cm vs mocap in 15x15 m room) — [arXiv 2307.03890 HTML](https://arxiv.org/html/2307.03890v1)
- DCReg parking-lot prior_map.pcd distributed via Google Drive; bundled frame pk01-1976 shows weakest translational direction along x — [DCReg README](https://github.com/JokerJohn/DCReg)
- PALoc self-collected MS dataset: parkinglot_01 GT map, redbird_02/03 GT trajectories, Pandar XT32 — [PALoc README](https://github.com/JokerJohn/PALoc)

### Inferences
- For geometry-based oracle labels (compute Hessian/eigenvalues of scan-to-GT-map registration at GT pose), the strongest candidates are FusionPortable corridor_day (OS128 + STIM300 + GT map, x-degenerate), GEODE stairs (VLP-16 and OS1-64 + GT map), DCReg/MS parking lot (prior map), Newer College stairs/maths (BLK360 map), and BotanicGarden (if the RTC360 map is downloadable).
- ENWIDE is the most explicitly "degenerate by design" above-ground set (flat field, runway, tunnel), but lacks orientation GT and maps, so it only supports position-based labels.

### Gaps
- Exact per-sequence degeneracy directions for GEODE (homepage thisparticle.github.io/geode could not be fetched: proxy 403).
- FusionPortableV2 per-sequence GT-map list and GT accuracy (arXiv blocked).
- Whether BotanicGarden's RTC360 GT map and Newer College's BLK360 map are freely downloadable (pages suggest yes but not confirmed).
- Whether Hilti 2022 Exp03/07/11 are among the 8 public-GT sequences.
- MCD: which sequences have withheld GT.

## Which offer a 16-beam LiDAR (A-LOAM VLP-16 compatibility) or multiple LiDARs on the same trajectory?

### Takeaway
16-beam: GEODE (alpha rig VLP-16), BotanicGarden (VLP-16), HeLiPR (VLP-16), Ground-Challenge (VLP-16), NTU VIRAL (2x OS1-16). Multiple LiDARs on the same trajectory: GEODE (VLP-16 + OS1-64 + Avia simultaneously on off-road, inland waterways, metro tunnels), BotanicGarden (VLP-16 + Avia), HeLiPR (OS2-128 + VLP-16 + Avia + Aeva), MCD (OS1 + Mid-70), M3DGR (Avia + MID-360), NTU VIRAL (two OS1-16). Any 64/128-beam Ouster set can also be beam-decimated synthetically.

### Cited Findings
- GEODE alpha = VLP-16, beta = OS1-64, gamma = Livox AVIA; simultaneous three-rig recording for off-road, inland_waterways, Metro_Tunnels — [GEODE README](https://github.com/PengYu-Team/GEODE_dataset)
- BotanicGarden topics /velodyne_points (VLP16) and /livox/lidar (AVIA) in same bags — [BotanicGarden README](https://github.com/robot-pesg/BotanicGarden)
- HeLiPR: OS2-128, VLP-16, Livox Avia, Aeva Aeries II; "All scenes are acquired at same location" — [HeLiPR site](https://sites.google.com/view/heliprdataset); list also in [Awesome-3D-LiDAR-Datasets](https://github.com/minwoo0611/Awesome-3D-LiDAR-Datasets)
- Ground-Challenge: VLP-16 + Xsens MTi-300 400 Hz — [Ground-Challenge README](https://github.com/sjtuyinjie/Ground-Challenge)
- NTU VIRAL: 2x OS1-16 — [Awesome-3D-LiDAR-Datasets](https://github.com/minwoo0611/Awesome-3D-LiDAR-Datasets) (secondary source); "Two 3D lidars" — [NTU VIRAL README](https://github.com/ntu-aris/ntu_viral_dataset)
- DiTer++ listed with 1x OS1-32/64/128 (multi) — [Awesome-3D-LiDAR-Datasets](https://github.com/minwoo0611/Awesome-3D-LiDAR-Datasets); its site says GT from survey-grade prior map + scan-to-map matching, ICRA 2024 workshop — [DiTer++ site](https://sites.google.com/view/diter-plusplus/)
- PALoc provides launch configs for velodyne16 (GEODE) and ouster64 (GEODE) on the stairs sequence — [PALoc README](https://github.com/JokerJohn/PALoc)

### Inferences
- GEODE stairs is the only verified case with BOTH a VLP-16 run and a GT map in a degenerate indoor scene (alpha and beta have GT; gamma does not).
- BotanicGarden is the best VLP-16 + open-field/forest/bridge candidate with cm-level 6-DoF GT.

### Gaps
- Whether GEODE stairs alpha/beta were captured simultaneously (same trajectory) or as separate runs: unverified.
- DiTer/DiTer++ sensor specifics and download status not confirmed; dropped from main table.
- S3E (RA-L; github.com/PengYu-Team/S3E) sensors and GT not retrieved; dropped.

## Which papers used each for degeneracy evaluation?

### Takeaway
DCReg (IJRR 2026) uses FusionPortable corridor + building, GEODE stairs (OS64), MS parking lot (Pandar32) and SubT-MRS caves; COIN-LIO introduced ENWIDE; Nissov et al. introduced the NTNU tunnel/fog set; M3DGR defines its own LiDAR-degeneracy group; PALoc uses GEODE, FusionPortable, Newer College and MS for GT generation in degenerate scenes.

### Cited Findings
- DCReg Table 2: Corridor (OS128, FP, 572 s, trans+rot degenerate), Building (OS128, FP), Stairs (OS64, GEODE, 331 s), Parking Lot (Pandar32, MS, 502 s), Cave01/02/04 (VLP16, SubT-MRS); range artificially limited to 10 m on parking lot and corridor to induce degeneracy — DCReg paper, arXiv 2509.06285v3 (project file), [arXiv](https://arxiv.org/abs/2509.06285)
- DCReg parking lot: frame 2314 X,Y degenerate; frame 2924 adds yaw degeneracy (planar). Corridor frames 1096 (X + roll) and 1142 (roll only) — same source
- Note inconsistency: DCReg Fig. 6 caption attributes the open parking lot to "Wei et al. (2024)" (FusionPortableV2) while Table 2 and text label it "MS" self-collected (Pandar XT-32 + RTK-INS) — same source
- DCReg simulated cylinder follows protocol of Tuna et al. (2025) — same source
- X-ICP (Tuna et al., T-RO 2023, arXiv 2211.16335) field data page says "Additional Data (Will be shared upon acceptance)" with no download links — [X-ICP site](https://sites.google.com/leggedrobotics.com/x-icp)
- COIN-LIO introduces ENWIDE for degenerate scenes — [COIN-LIO README](https://github.com/ethz-asl/COIN-LIO)
- Degradation Resilient LiDAR-Radar-Inertial Odometry (ICRA 2024) released tunnel + fog corridor — [NTNU README](https://github.com/ntnu-arl/lidar_degeneracy_datasets)
- M3DGR README lists downstream users including FAST-LIVGO "Degeneracy-Robust" (IROS 2026, arXiv 2606.19190) and RoLe-LIO (TII 2026) — [M3DGR README](https://github.com/sjtuyinjie/M3DGR)
- A curated degeneracy dataset list includes GEODE, SubT-MRS, ENWIDE, NTNU LiDAR degeneracy, WHU-Helmet, Railroad-dataset, SubT team datasets — [Awesome-Algorithms-Against-Degeneracy](https://github.com/thisparticle/Awesome-Algorithms-Against-Degeneracy)

### Inferences
- Reproducing DCReg's real-world detection protocol is feasible with public data: FP corridor/building (GT map via PALoc), GEODE stairs (map via PALoc), MS parking lot (prior map via DCReg Drive + PALoc). SubT-MRS caves are underground (out of this file's scope).

### Gaps
- Systematic list of other 2024-2026 degeneracy-detection papers per dataset not compiled (search budget). WHU-Helmet and Railroad-dataset not verified.
- Tuna et al. X-ICP data appears still not public as of the fetched page; no alternative release found.
