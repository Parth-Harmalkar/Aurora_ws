import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    # 1. Mapping Launch (Hardware + SLAM + Nav2)
    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'mapping.launch.py')
        )
    )
    
    # 2. Intelligence Launch (AI Bridge + Whisper)
    intelligence_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'intelligence.launch.py')
        )
    )
    
    # 3. Vision Launch (OAK-D Lite)
    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'camera.launch.py')
        )
    )

    from launch_ros.actions import Node
    camera_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='base_link_to_camera',
        arguments=['0.10', '0', '0.20', '0', '0', '0', 'base_link', 'camera_link']
    )
    
    return LaunchDescription([
        mapping_launch,
        intelligence_launch,
        camera_launch,
        camera_tf
    ])
