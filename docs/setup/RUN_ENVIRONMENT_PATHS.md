# Standing paths and rules of the original setup (21-22 Oct 2026)

- All test bags are on the external drive `/media/<user>/One Touch1/laptop_bags/` (the space in "One Touch1" means every path must be quoted). Never default to `~/Downloads` for bags.
- Folders on that drive: `Cave/cave02_bag/cave02.bag` (+ `Cave/cave02_gt.txt`), `Corridor02/corridor02.bag` (+ `corridor02_gt.txt`), `Long_Corridor_Rosbag/raw_data_core_2023-07-25-03-01-44.bag`, `multifloor/` (earlier `RosBag/multifloor_0|1|2.bag`), `GEODE/` (`stairs_alpha.bag`, `alpha_config.yaml`, `stairs_alpha.txt`). The run script tries `multifloor`, `MultiFloor`, `Multi_Floor`, `multi_floor`, then `RosBag` for the Multi Floor folder.
- Ground truth for Multi Floor: `~/Downloads/SubT_MRS_Hawkins_Multi_Floor_LegRobot/ground_truth_path.csv` (override with `MULTIFLOOR_GT`); the script stops with a clear message if it is missing.
- `fusion_v4/run_fusion_study.sh` defaults `BAGS_ROOT` to that drive path, quotes all ground-truth paths, and finds `multifloor_ate_eval.py` / `clean_restart.sh` next to itself; `setup_sequence.sh` writes quoted `BAG_DIR`/`GT` into `seq.env`. (The master `fusion_v3` script still contains the older `~/switchslam_project` / `~/Downloads` paths.)
- Bag check results: Corridor02, Cave02 and GEODE alpha carry a per-point `time` field that varies over ~0.1 s, so GenZ-LIO can deskew them.
- Settings are not tuned on held-out bags; results are reported as found.
- GenZ-LIO build: needs Eigen 3.4 installed into the container from a host download (the gitlab clone is blocked inside the container).
- Disk: a failed run can leave multi-GB node output; the run script removes stale copies before each run. If a run fails at scoring with "no space left on device", free space and score the saved log offline with `score_run.py`.
- Long batches must be detached from the terminal (`setsid nohup systemd-inhibit ... < /dev/null &`) — on 22 Oct 2026 a batch started with plain `nohup ... &` (output to /dev/null) never got past its first run; the cause was not confirmed, and the detached form above is the one to use.
