# Phase 3 Research: Map Persistence & Management

## 1. Custom Messages Package (`aurora_msgs`)
The `aurora_msgs` directory exists but lacks initialization (no `CMakeLists.txt` or `package.xml`). We need to:
- Establish it as a ROS2 `ament_cmake` package.
- Depend on `rosidl_default_generators` and `rosidl_default_runtime`.
- Define `srv/SaveMap.srv`.
```
string map_name
---
bool success
string message
```

## 2. Nav2 Map Saver Integration
Nav2 provides `nav2_map_server` and its `map_saver_cli`. The python `map_saver_node.py` will:
- Provide a `SaveMap` service.
- On request, format a target map name (e.g. `~/.aurora/maps/<name>`).
- Run `ros2 run nav2_map_server map_saver_cli -f ~/.aurora/maps/<name>` as a shell command (or use the python API, but the CLI wrapper is most reliable across different Nav2 setups).
- Auto-save on a 5-minute timer utilizing the same CLI.

## 3. RTAB-Map Persistence
- **Default Behavior**: Right now, `mapping.launch.py` hardcodes `arguments=['-d']` which wipes the RTAB-Map DB at start.
- **Conditional Erasure**: We will replace `arguments=['-d']` with `LaunchConfiguration('delete_db_on_start')`, resolving it dynamically:
  ```python
  arguments=PythonExpression(["['-d'] if '", delete_db_on_start, "' == 'true' else []"])
  ```
- **DB Path**: `~/.aurora/rtabmap.db` must be passed as `database_path` to the RTAB-Map node.
- The `~/.aurora/` directory will be created if it doesn't exist.
