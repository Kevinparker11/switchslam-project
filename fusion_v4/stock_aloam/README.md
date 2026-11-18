# Stock A-LOAM runs

The unmodified A-LOAM on a bag, through the same pipeline as every other run (same containers, bag, replay rate, ground truth and logging). One change: the remap `/laser_odom_to_init -> /switch_fused_pose` is removed from the sequence's A-LOAM launch file, so the mapping node takes its initial guess from A-LOAM's own scan-to-scan odometry. Configuration F5 only starts the logger node; nothing it publishes reaches A-LOAM. VINS-Mono runs beside it and influences nothing.

| File | Role |
|---|---|
| `run_stock_aloam.sh` | `REPEAT=1 PLAY_RATE=<rate> ./stock_aloam/run_stock_aloam.sh <name> <seq.env or ->`; starts the containers if stopped, swaps the launch file, runs, restores the launch file, scores |
| `score_aft.py` | full-span ATE of the `aft_` columns of a log (Umeyama SE(3), no scale) |

Commands per sequence and replay rates: [`docs/setup/REPRODUCE.md`](../../docs/setup/REPRODUCE.md). Draw a result with `docs/thesis/scripts/render_aloam_alone.py`.

Difference to "A-LOAM alone (F5)" in the thesis: F5 runs through the fusion node, which hands A-LOAM its own last pose as the guess of each scan (no motion model). Stock A-LOAM uses the scan-to-scan odometry. Done so far: Long Corridor, one run, 13.25 / 24.29 m (RMSE / max).
