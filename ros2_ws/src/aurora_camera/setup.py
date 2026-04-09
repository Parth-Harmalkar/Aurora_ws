from setuptools import find_packages, setup
from ament_index_python.packages import get_package_share_directory
import os
from glob import glob

package_name = 'aurora_camera'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'models'), ['models/mobilenet-ssd_openvino_2021.4_6shave.blob']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='aurora',
    maintainer_email='aurora@todo.todo',
    description='Aurora Camera Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_node = aurora_camera.camera_node:main'
        ],
    },
)
