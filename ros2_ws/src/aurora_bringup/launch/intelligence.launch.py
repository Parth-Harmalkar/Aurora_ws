import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('aurora_bringup')
    intel_config = os.path.join(pkg_bringup, 'config', 'intelligence.yaml')

    # Semantic Memory Node (The "Brain" that remembers objects)
    semantic_memory_node = Node(
        package='aurora_semantic_memory',
        executable='semantic_memory_node',
        name='semantic_memory_node',
        output='screen',
        parameters=[intel_config]
    )

    # AI Bridge Node (Handles high-level AI tasks/Dashboard logic)
    ai_bridge_node = Node(
        package='aurora_ai_bridge',
        executable='ai_bridge_node',
        name='ai_bridge_node',
        output='screen'
    )

    return LaunchDescription([
        semantic_memory_node,
        ai_bridge_node
    ])
