#!/usr/bin/env python3
import rospy
import numpy as np
import csv
import time
import message_filters
from std_msgs.msg import Float64MultiArray
from nav_msgs.msg import Odometry
from gazebo_msgs.msg import ModelStates

e1=(0+1/np.sqrt(3))/2; e2=(e1+1/np.sqrt(2))/2; e3=(e2+1)/2
e_m=np.array([e1,e2,e3])
thr=e_m-np.sqrt(0.103*e_m)
VO_FAIL_V=3.0
EPS=1e-6

prev_l_p=None; prev_l_q=None
prev_v_p=None; prev_v_q=None
prev_T_p=None; prev_T_q=None
latest_gt={"x":None,"y":None,"z":None}

log=open("switching_log_v4.csv","w",newline="")
w=csv.writer(log)
w.writerow(["time","mode","fused_x","fused_y","fused_z","fused_qx","fused_qy","fused_qz","fused_qw","gt_x","gt_y","gt_z"])
cnt=[0]

def gt_cb(msg):
    try: idx=msg.name.index("husky")
    except ValueError: return
    p=msg.pose[idx].position
    latest_gt["x"]=p.x; latest_gt["y"]=p.y; latest_gt["z"]=p.z

def quat_to_rotvec(q):
    x,y,z,w_ = q
    w_ = np.clip(w_,-1,1)
    angle = 2*np.arccos(w_)
    s = np.sqrt(max(1-w_*w_,1e-12))
    if s < 1e-6:
        return np.array([0.0,0.0,0.0])
    return np.array([x,y,z])/s*angle

def rotvec_to_quat(rv):
    angle = np.linalg.norm(rv)
    if angle < 1e-9:
        return np.array([0.0,0.0,0.0,1.0])
    axis = rv/angle
    return np.array([axis[0]*np.sin(angle/2), axis[1]*np.sin(angle/2), axis[2]*np.sin(angle/2), np.cos(angle/2)])

def quat_mul(q1,q2):
    x1,y1,z1,w1=q1; x2,y2,z2,w2=q2
    return np.array([
        w1*x2+x1*w2+y1*z2-z1*y2,
        w1*y2-x1*z2+y1*w2+z1*x2,
        w1*z2+x1*y2-y1*x2+z1*w2,
        w1*w2-x1*x2-y1*y2-z1*z2])

def quat_inv(q):
    x,y,z,w_=q
    return np.array([-x,-y,-z,w_])

def sync_cb(h_msg,v_msg,l_msg,vo_msg):
    global prev_l_p,prev_l_q,prev_v_p,prev_v_q,prev_T_p,prev_T_q
    if latest_gt["x"] is None: return

    H_l=np.array(h_msg.data).reshape(6,6)
    Hv=np.array(v_msg.data).reshape(6,6)
    eig=np.linalg.eigvalsh(H_l)
    lb=np.clip(eig[:3],1e-9,None); lb=lb/np.linalg.norm(lb)
    degen=bool(np.any(lb<thr))

    Htt_l = H_l[3:6,3:6]; Hrr_l = H_l[0:3,0:3]
    Htt_v = Hv[0:3,0:3]; Hrr_v = Hv[3:6,3:6]

    l_p=np.array([l_msg.pose.pose.position.x,l_msg.pose.pose.position.y,l_msg.pose.pose.position.z])
    l_q=np.array([l_msg.pose.pose.orientation.x,l_msg.pose.pose.orientation.y,l_msg.pose.pose.orientation.z,l_msg.pose.pose.orientation.w])
    v_p=np.array([vo_msg.pose.pose.position.x,vo_msg.pose.pose.position.y,vo_msg.pose.pose.position.z])
    v_q=np.array([vo_msg.pose.pose.orientation.x,vo_msg.pose.pose.orientation.y,vo_msg.pose.pose.orientation.z,vo_msg.pose.pose.orientation.w])
    v_vel=np.array([vo_msg.twist.twist.linear.x,vo_msg.twist.twist.linear.y,vo_msg.twist.twist.linear.z])
    vo_fail=bool(np.linalg.norm(v_vel)>VO_FAIL_V)

    if prev_l_p is None:
        prev_l_p=l_p; prev_l_q=l_q; prev_v_p=v_p; prev_v_q=v_q
        prev_T_p=l_p.copy(); prev_T_q=l_q.copy()
        return

    d_l_p=l_p-prev_l_p
    d_v_p=v_p-prev_v_p
    d_l_rv=quat_to_rotvec(quat_mul(l_q,quat_inv(prev_l_q)))
    d_v_rv=quat_to_rotvec(quat_mul(v_q,quat_inv(prev_v_q)))

    if vo_fail:
        mode="LIDAR_ONLY"; dp=d_l_p; drv=d_l_rv
    elif not degen:
        mode="LIDAR_ONLY"; dp=d_l_p; drv=d_l_rv
    else:
        mode="TIGHTLY_COUPLED"
        Hp=Htt_l+Htt_v+EPS*np.eye(3)
        Hr=Hrr_l+Hrr_v+EPS*np.eye(3)
        try:
            dp=np.linalg.solve(Hp, Htt_l@d_l_p+Htt_v@d_v_p)
            drv=np.linalg.solve(Hr, Hrr_l@d_l_rv+Hrr_v@d_v_rv)
        except np.linalg.LinAlgError:
            dp=d_v_p; drv=d_v_rv

    T_p=prev_T_p+dp
    dq=rotvec_to_quat(drv)
    T_q=quat_mul(dq,prev_T_q)
    T_q=T_q/np.linalg.norm(T_q)

    t=time.time()
    w.writerow([t,mode,T_p[0],T_p[1],T_p[2],T_q[0],T_q[1],T_q[2],T_q[3],
                latest_gt["x"],latest_gt["y"],latest_gt["z"]])
    log.flush()

    prev_l_p=l_p; prev_l_q=l_q; prev_v_p=v_p; prev_v_q=v_q
    prev_T_p=T_p; prev_T_q=T_q

    cnt[0]+=1
    if cnt[0]%20==0:
        print("[%d] %s T=(%.2f,%.2f,%.2f)"%(cnt[0],mode,T_p[0],T_p[1],T_p[2]))

def main():
    rospy.init_node("switching_node_v4",anonymous=True)
    rospy.Subscriber("/gazebo/model_states",ModelStates,gt_cb)
    h=message_filters.Subscriber("/laser_hessian",Float64MultiArray)
    v=message_filters.Subscriber("/vins_mono_hessian",Float64MultiArray)
    l=message_filters.Subscriber("/laser_odom_to_init",Odometry)
    vo=message_filters.Subscriber("/vins_estimator/odometry",Odometry)
    ts=message_filters.ApproximateTimeSynchronizer([h,v,l,vo],queue_size=20,slop=0.15,allow_headerless=True)
    ts.registerCallback(sync_cb)
    print("Switching node v4 (full 6-DOF) listening... drive now.")
    rospy.spin()

if __name__=="__main__":
    try: main()
    finally:
        log.close(); print("Saved switching_log_v4.csv")
