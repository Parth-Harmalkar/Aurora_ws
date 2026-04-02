import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    # 1. Declare Launch Arguments
    use_tui = LaunchConfiguration('use_tui', default='false')
    declare_use_tui = DeclareLaunchArgument('use_tui', default_value='false')
    
    delete_db_on_start = LaunchConfiguration('delete_db_on_start', default='false')
    declare_delete_db = DeclareLaunchArgument('delete_db_on_start', default_value='false', description='Erase the RTAB-Map DB at startup.')
    
    # 2. Hardware Foundation (Motors, Sensors)
    foundation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'foundation.launch.py')
        ),
        launch_arguments={'use_tui': use_tui}.items()
    )

    # 3. Perception Module (Processing Scan/Depth data)
    perception_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'perception.launch.py')
        )
    )

    # 4. SLAM Module (RTAB-Map using modular config)
    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'slam.launch.py')
        ),
        launch_arguments={'delete_db_on_start': delete_db_on_start}.items()
    )

    # 5. Autonomous Navigation (Nav2)
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_tui': use_tui,
            'slam_mode': 'true'
        }.items()
    )

    return LaunchDescription([
        declare_use_tui,
        declare_delete_db,
        foundation_launch,
        perception_launch,
        slam_launch,
        nav2_launch
    ])
