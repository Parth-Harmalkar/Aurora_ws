import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    # Launch Arguments
    use_tui = LaunchConfiguration('use_tui', default='false')
    declare_use_tui = DeclareLaunchArgument('use_tui', default_value='false')
    
    delete_db_on_start = LaunchConfiguration('delete_db_on_start', default='false')
    declare_delete_db = DeclareLaunchArgument('delete_db_on_start', default_value='false')

    # 1. Foundation (Hardware: Motors, IMU, Lidar)
    foundation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'foundation.launch.py')
        ),
        launch_arguments={'use_tui': use_tui}.items()
    )

    # 2. Perception (Processing: Scans, Depth)
    perception_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'perception.launch.py')
        )
    )

    # 3. Intelligence (AI, Memory, Voice)
    intelligence_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'intelligence.launch.py')
        ),
        launch_arguments={'use_tui': use_tui}.items()
    )

    return LaunchDescription([
        declare_use_tui,
        declare_delete_db,
        foundation_launch,
        perception_launch,
        intelligence_launch
    ])
