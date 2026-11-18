# Documentation index

<sub>Back to the [project page](../README.md)</sub>

## Start here

| If you want to... | Read |
|---|---|
| read the thesis, its figures and the report scripts | [thesis/README.md](thesis/README.md) |
| set up a new PC | [setup/INSTALL.md](setup/INSTALL.md) |
| see exactly what the original machine had (versions, revisions, mounts) | [setup/ENVIRONMENT.md](setup/ENVIRONMENT.md) |
| find and place the bags and ground truth | [setup/DATASETS.md](setup/DATASETS.md) |
| repeat a run, a table or a figure | [setup/REPRODUCE.md](setup/REPRODUCE.md) |
| understand F0 to F16 and G0 to G17 and see all numbers up to 21 Oct | [results/Configurations_Explained_and_Results_To_Date.md](results/Configurations_Explained_and_Results_To_Date.md) |
| see the final version (F35 in the report, tag `F26` in the repo) on every bag | [results/F35_All_Bags_Test.md](results/F35_All_Bags_Test.md) |

**Names.** The report calls the final version F35; the repo files, run tags and batch scripts call it F26. The channels-only variant is F35 in the repo and F26 in the report. Details: [thesis/Report_Corrections_Log.md](thesis/Report_Corrections_Log.md), entry A10.

## setup/

Installation, datasets, reproduction commands. Path rules: [setup/RUN_ENVIRONMENT_PATHS.md](setup/RUN_ENVIRONMENT_PATHS.md).

## results/ (what was found)

### Final method: F20 to F35 (Oct 29 to Nov 11, thesis versions)

| Document | What it is |
|---|---|
| [OT_Channel_Study.md](results/OT_Channel_Study.md) | R + T + OT on the A-LOAM stack: how to use the orientation-tensor channel (study of 28 Oct 2026) |
| [OT_Channel_Round2.md](results/OT_Channel_Round2.md) | OT channel, round 2: separate third weight, other feasible rules, generality (2026-10-29) |
| [G20_OT_Results.md](results/G20_OT_Results.md) | G20 + OT (orientation-tensor channel on the GenZ-LIO stack): results of the pre-registered replay (2026-10-29) |
| [F20_Live_Results.md](results/F20_Live_Results.md) | F20 live results (batch of 2026-10-29, scored against the criteria pre-registered in OT_Channel_Study.md section 6) |
| [F22_Handover_Anchor.md](results/F22_Handover_Anchor.md) | F22 / F23: anchored WARMUP -> FUSED handover (3 Nov 2026) |
| [F24_Predict_Guard.md](results/F24_Predict_Guard.md) | F24: no VINS motion in A-LOAM's mapping guess while VINS is failing (3 Nov 2026) |
| [F24_Live_Corridor02_Cave02_GEODE.md](results/F24_Live_Corridor02_Cave02_GEODE.md) | F24, one live run each on Corridor02, Cave02 and GEODE stairs (4 Nov 2026, laptop, front end only, no loop closure) |
| [F24_Coverage_Run_and_Missing.md](results/F24_Coverage_Run_and_Missing.md) | F24: results to date on every dataset, and what has not been run (6 Nov 2026) |
| [F25_Fixes.md](results/F25_Fixes.md) | F25A: one fix to F24 from the Cave02 / GEODE logs, and one idea that failed (4 Nov 2026) |
| [F26_Status_Guess.md](results/F26_Status_Guess.md) | F26 and F27: two changes to the scan-to-map guess of F24 (6 Nov 2026) - built, not yet run live |
| [F26_Rotation_Weight_Replay_Test.md](results/F26_Rotation_Weight_Replay_Test.md) | F26: does a LiDAR rotation weight (the R channel) change the output? Open-loop replay, rules written before any run (10 Nov 2026) |
| [F24_vs_F26_Tables.md](results/F24_vs_F26_Tables.md) | F24 against F26, every bag (6 Nov 2026) |
| [F24_to_F27_All_Bags.md](results/F24_to_F27_All_Bags.md) | F24 to F27: versions and every tested value on every bag (6 Nov 2026) |
| [F30_Switch_Structure_Our_Detection.md](results/F30_Switch_Structure_Our_Detection.md) | F30: Switch-SLAM's structure and output, our detection only (10 Nov 2026), rules written before any run |
| [F31_LiDAR_Primary_Status_Guess.md](results/F31_LiDAR_Primary_Status_Guess.md) | F31 (named F31 until 10 Nov 2026, never run): F26's guess with LiDAR as the primary sensor, no remap |
| [F32_F30_With_F24_VINS_Checks.md](results/F32_F30_With_F24_VINS_Checks.md) | F32: F30 with F24's VINS-Mono failure checks (10 Nov 2026), rules written before any run |
| [F33_F32_With_VINS_Rotation.md](results/F33_F32_With_VINS_Rotation.md) | F33: F32 with the output rotation taken from VINS-Mono (10 Nov 2026), rules written before any run |
| [F34_F33_With_Split_Eq15_And_SAH.md](results/F34_F33_With_Split_Eq15_And_SAH.md) | F34: F33 with a split Eq. 15 and the structure-anchored heading (10 Nov 2026), rules written before the run |
| [F35_Guess_With_Own_Channels.md](results/F35_Guess_With_Own_Channels.md) | F35: F26 with the starting guess decided by our own channels (10 Nov 2026), rules written before any run |
| [F35_All_Bags_Test.md](results/F35_All_Bags_Test.md) | F35 on all bags: rules written before the runs (10 Nov 2026) |
| [F35_Farm_L_Live.md](results/F35_Farm_L_Live.md) | F35 on the Farm L route, live in Gazebo (protocol written 10 Nov 2026, before the run) |
| [Cave02_F24_vs_F8_F16.md](results/Cave02_F24_vs_F8_F16.md) | Cave02: where F24 (7.55) differs from the earlier F8 / F16 runs (4.3 to 5.1), from the logged runs (6 Nov 2026) |
| [Cave02_GEODE_Error_Diagnosis.md](results/Cave02_GEODE_Error_Diagnosis.md) | Cave02 and GEODE: where the F24 error comes from (9 Nov 2026, read from the saved switching logs) |

