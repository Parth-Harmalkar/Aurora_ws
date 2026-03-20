import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    
    # Package Directories
    pkg_bringup = get_package_share_directory('aurora_bringup')
    pkg_motor = get_package_share_directory('aurora_motor_driver')
    pkg_odom = get_package_share_directory('aurora_odometry')
    pkg_lidar = get_package_share_directory('sllidar_ros2')
    pkg_imu = get_package_share_directory('aurora_imu')
    
    # Config Files
    ekf_config = os.path.join(pkg_bringup, 'config', 'ekf.yaml')
    mux_config = os.path.join(pkg_bringup, 'config', 'twist_mux.yaml')
    
    # Launch Arguments
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    
    return LaunchDescription([
        DeclareLaunchArgument('lidar_port', default_value='/dev/ttyUSB0'),

        # 1. Motor Driver Node (Sub: /cmd_vel_out, Pub: ticks)
        Node(
            package='aurora_motor_driver',
            executable='motor_node',
            name='motor_driver',
            parameters=[{'port': '/dev/ttyACM0', 'baudrate': 1000000}],
            remappings=[('/cmd_vel', '/cmd_vel_out')] # Sub from mux output
        ),

        # 2. Wheel Odometry Node (Sub: ticks, Pub: /wheel/odom)
        Node(
            package='aurora_odometry',
            executable='ekf_odom_node',
            name='wheel_odom_node',
            parameters=[{'publish_tf': False}] # robot_localization handles TF
        ),

        # 3. IMU Node (Pub: /imu/data)
        Node(
            package='aurora_imu',
            executable='imu_node',
            name='imu_node',
            remappings=[('/imu', '/imu/data')]
        ),

        # 4. Lidar Node (Pub: /scan)
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[{
                'serial_port': lidar_port,
                'serial_baudrate': 460800,
                'frame_id': 'laser',
                'inverted': False,
                'angle_compensate': True,
                'scan_mode': 'Standard'
            }]
        ),

        # 5. Robot Localization (EKF Fusion)
        # Fuses /wheel/odom + /imu/data -> Publishes /odom and odom->base_link TF
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config],
            remappings=[('/odometry/filtered', '/odom')]
        ),

        # 6. Twist Mux (Arbitration)
        Node(
            package='twist_mux',
            executable='twist_mux',
            name='twist_mux',
            output='screen',
            parameters=[mux_config],
            remappings=[('/cmd_vel_out', '/cmd_vel_out')] # Standard output
        ),

        # 7. Ultrasonic Node (Pub: /ultrasonic/front_left, /ultrasonic/front_right)
        Node(
            package='aurora_ultrasonic',
            executable='ultra_node',
            name='ultrasonic_node',
            output='screen'
        ),

        # 8. Static Transforms
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_laser',
            arguments=['0', '0', '0.09', '0', '0', '0', 'base_link', 'laser']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_imu',
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'imu_link']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_ultra_left',
            arguments=['0.15', '0.1', '0.05', '0.1', '0', '0', 'base_link', 'ultrasonic_front_left']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_ultra_right',
            arguments=['0.15', '-0.1', '0.05', '-0.1', '0', '0', 'base_link', 'ultrasonic_front_right']
        )
    ])
