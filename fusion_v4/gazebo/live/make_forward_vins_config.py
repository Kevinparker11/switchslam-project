#!/usr/bin/env python3
"""Write the VINS-Mono config for the FORWARD-facing camera (husky_sim_extras.urdf.xacro) from the farm config.
Only extrinsicRotation changes: camera->IMU rotation of a camera at base_link (0.3, 0, 0.3), no rotation, Gazebo camera looking along +x,
optical axes (x right, y down, z forward) in the base frame = (0,-1,0), (0,0,-1), (1,0,0)  ->  R_ic = [[0,0,1],[-1,0,0],[0,-1,0]]
(same matrix as gazebo/make_sim_calib.py). Translation (0.3, 0, 0.3), intrinsics (fx = fy = 381.361), estimate_extrinsic 1 stay as in the farm config.
usage: python3 make_forward_vins_config.py <farm_mono_config.yaml> <out farm_fwd_config.yaml>"""
import re, sys
src = open(sys.argv[1]).read()
new = """extrinsicRotation: !!opencv-matrix
   rows: 3
   cols: 3
   dt: d
   data: [0, 0, 1,
          -1, 0, 0,
          0, -1, 0]
"""
out, n = re.subn(r"extrinsicRotation: !!opencv-matrix\s+rows: 3\s+cols: 3\s+dt: d\s+data: \[[^\]]*\]\n", new, src)
assert n == 1, "extrinsicRotation block not found exactly once"
open(sys.argv[2], "w").write(out)
print("wrote", sys.argv[2])
