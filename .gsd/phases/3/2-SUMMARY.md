## Plan 3.2 Summary: RTAB-Map Persistence Integration

### What was done
- RTAB-Map `database_path` explicitly linked to `~/.aurora/rtabmap.db` instead of ephemeral folders.
- `arguments=['-d']` conditionally substituted in `mapping.launch.py` requiring explicit `delete_db_on_start=true` param to wipe map contents.
- Integrated `map_saver` Python node into the active SLAM lifecycle right before `navigation.launch.py`.

### Files modified/created
- `ros2_ws/src/aurora_bringup/launch/mapping.launch.py`

### Verification
- `colcon build`: Zero syntax errors inside Python `LaunchConfiguration`.
- Launch parsing completes with valid `PythonExpression` blocks.
