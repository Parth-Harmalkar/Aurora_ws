import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. AI Bridge Node (LangGraph + Ollama)
        Node(
            package='aurora_ai_bridge',
            executable='ai_bridge_node',
            name='ai_bridge_node',
            output='screen'
        ),
        
        # 2. Whisper Node (Voice STT)
        Node(
            package='aurora_ai_bridge',
            executable='whisper_node',
            name='whisper_node',
            output='screen'
        )
    ])
