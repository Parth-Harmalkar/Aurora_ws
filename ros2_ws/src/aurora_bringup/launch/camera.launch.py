import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression

def generate_launch_description():
    depthai_prefix = get_package_share_directory('depthai_ros_driver')
    use_tui = LaunchConfiguration('use_tui', default='false')
    
    # Launch standard OAK-D node
    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(depthai_prefix, 'launch', 'camera.launch.py')
        ),
        launch_arguments={
            'camera_model': 'OAK-D-PRO',
            'name': 'oak',
            'parent_frame': 'camera_link',
            'cam_pos_x': '0.0',
            'cam_pos_y': '0.0',
            'cam_pos_z': '0.0',
            'cam_roll': '0.0',
            'cam_pitch': '0.0',
            'cam_yaw': '0.0',
            'rgb.i_publish_topic': 'true',
            'rgb.i_low_bandwidth': 'true',
            'left.i_publish_topic': 'true',
            'right.i_publish_topic': 'true',
            'i_enable_ir': 'true',
            'i_laser_dot_brightness': '800' # Typical integer value for some versions
        }.items(),
    )
    # Wrap Include in a way to set output, but since Include doesn't support 'output' at top level
    # we just pass use_tui down if it supported it, but depthai launch likely doesn't.
    # We'll just declare it here to satisfy the interface.
    
    return LaunchDescription([
        DeclareLaunchArgument('use_tui', default_value='false'),
        camera_launch
    ])
