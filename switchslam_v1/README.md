# switchslam_v1: generation 1 (Sep 2026)

The original SwitchSLAM implementation: Switch-SLAM-style switching between A-LOAM and VINS-Mono with Schur-complement (Channel R) and Bingham/orientation-tensor (Channel T) degeneracy detection, run in Gazebo (Farm/Panels world, Husky robot) and on the SubT-MRS Multi Floor bag. It is superseded by the fusion study in `../fusion_v3/` and `../fusion_v4/` (see `../docs/results/Configurations_Explained_and_Results_To_Date.md`), and kept as the record of how the method developed.

| Folder | Content |
|---|---|
| `nodes/` | switching nodes `switching_node_v3.py` ... `v7` (earlier variants) |
| `farm/` | final Farm/Panels set: `switching_node_v9.py` (+ verbose), three-way / dual-confidence / time-decay / Schur-Bingham nodes, `waypoint_driver_panels.py`, `waypoint_driver_v4.py` (autonomous L-shape route, best Farm result: LOAM RMSE 0.32 m), Farm VINS config, 200 Hz IMU xacro, launch file |
| `multifloor/` | the Multi Floor versions of the node, ATE evaluation (`compute_ate_multifloor.py`), offline ablation replay, launch/config files |
| `drivers/` | earlier waypoint drivers |
| `analysis/` | A-LOAM-only logger, plotting, ground-truth export, threshold test |
| `logs/` | switching logs of the generation-1 runs (CSV) |
| `figures/` | Multi Floor baseline vs time-decay plot |
| `scripts/clean_restart.sh` | restarts both containers (also copied into `fusion_v4/`) |

The third-party patches these nodes depend on are in `../patches/aloam_vins/`.
Status: the generation-1 Multi Floor result (RMSE ~1.39 m, old switching node) is in the results table; Farm results are in `../docs/results/farm_generalization_findings.md`.
