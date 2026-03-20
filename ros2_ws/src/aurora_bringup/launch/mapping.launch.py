import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    
    # 1. Paths to other launch files and configs
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    foundation_launch_path = os.path.join(pkg_bringup, 'launch', 'foundation.launch.py')
    slam_config_path = os.path.join(pkg_bringup, 'config', 'slam_toolbox_async.yaml')
    
    # 2. Launch Description
    return LaunchDescription([
        
        # Bring up hardware foundation (Motor, Lidar, EKF, etc.)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(foundation_launch_path)
        ),
        
        # Start SLAM Toolbox
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                slam_config_path,
                {'use_sim_time': False}
            ]
        )
    ])
