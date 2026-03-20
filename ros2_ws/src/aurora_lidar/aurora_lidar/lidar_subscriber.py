import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np

class LidarSubscriber(Node):

    def __init__(self):
        super().__init__('lidar_subscriber')
        self.subscription = self.create_subscription(
            LaserScan,
            'scan',
            self.listener_callback,
            10)
        self.get_logger().info("Aurora Lidar Subscriber initialized and listening to /scan")

    def listener_callback(self, msg):
        # Filter out inf and NaN values
        ranges = np.array(msg.ranges)
        valid_ranges = ranges[np.isfinite(ranges)]
        
        if len(valid_ranges) > 0:
            min_dist = np.min(valid_ranges)
            avg_dist = np.mean(valid_ranges)
            self.get_logger().info(f'Scan: {len(msg.ranges)} points. Min dist: {min_dist:.2f}m, Avg dist: {avg_dist:.2f}m')
        else:
            self.get_logger().warn('No valid ranges in current scan')

def main(args=None):
    rclpy.init(args=args)
    node = LidarSubscriber()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
