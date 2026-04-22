#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from aurora_msgs.srv import SaveMap
from datetime import datetime
import shutil

class MapSaverNode(Node):
    def __init__(self):
        super().__init__('map_saver')
        # Create maps directory if it doesn't exist
        self.maps_dir = os.path.expanduser('~/.aurora/maps')
        os.makedirs(self.maps_dir, exist_ok=True)
        
        # Provide the SaveMap service
        self.srv = self.create_service(SaveMap, 'save_map', self.save_map_callback)
        
        # Auto-save timer (1 minute = 60 seconds)
        self.timer_period = 60.0  
        self.timer = self.create_timer(self.timer_period, self.auto_save_callback)
        
        self.get_logger().info('Map Saver Node initialized. Auto-saving every 1 minute.')

    def save_map(self, map_name):
        map_path = os.path.join(self.maps_dir, map_name)
        # Call Nav2 map_saver_cli
        cmd = f'ros2 run nav2_map_server map_saver_cli -f {map_path}'
        self.get_logger().info(f'Saving map to {map_path}...')
        
        result = os.system(cmd)
        
        # Backup the RTAB-Map database (The "Whole 3D Map")
        db_src = os.path.expanduser('~/.aurora/rtabmap.db')
        db_dst = os.path.join(self.maps_dir, f'{map_name}.db')
        
        try:
            if os.path.exists(db_src):
                shutil.copy2(db_src, db_dst)
                self.get_logger().info(f'Successfully backed up 3D database to {db_dst}')
            else:
                self.get_logger().warn(f'RTAB-Map database not found at {db_src}')
        except Exception as e:
            self.get_logger().error(f'Failed to backup database: {str(e)}')

        if result == 0:
            self.get_logger().info(f'Successfully saved 2D map to {map_path}')
            return True, f'Successfully saved 2D and 3D maps to {self.maps_dir}'
        else:
            self.get_logger().error(f'Failed to save 2D map. Command returned {result}')
            return False, f'Failed to save 2D map with exit code {result}'

    def save_map_callback(self, request, response):
        success, msg = self.save_map(request.map_name)
        response.success = success
        response.message = msg
        return response

    def auto_save_callback(self):
        # Overwrite the same 'auto_map' file every time instead of spamming timestamps
        map_name = 'auto_map'
        self.save_map(map_name)

def main(args=None):
    rclpy.init(args=args)
    node = MapSaverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
