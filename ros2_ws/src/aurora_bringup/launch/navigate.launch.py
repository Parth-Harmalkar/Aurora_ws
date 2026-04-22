"""
navigate.launch.py — Autonomous Navigation Mode (Localization + Nav2)

Prerequisites:
    A map must exist at ~/.aurora/rtabmap.db (created via mapping_only.launch.py)

Usage:
    ros2 launch aurora_bringup navigate.launch.py
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')

    # Launch Arguments
    use_tui = LaunchConfiguration('use_tui', default='false')
    declare_use_tui = DeclareLaunchArgument('use_tui', default_value='false')

    # 1. Hardware Foundation (Motors, Sensors, EKF, TFs)
    foundation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'foundation.launch.py')
        ),
        launch_arguments={'use_tui': use_tui}.items()
    )

    # 2. Perception (Decimated Depth PointCloud for Nav2 costmap)
    perception_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'perception.launch.py')
        )
    )

    # 3. RTAB-Map in LOCALIZATION mode (lightweight — no map updates)
    # DO NOT pass -d flag here — we need the saved map!
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        parameters=[
            os.path.join(pkg_bringup, 'config', 'rtabmap_localization.yaml')
        ],
        remappings=[
            ('/rgb/image', '/oak/rgb/image_raw'),
            ('/depth/image', '/oak/stereo/image_raw'),
            ('/rgb/camera_info', '/oak/rgb/camera_info'),
            ('/depth/camera_info', '/oak/rgb/camera_info'),
            ('/scan', '/scan'),
            ('/odom', '/odom'),
            ('/imu', '/imu/data'),
            ('/cloud_map', '/cloud_map'),
            ('/cloud_obstacles', '/cloud_obstacles'),
            ('/cloud_ground', '/cloud_ground')
        ]
    )

    # 4. Navigation Stack (Nav2 — full autonomous driving)
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_tui': use_tui,
            'slam_mode': 'true'  # RTAB-Map provides map→odom TF, not AMCL
        }.items()
    )

    return LaunchDescription([
        declare_use_tui,
        foundation_launch,
        perception_launch,
        rtabmap_node,
        navigation_launch
    ])
