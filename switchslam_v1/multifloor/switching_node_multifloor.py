#!/usr/bin/env python3
import rospy
import numpy as np
import csv
import time
import message_filters
from std_msgs.msg import Float64MultiArray
from nav_msgs.msg import Odometry
fused_pub=[None]
from sensor_msgs.msg import PointCloud
from collections import deque

e1=(0+1/np.sqrt(3))/2; e2=(e1+1/np.sqrt(2))/2; e3=(e2+1)/2
e_m=np.array([e1,e2,e3])
thr=e_m-np.sqrt(0.103*e_m)
EPS=1e-6

FEATURE_MIN=20
POS_JUMP_MAX=1.5
ROT_JUMP_MAX=0.8

prev_l_p=None; prev_l_q=None
prev_v_p=None; prev_v_q=None
prev_T_p=None; prev_T_q=None
latest_aft={"x":None,"y":None,"z":None}
latest_feat_count=[999]
status_buf=deque(maxlen=5)

log=open("switching_log_multifloor.csv","w",newline="")
w=csv.writer(log)
w.writerow(["time","mode","fused_x","fused_y","fused_z","fused_qx","fused_qy","fused_qz","fused_qw","feat_count","aft_x","aft_y","aft_z"])
cnt=[0]

def aft_cb(msg):
    p=msg.pose.pose.position
    latest_aft["x"]=p.x; latest_aft["y"]=p.y; latest_aft["z"]=p.z

def feat_cb(msg):
    latest_feat_count[0]=len(msg.points)

def quat_to_rotvec(q):
    x,y,z,w_=q
    w_=np.clip(w_,-1,1)
    angle=2*np.arccos(w_)
    s=np.sqrt(max(1-w_*w_,1e-12))
    if s<1e-6: return np.array([0.,0.,0.])
    return np.array([x,y,z])/s*angle

def rotvec_to_quat(rv):
    angle=np.linalg.norm(rv)
    if angle<1e-9: return np.array([0.,0.,0.,1.])
    axis=rv/angle
    return np.array([axis[0]*np.sin(angle/2),axis[1]*np.sin(angle/2),axis[2]*np.sin(angle/2),np.cos(angle/2)])

def quat_mul(q1,q2):
    x1,y1,z1,w1=q1; x2,y2,z2,w2=q2
    return np.array([w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2,
                      w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2])

def quat_inv(q):
    x,y,z,w_=q
    return np.array([-x,-y,-z,w_])

def zero_degenerate(H3, lb, thr):
    eigval,eigvec=np.linalg.eigh(H3)
    lam_safe=eigval.copy()
    lam_safe[lb<thr]=EPS
    return eigvec @ np.diag(lam_safe) @ eigvec.T

latest_fused={"p":None,"q":None}

def fast_odom_cb(l_msg):
    if fused_pub[0] is None: return
    om=Odometry()
    om.header.stamp=l_msg.header.stamp
    om.header.frame_id="camera_init"
    if latest_fused["p"] is not None:
        p,q=latest_fused["p"],latest_fused["q"]
    else:
        p=[l_msg.pose.pose.position.x,l_msg.pose.pose.position.y,l_msg.pose.pose.position.z]
        q=[l_msg.pose.pose.orientation.x,l_msg.pose.pose.orientation.y,l_msg.pose.pose.orientation.z,l_msg.pose.pose.orientation.w]
    om.pose.pose.position.x=p[0]; om.pose.pose.position.y=p[1]; om.pose.pose.position.z=p[2]
    om.pose.pose.orientation.x=q[0]; om.pose.pose.orientation.y=q[1]
    om.pose.pose.orientation.z=q[2]; om.pose.pose.orientation.w=q[3]
    fused_pub[0].publish(om)

