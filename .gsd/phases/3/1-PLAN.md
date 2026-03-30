---
phase: 3
plan: 1
wave: 1
---

# Plan 3.1: Map Persistence & Core Services

## Objective
Initialize the `aurora_msgs` package to provide custom services and create the auto-saving map node (`map_saver_node`) that integrates with Nav2 to save occupancy grids every 5 minutes and on-demand via a `/save_map` service call.

## Context
- .gsd/ROADMAP.md (Phase 3 requirements)
- .gsd/phases/3/RESEARCH.md
- ros2_ws/src/aurora_msgs/
- ros2_ws/src/aurora_bringup/CMakeLists.txt

## Tasks

<task type="auto">
  <name>Initialize aurora_msgs package</name>
  <files>
    ros2_ws/src/aurora_msgs/CMakeLists.txt
    ros2_ws/src/aurora_msgs/package.xml
    ros2_ws/src/aurora_msgs/srv/SaveMap.srv
  </files>
  <action>
    Create the ROS2 standard CMake files for generating custom services.
    - Write `package.xml` specifying `aurora_msgs` package, `rosidl_default_generators` (buildtool), `rosidl_default_runtime` (exec).
    - Write `CMakeLists.txt` with `find_package(rosidl_default_generators REQUIRED)` and `rosidl_generate_interfaces` including `srv/SaveMap.srv`.
    - Create `srv/SaveMap.srv` containing:
      ```
      string map_name
      ---
      bool success
      string message
      ```
    
    Avoid using Python for a `msgs` package; standard ROS2 msg packages must use `ament_cmake`.
  </action>
  <verify>test -f ros2_ws/src/aurora_msgs/CMakeLists.txt && test -f ros2_ws/src/aurora_msgs/srv/SaveMap.srv</verify>
  <done>aurora_msgs supports generating SaveMap.srv</done>
</task>

<task type="auto">
  <name>Create map_saver Python script inside aurora_bringup</name>
  <files>
    ros2_ws/src/aurora_bringup/scripts/map_saver_node.py
    ros2_ws/src/aurora_bringup/CMakeLists.txt
  </files>
  <action>
    1. Create `ros2_ws/src/aurora_bringup/scripts/map_saver_node.py`:
       - Use `rclpy`. The node provides `/save_map` (`SaveMap` service from `aurora_msgs.srv`).
       - Implements a 5-minute timer that automatically calls the save function with a generated timestamp name.
       - The save function calls `os.system("ros2 run nav2_map_server map_saver_cli -f ~/.aurora/maps/<name>")`.
       - Before saving, ensure `~/.aurora/maps/` directory exists (`os.makedirs(os.path.expanduser('~/.aurora/maps'), exist_ok=True)`).
    2. Make the file executable. Note: Since `aurora_bringup` is an `ament_cmake` package, update `CMakeLists.txt`:
       - Add an `install(PROGRAMS scripts/map_saver_node.py DESTINATION lib/${PROJECT_NAME})` rule at the bottom to expose it as an executable binary.
       
    Avoid manually calling Nav2 library C++ functions; dropping to shell (`map_saver_cli`) is vastly more reliable and avoids threading deadlocks.
  </action>
  <verify>grep "install(PROGRAMS" ros2_ws/src/aurora_bringup/CMakeLists.txt && test -f ros2_ws/src/aurora_bringup/scripts/map_saver_node.py</verify>
  <done>map_saver_node.py implemented and registered in CMakeLists.txt</done>
</task>

## Success Criteria
- [ ] aurora_msgs package has CMakeLists and package.xml
- [ ] SaveMap.srv is defined
- [ ] map_saver_node script relies on map_saver_cli and handles 5min repeating saves
- [ ] aurora_bringup builds and installs the script properly
