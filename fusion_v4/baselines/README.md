# Shared helpers for the stock baselines

Used by every `fusion_v4/stock_<method>/run_<method>.sh`.

| File | What it does |
|---|---|
| `common.sh` | `bl_find_bags_root` (finds `laptop_bags` on the mounted drive), `bl_require_mounted` (refuses bags that are not on a mounted drive, `ALLOW_LOCAL_BAGS=1` overrides), `bl_require_docker` (docker without sudo), `bl_lock` / `bl_unlock` (flock on `~/.replay.lock`, shared with the F35 runner) |
| `test_common.py` | offline tests: mount checks, lock waits for a plain `flock ~/.replay.lock <cmd>` holder, and a stub-docker dry run of `run_liosam.sh` that checks every `docker run` holds the lock and that unmounted bags never reach docker |

Run the tests with `python3 test_common.py` from this folder (needs a tmpfs at `/dev/shm`, as on any Ubuntu).

The lock is a plain `flock` on `$HOME/.replay.lock`. Any other runner, in any language, that takes `flock` on the same file is serialised with these. `REPLAY_LOCK=` points it elsewhere (tests only).

| File | What it does |
|---|---|
| `check_isa.sh` | scans compiled binaries for AVX-512 (neither the laptop's Ryzen 5 5600H nor the desktop's i7-12700 has it); prints the count of AVX/AVX2 instructions too, 0 means a plain x86-64 build |
| `save_image.sh` | desktop: `docker save` to `<drive>/docker_images/<image>_<commit8>.tar.gz` with `.sha256`, `.size`, `.commit` |
| `load_image.sh` | laptop: loads from the drive, a given file or `ssh://user@desktop`; checks the checksum, refuses when the free disk space is smaller than the image, checks the tag and the commit label. Never builds |
| `make_slice.py`, `prep_pc_transfer.sh` | slices of the bags for the desktop, transfer folder on the drive |
| `test_tools.py` | offline tests of `check_isa.sh` and `load_image.sh` |

## Camera rectification (MEI to pinhole)

`mei_model.py` (projection of the camodocal MEI model, rectification maps), `mei_rectify.py` (ROS node, used inside the R3LIVE image, reusable for R2LIVE and FAST-LIVO) and `test_rectify.py`. The output image has the size and principal point of the input and no distortion, so the camera-IMU extrinsic of the original camera is also the extrinsic of the rectified one.
