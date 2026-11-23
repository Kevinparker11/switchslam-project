# Stock LVI-SAM (TixiaoShan/LVI-SAM, original repository, one pinned commit) on ROS Noetic, in its own image.
# Nothing here touches the switchslam_gpu_v2 / vinsmono_test containers.
#   docker build --network host -t lvisam_stock fusion_v4/stock_lvisam
# Base: the same ros:noetic layers as the laptop's image (pinned by digest), so loading this image there adds only the new layers.
# Build is portable: plain x86-64, no -march=native anywhere (LVI-SAM's CMakeLists has none; Ceres is Ubuntu's libceres-dev 1.14,
# GTSAM comes from the borglab PPA or is built from source with GTSAM_BUILD_WITH_MARCH_NATIVE=OFF).
# Two patch files, applied in this order, both listed in the README:
#   lvisam_noetic_build.patch   C++14, <opencv2/opencv.hpp> after the PCL headers, three removed OpenCV 3 constants
#   lvisam_extrinsics.patch     the two hard-coded 180 deg rotations of the authors' rig are read from the VINS config instead
FROM ros@sha256:72b8bc59035dc0a5b8e07aae28c16caa84192971d72d207c72ed734fb1d5e97d
ARG LVISAM_COMMIT=0d822f6dcac3378312f6703b4f45829e049f221a
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake git ca-certificates software-properties-common procps binutils \
      python3-numpy python3-yaml python3-scipy \
      ros-noetic-tf ros-noetic-cv-bridge ros-noetic-pcl-conversions ros-noetic-pcl-ros \
      ros-noetic-common-msgs ros-noetic-message-generation ros-noetic-message-runtime \
      ros-noetic-rosbag ros-noetic-nodelet ros-noetic-velodyne-pointcloud \
      ros-noetic-image-transport ros-noetic-compressed-image-transport \
      ros-noetic-rospy ros-noetic-roslaunch ros-noetic-rostopic ros-noetic-rosnode \
      libpcl-dev libopencv-dev libboost-all-dev libtbb-dev libeigen3-dev \
      libceres-dev libgoogle-glog-dev libatlas-base-dev libsuitesparse-dev \
 && rm -rf /var/lib/apt/lists/*

# GTSAM 4.0 as in the upstream README (borglab PPA); source fallback without -march=native, same as the LIO-SAM image
RUN ( add-apt-repository -y ppa:borglab/gtsam-release-4.0 && apt-get update \
      && apt-get install -y libgtsam-dev libgtsam-unstable-dev ) \
 || ( git clone --depth 1 --branch 4.0.3 https://github.com/borglab/gtsam.git /tmp/gtsam \
      && cmake -S /tmp/gtsam -B /tmp/gtsam/build -DCMAKE_BUILD_TYPE=Release -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF \
           -DGTSAM_USE_SYSTEM_EIGEN=ON -DGTSAM_BUILD_UNSTABLE=ON -DGTSAM_BUILD_TESTS=OFF \
           -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF -DGTSAM_BUILD_TIMING_ALWAYS=OFF -DGTSAM_BUILD_PYTHON=OFF \
      && cmake --build /tmp/gtsam/build -j2 && cmake --install /tmp/gtsam/build && ldconfig \
      && rm -rf /tmp/gtsam )

COPY lvisam_noetic_build.patch lvisam_extrinsics.patch /tmp/
SHELL ["/bin/bash", "-c"]
RUN mkdir -p /root/lvi_ws/src && cd /root/lvi_ws/src \
 && git clone https://github.com/TixiaoShan/LVI-SAM.git && cd LVI-SAM \
 && git checkout ${LVISAM_COMMIT} \
 && git apply /tmp/lvisam_noetic_build.patch && git apply /tmp/lvisam_extrinsics.patch \
 && git rev-parse HEAD > /root/lvi_ws/COMMIT && git status --short >> /root/lvi_ws/COMMIT \
 && cd /root/lvi_ws && source /opt/ros/noetic/setup.bash && catkin_make -j2 -DCMAKE_BUILD_TYPE=Release

LABEL baseline.method="lvisam" baseline.upstream_commit="0d822f6dcac3378312f6703b4f45829e049f221a"
WORKDIR /root/lvi_ws
