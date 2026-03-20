---
phase: 2
plan: 1
wave: 1
---

# Plan 2.1: Mapping Foundation

## Objective
Establish the SLAM (Simultaneous Localization and Mapping) foundation using `slam_toolbox` in asynchronous mode, optimized for Jetson Orin Nano.

## Context
- .gsd/SPEC.md
- .gsd/phases/2/RESEARCH.md
- ros2_ws/src/aurora_bringup/launch/foundation.launch.py

## Tasks

<task type="auto">
  <name>Install SLAM & Nav2 Dependencies</name>
  <files></files>
  <action>
    Install the following ROS2 Humble packages:
    - ros-humble-slam-toolbox
    - ros-humble-navigation2
    - ros-humble-nav2-bringup
  </action>
  <verify>ros2 pkg list | grep -E "slam_toolbox|nav2_bringup"</verify>
  <done>Packages are installed and accessible in the environment.</done>
</task>

<task type="auto">
  <name>Configure Async SLAM Toolbox</name>
  <files>ros2_ws/src/aurora_bringup/config/slam_toolbox_async.yaml</files>
  <action>
    Create `slam_toolbox_async.yaml` with the following key settings:
    - mode: async
    - map_update_interval: 2.0
    - resolution: 0.05
    - max_laser_range: 12.0
    - minimum_time_interval: 0.1
    - transform_timeout: 0.2
    - use_scan_matching: true
  </action>
  <verify>test -f ros2_ws/src/aurora_bringup/config/slam_toolbox_async.yaml</verify>
  <done>Configuration file exists with correct async parameters.</done>
</task>

<task type="auto">
  <name>Create Mapping Launch</name>
  <files>ros2_ws/src/aurora_bringup/launch/mapping.launch.py</files>
  <action>
    Create `mapping.launch.py` that:
    1. Includes `foundation.launch.py`.
    2. Starts `slam_toolbox` in `async_slam_toolbox_node` using the new config.
  </action>
  <verify>ros2 launch aurora_bringup mapping.launch.py --summarize</verify>
  <done>Launch file successfully includes all necessary nodes.</done>
</task>

## Success Criteria
- [ ] SLAM Toolbox starts without errors.
- [ ] `/map` topic is published.
- [ ] Robot can generate a map while moving via teleop.
