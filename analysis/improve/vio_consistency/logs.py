# Recordings used in the study: name, sequence, log, keyframes, ground truth, extrinsics ("-" = Multi Floor default).
# Paths are those of the analysis machine; the logs of 22 Oct are in results_data/2026-10-22/ (gzipped), the Multi Floor
# GenZ-stack logs are the fusion_v4 Multi Floor runs of 21 Oct.
S="/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad"
R="/home/claude/switchslam-project"
U="/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6"
MFGT="/tmp/claude-0/g0mf/ground_truth_path.csv"
GEO=U+"/b6b27018-stairs_alpha.txt"; GX=R+"/fusion_v4/geode/geode_extrinsics.yaml"
LOGS = [  # name, seq, log, keyframes, gt, extrinsics
 ("MF-G17r1","MF","/tmp/claude-0/g17/switching_log_v2_G17_kf_run1.csv","/tmp/claude-0/g17/keyframes_G17_kf_run1.npz",MFGT,"-"),
 ("MF-G0r1","MF","/tmp/claude-0/g0mf/switching_log_v2_G0_kf_run1.csv","/tmp/claude-0/g0mf/keyframes_G0_kf_run1.npz",MFGT,"-"),
 ("MF-G0r2","MF","/tmp/claude-0/g0mf/switching_log_v2_G0_kf_run2.csv","/tmp/claude-0/g0mf/keyframes_G0_kf_run2.npz",MFGT,"-"),
 ("MF-G0r3","MF","/tmp/claude-0/g0mf/switching_log_v2_G0_kf_run3.csv","/tmp/claude-0/g0mf/keyframes_G0_kf_run3.npz",MFGT,"-"),
 ("C02-G17","C02",S+"/lap/runs_corridor2_rate033_L_genz/switching_log_v2_G17_kf_run1.csv",S+"/lap/runs_corridor2_rate033_L_genz/keyframes_G17_kf_run1.npz",U+"/db62c9b7-corridor02_gt.txt",R+"/configs/corridor2/corridor2_extrinsics.yaml"),
 ("CAVE-G17","CAVE",S+"/lap/runs_cave02_rate05_L_genz/switching_log_v2_G17_kf_run1.csv",S+"/lap/runs_cave02_rate05_L_genz/keyframes_G17_kf_run1.npz","/home/claude/data_in14/cave02_gt.txt",R+"/configs/cave02/cave02_extrinsics.yaml"),
 ("GEO-G17r1","GEO",S+"/geo2/runs_geode_P_genz/switching_log_v2_G17_kf_run1.csv",S+"/geo2/runs_geode_P_genz/keyframes_G17_kf_run1.npz",GEO,GX),
 ("GEO-G17r2","GEO",S+"/geo2/runs_geode_P_genz/switching_log_v2_G17_kf_run2.csv",S+"/geo2/runs_geode_P_genz/keyframes_G17_kf_run2.npz",GEO,GX),
 ("GEO-G0r1","GEO",S+"/geo2/runs_geode_P_genz/switching_log_v2_G0_kf_run1.csv",S+"/geo2/runs_geode_P_genz/keyframes_G0_kf_run1.npz",GEO,GX),
 ("GEO-G0r2","GEO",S+"/geo2/runs_geode_P_genz/switching_log_v2_G0_kf_run2.csv",S+"/geo2/runs_geode_P_genz/keyframes_G0_kf_run2.npz",GEO,GX),
]
