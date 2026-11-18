# Thesis folder

<sub>Back to the [project page](../../README.md) · [docs index](../README.md)</sub>

M.Tech thesis of Kavinkumar S (CB.EN.P2MFA25004), advisor Dr. G. Sivasankar. Everything that produces the report, its figures and its videos is here.

## Which file is which

| File | Status |
|---|---|
| `Final_Report_5.14_removed.docx` | **Latest report** (76 pages): the owner's edits of 12 Nov on top of the v3 rewrite, Table 5.14 removed, Discussion rewritten |
| `CB.EN.P2MFA25004_Thesis_Report_v3_rewrite.docx` | v3: extended introduction and literature review, flowcharts, new headings and captions (log entry D5) |
| `CB.EN.P2MFA25004_Thesis_Report_v2_clarity.docx` | v2: clarity changes after the guide's comments (D4) |
| `Final_Report_ch3_to_ch4_moved.docx`, `Final_Report_owner_12Nov.docx`, `CB.EN.P2MFA25004_Thesis_Report.docx` | intermediate copies (D1 to D3) |
| `Thesis_Report_Kavinkumar_S.docx`, `Thesis_Report_Kavinkumar_S_F26.docx` (+ `_preview.pdf`) | the earlier drafts |
| [`Report_Corrections_Log.md`](Report_Corrections_Log.md) | every correction, decision and name map (A10: report F35 = repo F26), newest entries last |

## Sub-folders

| Folder | Content |
|---|---|
| [`figure_data/`](figure_data/MANIFEST.md) | the run logs, keyframe maps and ground truth behind the RViz-style images (about 50 MB, with SHA-256 manifest) |
| `figures_final/` | the six F35 renders (`final_MF`, `_LC`, `_C02`, `_CAVE`, `_GEODE`, `_FARM`), the flowcharts (`flowcharts/`), the Gazebo world and Husky pictures, and the replaced renders (`clarity_changes/`) |
| `videos_final/` | one trajectory video per bag (`*_F35_final.mp4`) |
| `scripts/` | figure and video scripts (below) and the v3 report build (`v3_rewrite/`) |
| `work_v3/` | the base file and helper scripts the v3 pipeline needs |
| `work_final_report/` | `edit514.py` (Table 5.14 removal and Discussion rewrite), `chk.py` (contents check) and the owner's input file |

## Redraw the figures (no bags, no ROS)

```bash
cd docs/thesis/scripts
FIG_OUT=/tmp/regen python3 render_final.py MF LC C02 CAVE GEODE FARM
FIG_OUT=/tmp/regen python3 render_aloam_alone.py LC ../figure_data/data/for_claude7/*.csv.gz
```

`render_final.py` draws ground truth (white), the A-LOAM output of the same run (orange), VINS-Mono alone from the same run (red, only where it stays on the plot) and F35 (green), each path aligned to the ground truth on its own (Umeyama SE(3), no scale). The orange line is the pose that F35 feeds back to A-LOAM, not stock A-LOAM. `render_aloam_alone.py` draws the `aft_` pose of any run log of `fusion_v4/run_fusion_study.sh` or `fusion_v4/stock_aloam/`. Own runs: `FIG_DATA=<dir>` with the same layout as `figure_data/`.

Other scripts: `make_final_videos.py` (the videos, needs ffmpeg), `figs3.py` (the print figures of the F35 report), `rrt_f26.py` (hypothesis tests), `rviz_render.py`, `make_all.py`, `figs.py` and `figs2.py` (older renders and figures; they need logs of the first sessions that are not shipped). `build.py`, `build2.py`, `content*.py` and `pages*.py` are the builders of the first two report versions; they read template folders of their own session and are superseded by `v3_rewrite/`.

## Rebuild the v3 report

```bash
bash docs/thesis/scripts/v3_rewrite/setup_workdir.sh      # copies the inputs to /tmp/w and /tmp/w/v3
cd /tmp/w/v3 && bash pipe.sh                              # builds final.docx and a PDF
```

Needs python-docx, lxml, LibreOffice and poppler. The build reproduces the v3 text (464 paragraphs) and 77 pages. To get the latest report, run `work_final_report/edit514.py <v3 or owner input>.docx <out>.docx` on the result.
