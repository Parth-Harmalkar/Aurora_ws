import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    pkg_bringup = get_package_share_directory('aurora_bringup')
    nav2_params_path = os.path.join(pkg_bringup, 'config', 'nav2_params.yaml')
    use_tui = LaunchConfiguration('use_tui')
    slam_mode = LaunchConfiguration('slam_mode')
    output_cfg = PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])

    slam_mode_val = context.perform_substitution(slam_mode)
    is_slam = slam_mode_val.lower() == 'true'

    nodes = []
    lifecycle_nodes = [
        'controller_server',
        'planner_server',
        'behavior_server',
        'bt_navigator',
    ]

    # In SLAM mode, RTAB-Map owns map→odom TF and /map topic.
    # Do NOT start map_server or AMCL — they conflict with RTAB-Map.
    if not is_slam:
        lifecycle_nodes.append('map_server')
        nodes.append(Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output=output_cfg,
            parameters=[nav2_params_path]
        ))

    nodes.extend([
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output=output_cfg,
            parameters=[nav2_params_path],
            remappings=[('cmd_vel', '/nav_vel')]
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output=output_cfg,
            parameters=[nav2_params_path]
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output=output_cfg,
            parameters=[nav2_params_path],
            remappings=[('cmd_vel', '/nav_vel')]
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

    return nodes


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_tui', default_value='false'),
        DeclareLaunchArgument('slam_mode', default_value='false',
                             description='Set true when RTAB-Map SLAM provides map and TF'),
        OpaqueFunction(function=launch_setup)
    ])
