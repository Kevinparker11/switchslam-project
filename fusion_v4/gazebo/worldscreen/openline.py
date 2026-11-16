import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt, uniform_filter

S = '/tmp/claude-0/-home-claude/3f90fe9f-923e-500d-a688-dedb31fbfbe6/scratchpad/'
g = np.load(S + 'agri_grid.npz')
zmin, zmax, x0, y0 = g['zmin'], g['zmax'], float(g['x0']), float(g['y0'])
nx, ny = zmin.shape
struct = np.nan_to_num(zmax - zmin) > 0.8
# remove isolated single cells (sampling noise)
cnt = uniform_filter(struct.astype(float), size=3) * 9
struct &= cnt >= 2.5
# barn footprint (large block) and fences are structure; distance in metres to nearest structure
dist = distance_transform_edt(~struct)
z = np.where(np.isfinite(zmin), zmin, np.nanmedian(zmin))
zs = uniform_filter(z, size=5, mode='nearest')


def cell(x, y):
    return int(round(x - x0)), int(round(y - y0))


best = []
CL = 4.0
for sx in np.arange(x0 + 4, x0 + nx - 4, 3.0):
    for sy in np.arange(y0 + 4, y0 + ny - 4, 3.0):
        i, j = cell(sx, sy)
        if not (0 <= i < nx and 0 <= j < ny) or dist[i, j] < CL:
            continue
        for ang in np.deg2rad(np.arange(0, 360, 5)):
            L = 0.0
            while True:
                x = sx + (L + 1) * np.cos(ang); y = sy + (L + 1) * np.sin(ang)
                i, j = cell(x, y)
                if not (0 <= i < nx and 0 <= j < ny) or dist[i, j] < CL:
                    break
                L += 1
            if L >= 40:
                ex, ey = sx + L * np.cos(ang), sy + L * np.sin(ang)
                # slope along the line
                ss = np.arange(0, L, 1.0)
                zz = [zs[cell(sx + s * np.cos(ang), sy + s * np.sin(ang))] for s in ss]
                sl = np.degrees(np.arctan(np.abs(np.diff(zz)).max())) if len(zz) > 1 else 0
                best.append((L, sx, sy, ex, ey, sl, float(np.ptp(zz))))
best.sort(reverse=True)
print('longest straight lines with >= %.0f m clearance to any fence/barn/panel (1 m cells, start grid 3 m):' % CL)
seen = []
for b in best:
    if any(np.hypot(b[1] - s[1], b[2] - s[2]) < 15 and abs(((np.degrees(np.arctan2(b[4] - b[2], b[3] - b[1])) - np.degrees(np.arctan2(s[4] - s[2], s[3] - s[1])) + 90) % 180) - 90) < 20 for s in seen):
        continue
    seen.append(b)
    print('  %.0f m  (%.0f,%.0f) -> (%.0f,%.0f)  max 1 m slope %.1f deg, height range %.1f m' % b[:5] + ('' if False else '') if False else
          '  %.0f m  (%.0f,%.0f) -> (%.0f,%.0f)  max 1 m slope %.1f deg, height range %.1f m' % (b[0], b[1], b[2], b[3], b[4], b[5], b[6]))
    if len(seen) >= 6:
        break
np.save(S + 'agri_dist.npy', dist)
fig, ax = plt.subplots(figsize=(9, 10))
ext = [x0, x0 + nx, y0, y0 + ny]
ax.imshow(dist.T, origin='lower', extent=ext, cmap='Greens', vmax=40)
ax.imshow(np.ma.masked_where(~struct.T, struct.T.astype(float)), origin='lower', extent=ext, cmap='gray_r', vmin=0, vmax=1, alpha=1)
L_ = np.loadtxt('/home/claude/switchslam-project/fusion_v4/gazebo/routes/farm_L.csv', delimiter=',', comments='#')
ax.plot(L_[:, 0], L_[:, 1], 'r-', lw=2.5, label='farm L route used so far (80 m)')
pp = np.array([-77., -13.]); dd = np.array([101., -71.]); dd /= np.linalg.norm(dd)
a_ = pp + dd * 8; b_ = pp + dd * 113
ax.plot([a_[0], b_[0]], [a_[1], b_[1]], 'b-', lw=3, label='proposed open-ground route, 105 m')
ax.plot(*a_, 'bo', ms=9, label='spawn point (-70.5, -17.6)')
ax.text(-8, -20, 'barn', ha='center', color='w', fontsize=9)
ax.text(-45, 33, 'solar rows', color='k', fontsize=9)
ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]'); ax.set_aspect('equal'); ax.legend(loc='upper left', fontsize=8)
ax.set_title('Agriculture world: green = distance to nearest fence, barn or panel (m); black = structure')
plt.tight_layout(); plt.savefig(S + 'agri_open_lines.png', dpi=90)
