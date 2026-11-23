# Stock R3LIVE (hku-mars/r3live, original repository, one pinned commit) on ROS Noetic, in its own image.
# Nothing here touches the switchslam_gpu_v2 / vinsmono_test containers.
#   docker build --network host -t r3live_stock fusion_v4/stock_r3live
# Base: the same ros:noetic layers as the laptop's image (pinned by digest), so loading this image there adds only the new layers.
# Build is portable: plain x86-64, no -march=native. r3live's own CMake flags are -O3 -msse2 -msse3 (both SSE, baseline on x86-64
# v1 plus SSE3, present on every CPU used here); check_isa.sh checks the finished binaries.
# Changes to upstream, all listed in the README:
#   livox_ros_driver: message definitions only (livox_msgs_*), at the commit r3live's README points to
#   r3live_rig.patch: the LiDAR-to-IMU offset (compiled in for the authors' Livox Avia) becomes a parameter, default = the upstream value
# Not built: r3live_meshing (needs OpenMVS, not used), the calibration tools.
FROM ros@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d
ARG R3LIVE_COMMIT=6143a38537f28cb36eb24e9bbe2e39c8f7967157
ARG LIVOX_DRIVER_COMMIT=3d240d5666129e1a3052e78ee8487a04b08fdda3
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake git ca-certificates procps binutils \
      python3-numpy python3-yaml python3-scipy python3-opencv \
      xvfb x11-utils \
      ros-noetic-tf ros-noetic-cv-bridge ros-noetic-pcl-conversions ros-noetic-pcl-ros \
      ros-noetic-common-msgs ros-noetic-message-generation ros-noetic-message-runtime \
      ros-noetic-rosbag ros-noetic-image-transport ros-noetic-compressed-image-transport \
      ros-noetic-rospy ros-noetic-roslaunch ros-noetic-rostopic ros-noetic-rosnode ros-noetic-velodyne-pointcloud ros-noetic-nodelet \
      libpcl-dev libopencv-dev libboost-all-dev libeigen3-dev libcgal-dev libtbb-dev \
 && rm -rf /var/lib/apt/lists/*

COPY livox_msgs_CMakeLists.txt livox_msgs_package.xml r3live_rig.patch /tmp/
SHELL ["/bin/bash", "-c"]
RUN mkdir -p /root/r3_ws/src && cd /root/r3_ws/src \
 && git clone https://github.com/Livox-SDK/livox_ros_driver.git /tmp/livox_up && git -C /tmp/livox_up checkout ${LIVOX_DRIVER_COMMIT} \
 && mkdir -p livox_ros_driver/msg && cp /tmp/livox_up/livox_ros_driver/msg/CustomPoint.msg /tmp/livox_up/livox_ros_driver/msg/CustomMsg.msg livox_ros_driver/msg/ \
 && cp /tmp/livox_msgs_CMakeLists.txt livox_ros_driver/CMakeLists.txt && cp /tmp/livox_msgs_package.xml livox_ros_driver/package.xml \
 && rm -rf /tmp/livox_up \
 && git clone https://github.com/hku-mars/r3live.git && cd r3live && git checkout ${R3LIVE_COMMIT} \
 && git apply /tmp/r3live_rig.patch \
 && git rev-parse HEAD > /root/r3_ws/COMMIT && git status --short >> /root/r3_ws/COMMIT \
 && cd /root/r3_ws && source /opt/ros/noetic/setup.bash \
 && catkin_make --pkg livox_ros_driver -DCMAKE_BUILD_TYPE=Release \
 && source devel/setup.bash \
 && catkin_make --pkg r3live -DCMAKE_BUILD_TYPE=Release -j2 --make-args r3live_LiDAR_front_end r3live_mapping

LABEL baseline.method="r3live" baseline.upstream_commit="6143a38537f28cb36eb24e9bbe2e39c8f7967157"
WORKDIR /root/r3_ws
