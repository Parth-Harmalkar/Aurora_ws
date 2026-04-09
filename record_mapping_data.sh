#!/bin/bash
# Script to record a ROS 2 bag with all necessary topics for RTAB-Map and Navigation testing

BAG_DIR="aurora_mapping_bag_$(date +%Y%m%d_%H%M%S)"

echo "Starting ROS 2 Bag Recording for mapping..."
echo "Saving to directory: $BAG_DIR"
echo "Press Ctrl+C to stop recording."

ros2 bag record -o $BAG_DIR \
  /tf \
  /tf_static \
  /odom \
  /scan \
  /camera/color/image_raw \
  /camera/color/camera_info \
  /camera/depth/image_raw \
  /camera/imu/data \
  /joint_states
