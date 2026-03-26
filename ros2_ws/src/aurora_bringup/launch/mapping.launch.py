import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    use_tui = LaunchConfiguration('use_tui', default='false')
    declare_use_tui = DeclareLaunchArgument('use_tui', default_value='false')
    
    foundation_launch_path = os.path.join(pkg_bringup, 'launch', 'foundation.launch.py')
    
    return LaunchDescription([
        declare_use_tui,
        
        # 1. Bring up hardware foundation
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(foundation_launch_path),
            launch_arguments={'use_tui': use_tui}.items()
        ),
        
        # 2. Add base_footprint -> base_link TF (Arjuna pattern)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_footprint_to_base_link',
            arguments=['0', '0', '0.09', '0', '0', '0', 'base_footprint', 'base_link'],
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        ),

        # 3. Start RTAB-Map VSLAM
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"]),
            parameters=[{
                'frame_id': 'base_footprint',
                'subscribe_depth': True,
                'subscribe_scan': True,   # HYBRID SLAM: Integrate Lidar
                'subscribe_odom_info': False,
                'approx_sync': True,
                'use_sim_time': False,
                'sync_queue_size': 30,    # Correct name for Humble
                'RGBD/AngularUpdate': '0.1',
                'RGBD/LinearUpdate': '0.1',
                'RGBD/OptimizeMaxError': '10.0', # Relaxed for uncalibrated hardware
                'RGBD/OptimizeFromGraphEnd': 'false',
                'RGBD/NeighborLinkRefining': 'true', # Help with small errors
                'RGBD/ProximityBySpace': 'true',
                'Vis/MaxFeatures': '500',
                'Vis/MinInliers': '5',
                'Grid/FromDepth': 'true',      # Populate 3D clouds from camera
                'Grid/3D': 'true',             # ENABLE 3D MAPPING
                'Grid/RayTracing': 'true',     
                'Grid/MaxObstacleHeight': '1.5',
                'Grid/CellSize': '0.05',       # 5cm grid cells
                'cloud_decimation': 2,          # Use every 2nd pixel (denser cloud)
                'cloud_voxel_size': 0.03,       # 3cm voxels for point cloud output
                'cloud_output_voxelized': True,
                'Mem/IncrementalMemory': 'true',
                'Mem/InitWMWithAllNodes': 'false'
            }],
            remappings=[
                ('/rgb/image', '/camera/image_raw'),
                ('/depth/image', '/camera/depth'),
                ('/rgb/camera_info', '/camera/camera_info'),
                ('/depth/camera_info', '/camera/camera_info'),
                ('/scan', '/scan'),          # Remap Lidar
                ('/odom', '/odom'),
                ('/grid_map', '/map')
            ],
            arguments=['-d'] # Delete database at startup (clean map every time as requested)
        ),
        
        # 4. Start Nav2 Navigation Stack
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
            ),
            launch_arguments={'use_tui': use_tui}.items()
        )
    ])
