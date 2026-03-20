---
phase: 2
plan: 3
wave: 2
---

# Plan 2.3: Short-Range Perception Integration

## Objective
Integrate the ultrasonic range data into the Nav2 costmaps to provide short-range protection against obstacles that Lidar might miss.

## Context
- .gsd/phases/2/RESEARCH.md
- ros2_ws/src/aurora_bringup/config/nav2_params.yaml

## Tasks

<task type="auto">
  <name>Integrate Range into Costmaps</name>
  <files>ros2_ws/src/aurora_bringup/config/nav2_params.yaml</files>
  <action>
    - Add `RangeSensorLayer` to `local_costmap` and `global_costmap` plugins.
    - Configure `range_sensor_layer` to subscribe to `/ultrasonic/front_left` and `/ultrasonic/front_right`.
    - Set `topics: ["/ultrasonic/front_left", "/ultrasonic/front_right"]`.
  </action>
  <verify>ros2 param get /local_costmap/local_costmap plugins</verify>
  <done>Range sensor layer is active in Nav2 costmap configuration.</done>
</task>

<task type="auto">
  <name>Define Ultrasonic Transforms</name>
  <files>ros2_ws/src/aurora_bringup/launch/foundation.launch.py</files>
  <action>
    Add static transform publishers for the two ultrasonic sensors:
    - `ultrasonic_front_left`: x=0.15, y=0.1, z=0.05
    - `ultrasonic_front_right`: x=0.15, y=-0.1, z=0.05
    (Adjust coordinates as per physical robot mounting).
  </action>
  <verify>ros2 run tf2_ros tf2_echo base_link ultrasonic_front_left</verify>
  <done>Static transforms for ultrasonic sensors are published.</done>
</task>

## Success Criteria
- [ ] Ultrasonic readings appear as obstacles in the local costmap.
- [ ] Robot stops or replans when ultrasonic sensors detect a close-range obstacle.
- [ ] Unified foundation + navigation launch is operational.
