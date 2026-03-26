import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """
    Unified Laptop Launch: Starts RViz and the Whisper Consumer.
    """
    return LaunchDescription([
        # 1. RViz for 3D Visualization
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen'
        ),
        
        # 2. Whisper Node (Consumer mode: uses laptop GPU for Jetson's audio)
        Node(
            package='aurora_ai_bridge',
            executable='whisper_node',
            name='whisper_consumer',
            parameters=[{'mode': 'consumer'}],
            output='screen'
        )
    ])
