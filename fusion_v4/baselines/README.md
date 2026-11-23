# Shared helpers for the stock baselines

Used by every `fusion_v4/stock_<method>/run_<method>.sh`.

| File | What it does |
|---|---|
| `common.sh` | `bl_find_bags_root` (finds `laptop_bags` on the mounted drive), `bl_require_mounted` (refuses bags that are not on a mounted drive, `ALLOW_LOCAL_BAGS=1` overrides), `bl_require_docker` (docker without sudo), `bl_lock` / `bl_unlock` (flock on `~/.replay.lock`, shared with the F35 runner) |
| `test_common.py` | offline tests: mount checks, lock waits for a plain `flock ~/.replay.lock <cmd>` holder, and a stub-docker dry run of `run_liosam.sh` that checks every `docker run` holds the lock and that unmounted bags never reach docker |

Run the tests with `python3 test_common.py` from this folder (needs a tmpfs at `/dev/shm`, as on any Ubuntu).

The lock is a plain `flock` on `$HOME/.replay.lock`. Any other runner, in any language, that takes `flock` on the same file is serialised with these. `REPLAY_LOCK=` points it elsewhere (tests only).
