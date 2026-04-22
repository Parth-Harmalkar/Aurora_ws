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
        
        # Publisher (Priority 100 in twist_mux)
        self.stop_pub = self.create_publisher(Twist, '/stop_vel', 10)
        
        self.stop_triggered = False
        self.last_stop_time = 0
        
        self.get_logger().info("Failsafe Stop Layer Initialized (V2: Robust Filtering Enabled)")

    def scan_callback(self, msg):
        # Lidar is at center. robot_radius is 0.22. 
        # Anything < 0.20 is likely the robot itself or too close.
        CHASSIS_LIMIT = 0.20 
        STOP_THRESHOLD = 0.25 # Stop only for TRUE imminent collision (20-25cm)
        
        ranges = msg.ranges
        num_ranges = len(ranges)
        
        # Front 45 degree arc (337.5 to 22.5)
        indices = list(range(int(num_ranges * 337.5 / 360), num_ranges)) + list(range(0, int(num_ranges * 22.5 / 360)))
        
        collision_detected = False
        for i in indices:
            r = ranges[i]
            if r > CHASSIS_LIMIT and r < STOP_THRESHOLD:
                self.trigger_stop(f"Lidar Critical at {r:.2f}m")
                collision_detected = True
                break
        
        # Auto-reset: if no collision detected, and it's been > 1s since last check
        if not collision_detected and self.stop_triggered:
             current_time = self.get_clock().now().nanoseconds / 1e9
             if current_time - self.last_stop_time > 1.0:
                 self.get_logger().info("✅ Failsafe Cleared: Path is now open.")
                 self.stop_triggered = False

    def trigger_stop(self, reason):
        current_time = self.get_clock().now().nanoseconds / 1e9
        self.last_stop_time = current_time
        
        if not self.stop_triggered:
            self.get_logger().warn(f"🛑 FAILSAFE TRIGGERED: {reason}")
            self.stop_triggered = True
        else:
            self.get_logger().debug(f"🛑 FAILSAFE ACTIVE: {reason}")
            
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
