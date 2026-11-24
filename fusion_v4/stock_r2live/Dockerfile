# Stock R2LIVE (hku-mars/r2live, original repository, one pinned commit) on ROS Noetic, in its own image.
# Nothing here touches the switchslam_gpu_v2 / vinsmono_test containers.
#   docker build --network host -t r2live_stock fusion_v4/stock_r2live
# Base: the same ros:noetic layers as the laptop's image (pinned by digest). The first three apt steps are the same text as in the R3LIVE
# image, so on the desktop Docker reuses their layers and on the laptop they are stored once for both images.
# Build is portable: plain x86-64, no -march=native anywhere (r2live's CMake has none; Ceres is Ubuntu's libceres-dev 1.14, the version r2live's docker file builds).
# Changes to upstream, all listed in the README:
#   livox_ros_driver: message definitions only (livox_msgs_*), the commit r2live's README points to
#   r2live_noetic_build.patch: OpenCV 4 / PCL 1.10 build fixes (listed in the README)
#   r2live_rig.patch: the LiDAR-to-IMU offset (compiled in for the authors' Livox Avia) becomes a parameter, default = the upstream value
FROM ros@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d
ARG R2LIVE_COMMIT=e719ca266ab53ca8915ca4e1416152993f2a55d7
ARG LIVOX_DRIVER_COMMIT=3d240d5666129e1a3052e78ee8487a04b08fdda3
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends -o Acquire::Retries=10 --fix-missing \
      build-essential cmake git ca-certificates procps binutils libpcl-dev libopencv-dev \
 && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends -o Acquire::Retries=10 --fix-missing \
      libboost-all-dev libeigen3-dev libcgal-dev libtbb-dev xvfb x11-utils \
      python3-numpy python3-yaml python3-scipy python3-opencv \
 && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends -o Acquire::Retries=10 --fix-missing \
      ros-noetic-tf ros-noetic-cv-bridge ros-noetic-pcl-conversions ros-noetic-pcl-ros \
      ros-noetic-common-msgs ros-noetic-message-generation ros-noetic-message-runtime \
      ros-noetic-rosbag ros-noetic-image-transport ros-noetic-compressed-image-transport \
      ros-noetic-rospy ros-noetic-roslaunch ros-noetic-rostopic ros-noetic-rosnode ros-noetic-velodyne-pointcloud ros-noetic-nodelet \
      ros-noetic-eigen-conversions \
 && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends -o Acquire::Retries=10 --fix-missing \
      libceres-dev libgoogle-glog-dev libatlas-base-dev libsuitesparse-dev libpython3-dev \
      ros-noetic-message-filters \
 && rm -rf /var/lib/apt/lists/*

COPY livox_msgs_CMakeLists.txt livox_msgs_package.xml r2live_noetic_build.patch r2live_rig.patch /tmp/
SHELL ["/bin/bash", "-c"]
# The r2live executables include their own generated message headers (States.h) without declaring the dependency, so the message target is built
# first (a parallel build otherwise races and fails with 'r2live/States.h: No such file').
# livox_ros_driver (messages only) in its own workspace: r2live's package.xml does not declare it as a dependency, so in one workspace catkin may
# configure r2live before the messages exist. r2_ws is built on top of this workspace and its setup.bash chains to it at run time.
RUN mkdir -p /root/livox_ws/src/livox_ros_driver/msg && cd /root/livox_ws/src \
 && git clone https://github.com/Livox-SDK/livox_ros_driver.git /tmp/livox_up && git -C /tmp/livox_up checkout ${LIVOX_DRIVER_COMMIT} \
 && cp /tmp/livox_up/livox_ros_driver/msg/CustomPoint.msg /tmp/livox_up/livox_ros_driver/msg/CustomMsg.msg livox_ros_driver/msg/ \
 && cp /tmp/livox_msgs_CMakeLists.txt livox_ros_driver/CMakeLists.txt && cp /tmp/livox_msgs_package.xml livox_ros_driver/package.xml \
 && rm -rf /tmp/livox_up \
 && cd /root/livox_ws && source /opt/ros/noetic/setup.bash && catkin_make -DCMAKE_BUILD_TYPE=Release
RUN mkdir -p /root/r2_ws/src && cd /root/r2_ws/src \
 && git clone https://github.com/hku-mars/r2live.git && cd r2live && git checkout ${R2LIVE_COMMIT} \
 && git apply /tmp/r2live_noetic_build.patch && git apply /tmp/r2live_rig.patch \
 && git rev-parse HEAD > /root/r2_ws/COMMIT && git status --short >> /root/r2_ws/COMMIT \
 && cd /root/r2_ws && source /root/livox_ws/devel/setup.bash \
 && catkin_make --pkg camera_model feature_tracker -DCMAKE_BUILD_TYPE=Release -j2 \
 && catkin_make --pkg r2live -DCMAKE_BUILD_TYPE=Release --make-args r2live_generate_messages \
 && catkin_make --pkg r2live -DCMAKE_BUILD_TYPE=Release -j2

LABEL baseline.method="r2live" baseline.upstream_commit="e719ca266ab53ca8915ca4e1416152993f2a55d7"
WORKDIR /root/r2_ws
