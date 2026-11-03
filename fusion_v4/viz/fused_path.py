#!/usr/bin/env python3
"""Fused pose (/switch_fused_pose, nav_msgs/Odometry) -> growing nav_msgs/Path on /fused_path, for RViz (a clean line instead of arrows)."""
import numpy as np

class Trail:
    def __init__(self, step=0.2):
        self.step, self.pts, self.last_t = step, [], None
    def add(self, t, p, q):
        """returns True if the trail changed; a jump back in time (new run) starts a new trail"""
        if self.last_t is not None and t < self.last_t - 1.0:
            self.pts = []
        self.last_t = t
        if self.pts and np.linalg.norm(np.asarray(p) - self.pts[-1][0]) < self.step:
            return False
        self.pts.append((np.asarray(p, float), np.asarray(q, float)))
        return True

if __name__ == "__main__":
    import rospy
    from nav_msgs.msg import Odometry, Path
    from geometry_msgs.msg import PoseStamped
    rospy.init_node("fused_path"); tr = Trail(); dirty = [False]
    pub = rospy.Publisher("/fused_path", Path, queue_size=1)
    def cb(m):
        P, O = m.pose.pose.position, m.pose.pose.orientation
        if tr.add(m.header.stamp.to_sec(), (P.x, P.y, P.z), (O.x, O.y, O.z, O.w)): dirty[0] = True
    def tick(_):
        if not dirty[0]: return
        dirty[0] = False
        msg = Path(); msg.header.frame_id = "camera_init"; msg.header.stamp = rospy.Time.now()
        for p, q in tr.pts:
            s = PoseStamped(); s.header = msg.header
            s.pose.position.x, s.pose.position.y, s.pose.position.z = p
            s.pose.orientation.x, s.pose.orientation.y, s.pose.orientation.z, s.pose.orientation.w = q
            msg.poses.append(s)
        pub.publish(msg)
    rospy.Subscriber("/switch_fused_pose", Odometry, cb, queue_size=50)
    rospy.Timer(rospy.Duration(0.5), tick); rospy.spin()
