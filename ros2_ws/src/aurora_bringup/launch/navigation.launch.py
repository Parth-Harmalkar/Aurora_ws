import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    nav2_params_path = os.path.join(pkg_bringup, 'config', 'nav2_params.yaml')
    use_tui = LaunchConfiguration('use_tui', default='false')
    output_cfg = PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])

    lifecycle_nodes = [
        'controller_server',
        'planner_server',
        'recoveries_server',
        'bt_navigator',
        'map_server'
    ]

    return LaunchDescription([
        DeclareLaunchArgument('use_tui', default_value='false'),
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output=output_cfg,
            parameters=[nav2_params_path]
        ),
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output=output_cfg,
            arguments=['--ros-args', '--log-level', 'warn'],
            parameters=[nav2_params_path]
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output=output_cfg,
            arguments=['--ros-args', '--log-level', 'warn'],
            parameters=[nav2_params_path]
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='recoveries_server',
            output=output_cfg,
            parameters=[nav2_params_path]
        ),
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output=output_cfg,
            parameters=[nav2_params_path]
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output=output_cfg,
            parameters=[
                {'use_sim_time': False},
                {'autostart': True},
                {'node_names': lifecycle_nodes}
            ]
        )
    ])
