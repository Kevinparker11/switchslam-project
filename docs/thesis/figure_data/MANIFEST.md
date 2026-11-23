# Figure inputs

Everything `docs/thesis/scripts/render_final.py` and `render_aloam_alone.py` need to redraw the RViz-style images of the thesis, with no bags and no ROS. Point the scripts elsewhere with `FIG_DATA=<dir>`; pictures go to `$FIG_OUT` (default `figure_data/img`).

```bash
cd docs/thesis/scripts
FIG_OUT=/tmp/regen python3 render_final.py MF LC C02 CAVE GEODE FARM     # the six F35 images (pixel-identical to ../figures_final/)
FIG_OUT=/tmp/regen python3 render_aloam_alone.py LC ../figure_data/data/for_claude7/*.csv.gz   # A-LOAM alone, Long Corridor
FIG_OUT=/tmp/regen python3 render_final_stock.py MF LC C02 CAVE GEODE FARM       # F35 with the stock A-LOAM line
```

**Names.** The repo calls the final version `F26` (tag `F26_kf_run1`); the thesis report calls it F35. Same runs, same numbers (see `docs/thesis/Report_Corrections_Log.md`, A10).
**Logs** are `fusion_v4/fusion_node_v2.py` output (`switching_log_v2_<tag>.csv`, gzipped here); **keyframe maps** (`.npz`) were recorded with `RECORD_KF=1` and are kept in git by an exception in `.gitignore`.
A new run recorded on your own machine (including the stock A-LOAM runs of `fusion_v4/stock_aloam/`) drops in the same way: same file names, same columns.

