# ot_study: offline replay study of the orientation-tensor (OT) channel (28 Oct 2026)
Results and reading: `docs/results/OT_Channel_Study.md`. Selection rules, written before each stage: `PREREG.md`.
- `node_harness.py LOG.csv KEYFRAMES.npz OUTDIR` drives the real `fusion_node_v2` callbacks (rospy and messages stubbed) with a logged run
  and its keyframe scans; the node settings come from the environment (as live). `FAULT=1` injects the stage-3 solver fault.
  `FUSION_DIR` points at the fusion_v4 folder (default: the sandbox copy).
- `batch.sh TAG "SETTINGS"` runs it on the 12 logs (MF F8 kf 1-6, LC F8 kf 1-3, C02 F8 kf 1-3); `summ.py TAGS...` scores them
  (ATE RMSE full span, Umeyama SE(3), no scale); `be_batch.sh TAG` runs the loop back end (none / iso / ot) on a tag; `be_summ.py`.
- Data paths are those of the analysis sandbox (/home/claude/data_in*, uploads); on another machine edit the LOGS list in batch.sh / be_batch.sh.
