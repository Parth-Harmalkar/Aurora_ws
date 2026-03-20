import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
import numpy as np

class ObstacleAvoidanceNode(Node):

    def __init__(self):
        super().__init__('obstacle_avoidance_node')
        
        # Parameters
        self.declare_parameter('obstacle_threshold', 0.5)  # meters
        self.declare_parameter('linear_speed', 0.15)
        self.declare_parameter('angular_speed', 0.6)
        
        self.threshold = self.get_parameter('obstacle_threshold').get_parameter_value().double_value
        self.linear_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        self.angular_speed = self.get_parameter('angular_speed').get_parameter_value().double_value
        
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.subscription = self.create_subscription(
            LaserScan,
            'scan',
            self.listener_callback,
            10)
            
        self.get_logger().info(f"Obstacle Avoidance Node initialized. Threshold: {self.threshold}m")

    def listener_callback(self, msg):
        # The Lidar C1 usually provides ~720 points for 360 degrees
        # angle_min is -pi, so index 0 is BACK.
        # Front (0 deg) is at index len(msg.ranges) / 2.
        
        n_points = len(msg.ranges)
        if n_points == 0:
            return
            
        mid = n_points // 2
        
        # Map regions based on Arjuna logic (approx 118 degrees coverage)
        # Assuming 1 deg ~= n_points / 360
        deg_to_pts = n_points / 360.0
        
        # Region sizes in degrees from Arjuna
        # front: 55 each side, fside: 42, side: 21
        s_front = int(55 * deg_to_pts)
        s_fside = int(42 * deg_to_pts)
        s_side = int(21 * deg_to_pts)
        
        # Define region ranges (clamped to available points)
        regions = {
            'front_L': self.get_min_dist(msg.ranges, mid, mid + s_front),
            'fleft':   self.get_min_dist(msg.ranges, mid + s_front, mid + s_front + s_fside),
            'left':    self.get_min_dist(msg.ranges, mid + s_front + s_fside, mid + s_front + s_fside + s_side),
            'right':   self.get_min_dist(msg.ranges, mid - s_front - s_fside - s_side, mid - s_front - s_fside),
            'fright':  self.get_min_dist(msg.ranges, mid - s_front - s_fside, mid - s_front),
            'front_R': self.get_min_dist(msg.ranges, mid - s_front, mid)
        }
        
        self.take_action(regions)

    def get_min_dist(self, ranges, start_idx, end_idx):
        # Clip indices
        n = len(ranges)
        start = max(0, min(n - 1, start_idx))
        end = max(0, min(n, end_idx))
        
        if start >= end:
            return 10.0
            
        region_ranges = np.array(ranges[start:end])
        # Filter out invalid values (inf, nan, 0)
        valid_ranges = region_ranges[(np.isfinite(region_ranges)) & (region_ranges > 0.01)]
        
        if len(valid_ranges) > 0:
            return float(np.min(valid_ranges))
        return 10.0

    def take_action(self, regions):
        msg = Twist()
        linear_x = 0.0
        angular_z = 0.0
        
        front_obstacle = regions['front_L'] < self.threshold or regions['front_R'] < self.threshold
        left_obstacle = regions['fleft'] < self.threshold or regions['left'] < self.threshold
        right_obstacle = regions['fright'] < self.threshold or regions['right'] < self.threshold
        
        status = ""
        
        if front_obstacle and left_obstacle and right_obstacle:
            status = "Case 1: Surrounded - Backing up"
            linear_x = -0.1
            angular_z = 0.0
        elif front_obstacle and left_obstacle:
            status = "Case 2: Front & Left - Turning Right"
            linear_x = 0.0
            angular_z = -self.angular_speed
        elif front_obstacle and right_obstacle:
            status = "Case 3: Front & Right - Turning Left"
            linear_x = 0.0
            angular_z = self.angular_speed
        elif front_obstacle:
            if regions['left'] > regions['right']:
                status = "Case 4: Front - Turning Left (more space)"
                linear_x = 0.0
                angular_z = self.angular_speed
            else:
                status = "Case 5: Front - Turning Right (more space)"
                linear_x = 0.0
                angular_z = -self.angular_speed
        elif left_obstacle:
            status = "Case 6: Left obstacle - Adjusting Right"
            linear_x = self.linear_speed
            angular_z = -self.angular_speed * 0.5
        elif right_obstacle:
            status = "Case 7: Right obstacle - Adjusting Left"
            linear_x = self.linear_speed
            angular_z = self.angular_speed * 0.5
        else:
            status = "Case 8: Path clear - Moving Forward"
            linear_x = self.linear_speed
            angular_z = 0.0
            
        self.get_logger().info(status)
        msg.linear.x = linear_x
        msg.angular.z = angular_z
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
