# patches/: modifications of third-party code

`aloam_vins/` holds the scripts that modify A-LOAM and VINS-Mono inside the containers (Hessian export on `/laser_hessian`, buffer and timestamp fixes for the feedback loop, VINS-Mono Hessian export). Descriptions, targets and application order: [`../docs/setup/INSTALL.md`](../docs/setup/INSTALL.md) section 3. GenZ-LIO's patch is `../fusion_v4/genz/patch_genz_information.py`.

## captured_diffs/
The authoritative record of the local changes made to A-LOAM (`e51f88c`) and VINS-Mono (`90dabb5`) on the working machine, taken with `git diff` on 22 Oct 2026 (rviz layout and a binary mask image left out). Apply on a fresh checkout with `git apply`. See `docs/setup/ENVIRONMENT.md`.
