---
phase: 3
plan: 2
wave: 1
---

# Plan 3.2: AI Bridge Node (ROS2/Asyncio)

## Objective
Create the foundational ROS 2 node that bridges the robot's ecosystem with the LLM/reasoning layer using asynchronous I/O.

## Context
- .gsd/SPEC.md
- .gsd/phases/3/RESEARCH.md
- aurora_bringup/launch/foundation.launch.py

## Tasks

<task type="auto">
  <name>Create AI Bridge Package</name>
  <files>[ros2_ws/src/aurora_ai_bridge]</files>
  <action>
    Create a new ament_python package named `aurora_ai_bridge`.
    Define dependencies in `package.xml`: `rclpy`, `std_msgs`, `geometry_msgs`, `sensor_msgs`.
  </action>
  <verify>ros2 pkg list | grep aurora_ai_bridge</verify>
  <done>Package created and detectable by the ROS 2 environment.</done>
</task>

<task type="auto">
  <name>Implement Async AI Bridge Node</name>
  <files>[ros2_ws/src/aurora_ai_bridge/aurora_ai_bridge/ai_bridge_node.py]</files>
  <action>
    Implement a node using `asyncio` to handle ROS 2 spinning and Ollama API calls concurrently.
    Add Subscriptions: `/voice_command` (String), `/imu/data`, `/odom`.
    Add Publishers: `/ai_vel` (Twist), `/ai_status` (String).
    Implement a simple "Echo" logic to verify the async flow.
  </action>
  <verify>ros2 run aurora_ai_bridge ai_bridge_node</verify>
  <done>Node spins and processes callbacks without blocking the main event loop.</done>
</task>

## Success Criteria
- [ ] `aurora_ai_bridge` package functional.
- [ ] `ai_bridge_node` implements `asyncio` + `rclpy` bridge pattern.
- [ ] Subscribing and publishing is verified via `ros2 topic`.
