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
        
        # 3. Start RTAB-Map VSLAM
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"]),
            parameters=[{
                'database_path': os.path.expanduser('~/.aurora/rtabmap.db'),
                'frame_id': 'base_link',
                'subscribe_depth': True,
                'subscribe_scan': True,   # HYBRID SLAM: Integrate Lidar
                'subscribe_imu': True,    # New: Integrate Camera IMU
                'subscribe_odom_info': False,
                'approx_sync': True,
                'use_sim_time': False,
                'wait_imu_to_init': True, # Ensure gravity alignment at start
                'sync_queue_size': 30,    # Correct name for Humble
                'RGBD/AngularUpdate': '0.1',
                'RGBD/LinearUpdate': '0.1',
                'RGBD/OptimizeMaxError': '10.0', # Relaxed for uncalibrated hardware
                'RGBD/OptimizeFromGraphEnd': 'false',
                'RGBD/NeighborLinkRefining': 'true', # Help with small errors
                'RGBD/ProximityBySpace': 'true',
                'Vis/MaxFeatures': '500',
                'Vis/MinInliers': '6',
                'Grid/FromDepth': 'true',      # Populate 3D clouds from camera
                'Grid/3D': 'true',             # ENABLE 3D MAPPING
                'Grid/Sensor': '1',            # 0=lidar(2D only), 1=depth camera(3D), 2=both
                'Grid/RayTracing': 'true',     
                'Grid/MaxObstacleHeight': '1.5',
                'Grid/CellSize': '0.02',       # Increased to 2cm grid cells for hyper-sharp 2D map
                'Grid/NoiseFilteringRadius': '0.1',       # Cleans up floating ghost pixels
                'Grid/NoiseFilteringMinNeighbors': '5',   # Cleans up floating ghost pixels
                'cloud_decimation': 1,          # (MAX RESOLUTION) Use 100% of camera pixels!
                'cloud_voxel_size': 0.01,       # Increased to 1cm voxels for point cloud output
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
                ('/imu', '/imu/data'),      # New: Use BNO055 IMU data
                ('/grid_map', '/map')
            ],
            arguments=PythonExpression(["['-d'] if '", delete_db_on_start, "' == 'true' else []"])
        ),
        
        # 3.5 Depth to PointCloud2 for Nav2 costmaps (CPU-efficient, no RGB)
        Node(
            package='depth_image_proc',
            executable='point_cloud_xyz_node',
            name='depth_to_pointcloud',
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"]),
            parameters=[{'queue_size': 5}],
            remappings=[
                ('image_rect', '/camera/depth'),
                ('camera_info', '/camera/camera_info'),
                ('points', '/camera/depth/points')
            ]
        ),

        # 3.8 Map Saver Node (Auto-saves occupancy_grid maps every 5min and manually)
        Node(
            package='aurora_bringup',
            executable='map_saver_node.py',
            name='map_saver',
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        ),

        # 4. Start Nav2 Navigation Stack
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'navigation.launch.py')
            ),
            launch_arguments={
                'use_tui': use_tui,
                'slam_mode': 'true'
            }.items()
        )
    ])
