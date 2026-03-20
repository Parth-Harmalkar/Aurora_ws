---
phase: 2
plan: 2
wave: 1
---

# Plan 2.2: Navigation & Safety Architecture

## Objective
Configure Navigation2 with low-memory optimizations and prepare the system for short-range obstacle avoidance.

## Context
- .gsd/SPEC.md
- .gsd/phases/2/RESEARCH.md
- ros2_ws/src/aurora_bringup/config/twist_mux.yaml

## Tasks

<task type="auto">
  <name>Configure Low-Memory Nav2</name>
  <files>ros2_ws/src/aurora_bringup/config/nav2_params.yaml</files>
  <action>
    Create `nav2_params.yaml` optimized for 8GB RAM:
    - Set `use_composition: true` for all servers.
    - Configure `controller_server` with `RegulatedPurePursuitController`.
    - Configure `bt_navigator` with standard defaults.
    - Minimal costmap layers (Static, Obstacle, Inflation).
  </action>
  <verify>test -f ros2_ws/src/aurora_bringup/config/nav2_params.yaml</verify>
  <done>Nav2 parameters file created with memory-saving settings.</done>
</task>

<task type="auto">
  <name>Update Ultrasonic Bridging</name>
  <files>ros2_ws/src/aurora_ultrasonic/aurora_ultrasonic/ultra_node.py</files>
  <action>
    Modify `ultra_node.py` to:
    - Publish `sensor_msgs/msg/Range` instead of `Float32MultiArray`.
    - Create two publishers: `/ultrasonic/front_left` and `/ultrasonic/front_right`.
    - Set field_of_view (0.5 rad), min_range (0.02), max_range (2.0) for HC-SR04.
    - Convert cm readings to meters (value / 100.0).
  </action>
  <verify>ros2 topic info /ultrasonic/front_left</verify>
  <done>Ultrasonic node publishes standard Range messages.</done>
</task>

<task type="auto">
  <name>Update Ultrasonic Metadata</name>
  <files>ros2_ws/src/aurora_ultrasonic/package.xml</files>
  <action>
    Add `sensor_msgs` to the dependencies in `package.xml`.
  </action>
  <verify>grep "sensor_msgs" ros2_ws/src/aurora_ultrasonic/package.xml</verify>
  <done>Package dependencies are correctly updated.</done>
</task>

## Success Criteria
- [ ] Nav2 can be launched with composed nodes.
- [ ] Ultrasonic sensors publish standard `Range` messages in meters.
- [ ] Memory usage remains stable during Nav2 startup.
