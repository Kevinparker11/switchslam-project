# Every GenZ-stack recording available on the analysis machine (24 Oct 2026): name, sequence, log, keyframes, GT, extrinsics.
# GenZ-LIO and VINS-Mono take no feedback from the fusion, so any configuration replayed on any of these logs equals a live run.
S="/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad"
R="/home/claude/switchslam-project"
U="/root/.claude/uploads/3f90fe9f-923e-500d-a688-dedb31fbfbe6"
MFGT="/tmp/claude-0/g0mf/ground_truth_path.csv"
GEO=U+"/b6b27018-stairs_alpha.txt"; GX=R+"/fusion_v4/geode/geode_extrinsics.yaml"
LCGT=U+"/26b723ff-corridor01_gt.txt"; LCX=R+"/configs/corridor/corridor_extrinsics.yaml"
CVGT="/home/claude/data_in14/cave02_gt.txt"; CVX=R+"/configs/cave02/cave02_extrinsics.yaml"
def L(name, seq, folder, tag, gt, ext): return (name, seq, folder+"/switching_log_v2_"+tag+".csv", folder+"/keyframes_"+tag+".npz", gt, ext)
LOGS = [
 L("MF-a1","MF","/tmp/claude-0/g17","G17_kf_run1",MFGT,"-"),
 L("MF-a2","MF","/tmp/claude-0/g0mf","G0_kf_run1",MFGT,"-"),
 L("MF-a3","MF","/tmp/claude-0/g0mf","G0_kf_run2",MFGT,"-"),
 L("MF-a4","MF","/tmp/claude-0/g0mf","G0_kf_run3",MFGT,"-"),
] + [L("MF-b%d"%r,"MF",S+"/lapres/runs_v2_genz","G19_kf_run%d"%r,MFGT,"-") for r in range(1,7)] + [
 L("C02-a1","C02",S+"/lap/runs_corridor2_rate033_L_genz","G17_kf_run1",U+"/db62c9b7-corridor02_gt.txt",R+"/configs/corridor2/corridor2_extrinsics.yaml"),
 L("CV-a1","CV",S+"/lap/runs_cave02_rate05_L_genz","G17_kf_run1",CVGT,CVX),
 L("CV-b1","CV",S+"/lapres/runs_cave02_authcfg_L_genz","G19_kf_run1",CVGT,CVX),
] + [L("LC-a%d"%r,"LC",S+"/lapres/runs_corridor_A_L_genz","G19_kf_run%d"%r,LCGT,LCX) for r in (1,2,3)] \
  + [L("LC-b%d"%r,"LC",S+"/lapres/runs_corridor_B_L_genz","G19_kf_run%d"%r,LCGT,LCX) for r in (1,2,3)] + [
 L("GEO-a1","GEO",S+"/pcres/runs_geode_P_genz","G17_kf_run1",GEO,GX),
 L("GEO-a2","GEO",S+"/pcres/runs_geode_P_genz","G17_kf_run2",GEO,GX),
 L("GEO-a3","GEO",S+"/pcres/runs_geode_P_genz","G0_kf_run1",GEO,GX),
 L("GEO-a4","GEO",S+"/pcres/runs_geode_P_genz","G0_kf_run2",GEO,GX),
 L("GEO-b1","GEO",S+"/pcres/runs_geode_P_genz","G18_kf_run1",GEO,GX),
 L("GEO-b2","GEO",S+"/pcres/runs_geode_P_genz","G18_kf_run2",GEO,GX),
 L("GEO-b3","GEO",S+"/pcres/runs_geode_P_genz","G19_kf_run1",GEO,GX),
 L("GEO-b4","GEO",S+"/pcres/runs_geode_P_genz","G19_kf_run2",GEO,GX),
 L("GEO-b5","GEO",S+"/pcres/runs_geode_P_genz","G0_kf_run3",GEO,GX),
 L("GEO-b6","GEO",S+"/pcres/runs_geode_P_genz","G0_kf_run4",GEO,GX),
 L("GEO-c1","GEO",S+"/pcres/runs_geode_P_rate1.0_genz","G0_kf_run1",GEO,GX),
 L("GEO-c2","GEO",S+"/pcres/runs_geode_P_rate1.0_genz","G0_kf_run2",GEO,GX),
 L("GEO-c3","GEO",S+"/pcres/runs_geode_P_rate1.0_genz","G19_kf_run1",GEO,GX),
 L("GEO-c4","GEO",S+"/pcres/runs_geode_P_rate1.0_genz","G19_kf_run2",GEO,GX),
]
