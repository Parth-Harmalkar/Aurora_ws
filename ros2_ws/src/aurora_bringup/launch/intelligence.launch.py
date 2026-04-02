import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    use_tui = LaunchConfiguration('use_tui', default='false')
    remote_ai = LaunchConfiguration('remote_ai', default='false')
    enable_voice = LaunchConfiguration('enable_voice', default='false')
    
    config_intelligence = os.path.join(pkg_bringup, 'config', 'intelligence.yaml')
    
    return LaunchDescription([
        DeclareLaunchArgument('use_tui', default_value='false'),
        DeclareLaunchArgument('remote_ai', default_value='false', description='Offload AI heavy lifting to remote PC'),
        DeclareLaunchArgument('enable_voice', default_value='false', description='Enable Whisper voice transcription (CPU heavy)'),
        
        # 1. AI Bridge Node
        Node(
            package='aurora_ai_bridge',
            executable='ai_bridge_node',
            name='ai_bridge_node',
            parameters=[config_intelligence],
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        ),
        
        # 2. Whisper Node (Conditional)
        Node(
            package='aurora_ai_bridge',
            executable='whisper_node',
            name='whisper_node',
            parameters=[
                config_intelligence,
                {'mode': PythonExpression(["'producer' if '", remote_ai, "' == 'true' else 'local'"])}
            ],
            condition=IfCondition(enable_voice),
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        ),
        
        # 3. Status Monitor (UX Feedback)
        Node(
            package='aurora_ai_bridge',
            executable='status_monitor',
            name='status_monitor',
            parameters=[config_intelligence],
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        ),
        
        # 4. Semantic Memory Node (Persistent object memory)
        Node(
            package='aurora_semantic_memory',
            executable='semantic_memory_node',
            name='semantic_memory_node',
            parameters=[config_intelligence],
            remappings=[
                ('/camera/detections', '/camera/detections') # Standardized
            ],
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        )
    ])
