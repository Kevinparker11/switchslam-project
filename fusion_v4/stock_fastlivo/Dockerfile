# Stock FAST-LIVO (hku-mars/FAST-LIVO, original repository, one pinned commit) on ROS Noetic, in its own image.
# Nothing here touches the switchslam_gpu_v2 / vinsmono_test containers.
#   docker build --network host -t fastlivo_stock fusion_v4/stock_fastlivo
# Base: the same ros:noetic layers as the laptop's image (pinned by digest). The first three apt steps are the same text as in the R3LIVE
# and R2LIVE images, so Docker reuses their layers on the desktop and stores them once on the laptop.
# Build is portable: plain x86-64, no -march=native anywhere (FAST-LIVO's CMake has none). Upstream sets the build type to Debug in its own CMakeLists
# (with -O3 in the flags); that stays. CMake counts the build machine's cores for the OpenMP setting (MP_PROC_NUM); the image is built once on the
# desktop and shipped, so the laptop runs the same binary.
# Dependencies built from source, the ones the FAST-LIVO README names: Sophus (a621ff, non-templated version), rpg_vikit, livox_ros_driver (messages only).
# Changes to upstream, all listed in the README:
#   sophus_noetic_build.patch, vikit_noetic_build.patch, fastlivo_noetic_build.patch: build fixes for GCC 9 / OpenCV 4
#   fastlivo_rig.patch: the Odometry message is stamped with the time of its state instead of the wall clock at publication
FROM ros@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d
ARG FASTLIVO_COMMIT=f7e1af5b10c89ba38c5e2c5e4d458195c58eba6b
ARG VIKIT_COMMIT=10871da6d84c8324212053c40f468c6ab4862ee0
ARG SOPHUS_COMMIT=a621ff2e56c56c839a6c40418d42c3c254424b5c
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
      libpython3-dev python3-dev \
 && rm -rf /var/lib/apt/lists/*

COPY livox_msgs_CMakeLists.txt livox_msgs_package.xml sophus_noetic_build.patch vikit_noetic_build.patch fastlivo_noetic_build.patch fastlivo_rig.patch /tmp/
SHELL ["/bin/bash", "-c"]
# Sophus: "make install" puts headers and libSophus.so in /usr/local; the build folder stays (its CMake package file is registered from there)
RUN git clone https://github.com/strasdat/Sophus.git /root/Sophus && cd /root/Sophus && git checkout ${SOPHUS_COMMIT} \
 && git apply /tmp/sophus_noetic_build.patch \
 && mkdir build && cd build && cmake -DCMAKE_SKIP_INSTALL_ALL_DEPENDENCY=ON .. && make -j2 Sophus && make install && ldconfig
RUN mkdir -p /root/fl_ws/src && cd /root/fl_ws/src \
 && git clone https://github.com/Livox-SDK/livox_ros_driver.git /tmp/livox_up && git -C /tmp/livox_up checkout ${LIVOX_DRIVER_COMMIT} \
 && mkdir -p livox_ros_driver/msg && cp /tmp/livox_up/livox_ros_driver/msg/CustomPoint.msg /tmp/livox_up/livox_ros_driver/msg/CustomMsg.msg livox_ros_driver/msg/ \
 && cp /tmp/livox_msgs_CMakeLists.txt livox_ros_driver/CMakeLists.txt && cp /tmp/livox_msgs_package.xml livox_ros_driver/package.xml \
 && rm -rf /tmp/livox_up \
 && git clone https://github.com/uzh-rpg/rpg_vikit.git && git -C rpg_vikit checkout ${VIKIT_COMMIT} && git -C rpg_vikit apply /tmp/vikit_noetic_build.patch \
 && git clone https://github.com/hku-mars/FAST-LIVO.git && cd FAST-LIVO && git checkout ${FASTLIVO_COMMIT} \
 && git apply /tmp/fastlivo_noetic_build.patch && git apply /tmp/fastlivo_rig.patch \
 && git rev-parse HEAD > /root/fl_ws/COMMIT && git status --short >> /root/fl_ws/COMMIT \
 && git -C ../rpg_vikit rev-parse HEAD >> /root/fl_ws/COMMIT && git -C /root/Sophus rev-parse HEAD >> /root/fl_ws/COMMIT \
 && cd /root/fl_ws && source /opt/ros/noetic/setup.bash \
 && catkin_make --pkg livox_ros_driver -DCMAKE_BUILD_TYPE=Release \
 && source devel/setup.bash \
 && catkin_make --pkg vikit_common vikit_ros -DCMAKE_BUILD_TYPE=Release -j2 \
 && source devel/setup.bash \
 && catkin_make --pkg fast_livo -DCMAKE_BUILD_TYPE=Release -j2

LABEL baseline.method="fastlivo" baseline.upstream_commit="f7e1af5b10c89ba38c5e2c5e4d458195c58eba6b"
WORKDIR /root/fl_ws
