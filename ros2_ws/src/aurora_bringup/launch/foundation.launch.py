import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    
    # Package Directories
    pkg_bringup = get_package_share_directory('aurora_bringup')
    pkg_camera = get_package_share_directory('aurora_camera')
    pkg_motor = get_package_share_directory('aurora_motor_driver')
    pkg_odom = get_package_share_directory('aurora_odometry')
    pkg_lidar = get_package_share_directory('sllidar_ros2')
    pkg_imu = get_package_share_directory('aurora_imu_cpp')
    
    # Config Files
    ekf_config = os.path.join(pkg_bringup, 'config', 'ekf.yaml')
    mux_config = os.path.join(pkg_bringup, 'config', 'twist_mux.yaml')
    
    # Launch Arguments
    lidar_port = LaunchConfiguration('lidar_port', default='/dev/ttyUSB0')
    use_tui = LaunchConfiguration('use_tui', default='false')
    declare_use_tui = DeclareLaunchArgument('use_tui', default_value='false')
    
    output_cfg = PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
    
    return LaunchDescription([
        declare_use_tui,
        DeclareLaunchArgument('lidar_port', default_value='/dev/ttyUSB0'),

        # 1. Motor Driver Node (Sub: /cmd_vel_out, Pub: ticks)
        Node(
            package='aurora_motor_driver',
            executable='motor_node',
            name='motor_driver',
            output=output_cfg,
            parameters=[{'port': '/dev/ttyACM0', 'baudrate': 1000000}],
            remappings=[('/cmd_vel', '/cmd_vel_out')], # Sub from mux output
            respawn=True
        ),

        # 2. Wheel Odometry Node (Sub: ticks, Pub: /wheel/odom)
        Node(
            package='aurora_odometry',
            executable='ekf_odom_node',
            name='wheel_odom_node',
            output=output_cfg,
            parameters=[{'publish_tf': False}] # robot_localization handles TF
        ),

        # 3. Dedicated Hardware IMU Node (BNO055 Bare-Metal Driver - C++ Port)
        Node(
            package='aurora_imu_cpp',
            executable='bno055_bare',
            name='bno_imu_node',
            output=output_cfg,
            parameters=[{
                'i2c_bus': 1,
                'i2c_addr': 0x28,
                'frame_id': 'bno_link',
                # Direction is correct (Red=Front), but Roll/Pitch are inverted.
                # Inverting signs to align with Right-Hand Rule.
                'axis_x': 0, 'axis_y': 1, 'axis_z': 2,
                'sign_x': 1, 'sign_y': 1, 'sign_z': 1
            }],
            remappings=[
                ('/imu/data', '/imu/data') # Native topic in C++ version
            ]
        ),

        # 4. Lidar Node (Pub: /scan)
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            output=output_cfg,
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
            output=output_cfg,
            parameters=[ekf_config],
            remappings=[('/odometry/filtered', '/odom')]
        ),

        # 6. Twist Mux (Arbitration)
        Node(
            package='twist_mux',
            executable='twist_mux',
            name='twist_mux',
            output=output_cfg,
            parameters=[mux_config],
            remappings=[('cmd_vel', '/cmd_vel_out')] # Arbitrated output
        ),

        # 7. Ultrasonic Node (Pub: /ultrasonic/front_left, /ultrasonic/front_right)
        Node(
            package='aurora_ultrasonic',
            executable='ultra_node',
            name='ultrasonic_node',
            output=output_cfg
        ),

        # 9. Camera Stack (C++ Driver - OAK-D Lite Optimized)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'camera_v2.launch.py')
            )
        ),

        # 10. Failsafe Stop Node (Layer-0 Safety)
        Node(
            package='aurora_lidar',
            executable='failsafe_stop',
            name='failsafe_stop',
            output=output_cfg
        ),

        # 11. Static Transforms
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_laser',
            output=output_cfg,
            # Lidar mounted with cable backward means it scans 180 opposite to camera
            arguments=['0', '0', '0.09', '3.14159', '0', '0', 'base_link', 'laser']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_imu',
            output=output_cfg,
            # Reset to identity as correction is now hardcoded in the C++ driver
            arguments=['0', '0', '0', '0', '0', '0', 'base_link', 'bno_link']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_camera',
            output=output_cfg,
            arguments=['0.1', '0', '0.2', '0', '0', '0', 'base_link', 'camera_link']
        ),
        # Camera optical frame: rotates from ROS convention (X-fwd, Y-left, Z-up)
        # to optical convention (X-right, Y-down, Z-forward) for RTAB-Map/vision
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='camera_link_to_optical',
            output=output_cfg,
            # Optical frame: X-right, Y-down, Z-forward
            arguments=['0', '0', '0', '-0.5', '0.5', '-0.5', '0.5', 'camera_link', 'oak_rgb_camera_optical_frame']
        ),
        # Bridge Camera IMU to Optical Frame (Identity since BMI270 is PCB-aligned with sensors)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='optical_to_imu',
            output=output_cfg,
            arguments=['0', '0', '0', '0', '0', '0', '1', 'oak_rgb_camera_optical_frame', 'camera_imu_optical_frame']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_ultra_left',
            output=output_cfg,
            arguments=['0.15', '0.1', '0.05', '3.24159', '0', '0', 'base_link', 'ultrasonic_front_left']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_link_to_ultra_right',
            output=output_cfg,
            arguments=['0.15', '-0.1', '0.05', '3.04159', '0', '0', 'base_link', 'ultrasonic_front_right']
        )
    ])
