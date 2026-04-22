import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    # Depth to PointCloud2 (Optimized with Decimation)
    depth_to_pc_node = Node(
        package='rtabmap_util',
        executable='point_cloud_xyz',
        name='depth_to_pointcloud',
        parameters=[{
            'decimation': 4,
            'voxel_size': 0.05,
            'approx_sync': True
        }],
        remappings=[
            ('depth/image', '/oak/stereo/image_raw'),
            ('depth/camera_info', '/oak/rgb/camera_info'),
            ('cloud', '/camera/depth/points')
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
