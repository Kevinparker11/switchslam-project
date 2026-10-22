# Documentation index

## Start here
| If you want to... | Read |
|---|---|
| set up a new PC | [setup/INSTALL.md](setup/INSTALL.md) |
| see exactly what the original machine had (versions, revisions, mounts) | [setup/ENVIRONMENT.md](setup/ENVIRONMENT.md) |
| find / place the bags and ground truth | [setup/DATASETS.md](setup/DATASETS.md) |
| repeat a run or a table | [setup/REPRODUCE.md](setup/REPRODUCE.md) |
| understand F0...F16 and G0...G17 and see all numbers | [results/Configurations_Explained_and_Results_To_Date.md](results/Configurations_Explained_and_Results_To_Date.md) |

## setup/
Installation, datasets, reproduction commands. Standing path rules are in [setup/RUN_ENVIRONMENT_PATHS.md](setup/RUN_ENVIRONMENT_PATHS.md).

## results/ (what was found, newest first)
| Document | Content |
|---|---|
| GenZ_fusion_v4_HeldOut_Results.md | **22 Oct:** frozen GenZ weights on Corridor02 and Cave02 did not generalise; diagnosis |
| Statistical_Tests_Multiple_Runs.md | hypothesis tests across runs (Welch, Mann-Whitney, bootstrap, chi-square variance, Kruskal-Wallis) |
| GenZ_fusion_v4_MultiFloor_Results.md | GenZ-LIO front end on Multi Floor; frozen weights; live G17 0.293 m |
| Configurations_Explained_and_Results_To_Date.md | every configuration, every result |
| Front_End_Upgrade_GenZ_fusion_v4.md | why GenZ-LIO, what was added, run order |
| Cave02_Control_Results.md | clean control sequence |
| Improvement_Replay_Tests.md | offline replay experiments (warm-up, loop gate, rotation weight, alternative T channel) |
| SAH_Live_Results_F16.md | SAH (structure-anchored heading) live results |
| Structure_Heading_Development_Results.md, Yaw_Drift_Diagnosis_and_Next_Direction.md | where the error comes from; SAH design and development |
| Published_Comparison_All_Datasets.md, COMPARISON_RESULTS.md | our numbers against published ones |
| Multifloor_Threshold_Study_Results.md | the 13 Oct threshold study |
| complete_test_record.md, Complete_Test_Record_Link.md, Master_Project_Report_Link.md | full test record and master report |
| update_2026-10-14_batch5.md, farm_generalization_findings.md | dated updates |

## protocols/ and planning/
Held-out test protocol, dataset test plan, long-corridor setup log; the thesis plan, the plan to beat published results, novelty and research gap.

## research/
Literature and method derivations, one folder per topic with a `README.md`: `method_proofs/` (provable degeneracy decisions D1-D9), `bingham_channel_tests/`, `research_gaps/`, `lidar_only_datasets/`, `datasets_with_ground_truth/`, `intro_references/`.
