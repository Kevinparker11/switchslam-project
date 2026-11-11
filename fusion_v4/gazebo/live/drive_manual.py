#!/usr/bin/env python3
"""Manual keyboard drive for the Plane route (11 Nov 2026). Publishes /husky_velocity_controller/cmd_vel at 10 Hz, nothing else.
The speed is latched (no key holding): the forward speed is either 0 or LINEAR_SPEED (default 0.25 m/s, the speed of the driver
of every other live run), the turn rate changes in steps.  Keys (type in this terminal, no Enter needed):
  w  go forward at LINEAR_SPEED      s  stop (also zeroes the turn rate)      x  zero the turn rate (drive straight)
  a  turn left  (+0.05 rad/s per press, max 0.4)      d  turn right (-0.05 rad/s per press)      q  stop and quit
Small steps: on open ground a turn rate of 0.05 rad/s is about 5 m of heading change per 100 m.  Drive about 105 m, no spins.
usage: python3 drive_manual.py     (env LINEAR_SPEED, TURN_STEP, TURN_MAX)"""
import os, sys, select, termios, tty
import rospy
from geometry_msgs.msg import Twist

LIN = float(os.environ.get("LINEAR_SPEED", "0.25"))
STEP = float(os.environ.get("TURN_STEP", "0.05"))
MAXW = float(os.environ.get("TURN_MAX", "0.4"))
MAX_ACC = 0.05            # per 10 Hz tick, the limit of the route driver (MAX_LINEAR_ACCEL in waypoint_driver_route.py)


def main():
    rospy.init_node("drive_manual", anonymous=True)
    pub = rospy.Publisher("/husky_velocity_controller/cmd_vel", Twist, queue_size=10)
    rate = rospy.Rate(10)
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    target, w, v = 0.0, 0.0, 0.0
    print("drive_manual: w forward, s stop, a/d turn, x straight, q quit.  speed %.2f m/s" % LIN, flush=True)
    try:
        while not rospy.is_shutdown():
            if select.select([sys.stdin], [], [], 0)[0]:
                k = sys.stdin.read(1)
                if k == "w": target = LIN
                elif k == "s": target, w = 0.0, 0.0
                elif k == "x": w = 0.0
                elif k == "a": w = min(MAXW, w + STEP)
                elif k == "d": w = max(-MAXW, w - STEP)
                elif k == "q": break
                print("\rtarget %.2f m/s  turn %+.2f rad/s     " % (target, w), end="", flush=True)
            v += max(-MAX_ACC, min(MAX_ACC, target - v))   # same per-tick limit as the route driver (0.05 per 0.1 s tick)
            cmd = Twist()
            cmd.linear.x, cmd.angular.z = v, w
            pub.publish(cmd)
            rate.sleep()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        for _ in range(5):
            pub.publish(Twist())
            rospy.sleep(0.1)
        print("\nstopped.")


if __name__ == "__main__":
    main()
