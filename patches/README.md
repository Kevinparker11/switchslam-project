# patches/: modifications of third-party code

`aloam_vins/` holds the scripts that modify A-LOAM and VINS-Mono inside the containers (Hessian export on `/laser_hessian`, buffer and timestamp fixes for the feedback loop, VINS-Mono Hessian export). Descriptions, targets and application order: [`../docs/setup/INSTALL.md`](../docs/setup/INSTALL.md) section 3. GenZ-LIO's patch is `../fusion_v4/genz/patch_genz_information.py`.
