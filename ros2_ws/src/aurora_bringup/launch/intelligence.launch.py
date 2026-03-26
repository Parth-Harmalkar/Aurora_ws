import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    use_tui = LaunchConfiguration('use_tui', default='false')
    remote_ai = LaunchConfiguration('remote_ai', default='false')
    
    return LaunchDescription([
        DeclareLaunchArgument('use_tui', default_value='false'),
        DeclareLaunchArgument('remote_ai', default_value='false', description='Offload AI heavy lifting to remote PC'),
        
        # 1. AI Bridge Node
        Node(
            package='aurora_ai_bridge',
            executable='ai_bridge_node',
            name='ai_bridge_node',
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        ),
        
        # 2. Whisper Node (Runs as PRODUCER if remote_ai is true)
        Node(
            package='aurora_ai_bridge',
            executable='whisper_node',
            name='whisper_node',
            parameters=[{'mode': PythonExpression(["'producer' if '", remote_ai, "' == 'true' else 'local'"])}],
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        ),
        
        # 3. Status Monitor (UX Feedback)
        Node(
            package='aurora_ai_bridge',
            executable='status_monitor',
            name='status_monitor',
            output=PythonExpression(["'log' if '", use_tui, "' == 'true' else 'screen'"])
        )
    ])
