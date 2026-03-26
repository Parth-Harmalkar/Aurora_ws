import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan, Range
import math

class FailsafeStopNode(Node):
    """
    Layer-0 Safety Logic. 
    Overrides everything with a STOP if obstacles are too close (20cm).
    Communicates via /stop_vel (High priority topic).
    """
    def __init__(self):
        super().__init__('failsafe_stop')
        
        # Subscriptions
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.us_fl_sub = self.create_subscription(Range, '/ultrasonic/front_left', self.us_callback, 10)
        self.us_fr_sub = self.create_subscription(Range, '/ultrasonic/front_right', self.us_callback, 10)
        
        # Publisher (Priority 100 in twist_mux)
        self.stop_pub = self.create_publisher(Twist, '/stop_vel', 10)
        
        self.stop_triggered = False
        self.get_logger().info("Failsafe Stop Layer Initialized")

    def us_callback(self, msg):
        if msg.range < 0.15: # Critical ultrasonic threshold
            self.trigger_stop("Ultrasonic Critical")

    def scan_callback(self, msg):
        # Check front arc (340 to 20 degrees)
        CHASSIS_LIMIT = 0.28
        ranges = msg.ranges
        num_ranges = len(ranges)
        
        # Front 45 degree arc
        indices = list(range(int(num_ranges * 337.5 / 360), num_ranges)) + list(range(0, int(num_ranges * 22.5 / 360)))
        
        for i in indices:
            r = ranges[i]
            if r > CHASSIS_LIMIT and r < 0.20: # 20cm hard safety
                self.trigger_stop(f"Lidar Critical at {r:.2f}m")
                return

    def trigger_stop(self, reason):
        if not self.stop_triggered:
            self.get_logger().warn(f"🛑 FAILSAFE TRIGGERED: {reason}")
            self.stop_triggered = True
            
        t = Twist() # Zero velocity
        self.stop_pub.publish(t)

def main(args=None):
    rclpy.init(args=args)
    node = FailsafeStopNode()
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