### Earlier systems: F0 to F16, SAH and the GenZ-LIO stack (Oct 13 to 29)

| Document | What it is |
|---|---|
| [Configurations_Explained_and_Results_To_Date.md](results/Configurations_Explained_and_Results_To_Date.md) | Configurations explained, and all results to date (21 Oct 2026) |
| [complete_test_record.md](results/complete_test_record.md) | SwitchSLAM QR — Complete Test Record |
| [Complete_Test_Record_Link.md](results/Complete_Test_Record_Link.md) | Complete test record (updated 19 Oct 2026) |
| [Master_Project_Report_Link.md](results/Master_Project_Report_Link.md) | Master project report (19 Oct 2026) |
| [update_2026-10-14_batch5.md](results/update_2026-10-14_batch5.md) | Update, 14 October 2026 (batch 5: F8 recordings 4-6 and LiDAR-only + loops; C_T = 0.03 fixed in advance) |
| [Multifloor_Threshold_Study_Results.md](results/Multifloor_Threshold_Study_Results.md) | Multi Floor threshold study: live results (run 1 of each, 2026-10-13) |
| [Yaw_Drift_Diagnosis_and_Next_Direction.md](results/Yaw_Drift_Diagnosis_and_Next_Direction.md) | Where the error comes from, and what to do next (17 October 2026) |
| [Structure_Heading_Development_Results.md](results/Structure_Heading_Development_Results.md) | Structure-anchored heading (SAH): development results on all three sequences (17 October 2026) |
| [SAH_Live_Results_F16.md](results/SAH_Live_Results_F16.md) | SAH live results (config F16), all three sequences (17-19 October 2026) |
| [Cave02_Control_Results.md](results/Cave02_Control_Results.md) | Cave02 control: SAH must switch itself off (19-20 October 2026) |
| [Improvement_Replay_Tests.md](results/Improvement_Replay_Tests.md) | Offline improvement tests (20 October 2026) |
| [Front_End_Upgrade_GenZ_fusion_v4.md](results/Front_End_Upgrade_GenZ_fusion_v4.md) | fusion_v4: the master system with GenZ-LIO in place of A-LOAM (21 Oct 2026) |
| [GenZ_fusion_v4_MultiFloor_Results.md](results/GenZ_fusion_v4_MultiFloor_Results.md) | fusion_v4 (GenZ-LIO front end): Multi Floor results and frozen weights (21 Oct 2026) |
| [GenZ_fusion_v4_HeldOut_Results.md](results/GenZ_fusion_v4_HeldOut_Results.md) | fusion_v4 (GenZ-LIO front end): held-out result on Corridor02 and Cave02 (21-22 Oct 2026) |
| [GenZ_fusion_v4_RateControl_and_GEODE_Results.md](results/GenZ_fusion_v4_RateControl_and_GEODE_Results.md) | fusion_v4: replay-rate controls (Corridor02, Cave02) and the GEODE stairs test (22 Oct 2026) |
| [GenZ_fusion_v4_VIO_Consistency_Results.md](results/GenZ_fusion_v4_VIO_Consistency_Results.md) | fusion_v4: same R / T / additional-T structure, with a VINS consistency check (G18, G19), 22 Oct 2026 |
| [GenZ_fusion_v4_G20_Universal_Fix.md](results/GenZ_fusion_v4_G20_Universal_Fix.md) | G20: a safety fix that keeps every good result and removes two failure modes (24 Oct 2026) |
| [Gap_Rule_Test_Protocol.md](results/Gap_Rule_Test_Protocol.md) | LiDAR-gap rule (G23): development evidence and the test fixed before it is run (26 Oct 2026) |
| [Gap_Test_Results.md](results/Gap_Test_Results.md) | Gap rule (G23) against G20: results of the test fixed in `Gap_Rule_Test_Protocol.md` (26 Oct 2026) |
| [IgLIO_Feasibility_Protocol.md](results/IgLIO_Feasibility_Protocol.md) | iG-LIO as a third LiDAR front end: desk check, staged feasibility test and the full test (27 Oct 2026) |
| [ChannelT_Mini_Test_Protocol.md](results/ChannelT_Mini_Test_Protocol.md) | Additional T (orientation-tensor channel): a very short synthetic test (protocol written 28 Oct 2026, before any run) |
| [ChannelT_MultiFloor_Single_Test.md](results/ChannelT_MultiFloor_Single_Test.md) | Additional T in the fusion: one live run on the A-LOAM stack (protocol written 28 Oct 2026, before any run) |
| [ChannelT_Farm_Single_Test.md](results/ChannelT_Farm_Single_Test.md) | Additional T: one live test in the farm (protocol written 28 Oct 2026, before the run) |
| [R_Channel_Rotation_Aware_Test_Protocol.md](results/R_Channel_Rotation_Aware_Test_Protocol.md) | Test of the full R + T + T+ structure on the A-LOAM stack: rotation-aware R channel (design B, "F17b") |
| [farm_generalization_findings.md](results/farm_generalization_findings.md) | Farm/panels generalization check: do Multi Floor's two Hessian-scale disparities hold? |

