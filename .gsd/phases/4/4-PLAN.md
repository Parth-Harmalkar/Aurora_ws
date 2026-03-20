---
phase: 4
plan: 1
wave: 1
---

# Plan 4.1: OAK-D Lite Hardware Base Integration

## Objective
Integrate the OAK-D Lite camera into the ROS 2 Humble stack using `depthai-ros` to enable basic RGB and depth node publishing. This establishes the visual layer required for upcoming semantic tracking missions.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md (Phase 4 goals)
- .gsd/phases/4/RESEARCH.md

## Tasks

<task type="auto">
  <name>Scaffold OAK-D ROS 2 Launch Configuration</name>
  <files>
    - /home/aurora/aurora_ws/ros2_ws/src/aurora_bringup/package.xml
    - /home/aurora/aurora_ws/ros2_ws/src/aurora_bringup/launch/camera.launch.py
  </files>
  <action>
    - Install `ros-humble-depthai-ros` via apt to the physical system.
    - Add `depthai_ros_driver` as an `<exec_depend>` in `aurora_bringup/package.xml`.
    - Create a ROS 2 launch file `camera.launch.py` inside `aurora_bringup/launch/` that includes the standard `camera.launch.py` from the `depthai_ros_driver` package.
  </action>
  <verify>Check package.xml syntatically and ensure camera.launch.py loads without failing.</verify>
  <done>The launch file for the camera successfully interfaces with DepthAI.</done>
</task>

<task type="auto">
  <name>Integrate Camera to Master Bringup</name>
  <files>
    - /home/aurora/aurora_ws/ros2_ws/src/aurora_bringup/launch/aurora_all.launch.py
  </files>
  <action>
    - Include the custom `camera.launch.py` inside the master `aurora_all.launch.py`.
    - Add a static transform from `base_link` to `camera_link` (assumed top-forward mounting, approx `[0.10, 0, 0.20]` for X Y Z).
  </action>
  <verify>`ros2 launch aurora_bringup aurora_all.launch.py` runs without crashing and publishes `camera_link` TF.</verify>
  <done>Camera framework initializes autonomously alongside Lidar and Motors.</done>
</task>

## Success Criteria
- [ ] `depthai-ros` ecosystem is cleanly referenced in the workspace.
- [ ] RGB and Depth output topics appear on the DDS network when launched.
- [ ] The `tf2` tree successfully bridges `camera_link` to the robot's `base_link`.
