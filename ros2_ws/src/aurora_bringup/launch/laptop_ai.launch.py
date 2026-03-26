from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Whisper Node (Runs as CONSUMER on Laptop)
        Node(
            package='aurora_ai_bridge',
            executable='whisper_node',
            name='whisper_node',
            parameters=[{'mode': 'consumer'}],
            output='screen'
        )
    ])
