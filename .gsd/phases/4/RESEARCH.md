# Phase 4 Research: OAK-D Lite on ROS 2 Humble

## Overview
The goal is to integrate the OAK-D Lite (DepthAI) camera into the existing ROS 2 Humble stack on the Jetson Orin Nano. This provides Visual SLAM and Scene Understanding capabilities without overloading the CPU.

## 1. DepthAI ROS 2 Integration
Luxonis provides the `depthai-ros` ecosystem natively for ROS 2 Humble.
- **Key Package**: `depthai_ros_driver`
- **Primary Topics**: `/camera/color/image_raw`, `/camera/stereo/depth`, and Spatial Object Bounding Boxes.
- **Hardware Advantage**: The Jetson Orin Nano is heavily constrained to 8GB unified RAM. The OAK-D Lite features a Myriad X VPU. All depth calculations and neural network inference (like YOLOv4) run *on the camera itself*, freeing the Jetson strictly for LangGraph AI reasoning and Nav2 execution.

## 2. Sensor Fusion Strategy
- **Current Architecture**: Nav2 calculates costmaps purely from Lidar (2D) and Ultrasonics (1D).
- **Camera Integration**: The OAK-D depth map will be published as a `PointCloud2`. Nav2's `obstacle_layer` can consume this directly via `observation_sources` to detect overhangs and 3D obstacles the 2D Lidar misses.

## 3. Implementation Risks & Limits
- **Power**: The OAK-D Lite draws heavy power over USB3. Ensure the Jetson USB ports provide stable current.
- **Bandwidth**: Publishing raw RGB + Depth Pointclouds over ROS DDS can choke the local network. We must ensure the `depthai_ros_driver` uses intra-process communication or down-samples the pointcloud before broadcasting it to Nav2.

## 4. Immediate Steps
1. Install `ros-humble-depthai-ros`.
2. Wrap `depthai_ros_driver` in an `aurora_bringup` launch file.
3. Setup `tf2` transformations mapping the `oak` frame to `base_link`.
