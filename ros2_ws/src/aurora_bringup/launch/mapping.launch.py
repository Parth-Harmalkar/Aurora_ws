import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def launch_setup(context, *args, **kwargs):
    pkg_bringup = get_package_share_directory('aurora_bringup')
    use_tui = LaunchConfiguration('use_tui')
    delete_db_on_start = LaunchConfiguration('delete_db_on_start').perform(context)
    
    output_cfg = PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
    
    rtabmap_arguments = []
    if delete_db_on_start.lower() == 'true':
        rtabmap_arguments = ['-d']

    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output=output_cfg,
        parameters=[{
            'database_path': os.path.expanduser('~/.aurora/rtabmap.db'),
            'frame_id': 'base_link',
            'subscribe_depth': True,
            'subscribe_scan': True,
            'subscribe_imu': True,
            'subscribe_odom_info': False,
            'approx_sync': True,
            'use_sim_time': False,
            'wait_imu_to_init': True,
            'sync_queue_size': 30,
            'Rtabmap/DetectionRate': '1.0',
            'RGBD/AngularUpdate': '0.1',
            'RGBD/LinearUpdate': '0.1',
            'RGBD/OptimizeMaxError': '20.0',
            'RGBD/OptimizeFromGraphEnd': 'false',
            'RGBD/NeighborLinkRefining': 'false',
            'RGBD/ProximityBySpace': 'true',
            'Vis/MaxFeatures': '500',
            'Vis/MinInliers': '10',  # Stricter for better stability
            'Vis/EstimationType': '1', # 0=3D->3D, 1=3D->2D (PnP) - much more robust
            'Vis/BundleAdjustment': '1', 
            'Vis/MaxError': '0.05',  # Filter out bad feature matches
            'Odom/ResetCountdown': '1', # Reset odom if track is lost (prevents crash)
            'Grid/FromDepth': 'true',
            'Grid/3D': 'true',
            'Grid/Sensor': '1',
            'Grid/RayTracing': 'true',
            'Grid/MaxObstacleHeight': '1.5',
            'Grid/CellSize': '0.05',
            'Grid/NoiseFilteringRadius': '0.2',
            'Grid/NoiseFilteringMinNeighbors': '2',
            'cloud_decimation': 1,
            'cloud_voxel_size': 0.05,
            'cloud_output_voxelized': True,
            'Mem/IncrementalMemory': 'true',
            'Mem/InitWMWithAllNodes': 'false'
        }],
        remappings=[
            ('/rgb/image', '/camera/image_raw'),
            ('/depth/image', '/camera/depth'),
            ('/rgb/camera_info', '/camera/camera_info'),
            ('/depth/camera_info', '/camera/camera_info'),
            ('/scan', '/scan'),
            ('/odom', '/odom'),
            ('/imu', '/imu/data'),
            ('/grid_map', '/map')
        ],
        arguments=rtabmap_arguments
    )

    # 3.5 Depth to PointCloud2 for Nav2 costmaps (CPU-efficient, no RGB)
    depth_to_pc_node = Node(
        package='depth_image_proc',
        executable='point_cloud_xyz_node',
        name='depth_to_pointcloud',
        output=output_cfg,
        parameters=[{'queue_size': 5}],
        remappings=[
            ('image_rect', '/camera/depth'),
            ('camera_info', '/camera/camera_info'),
            ('points', '/camera/depth/points')
        ]
    )

    # 3.8 Map Saver Node (Auto-saves occupancy_grid maps every 5min and manually)
    map_saver_node = Node(
        package='aurora_bringup',
        executable='map_saver_node.py',
        name='map_saver',
        output=output_cfg
    )

    # 4. Start Nav2 Navigation Stack
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_tui': use_tui,
            'slam_mode': 'true'
        }.items()
    )

    return [rtabmap_node, depth_to_pc_node, map_saver_node, nav2_launch]

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    use_tui = LaunchConfiguration('use_tui', default='false')
    declare_use_tui = DeclareLaunchArgument('use_tui', default_value='false')
    
    delete_db_on_start = LaunchConfiguration('delete_db_on_start', default='false')
    declare_delete_db = DeclareLaunchArgument('delete_db_on_start', default_value='false', description='Erase the RTAB-Map DB at startup.')
    
    foundation_launch_path = os.path.join(pkg_bringup, 'launch', 'foundation.launch.py')
    
    return LaunchDescription([
        declare_use_tui,
        declare_delete_db,
        
        # 1. Bring up hardware foundation
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(foundation_launch_path),
            launch_arguments={'use_tui': use_tui}.items()
        ),
        
        # OpaqueFunction to handle conditional logic the rtabmap node and subsequent nodes
        OpaqueFunction(function=launch_setup)
    ])
