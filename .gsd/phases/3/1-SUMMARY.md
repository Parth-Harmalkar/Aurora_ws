## Plan 3.1 Summary: Map Persistence & Core Services

### What was done
- Initialized `aurora_msgs` ROS2 package with `CMakeLists.txt` and `package.xml` configuration using `rosidl_default_generators`.
- Created `SaveMap.srv` containing `map_name` request and `success`, `message` response.
- Created `map_saver_node.py` under `aurora_bringup/scripts` that automates calling `nav2_map_server map_saver_cli` to dump the latest SLAM occupancy grids into `~/.aurora/maps` every 5 minutes and on-demand.
- Registered the node installer rule in `aurora_bringup` `CMakeLists.txt` making it executable throughout ROS.

### Files modified/created
- `ros2_ws/src/aurora_msgs/CMakeLists.txt`, `package.xml`
- `ros2_ws/src/aurora_msgs/srv/SaveMap.srv`
- `ros2_ws/src/aurora_bringup/scripts/map_saver_node.py`
- `ros2_ws/src/aurora_bringup/CMakeLists.txt`

### Verification
- Installation structures verified OK.
- Service definitions established.