### Fault injection and statistics

| Document | What it is |
|---|---|
| [Fault_Injection_Protocol.md](results/Fault_Injection_Protocol.md) | Sensor-outage campaign on real recordings: protocol written before any run (25 Oct 2026) |
| [Outage_Campaign_Results.md](results/Outage_Campaign_Results.md) | Sensor-outage campaign: results (run 26 Oct 2026, laptop, 00:25 to 07:15 IST) |
| [Statistical_Tests_Multiple_Runs.md](results/Statistical_Tests_Multiple_Runs.md) | Statistical tests across multiple runs (21 Oct 2026) |
| [RRT_Style_Statistical_Tests.md](results/RRT_Style_Statistical_Tests.md) | Statistical evaluation in the style of the Hybrid-RRT* paper (27 Oct 2026) |
| [RTS_Table3_Hypothesis_Tests.md](results/RTS_Table3_Hypothesis_Tests.md) | Table 3 of the Hybrid-RRT* paper, for this project (27 Oct 2026) |

### Comparison with published results

| Document | What it is |
|---|---|
| [SwitchSLAM_TableII_Verified.md](results/SwitchSLAM_TableII_Verified.md) | Switch-SLAM Table I and Table II, read from the page images of the paper (6 Nov 2026) |
| [Published_Comparison_All_Datasets.md](results/Published_Comparison_All_Datasets.md) | Our configurations against published results, all sequences (21 October 2026) |
| [COMPARISON_RESULTS.md](results/COMPARISON_RESULTS.md) | Old vs new: comparison test results |
| [Report_Comparison_Table_Draft.md](results/Report_Comparison_Table_Draft.md) | DRAFT: comparison with Switch-SLAM, front end only, A-LOAM + VINS-Mono (6 Nov 2026) |
| [Novelty_Scan_28Oct.md](results/Novelty_Scan_28Oct.md) | Is F8 / F16 novel? Literature scan of 28 October 2026 |

