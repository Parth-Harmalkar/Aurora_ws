import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    pkg_camera = get_package_share_directory('aurora_camera')
    model_path = os.path.join(pkg_camera, 'models', 'mobilenet-ssd_openvino_2021.4_6shave.blob')

    return LaunchDescription([
        ComposableNodeContainer(
            name='oak_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='depthai_ros_driver',
                    plugin='depthai_ros_driver::Camera',
                    name='oak',
                    parameters=[{
                        'camera.i_nn_type': 'spatial',
                        'camera.i_nn_path': model_path,
                        'camera.i_pipeline_type': 'rgbd',
                        'camera.i_publish_tf': False,
                        'camera.i_frame_prefix': '',
                        'rgb.i_resolution': '720p',
                        'rgb.i_width': 1280,
                        'rgb.i_height': 720,
                        'rgb.i_frame_id': 'camera_optical_frame',
                        'rgb.i_fps': 10.0,
                        'rgb.i_low_bandwidth': True,
                        'stereo.i_align_depth': True,
                        'stereo.i_subpixel': True,
                        'stereo.i_lr_check': True,
                        'stereo.i_median_filter': '5x5',
                        'stereo.i_low_bandwidth': True,
                        'stereo.i_fps': 10.0,
                        'stereo.i_resolution': '720p',
                        'stereo.i_width': 1280,
                        'stereo.i_height': 720,
                        'stereo.i_frame_id': 'camera_optical_frame',
                        'nn.i_label_map': [
                            "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair",
                            "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"
                        ]
                    }],
                    remappings=[],
                ),
            ],
            output='screen',
        ),
    ])
