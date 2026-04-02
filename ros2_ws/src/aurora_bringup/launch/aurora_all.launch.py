import os
import launch.conditions
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    
    use_tui = LaunchConfiguration('use_tui')
    declare_use_tui = DeclareLaunchArgument(
        'use_tui',
        default_value='false',
        description='If true, launch the TUI dashboard and silence other logs.'
    )

    remote_ai = LaunchConfiguration('remote_ai')
    declare_remote_ai = DeclareLaunchArgument(
        'remote_ai',
        default_value='false',
        description='If true, offload AI tasks to remote laptop.'
    )

    enable_voice = LaunchConfiguration('enable_voice')
    declare_enable_voice = DeclareLaunchArgument(
        'enable_voice',
        default_value='false',
        description='If true, enable Whisper voice transcription (CPU heavy).'
    )

    delete_db_on_start = LaunchConfiguration('delete_db_on_start')
    declare_delete_db = DeclareLaunchArgument(
        'delete_db_on_start',
        default_value='false',
        description='Erase the RTAB-Map DB at startup.'
    )

    # 1. Mapping & SLAM Launch
    mapping_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'mapping.launch.py')
        ),
        launch_arguments={
            'use_tui': use_tui,
            'delete_db_on_start': delete_db_on_start
        }.items()
    )
    
    # 2. Intelligence Launch (AI and Memory)
    intelligence_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bringup, 'launch', 'intelligence.launch.py')
        ),
        launch_arguments={
            'use_tui': use_tui,
            'remote_ai': remote_ai,
            'enable_voice': enable_voice
        }.items()
    )
    
    # 4. TUI Dashboard
    tui_node = Node(
        package='aurora_ai_bridge',
        executable='tui_node',
        name='aurora_tui',
        output='screen',
        emulate_tty=True,
        condition=launch.conditions.IfCondition(use_tui)
    )
    
    return LaunchDescription([
        declare_use_tui,
        declare_remote_ai,
        declare_enable_voice,
        declare_delete_db,
        mapping_launch,
        intelligence_launch,
        tui_node
    ])
