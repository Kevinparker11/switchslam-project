import sys
sys.argv = [sys.argv[0]]
exec(open("figs.py").read().split('if __name__ == "__main__":')[0])

def seg(ax, pts, arrow_end=True, color="#333333", ls="-"):
    xs, ys = zip(*pts)
    ax.plot(xs[:-1] + (xs[-1],), ys[:-1] + (ys[-1],), color=color, lw=1.1, ls=ls) if not arrow_end else None
    if arrow_end:
        ax.plot(xs[:-1], ys[:-1], color=color, lw=1.1, ls=ls)
        ax.plot([xs[-2], xs[-1]], [ys[-2], ys[-1]], color=color, lw=0) 
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1, ls=ls, shrinkA=0, shrinkB=0))

def fig_arch():
    fig = plt.figure(figsize=(7.6, 5.0)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    box(ax, 0.10, 0.84, 0.16, 0.08, "VLP-16 LiDAR", "#f4f4f4", fs=10)
    box(ax, 0.10, 0.56, 0.16, 0.08, "Camera + IMU", "#f4f4f4", fs=10)
    box(ax, 0.335, 0.84, 0.21, 0.10, "A-LOAM\nscan-to-map, Hessian H", "#fdf0e3", fs=9.5)
    box(ax, 0.335, 0.56, 0.21, 0.10, "VINS-Mono\nVIO pose", "#fbe4e1", fs=9.5)
    box(ax, 0.335, 0.30, 0.21, 0.10, "Keyframe scan\nk-NN PCA: normals, edges", "#f4f4f4", fs=9.5)
    box(ax, 0.62, 0.90, 0.25, 0.075, "Channel R: Schur $S_{RR}$\n+ rotation check", "#e8f1fb", fs=9.5)
    box(ax, 0.62, 0.775, 0.25, 0.075, "Channel T: Schur $S_{tt}$", "#e8f1fb", fs=9.5)
    box(ax, 0.62, 0.56, 0.25, 0.10, "Safeguards: VIO-trust check,\nanchored handover,\nmapping-guess guard", "#f6f0dc", fs=9.2)
    box(ax, 0.62, 0.30, 0.25, 0.11, "Additional T (orientation tensor G):\ngmax rule on $S_{tt}$\n+ heading read-out (SAH)", "#e7f5ec", fs=9.2)
    box(ax, 0.90, 0.58, 0.16, 0.36, "Fusion\n\n$W_R$, $W_t$\n\n$\\Delta t = W_t\\Delta t_L$\n$+(I-W_t)\\Delta t_V$", "#ffffff", fs=9.5)
    box(ax, 0.90, 0.12, 0.16, 0.07, "Fused pose", "#ffffff", fs=10)
    arrow(ax, 0.18, 0.84, 0.23, 0.84); arrow(ax, 0.18, 0.56, 0.23, 0.56)
    seg(ax, [(0.10, 0.80), (0.10, 0.30), (0.23, 0.30)])
    arrow(ax, 0.44, 0.86, 0.495, 0.90); arrow(ax, 0.44, 0.82, 0.495, 0.775)
    arrow(ax, 0.44, 0.56, 0.495, 0.56); arrow(ax, 0.44, 0.30, 0.495, 0.30)
    for y0, y1 in [(0.90, 0.72), (0.775, 0.66), (0.56, 0.56), (0.30, 0.46)]:
        arrow(ax, 0.745, y0, 0.82, y1)
    arrow(ax, 0.90, 0.40, 0.90, 0.155)
    seg(ax, [(0.82, 0.12), (0.205, 0.12), (0.205, 0.80), (0.23, 0.80)], color="#1b7f4c", ls="--")
    ax.text(0.45, 0.17, "closed loop: fused pose moved by the VINS motion\nis A-LOAM's initial guess for the next scan", fontsize=8.8, color="#1b7f4c")
    fig.savefig(O + "f3_2_arch.png"); plt.close(fig)

def fig_setup():
    fig = plt.figure(figsize=(7.4, 4.2)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off(); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(Rectangle((0.015, 0.04), 0.97, 0.86, fill=False, ec="#555555", lw=1, ls="--"))
    ax.text(0.03, 0.86, "Laptop (Ubuntu host): Docker network vins_bridge, ROS master 172.17.0.10", fontsize=9.5, color="#555555")
    box(ax, 0.16, 0.66, 0.24, 0.15, "Bag player\n(ros:noetic container)\nrosbag play, 0.33x to 0.5x", "#f4f4f4", fs=9.2)
    box(ax, 0.16, 0.24, 0.24, 0.15, "Gazebo farm world\nHusky: VLP-16,\ncamera, IMU", "#f4f4f4", fs=9.2)
    box(ax, 0.50, 0.66, 0.24, 0.15, "switchslam_gpu_v2\nroscore, A-LOAM,\nfusion_node_v2", "#e8f1fb", fs=9.2)
    box(ax, 0.50, 0.24, 0.24, 0.15, "vinsmono_test\nVINS-Mono feature\ntracker + estimator", "#fbe4e1", fs=9.2)
    box(ax, 0.84, 0.66, 0.24, 0.15, "RViz viewer\n(noetic-desktop-full)\nmap, GT, fused path", "#e7f5ec", fs=9.2)
    box(ax, 0.84, 0.24, 0.24, 0.15, "Logs: switching_log_v2,\nkeyframes, node output\n-> ATE scoring", "#f6f0dc", fs=9.2)
    arrow(ax, 0.28, 0.70, 0.38, 0.70); ax.text(0.295, 0.72, "LiDAR", fontsize=8.5)
    arrow(ax, 0.28, 0.62, 0.38, 0.29); ax.text(0.335, 0.50, "camera,\nIMU", fontsize=8.5)
    arrow(ax, 0.28, 0.20, 0.38, 0.20); ax.text(0.295, 0.135, "camera, IMU", fontsize=8.5)
    arrow(ax, 0.28, 0.28, 0.38, 0.62); 
    arrow(ax, 0.50, 0.315, 0.50, 0.585); ax.text(0.51, 0.45, "VINS odometry", fontsize=8.5)
    arrow(ax, 0.62, 0.66, 0.72, 0.66); arrow(ax, 0.62, 0.60, 0.72, 0.30)
    fig.savefig(O + "f4_1_setup.png"); plt.close(fig)

import re
src = open("figs.py").read()
fig_arch(); fig_setup()
