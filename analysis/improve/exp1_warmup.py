from common import *
SEQ = ["MF", "LC", "C02", "CAVE"]
TW = [0, 5, 10, 20, 30, 40, 60]
print("replay of logged F8 runs, ATE RMSE (m), mean over runs; c_t=0.03, no gate; only t_warm changes")
print("seq   n | " + " ".join("tw=%-5d" % t for t in TW) + " | live(logged fused)")
for s in SEQ:
    ps = logs(s)
    res = {t: [] for t in TW}; live = []
    for pth in ps:
        d = load(pth)
        live.append(score(s, d, d["df"][["fused_x","fused_y","fused_z"]].values.astype(float)))
        for t in TW:
            res[t].append(score(s, d, replay(d, c_t=0.03, t_warm=float(t))))
    print("%-5s %d | " % (s, len(ps)) + " ".join("%-8.3f" % np.mean(res[t]) for t in TW) + " | %.3f" % np.mean(live))
