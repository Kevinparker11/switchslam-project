import sys, time
import numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad')
from screen import World, route_stats, metric

C = '/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/cpr/cpr_gazebo/'
which = sys.argv[1]


def line(p, q, step=2.0):
    p = np.array(p, float); q = np.array(q, float)
    n = int(np.linalg.norm(q - p) / step) + 1
    return [tuple(p + (q - p) * t) for t in np.linspace(0, 1, n)]


t0 = time.time()
if which == 'agri':
    W = World([(C + 'cpr_agriculture_gazebo/meshes/agriculture_world.dae', np.pi, 1, 1)])
    print('built', W.shape, '%.0fs' % (time.time() - t0))
    L = np.loadtxt('/home/claude/switchslam-project/fusion_v4/gazebo/routes/farm_L.csv', delimiter=',', comments='#')[::8]
    route_stats(W, L, 'agri: farm L route (0,0)-(0,-40)-(-40,-40)')
    seg1 = L[(L[:, 0] > -1) & (L[:, 1] <= 0)]
    route_stats(W, seg1, 'agri: L leg 1 (x=0, y 0 to -40)')
    seg2 = L[(L[:, 1] < -39.5)]
    route_stats(W, seg2, 'agri: L leg 2 (y=-40, x 0 to -40)')
    route_stats(W, line((-45, -24), (-45, -88)), 'agri: pasture, x=-45, y -24 to -88')
    route_stats(W, line((-76, -56), (-14, -56)), 'agri: pasture, y=-56, x -76 to -14')
    route_stats(W, line((-74, -26), (-16, -86)), 'agri: pasture, diagonal')
    route_stats(W, line((-70, 30.5), (10, 30.5)), 'agri: solar farm lane y=30.5')
    route_stats(W, line((-45, -60), (-45, -60), 1), 'agri: pasture centre (-45,-60)')
if which == 'orch':
    W = World([(C + 'cpr_orchard_gazebo/meshes/orchard_world.dae', np.pi / 2, 1, 1),
               (C + 'cpr_orchard_gazebo/meshes/orchard_trunks.dae', np.pi / 2, 1, 1),
               (C + 'cpr_orchard_gazebo/meshes/orchard_leaves.dae', np.pi / 2, 1, 1)])
    print('built', W.shape, '%.0fs' % (time.time() - t0))
    for xl in (-23.4, -14.3, -8.3):
        route_stats(W, line((xl, 5), (xl, 41)), 'orchard: lane x=%.1f, y 5 to 41' % xl)
    route_stats(W, line((-1.4, 2), (-1.4, 46)), 'orchard: east margin x=-1.4')
    route_stats(W, line((-36.5, 2), (-36.5, 46)), 'orchard: west margin x=-36.5')
    route_stats(W, line((-30, 1.5), (-5, 1.5)), 'orchard: south end y=1.5')
if which == 'insp':
    W = World([(C + 'cpr_inspection_gazebo/meshes/inspection_world.dae', np.pi, 2, 1)])
    print('built', W.shape, '%.0fs' % (time.time() - t0))
    route_stats(W, line((-30, 0), (30, -10)), 'insp: hilly terrain traverse')
    # cave: grid of floor positions with headroom
    xs = np.arange(-62, 2, 4.0); ys = np.arange(-134, -46, 4.0)
    cave = []
    for x in xs:
        for y in ys:
            g = W.ground_at(x, y)
            if not np.isfinite(g):
                continue
            i = int((x - W.lo[0]) / 0.3); j = int((y - W.lo[1]) / 0.3)
            col = W.occ[i, j, :]
            if col.sum() < 2 or col.sum() > 80:
                continue
            cave.append((x, y))
    print('cave floor candidate cells', len(cave))
    route_stats(W, cave, 'insp: cave floor grid (all cells)')
