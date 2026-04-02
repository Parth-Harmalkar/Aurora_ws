import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    # 1. Declare Launch Arguments
    delete_db_on_start = LaunchConfiguration('delete_db_on_start', default='false')
    declare_delete_db = DeclareLaunchArgument('delete_db_on_start', default_value='false', description='Erase the RTAB-Map DB at startup.')
    
    # RTAB-Map Node setup
    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        parameters=[
            os.path.join(pkg_bringup, 'config', 'rtabmap.yaml')
        ],
        remappings=[
            ('/rgb/image', '/camera/color/image_raw'),
            ('/depth/image', '/camera/depth/image_raw'),
            ('/rgb/camera_info', '/camera/color/camera_info'),
            ('/depth/camera_info', '/camera/color/camera_info'),
            ('/scan', '/scan'),
            ('/odom', '/odom'),
            ('/imu', '/camera/imu/data'),
            ('/grid_map', '/map')
        ],
        arguments=['-d'] if delete_db_on_start == 'true' else []
    )

    return LaunchDescription([
        declare_delete_db,
        rtabmap_node
    ])
