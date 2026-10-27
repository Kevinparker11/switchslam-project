#!/usr/bin/env python3
import rospy
import numpy as np
from std_msgs.msg import Float64MultiArray

e1=(0+1/np.sqrt(3))/2; e2=(e1+1/np.sqrt(2))/2; e3=(e2+1)/2
e_m=np.array([e1,e2,e3])
thr_old=e_m-np.sqrt(0.103*e_m)
thr_new=thr_old*0.7

cnt=[0,0,0]
def cb(msg):
    H=np.array(msg.data).reshape(6,6)
    eig=np.linalg.eigvalsh(H)
    lb=np.clip(eig[:3],1e-9,None); lb=lb/np.linalg.norm(lb)
    d_old=bool(np.any(lb<thr_old))
    d_new=bool(np.any(lb<thr_new))
    cnt[0]+=1
    cnt[1]+=int(d_old); cnt[2]+=int(d_new)
    if cnt[0]%20==0:
        print("n=%d old_trigger=%d(%.0f%%) new_trigger=%d(%.0f%%)"%(cnt[0],cnt[1],100*cnt[1]/cnt[0],cnt[2],100*cnt[2]/cnt[0]))

rospy.init_node("thr_test")
rospy.Subscriber("/laser_hessian",Float64MultiArray,cb)
print("comparing thresholds, drive normally, Ctrl+C when done")
rospy.spin()
