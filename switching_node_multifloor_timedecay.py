#!/usr/bin/env python3
import rospy
import numpy as np
import csv
import message_filters
from std_msgs.msg import Float64MultiArray
from nav_msgs.msg import Odometry
fused_pub=[None]
from sensor_msgs.msg import PointCloud, PointCloud2
import sensor_msgs.point_cloud2 as pc2
from collections import deque
from scipy.spatial import cKDTree

e1=(0+1/np.sqrt(3))/2; e2=(e1+1/np.sqrt(2))/2; e3=(e2+1)/2
e_m=np.array([e1,e2,e3])
thr=e_m-np.sqrt(0.103*e_m)
EPS=1e-6

FEATURE_MIN=20
POS_JUMP_MAX=1.5
ROT_JUMP_MAX=0.8

BINGHAM_MIN_NORMALS=15
BINGHAM_KNN=12
BINGHAM_SUBSAMPLE=400
BINGHAM_ISO_THR = 0.15

prev_l_p=None; prev_l_q=None
prev_v_p=None; prev_v_q=None
prev_T_p=None; prev_T_q=None
latest_aft={"x":None,"y":None,"z":None}
latest_feat_count=[999]
status_buf=deque(maxlen=5)
latest_bingham={"lam":np.array([1/3,1/3,1/3]),"degen":False,"axis":None}

chanT_streak=[0]
DECAY_WINDOW=100
DECAY_FLOOR=0.3

log=open("switching_log_multifloor_timedecay.csv","w",newline="")
w=csv.writer(log)
w.writerow(["time","mode","fused_x","fused_y","fused_z","fused_qx","fused_qy","fused_qz","fused_qw",
            "feat_count","aft_x","aft_y","aft_z",
            "chanR_degen","chanT_degen","bingham_l1","bingham_l2","bingham_l3",
            "schur_t1","schur_t2","schur_t3",
            "orig_semicircle_degen","orig_l1","orig_l2","orig_l3"])
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

def channel_r_degeneracy(H_l):
    H_rr = H_l[0:3,0:3]; H_rt = H_l[0:3,3:6]
    H_tr = H_l[3:6,0:3]; H_tt = H_l[3:6,3:6]

    try:
        S_tt = H_tt - H_tr @ np.linalg.solve(H_rr + EPS*np.eye(3), H_rt)
    except np.linalg.LinAlgError:
        S_tt = H_tt
    try:
        S_rr = H_rr - H_rt @ np.linalg.solve(H_tt + EPS*np.eye(3), H_tr)
    except np.linalg.LinAlgError:
        S_rr = H_rr

    eig_t = np.linalg.eigvalsh(S_tt)
    eig_r = np.linalg.eigvalsh(S_rr)

    lb_t = np.clip(eig_t, 1e-9, None); lb_t = lb_t/np.linalg.norm(lb_t)
    lb_r = np.clip(eig_r, 1e-9, None); lb_r = lb_r/np.linalg.norm(lb_r)

    degen_t = bool(np.any(lb_t < thr))
    degen_r = bool(np.any(lb_r < thr))

    lever_arm = np.trace(S_rr) / (np.trace(H_tt) + EPS)

    return degen_t or degen_r, lb_t, degen_t, degen_r, lever_arm

def estimate_normals_pca(points, k=BINGHAM_KNN):
    if len(points) < k+1:
        return np.zeros((0,3))
    tree = cKDTree(points)
    normals = []
    n_sample = min(len(points), BINGHAM_SUBSAMPLE)
    idxs = np.random.choice(len(points), n_sample, replace=False)
    for i in idxs:
        _, nn_idx = tree.query(points[i], k=k)
        neigh = points[nn_idx]
        cov = np.cov((neigh - neigh.mean(axis=0)).T)
        eigval, eigvec = np.linalg.eigh(cov)
        normals.append(eigvec[:,0])
    return np.array(normals)

