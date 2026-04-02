import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    # Depth to PointCloud2 (CPU-efficient conversion)
    depth_to_pc_node = Node(
        package='depth_image_proc',
        executable='point_cloud_xyz_node',
        name='depth_to_pointcloud',
        parameters=[{'queue_size': 5}],
        remappings=[
            ('image_rect', '/camera/depth/image_raw'),
            ('camera_info', '/camera/color/camera_info'),
            ('points', '/camera/depth/points')
        ]
    )

    # Automatic Map Saver
    map_saver_node = Node(
        package='aurora_bringup',
        executable='map_saver_node.py',
        name='map_saver'
    )

    return LaunchDescription([
        depth_to_pc_node,
        map_saver_node
    ])