| File | Kind | Run | Replay rate | Bytes | SHA-256 |
|---|---|---|---|---|---|
| `data/for_claude14/cave02_gt.txt` | ground truth | ground truth: SubT-MRS Cave02 | - | 420841 | `0783f8a121aa0d55a0ea5e8a13c118723535929c89fab994607fb9bcea101f2b` |
| `data/for_claude7/switching_log_v2_F5_run1.csv.gz` | run log | Long Corridor, A-LOAM alone (configuration F5), runs 1 to 3 | 1.0x | 1149380 | `b0bcb6e0f4cdeb1ae06d8e8af96e1b596ea0067dc7d2e60cd17c89a941e51d77` |
| `data/for_claude7/switching_log_v2_F5_run2.csv.gz` | run log | Long Corridor, A-LOAM alone (configuration F5), runs 1 to 3 | 1.0x | 1154209 | `8dc545d35a4dd623a6336958e22fed4ca865ebf94ff485dd1bb1e34e6f6d4cdd` |
| `data/for_claude7/switching_log_v2_F5_run3.csv.gz` | run log | Long Corridor, A-LOAM alone (configuration F5), runs 1 to 3 | 1.0x | 1154768 | `b9bfa5c066122b39724fdf825f2c8e96eb089938dc853384cde72d9b37a7e1e6` |
| `data/geode/gt_stairs_alpha.txt` | ground truth | ground truth: GEODE stairs alpha | - | 502174 | `94b2cb2d9e3f4e4bbfde0932ed3adf6b314b649b690c9e13d6f610c719d750f6` |
| `data/gt/c02_gt.txt` | ground truth | ground truth: SubT-MRS sequences (Multi Floor, Long Corridor, Corridor02) | - | 475805 | `cddb6739230ded86c57412e768e071e5cd6d62a5de5ff310618032ca2e38be0a` |
| `data/gt/lc_gt.txt` | ground truth | ground truth: SubT-MRS sequences (Multi Floor, Long Corridor, Corridor02) | - | 123311 | `3cabcc78ecea4d991aa6e3eddb811cefc4fdacf5f3387b98950fa09ad338dd03` |
| `data/gt/mf_gt_a.csv` | ground truth | ground truth: SubT-MRS sequences (Multi Floor, Long Corridor, Corridor02) | - | 176537 | `08af8507f70b9bdf5e788138aa257212356ed5e7ce882ab98d24716ae609ca12` |
| `f24cave/C02_keyframes_F26_kf_run1.npz` | keyframe map | Corridor02, F35 live run 1 | 0.33x | 9064601 | `4782e65981fdcfcc3f48853eb082af0dec203dc4a15bff14d1b53a17d09e99e9` |
| `f24cave/C02_switching_log_v2_F26_kf_run1.csv.gz` | run log | Corridor02, F35 live run 1 | 0.33x | 4432892 | `147690213b67e513247537a540b90e2a82d0b49fdc254d71adbfd3263b12c75c` |
| `f24cave/CAVE_keyframes_F26_kf_run1.npz` | keyframe map | Cave02, F35 live run 1 | 0.5x | 6441317 | `d7762f55f79b9cd051376a68d9026a555b2775193de2b5f89e42ba12d95c80e2` |
| `f24cave/CAVE_switching_log_v2_F26_kf_run1.csv.gz` | run log | Cave02, F35 live run 1 | 0.5x | 4805867 | `1639431a0c8e72c917e2e1aceee4e47a13c4fbf6cb10f1b2c82bdc312251710d` |
| `f24cave/GEODE_keyframes_F26_kf_run1.npz` | keyframe map | GEODE stairs, F35 live run 1 | 0.5x | 4351450 | `3baa7ccf94e8a478fe943c5fa7d1fe853f96483d60361abed6496a49f0f9cbed` |
| `f24cave/GEODE_switching_log_v2_F26_kf_run1.csv.gz` | run log | GEODE stairs, F35 live run 1 | 0.5x | 1575541 | `2a68c5ee6f6b78dec6b452e94524976029c8ec616cbfcc0bf47217942c14e1db` |
| `f24cave/LC_keyframes_F26_kf_run1.npz` | keyframe map | Long Corridor, F35 live run 1 | 1.0x | 4314768 | `d5cb8fd50cf12f1a30c0c65be1038cd58db601dc1ebfdd49592cad4ffac2bbbd` |
| `f24cave/LC_switching_log_v2_F26_kf_run1.csv.gz` | run log | Long Corridor, F35 live run 1 | 1.0x | 1508087 | `6c830c7451d91522e81a100c3be30b6e85b8ec5abc80d1078a51b5e8c9924816` |
| `f24cave/MF_keyframes_F26_kf_run1.npz` | keyframe map | Multi Floor, F35 live run 1 (repo tag F26_kf_run1) | 1.0x | 5339808 | `3547df8e51200f9f5e5ae7bb9a4c7c48799bd38d41a3da0606458679b57c9d5c` |
| `f24cave/MF_switching_log_v2_F26_kf_run1.csv.gz` | run log | Multi Floor, F35 live run 1 (repo tag F26_kf_run1) | 1.0x | 2191819 | `d507e63101d588248f210a2c33472291e59c640f70f706c1a6baf17b0d2097cc` |
| `f26z/farm_f26/gt_f26.txt` | ground truth | Farm L route, Gazebo, F35 live run (tag F26_fwdrgb_live1, forward RGB camera) | live | 619030 | `80237da9d965d42b231c233ff6ee27ee3f715c8c5aa5b8d5b2cf8b1b81e09390` |
| `f26z/farm_f26/switching_log_v2_F26_fwdrgb_live1.csv.gz` | run log | Farm L route, Gazebo, F35 live run (tag F26_fwdrgb_live1, forward RGB camera) | live | 1971426 | `534722f1bee9f5f5e8b11ec12c5ecd3fd82d4496d1e31e51e3c1b81553114cca` |
| `stock/MF_stock.csv.gz` | run log | MF, stock A-LOAM run 1 (`run_stock_aloam.sh`, `aft_` columns = stock A-LOAM pose) | 1.0x | 1422488 | `26d08e065f6c1a5f811cc803ecb6df9bc79e8d348b11a8eb13b8f0da281536a5` |
| `stock/LC_stock.csv.gz` | run log | LC, stock A-LOAM run 1 (`run_stock_aloam.sh`, `aft_` columns = stock A-LOAM pose) | 1.0x | 1158957 | `0bfde9147f8c594cb05a14f199a1407fa972a59a07cc47c39e0c8c809f7a3dfe` |
| `stock/C02_stock.csv.gz` | run log | C02, stock A-LOAM run 1 (`run_stock_aloam.sh`, `aft_` columns = stock A-LOAM pose) | 0.33x | 3570137 | `76a2080f28b4c0a069b80f1a59f10ca47c7527f3cb035d03db85eca1da85ad27` |
| `stock/CAVE_stock.csv.gz` | run log | CAVE, stock A-LOAM run 1 (`run_stock_aloam.sh`, `aft_` columns = stock A-LOAM pose) | 0.5x | 3920382 | `0c36a85b9ed4bfd66035cb102ead34ef10c2c3ad1e1b1b7f1795feed048bc357` |
| `stock/GEODE_stock.csv.gz` | run log | GEODE, stock A-LOAM run 1 (`run_stock_aloam.sh`, `aft_` columns = stock A-LOAM pose) | 0.5x | 1394272 | `bcac1a521dbd426c7a908365399ca548453741d4153a79d68ed3bc33d1b320e3` |
| `stock/FARM_stock_aft.txt.gz` | run log | FARM, unmodified A-LOAM scan-to-map output (`/aft_mapped_to_init`), live Gazebo run, `fusion_v4/stock_aloam/farm_stock.sh`, TUM text | live | 127343 | `52c0586c8f65e949c179be6cc78074d7aef417731c9079da3caaa502dd2505d7` |
| `stock/FARM_stock_gt.txt.gz` | ground truth | FARM, Gazebo ground truth of that run, TUM text | live | 161605 | `0b787f1581b9006f23a330cbad65aac77488567228780a8295a2518e756e2dd6` |
