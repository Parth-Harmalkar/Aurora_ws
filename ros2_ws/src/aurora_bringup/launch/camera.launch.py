import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    depthai_prefix = get_package_share_directory('depthai_ros_driver')
    
    # Launch standard OAK-D node
    camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(depthai_prefix, 'launch', 'camera.launch.py')
        ),
        launch_arguments={
            'camera_model': 'OAK-D-LITE',
            'name': 'oak',
            'parent_frame': 'camera_link',
            'cam_pos_x': '0.0',
            'cam_pos_y': '0.0',
            'cam_pos_z': '0.0',
            'cam_roll': '0.0',
            'cam_pitch': '0.0',
            'cam_yaw': '0.0'
        }.items()
    )
    
    return LaunchDescription([
        camera_launch
    ])