def surf_cloud_cb(msg):
    pts = np.array(list(pc2.read_points(msg, field_names=("x","y","z"), skip_nans=True)), dtype=np.float64)
    if len(pts) < BINGHAM_MIN_NORMALS:
        return
    normals = estimate_normals_pca(pts)
    if len(normals) < BINGHAM_MIN_NORMALS:
        return

    T = np.zeros((3,3))
    for n in normals:
        T += np.outer(n, n)
    T /= len(normals)

    eigval, eigvec = np.linalg.eigh(T)
    lam = eigval

    degen_T = bool(lam[0] < BINGHAM_ISO_THR)

    latest_bingham["lam"] = lam
    latest_bingham["degen"] = degen_T
    latest_bingham["axis"] = eigvec[:,0]

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

    degen_R, lb, chanR_t, chanR_r, lever_arm = channel_r_degeneracy(H_l)

    eig_orig = np.linalg.eigvalsh(H_l)
    lb_orig = np.clip(eig_orig[:3], 1e-9, None); lb_orig = lb_orig/np.linalg.norm(lb_orig)
    degen_orig = bool(np.any(lb_orig < thr))

    degen_T = latest_bingham["degen"]
    bingham_lam = latest_bingham["lam"]

    if degen_T:
        chanT_streak[0] += 1
    else:
        chanT_streak[0] = 0
    chanT_time_decay = max(DECAY_FLOOR, 1.0 - chanT_streak[0]/DECAY_WINDOW)

    degen = bool(degen_R or degen_T)

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
            conf = (chanR_r*1.0 + chanR_t*1.0 + (degen_T*chanT_time_decay)*2.0) / 4.0
            conf = float(np.clip(conf, 0.3, 1.0))
            idx=[3,4,5,0,1,2]
            H_l6=H_l[np.ix_(idx,idx)]
            Hv_w=Hv*conf
            d_l6=np.concatenate([d_l_p,d_l_rv])
            d_v6=np.concatenate([d_v_p,d_v_rv])
            H_sum6=H_l6+Hv_w+EPS*np.eye(6)
            try:
                delta6=np.linalg.solve(H_sum6, H_l6@d_l6+Hv_w@d_v6)
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

    t=rospy.Time.now().to_sec()
    w.writerow([t,mode,T_p[0],T_p[1],T_p[2],T_q[0],T_q[1],T_q[2],T_q[3],
                latest_feat_count[0],
                latest_aft["x"],latest_aft["y"],latest_aft["z"],
                int(degen_R),int(degen_T),bingham_lam[0],bingham_lam[1],bingham_lam[2],
                lb[0],lb[1],lb[2],
                int(degen_orig),lb_orig[0],lb_orig[1],lb_orig[2]])
    log.flush()

    latest_fused["p"]=T_p; latest_fused["q"]=T_q

    prev_l_p=l_p; prev_l_q=l_q; prev_v_p=v_p; prev_v_q=v_q
    prev_T_p=T_p; prev_T_q=T_q
    cnt[0]+=1
    if cnt[0]%20==0:
        print("[%d] %s R(t=%s,r=%s) T=%s lever=%.2f  pos=(%.2f,%.2f,%.2f)"%(
              cnt[0],mode,chanR_t,chanR_r,degen_T,lever_arm,T_p[0],T_p[1],T_p[2]))

def main():
    rospy.init_node("switching_node_multifloor_timedecay",anonymous=True)
    fused_pub[0]=rospy.Publisher("/switch_fused_pose",Odometry,queue_size=10)
    rospy.Subscriber("/feature_tracker/feature",PointCloud,feat_cb)
    rospy.Subscriber("/aft_mapped_to_init",Odometry,aft_cb)
    rospy.Subscriber("/laser_cloud_surf_last",PointCloud2,surf_cloud_cb,queue_size=1)
    h=message_filters.Subscriber("/laser_hessian",Float64MultiArray)
    v=message_filters.Subscriber("/vins_mono_hessian",Float64MultiArray)
    l=message_filters.Subscriber("/laser_odom_to_init",Odometry)
    rospy.Subscriber("/laser_odom_to_init",Odometry,fast_odom_cb)
    vo=message_filters.Subscriber("/vins_estimator/odometry",Odometry)
    ts=message_filters.ApproximateTimeSynchronizer([h,v,l,vo],queue_size=20,slop=0.15,allow_headerless=True)
    ts.registerCallback(sync_cb)
    print("Switching node (multifloor_timedecay) listening...")
    rospy.spin()

if __name__=="__main__":
    try: main()
    finally:
        log.close(); print("Saved switching_log_multifloor_timedecay.csv")
