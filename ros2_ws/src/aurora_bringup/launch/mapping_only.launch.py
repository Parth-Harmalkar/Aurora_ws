"""
mapping_only.launch.py — VSLAM Mapping Mode (No Nav2)

Usage:
    ros2 launch aurora_bringup mapping_only.launch.py
    ros2 launch aurora_bringup mapping_only.launch.py delete_db_on_start:=true

Drive with:
    ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/teleop_vel
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    pkg_bringup = get_package_share_directory('aurora_bringup')

    delete_db = context.launch_configurations.get('delete_db_on_start', 'false')
    use_tui = LaunchConfiguration('use_tui')

    # RTAB-Map Node (SLAM mode — full VSLAM mapping)
    node_args = []
    if delete_db.lower() == 'true':
        node_args.append('-d')

    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        parameters=[
            os.path.join(pkg_bringup, 'config', 'rtabmap_mapping.yaml')
        ],
        remappings=[
            ('rgb/image', '/oak/rgb/image_raw'),
            ('depth/image', '/oak/stereo/image_raw'),
            ('rgb/camera_info', '/oak/rgb/camera_info'),
            ('depth/camera_info', '/oak/rgb/camera_info'),
            ('scan', '/scan'),
            ('odom', '/odom'),
            ('imu', '/imu/data')
        ],
        arguments=node_args
    )

    return [rtabmap_node]


def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')

    # Launch Arguments
    declare_use_tui = DeclareLaunchArgument('use_tui', default_value='false')
    declare_delete_db = DeclareLaunchArgument(
        'delete_db_on_start', default_value='false',
        description='Erase the RTAB-Map DB at startup for a fresh map.'
    )

    # 1. Hardware Foundation (Motors, Sensors, EKF, TFs)
    foundation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'foundation.launch.py')
        ),
        launch_arguments={'use_tui': LaunchConfiguration('use_tui')}.items()
    )

    # NOTE: No perception.launch.py here — RTAB-Map handles depth internally
    #       during mapping. No need for depth_image_proc PointCloud conversion.
    #       This saves significant CPU during the mapping phase.

    # NOTE: No navigation.launch.py here — human drives via teleop.
    #       This saves the entire Nav2 stack CPU during mapping.

    # 2. Automatic Map Saver
    map_saver_node = Node(
        package='aurora_bringup',
        executable='map_saver_node.py',
        name='map_saver'
    )

    return LaunchDescription([
        declare_use_tui,
        declare_delete_db,
        foundation_launch,
        map_saver_node,
        OpaqueFunction(function=launch_setup)
    ])