### Readiness notes

| Document | What it is |
|---|---|
| [Handheld_Readiness.md](results/Handheld_Readiness.md) | Handheld (LVI-SAM dataset): what exists and what is needed before F26 / F35 runs (11 Nov 2026) |
| [Farm_L_Shape_Test_Protocol.md](results/Farm_L_Shape_Test_Protocol.md) | Farm L-shape test: the current method on the route used for the Switch-SLAM-style replication (protocol written 27 Oct 2026, before any run) |

## protocols/ (rules written before the runs)

| Document | What it is |
|---|---|
| [Corridor02_Held_Out_Test_Protocol.md](protocols/Corridor02_Held_Out_Test_Protocol.md) | Corridor02 held-out test: protocol written before the scored runs (15 October 2026) |
| [Dataset_Test_Plan.md](protocols/Dataset_Test_Plan.md) | Test datasets: what to run, where to get it, and how far to trust the ground truth |
| [F24_Upgrade_Replay_Screen.md](protocols/F24_Upgrade_Replay_Screen.md) | F24 upgrade screen: offline replay of F24 variants on saved logs (rules written 9 Nov 2026, before any variant was replayed) |
| [Farm_Forward_Camera_Test.md](protocols/Farm_Forward_Camera_Test.md) | Farm L route with the camera pointing along the direction of motion: test protocol, written 7 Nov 2026, before the run |
| [FastRotate_Plane_Test_Protocol.md](protocols/FastRotate_Plane_Test_Protocol.md) | Fast Rotate and Plane (Switch-SLAM's two other Gazebo datasets): test protocol, written 6 Nov 2026, before any run |
| [Handheld_Test_Protocol.md](protocols/Handheld_Test_Protocol.md) | Handheld (LVI-SAM dataset): F5, F26, F35 and SW replays, rules written before any run (11 Nov 2026) |
| [Least_Error_4h_Protocol.md](protocols/Least_Error_4h_Protocol.md) | Least-error 4-hour queue on Cave02 and GEODE: rules fixed before the runs (9 Nov 2026) |
| [Live_Gazebo_Working_Commands.md](protocols/Live_Gazebo_Working_Commands.md) | Live Gazebo working commands (kept here so they are not searched for again) |
| [Long_Corridor_Setup_Log.md](protocols/Long_Corridor_Setup_Log.md) | Long Corridor: what the downloaded files turned out to be |
| [Plane_Manual_Route_Test.md](protocols/Plane_Manual_Route_Test.md) | Plane, second recreation: spawn at the end of the L, manual route, two replays (11 Nov 2026, rules written before any run) |
| [SwitchSLAM_Exact_Replica.md](protocols/SwitchSLAM_Exact_Replica.md) | Switch-SLAM as published: our implementation, what it is, what it is not (4 Nov 2026) |
| [Switch_SLAM_With_Our_Detection_Protocol.md](protocols/Switch_SLAM_With_Our_Detection_Protocol.md) | Switch-SLAM structure with our detection (R, T, additional T): design and test rules, written before any run (10 Nov 2026) |

## planning/

| Document | What it is |
|---|---|
| [Novelty_and_Research_Gap.md](planning/Novelty_and_Research_Gap.md) | Novelty, research gap and evidence |
| [Plan_Beating_Published_Results.md](planning/Plan_Beating_Published_Results.md) | Plan: beating published results (Multi Floor, Long Corridor) |
| [Review_Paper_Prompt.md](planning/Review_Paper_Prompt.md) | Prompt: comprehensive theoretical review paper on LiDAR degeneracy (paste everything below into a new chat) |
| [Thesis_Methodology_Action_Plan.md](planning/Thesis_Methodology_Action_Plan.md) | Thesis methodology: action plan after the synthetic comparison |
| [Two_Machine_Plan_2026-10-22.md](planning/Two_Machine_Plan_2026-10-22.md) | Status and two-machine test plan (22 Oct 2026) |

## research/

Literature and method derivations, one folder per topic with a `README.md`: `method_proofs/` (degeneracy decisions D1 to D9), `bingham_channel_tests/`, `research_gaps/`, `lidar_only_datasets/`, `datasets_with_ground_truth/`, `intro_references/`.

## paper/

`main.tex` (8 pages), `refs.bib`, the figure scripts `make_traj_figs.py` and `make_static_figs.py` (they read `thesis/figure_data/`), the built `main.pdf` and an Overleaf bundle.
