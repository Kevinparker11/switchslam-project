import json,glob,sys,collections,numpy as np
cfgs=sys.argv[1].split(',') if len(sys.argv)>1 else ["GZ","G17","G18","G19"]
RES=collections.defaultdict(dict); seqof={}
for f in glob.glob('out/*.json'):
    r=json.load(open(f)); RES[r["log"]][r["cfg"]]=r; seqof[r['log']]=r['seq']
_g={}; exec(open('logs_all.py').read(),_g); order=[e[0] for e in _g['LOGS']]
print('%-8s'%'log'+''.join('%9s'%c for c in cfgs))
for l in order:
    print('%-8s'%l+''.join('%9s'%('%.3f'%RES[l][c]['ate'] if c in RES[l] else '-') for c in cfgs))
print('--- median per sequence (diverged MF-b2 excluded)')
for s in ["MF","LC","C02","CV","GEO"]:
    ls=[l for l in order if seqof.get(l)==s and l!='MF-b2']
    print('%-8s'%s+''.join('%9s'%('%.3f'%np.median([RES[l][c]['ate'] for l in ls if c in RES[l]]) if all(c in RES[l] for l in ls) else '-') for c in cfgs), ' n=%d'%len(ls))
