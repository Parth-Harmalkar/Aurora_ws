## Plan 2.1 Summary: Depth Camera Costmap Integration

### What was done
- Added `depth_image_proc` point_cloud_xyz_node to `mapping.launch.py` to efficiently convert depth images to PointCloud2.
- Remapped `image_rect` to `/camera/depth` and output to `/camera/depth/points`.
- Added `depth_camera` as an additional observation source to both `local_costmap` and `global_costmap` obstacle layers in `nav2_params.yaml`.
- Tuned `depth_camera` constraints: `max_obstacle_height` 1.5, `min_obstacle_height` 0.05, `clearing` false, and `observation_persistence` 0.5 for stable and safe multi-sensor detection alongside lidars.

### Files modified
- `ros2_ws/src/aurora_bringup/launch/mapping.launch.py`
- `ros2_ws/src/aurora_bringup/config/nav2_params.yaml`

### Verification
- Both Python logic and YAML parsed correctly ✓
- Appropriate configuration parameters found in `nav2_params.yaml` and `mapping.launch.py` ✓
