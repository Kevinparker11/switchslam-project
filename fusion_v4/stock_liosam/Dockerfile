# Stock LIO-SAM (TixiaoShan/LIO-SAM, original repository, one pinned commit) on ROS Noetic, in its own image.
# Nothing here touches the switchslam_gpu_v2 / vinsmono_test containers.
#   docker build -t liosam_stock fusion_v4/stock_liosam
# The upstream code targets Ubuntu 16/18 (Kinetic/Melodic). On Noetic it needs exactly two build fixes, kept as a
# patch file (liosam_noetic_build.patch): C++14 instead of C++11 (PCL 1.10) and <opencv2/opencv.hpp> instead of the
# removed <opencv/cv.h>, included after the PCL headers (OpenCV first breaks FLANN's serialization). No algorithm file
# is changed.
FROM ros:noetic
ARG LIOSAM_COMMIT=0be1fbe6275fb8366d5b800af4fc8c76a885c869
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake git ca-certificates software-properties-common procps \
      python3-numpy python3-yaml python3-scipy \
      ros-noetic-tf ros-noetic-cv-bridge ros-noetic-pcl-conversions ros-noetic-pcl-ros \
      ros-noetic-common-msgs ros-noetic-rosbag ros-noetic-nodelet ros-noetic-velodyne-pointcloud \
      ros-noetic-rospy ros-noetic-roslaunch ros-noetic-rostopic ros-noetic-rosnode \
      libpcl-dev libopencv-dev libboost-all-dev libtbb-dev libeigen3-dev \
 && rm -rf /var/lib/apt/lists/*

# GTSAM 4.0 as in the upstream README (borglab PPA). If the PPA has no package for this Ubuntu, build 4.0.3 from source
# with the same options the PPA uses for LIO-SAM (no -march=native, which breaks Eigen alignment against LIO-SAM).
RUN ( add-apt-repository -y ppa:borglab/gtsam-release-4.0 && apt-get update \
      && apt-get install -y libgtsam-dev libgtsam-unstable-dev ) \
 || ( git clone --depth 1 --branch 4.0.3 https://github.com/borglab/gtsam.git /tmp/gtsam \
      && cmake -S /tmp/gtsam -B /tmp/gtsam/build -DCMAKE_BUILD_TYPE=Release -DGTSAM_BUILD_WITH_MARCH_NATIVE=OFF \
           -DGTSAM_USE_SYSTEM_EIGEN=ON -DGTSAM_BUILD_UNSTABLE=ON -DGTSAM_BUILD_TESTS=OFF \
           -DGTSAM_BUILD_EXAMPLES_ALWAYS=OFF -DGTSAM_BUILD_TIMING_ALWAYS=OFF -DGTSAM_BUILD_PYTHON=OFF \
      && cmake --build /tmp/gtsam/build -j2 && cmake --install /tmp/gtsam/build && ldconfig \
      && rm -rf /tmp/gtsam )

COPY liosam_noetic_build.patch /tmp/liosam_noetic_build.patch
SHELL ["/bin/bash", "-c"]
RUN mkdir -p /root/lio_ws/src && cd /root/lio_ws/src \
 && git clone https://github.com/TixiaoShan/LIO-SAM.git && cd LIO-SAM \
 && git checkout ${LIOSAM_COMMIT} && git apply /tmp/liosam_noetic_build.patch \
 && git rev-parse HEAD > /root/lio_ws/COMMIT && git status --short >> /root/lio_ws/COMMIT \
 && cd /root/lio_ws && source /opt/ros/noetic/setup.bash && catkin_make -j2 -DCMAKE_BUILD_TYPE=Release

WORKDIR /root/lio_ws
