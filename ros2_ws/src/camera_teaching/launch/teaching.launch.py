import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. Main Teaching Node
        Node(
            package='camera_teaching',
            executable='teaching_node.py',
            name='teaching_node',
            output='screen'
        ),

        # 2. Transforms (base_link -> camera_link -> camera_optical_frame)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_camera',
            arguments=['--x', '0.1', '--y', '0', '--z', '0.2', '--yaw', '0', '--pitch', '0', '--roll', '0', '--frame-id', 'base_link', '--child-frame-id', 'camera_link']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_link_to_optical',
            arguments=['--x', '0', '--y', '0', '--z', '0', '--qx', '-0.5', '--qy', '0.5', '--qz', '-0.5', '--qw', '0.5', '--frame-id', 'camera_link', '--child-frame-id', 'camera_optical_frame']
        )
    ])
