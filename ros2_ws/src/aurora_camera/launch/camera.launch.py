import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    return LaunchDescription([
        # 1. Camera Node (Driver)
        Node(
            package='aurora_camera',
            executable='camera_node',
            name='camera_node',
            output='screen'
        ),

        # 2. Static Transforms (Required for RViz 3D View)
        # base_link -> camera_link (Physical position on robot)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_camera',
            output='screen',
            arguments=['0.1', '0', '0.2', '0', '0', '0', 'base_link', 'camera_link']
        ),
        
        # camera_link -> camera_optical_frame (Rotation to Optical convention)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_link_to_optical',
            output='screen',
            # Optical frame: X-right, Y-down, Z-forward
            arguments=['0', '0', '0', '-0.5', '0.5', '-0.5', '0.5', 'camera_link', 'camera_optical_frame']
        ),

        # camera_optical_frame -> camera_imu_optical_frame (IMU alignment)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='optical_to_imu',
            output='screen',
            arguments=['0', '0', '0', '0', '0', '0', '1', 'camera_optical_frame', 'camera_imu_optical_frame']
        )
    ])
