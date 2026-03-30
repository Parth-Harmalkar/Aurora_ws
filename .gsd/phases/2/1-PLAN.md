---
phase: 2
plan: 1
wave: 1
depends_on: []
files_modified:
  - ros2_ws/src/aurora_bringup/launch/mapping.launch.py
  - ros2_ws/src/aurora_bringup/config/nav2_params.yaml
autonomous: true
---

# Plan 2.1: Depth Camera Costmap Integration

## Objective
Add depth_image_proc point_cloud_xyz_node to mapping launch, wire depth PointCloud2 into both costmap obstacle layers alongside lidar.

## Tasks

<task type="auto">
  <name>Add depth_image_proc to mapping launch + add depth to costmaps</name>
  <files>
    ros2_ws/src/aurora_bringup/launch/mapping.launch.py
    ros2_ws/src/aurora_bringup/config/nav2_params.yaml
  </files>
  <action>
    1. Add point_cloud_xyz_node to mapping.launch.py
    2. Add depth_camera observation source to both costmap obstacle layers
  </action>
  <verify>grep point_cloud_xyz_node mapping.launch.py && grep depth_camera nav2_params.yaml</verify>
  <done>Depth camera feeds PointCloud2 into Nav2 costmaps</done>
</task>
