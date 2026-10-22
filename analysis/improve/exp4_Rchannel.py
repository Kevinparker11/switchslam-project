from common import *
SEQ = ["MF", "LC", "C02", "CAVE"]
CR = [0.0, 0.003, 0.03, 0.3, 3.0, 30.0]
print("Schur R channel: replay of logged F8 runs, ATE RMSE (m), mean over runs; c_t=0.03, no gate; rotation weight W_R=(c_R S_RR+I)^-1 c_R S_RR")
print("seq   n | " + " ".join("cR=%-6g" % c for c in CR), flush=True)
for s in SEQ:
    ps = logs(s); res = {c: [] for c in CR}
    for pth in ps:
        d = load(pth)
        for c in CR:
            res[c].append(score(s, d, replay(d, c_t=0.03, c_R=c)))
    print("%-5s %d | " % (s, len(ps)) + " ".join("%-9.3f" % np.mean(res[c]) for c in CR), flush=True)
