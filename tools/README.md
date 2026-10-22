# tools/

| Script | Run on | Purpose |
|---|---|---|
| `capture_environment.sh` | the working laptop | records OS/Docker/ROS versions, image history, source revisions and local modifications, and the files that exist only inside the containers. The capture of 22 Oct 2026 is stored in `docs/setup/` |
| `export_images.sh` | the working laptop | commits both containers and archives them together with the two bind-mounted catkin workspaces (`docs/setup/INSTALL.md`, section 2A) |
| `import_images.sh` | the new PC | loads the archive, creates the `vins_bridge` network and starts both containers with the original mounts |
