## Plan 1.2 Summary: SLAM/Nav2 TF Conflict Fix

### What was done
- Rewrote `navigation.launch.py` with `slam_mode` argument (default: false)
  - Uses `OpaqueFunction` for dynamic lifecycle_nodes list
  - When `slam_mode=true`: map_server excluded from nodes AND lifecycle_nodes
  - When `slam_mode=false`: map_server included normally
  - Renamed `recoveries_server` → `behavior_server` in launch file to match nav2_params.yaml
- Updated `mapping.launch.py` to pass `slam_mode=true` to navigation.launch.py
  - RTAB-Map now has sole ownership of map→odom TF and /map topic in SLAM mode

### Files modified
- `ros2_ws/src/aurora_bringup/launch/navigation.launch.py` (rewritten)
- `ros2_ws/src/aurora_bringup/launch/mapping.launch.py` (launch_arguments updated)

### Verification
- Python syntax valid ✓
- slam_mode argument declared and used ✓
- mapping.launch.py passes slam_mode=true ✓
