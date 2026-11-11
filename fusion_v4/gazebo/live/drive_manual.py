#!/usr/bin/env python3
"""Manual WASD drive for the Plane route (rewritten 11 Nov 2026 after the first latched-key version was found unusable).
Classic hold-to-move keys; publishes /husky_velocity_controller/cmd_vel at 10 Hz and nothing else.
  w forward   s backward   a turn left   d turn right   (hold the key; let go and the robot stops)   space stop   q quit
Terminal key repeat is used as the "key is held" signal: a command stays active for HOLD_LIN s (forward / backward) or HOLD_ANG s (turn)
after the last key character, so w held plus a short tap of a or d gives a gentle arc, and a tap of a or d alone is a small turn.
Speeds: forward LINEAR_SPEED (default 0.25 m/s, the speed of every other live run, ramped 0.05 per 0.1 s tick like the route driver),
backward half of that, turn TURN_RATE (default 0.3 rad/s).   usage: python3 drive_manual.py   (env LINEAR_SPEED, TURN_RATE)"""
import os, sys, select, termios, tty
import rospy
from geometry_msgs.msg import Twist

LIN = float(os.environ.get("LINEAR_SPEED", "0.25"))
TURN = float(os.environ.get("TURN_RATE", "0.3"))
HOLD_LIN, HOLD_ANG = 0.6, 0.25     # s a command stays active after its last key character (bridges the OS key-repeat delay)
MAX_ACC = 0.05                     # per 10 Hz tick, as MAX_LINEAR_ACCEL in waypoint_driver_route.py


def targets(now, last):
    """last: dict key -> time of the last character.  Returns (target linear, angular).  Pure function, unit-tested."""
    on = lambda k, h: k in last and now - last[k] <= h
    lin = LIN if on("w", HOLD_LIN) else (-0.5 * LIN if on("s", HOLD_LIN) else 0.0)
    ang = TURN if on("a", HOLD_ANG) else (-TURN if on("d", HOLD_ANG) else 0.0)
    if on("a", HOLD_ANG) and on("d", HOLD_ANG):
        ang = TURN if last["a"] > last["d"] else -TURN
    if on("w", HOLD_LIN) and on("s", HOLD_LIN):
        lin = LIN if last["w"] > last["s"] else -0.5 * LIN
    return lin, ang


def main():
    rospy.init_node("drive_manual", anonymous=True)
    pub = rospy.Publisher("/husky_velocity_controller/cmd_vel", Twist, queue_size=10)
    rate = rospy.Rate(10)
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    last, v = {}, 0.0
    print("drive_manual: hold w forward, s back, a left, d right; space stop, q quit.  speed %.2f m/s, turn %.2f rad/s" % (LIN, TURN), flush=True)
    try:
        while not rospy.is_shutdown():
            now = rospy.get_time()
            while select.select([sys.stdin], [], [], 0)[0]:
                k = sys.stdin.read(1).lower()
                if k == "q":
                    return
                if k == " ":
                    last.clear()
                elif k in "wasd":
                    last[k] = now
            tl, ang = targets(now, last)
            v += max(-MAX_ACC, min(MAX_ACC, tl - v))
            cmd = Twist()
            cmd.linear.x, cmd.angular.z = v, ang
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