def sync_cb(h_msg,v_msg,l_msg,vo_msg):
    global prev_l_p,prev_l_q,prev_v_p,prev_v_q,prev_T_p,prev_T_q

    H_l=np.array(h_msg.data).reshape(6,6)
    Hv=np.array(v_msg.data).reshape(6,6)
    eig=np.linalg.eigvalsh(H_l)
    lb=np.clip(eig[:3],1e-9,None); lb=lb/np.linalg.norm(lb)
    degen=bool(np.any(lb<thr))

    l_p=np.array([l_msg.pose.pose.position.x,l_msg.pose.pose.position.y,l_msg.pose.pose.position.z])
    l_q=np.array([l_msg.pose.pose.orientation.x,l_msg.pose.pose.orientation.y,l_msg.pose.pose.orientation.z,l_msg.pose.pose.orientation.w])
    v_p=np.array([vo_msg.pose.pose.position.x,vo_msg.pose.pose.position.y,vo_msg.pose.pose.position.z])
    v_q=np.array([vo_msg.pose.pose.orientation.x,vo_msg.pose.pose.orientation.y,vo_msg.pose.pose.orientation.z,vo_msg.pose.pose.orientation.w])

    if prev_l_p is None:
        prev_l_p=l_p; prev_l_q=l_q; prev_v_p=v_p; prev_v_q=v_q
        prev_T_p=l_p.copy(); prev_T_q=l_q.copy()
        return

    d_l_p=l_p-prev_l_p
    d_v_p=v_p-prev_v_p
    d_l_rv=quat_to_rotvec(quat_mul(l_q,quat_inv(prev_l_q)))
    d_v_rv=quat_to_rotvec(quat_mul(v_q,quat_inv(prev_v_q)))

    vo_fail = bool(latest_feat_count[0] < FEATURE_MIN or
                   np.linalg.norm(d_v_p) > POS_JUMP_MAX or
                   np.linalg.norm(d_v_rv) > ROT_JUMP_MAX)

    if vo_fail:
        mode="LIDAR_ONLY_SAFE"
        Htt_l=H_l[3:6,3:6]
        Htt_safe=zero_degenerate(Htt_l, lb, thr)
        dp=np.linalg.pinv(Htt_safe, rcond=1e-3) @ (Htt_l@d_l_p)
        if np.linalg.norm(dp) > 2.0:
            dp=d_l_p
        drv=d_l_rv
    else:
        status_buf.append(degen)
        n_full=sum(status_buf); n_tot=len(status_buf)
        if n_full==0:
            status="Normal"
        elif n_full==n_tot:
            status="Fully"
        else:
            status="Transition"

        if status=="Normal":
            mode="LIDAR_ONLY"; dp=d_l_p; drv=d_l_rv
        elif status=="Fully":
            mode="TIGHTLY_COUPLED"
            idx=[3,4,5,0,1,2]
            H_l6=H_l[np.ix_(idx,idx)]
            d_l6=np.concatenate([d_l_p,d_l_rv])
            d_v6=np.concatenate([d_v_p,d_v_rv])
            H_sum6=H_l6+Hv+EPS*np.eye(6)
            try:
                delta6=np.linalg.solve(H_sum6, H_l6@d_l6+Hv@d_v6)
            except np.linalg.LinAlgError:
                delta6=d_v6
            dp=delta6[0:3]; drv=delta6[3:6]
            if np.linalg.norm(dp) > 2.0:
                dp=d_l_p; drv=d_l_rv
        else:
            mode="TRANSITION"
            wv=np.clip(np.sqrt(3*lb[0]),0,1)
            wl=1-wv
            dp=wl*d_l_p+wv*d_v_p
            drv=wl*d_l_rv+wv*d_v_rv

    T_p=prev_T_p+dp
    dq=rotvec_to_quat(drv)
    T_q=quat_mul(dq,prev_T_q)
    T_q=T_q/np.linalg.norm(T_q)

    t=time.time()
    w.writerow([t,mode,T_p[0],T_p[1],T_p[2],T_q[0],T_q[1],T_q[2],T_q[3],
                latest_feat_count[0], latest_aft["x"],latest_aft["y"],latest_aft["z"]])
    log.flush()

    latest_fused["p"]=T_p; latest_fused["q"]=T_q

    prev_l_p=l_p; prev_l_q=l_q; prev_v_p=v_p; prev_v_q=v_q
    prev_T_p=T_p; prev_T_q=T_q
    cnt[0]+=1
    if cnt[0]%20==0:
        print("[%d] %s feat=%d T=(%.2f,%.2f,%.2f)"%(cnt[0],mode,latest_feat_count[0],T_p[0],T_p[1],T_p[2]))

def main():
    rospy.init_node("switching_node_multifloor",anonymous=True)
    fused_pub[0]=rospy.Publisher("/switch_fused_pose",Odometry,queue_size=10)
    rospy.Subscriber("/feature_tracker/feature",PointCloud,feat_cb)
    rospy.Subscriber("/aft_mapped_to_init",Odometry,aft_cb)
    h=message_filters.Subscriber("/laser_hessian",Float64MultiArray)
    v=message_filters.Subscriber("/vins_mono_hessian",Float64MultiArray)
    l=message_filters.Subscriber("/laser_odom_to_init",Odometry)
    rospy.Subscriber("/laser_odom_to_init",Odometry,fast_odom_cb)
    vo=message_filters.Subscriber("/vins_estimator/odometry",Odometry)
    ts=message_filters.ApproximateTimeSynchronizer([h,v,l,vo],queue_size=20,slop=0.15,allow_headerless=True)
    ts.registerCallback(sync_cb)
    print("Switching node (multifloor, real-world) listening...")
    rospy.spin()

if __name__=="__main__":
    try: main()
    finally:
        log.close(); print("Saved switching_log_multifloor.csv")
