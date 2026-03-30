---
phase: 3
plan: 2
wave: 2
depends_on: ["Plan 3.1"]
---

# Plan 3.2: RTAB-Map Persistence Integration

## Objective
Wire the RTAB-Map SLAM properties to correctly save its SLAM graph incrementally (instead of nuking it each time) and register the Map Saver node to the launch system.

## Context
- .gsd/ROADMAP.md (Phase 3 requirements)
- ros2_ws/src/aurora_bringup/launch/mapping.launch.py

## Tasks

<task type="auto">
  <name>Configure RTAB-Map Persistence Parameters</name>
  <files>ros2_ws/src/aurora_bringup/launch/mapping.launch.py</files>
  <action>
    Modify `mapping.launch.py` to handle RTAB-Map DB state properly:
    1. Define a LaunchArgument: `delete_db_on_start` (default 'false').
    2. Within the RTAB-Map Node `parameters=[]` list, explicitly set:
       ```python
       'database_path': '~/.aurora/rtabmap.db'
       ```
    3. Update the `arguments=['-d']` line on the `rtabmap` node to conditionally apply it:
       ```python
       arguments=PythonExpression(["['-d'] if '", LaunchConfiguration('delete_db_on_start'), "' == 'true' else []"])
       ```
    
    Avoid relying on the implicit `~/.ros/` database. The ROS parameter accepts `~/.aurora/rtabmap.db` natively but to be safe, expand the path prior mathematically if not resolved, actually RTAB-Map node itself handles `~`. So passing `'~/.aurora/rtabmap.db'` or using `os.path.expanduser('~/.aurora/rtabmap.db')` locally during python compilation is cleaner. Let's enforce `os.path.expanduser('~/.aurora/rtabmap.db')`.
  </action>
  <verify>grep "delete_db_on_start" ros2_ws/src/aurora_bringup/launch/mapping.launch.py && grep "rtabmap.db" ros2_ws/src/aurora_bringup/launch/mapping.launch.py</verify>
  <done>RTAB-Map conditionally deletes databases and uses aurora home directory consistently.</done>
</task>

<task type="auto">
  <name>Add Map Saver Node to mapping.launch.py</name>
  <files>ros2_ws/src/aurora_bringup/launch/mapping.launch.py</files>
  <action>
    Add the new python script `map_saver_node` to the top level elements inside `mapping.launch.py` (after RTAB-Map starts, since the graph generates the map).
    
    ```python
    # 3.8 Map Saver Node
    Node(
        package='aurora_bringup',
        executable='map_saver_node.py',
        name='map_saver',
        output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
    ),
    ```
    
    Avoid adding this to `foundation.launch.py` because mapping saving only makes sense when the map is produced by SLAM or Nav2 `navigation.launch.py`. Since `mapping.launch.py` wraps everything up, it's the safest boundary.
  </action>
  <verify>grep "map_saver_node" ros2_ws/src/aurora_bringup/launch/mapping.launch.py</verify>
  <done>Map Saver executes with the Nav stack, enabling dynamic backup.</done>
</task>

## Success Criteria
- [ ] RTAB-Map dynamically preserves mapped data across resets when `delete_db_on_start=false`.
- [ ] Map Saver runs seamlessly alongside mapping operations.
- [ ] Verified colcon graph functionality without dependency circles.
