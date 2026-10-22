#!/usr/bin/env python3
path = "/root/catkin_ws/src/A-LOAM/src/laserMapping.cpp"
with open(path) as f:
    content = f.read()

old = """	mBuf.lock();
	odometryBuf.push(laserOdometry);
	mBuf.unlock();"""

new = """	mBuf.lock();
	while (!odometryBuf.empty()) odometryBuf.pop();  // keep only latest, avoid cross-process latency stalls
	odometryBuf.push(laserOdometry);
	mBuf.unlock();"""

assert old in content, "anchor not found"
content = content.replace(old, new, 1)
with open(path, "w") as f:
    f.write(content)
print("Patched laserOdometryHandler to keep only latest message.")
