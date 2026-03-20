from setuptools import find_packages, setup

package_name = 'aurora_ai_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='aurora',
    maintainer_email='aurora@gsd.auto',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'ai_bridge_node = aurora_ai_bridge.ai_bridge_node:main',
            'whisper_node = aurora_ai_bridge.whisper_node:main',
            'custom_teleop = aurora_ai_bridge.custom_teleop:main',
            'text_commander = aurora_ai_bridge.text_commander:main'
        ],
    },
)
