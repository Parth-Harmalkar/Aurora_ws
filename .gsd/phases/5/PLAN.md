---
phase: 5
plan: 1
wave: 1
---

# Plan 5.1: Semantic Memory Package & Message Setup

## Objective
Establish the foundational ROS 2 package and custom service interface for persistent semantic memory.

## Context
- .gsd/SPEC.md
- .gsd/ROADMAP.md
- .gsd/phases/5/RESEARCH.md
- aurora_msgs (existing custom messages)

## Tasks

<task type="auto">
  <name>Create GetObjectPose Service</name>
  <files>
    - ros2_ws/src/aurora_msgs/srv/GetObjectPose.srv
    - ros2_ws/src/aurora_msgs/CMakeLists.txt
  </files>
  <action>
    Define GetObjectPose.srv (request: label, response: success, pose, message).
    Register the new service in CMakeLists.txt using rosidl_generate_interfaces.
  </action>
  <verify>colcon build --packages-select aurora_msgs</verify>
  <done>aurora_msgs builds successfully with the new service definition.</done>
</task>

<task type="auto">
  <name>Create aurora_semantic_memory Package</name>
  <files>
    - ros2_ws/src/aurora_semantic_memory/package.xml
    - ros2_ws/src/aurora_semantic_memory/setup.py
    - ros2_ws/src/aurora_semantic_memory/resource/aurora_semantic_memory
  </files>
  <action>
    Initialize a clean ament_python package.
    Add dependencies: rclpy, tf2_ros, tf2_geometry_msgs, vision_msgs, aurora_msgs, geometry_msgs, visualization_msgs.
  </action>
  <verify>colcon build --packages-select aurora_semantic_memory</verify>
  <done>The new package builds successfully within the workspace.</done>
</task>

## Success Criteria
- [ ] aurora_msgs contains GetObjectPose service.
- [ ] aurora_semantic_memory is a buildable ROS 2 package.

---

---
phase: 5
plan: 2
wave: 2
---

# Plan 5.2: Core Semantic Memory Node

## Objective
Implement the semantic_memory_node with coordinate transformation, clustering logic, and SQLite persistence.

## Context
- ros2_ws/src/aurora_camera/aurora_camera/camera_node.py (reference for detection output)
- .gsd/phases/5/RESEARCH.md (schema and clustering logic)

## Tasks

<task type="auto">
  <name>Implement Semantic Memory Node</name>
  <files>
    - ros2_ws/src/aurora_semantic_memory/aurora_semantic_memory/semantic_memory_node.py
  </files>
  <action>
    - Initialize SQLite database at ~/.aurora/semantic_memory.db.
    - Subscribe to /camera/detections.
    - Transform detections from camera_optical_frame to map frame.
    - Implement distance-based association (0.5m threshold).
    - Implement GetObjectPose service server.
  </action>
  <verify>ros2 run aurora_semantic_memory semantic_memory_node</verify>
  <done>Node initializes without errors and connects to the database.</done>
</task>

<task type="auto">
  <name>Integrate with Intelligence Launch</name>
  <files>
    - ros2_ws/src/aurora_bringup/launch/intelligence.launch.py
  </files>
  <action>
    Add the semantic_memory_node to the intelligence.launch.py stack.
  </action>
  <verify>ros2 launch aurora_bringup intelligence.launch.py</verify>
  <done>Full intelligence stack (including memory) launches correctly.</done>
</task>

## Success Criteria
- [ ] Objects detected by the camera are saved to the SQLite database.
- [ ] Objects are persistent across node restarts.
- [ ] Service /get_object_pose returns correct coordinates.
