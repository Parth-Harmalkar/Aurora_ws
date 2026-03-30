#!/usr/bin/env python3
import os
import rclpy
from rclpy.node import Node
from aurora_msgs.srv import SaveMap
from datetime import datetime

class MapSaverNode(Node):
    def __init__(self):
        super().__init__('map_saver')
        # Create maps directory if it doesn't exist
        self.maps_dir = os.path.expanduser('~/.aurora/maps')
        os.makedirs(self.maps_dir, exist_ok=True)
        
        # Provide the SaveMap service
        self.srv = self.create_service(SaveMap, 'save_map', self.save_map_callback)
        
        # Auto-save timer (5 minutes = 300 seconds)
        self.timer_period = 300.0  
        self.timer = self.create_timer(self.timer_period, self.auto_save_callback)
        
        self.get_logger().info('Map Saver Node initialized. Auto-saving every 5 minutes.')

    def save_map(self, map_name):
        map_path = os.path.join(self.maps_dir, map_name)
        # Call Nav2 map_saver_cli
        cmd = f'ros2 run nav2_map_server map_saver_cli -f {map_path}'
        self.get_logger().info(f'Saving map to {map_path}...')
        
        result = os.system(cmd)
        
        if result == 0:
            self.get_logger().info(f'Successfully saved map to {map_path}')
            return True, f'Successfully saved map to {map_path}'
        else:
            self.get_logger().error(f'Failed to save map. Command returned {result}')
            return False, f'Failed to save map with exit code {result}'

    def save_map_callback(self, request, response):
        success, msg = self.save_map(request.map_name)
        response.success = success
        response.message = msg
        return response

    def auto_save_callback(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_name = f'auto_map_{timestamp}'
        self.save_map(map_name)

def main(args=None):
    rclpy.init(args=args)
    node = MapSaverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
