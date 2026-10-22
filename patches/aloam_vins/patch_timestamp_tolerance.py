#!/usr/bin/env python3
path = "/root/catkin_ws/src/A-LOAM/src/laserMapping.cpp"
with open(path) as f:
    content = f.read()

old = """			if (timeLaserCloudCornerLast != timeLaserOdometry ||
				timeLaserCloudSurfLast != timeLaserOdometry ||
				timeLaserCloudFullRes != timeLaserOdometry)
			{
				printf("time corner %f surf %f full %f odom %f \\n", timeLaserCloudCornerLast, timeLaserCloudSurfLast, timeLaserCloudFullRes, timeLaserOdometry);
				printf("unsync messeage!");
				mBuf.unlock();
				break;
			}"""

new = """			double TOL = 0.02;
			if (fabs(timeLaserCloudCornerLast - timeLaserOdometry) > TOL ||
				fabs(timeLaserCloudSurfLast - timeLaserOdometry) > TOL ||
				fabs(timeLaserCloudFullRes - timeLaserOdometry) > TOL)
			{
				printf("time corner %f surf %f full %f odom %f \\n", timeLaserCloudCornerLast, timeLaserCloudSurfLast, timeLaserCloudFullRes, timeLaserOdometry);
				printf("unsync messeage!");
				mBuf.unlock();
				break;
			}"""

assert old in content, "anchor not found"
content = content.replace(old, new, 1)
with open(path, "w") as f:
    f.write(content)
print("Patched: exact timestamp equality replaced with 20ms tolerance.")
