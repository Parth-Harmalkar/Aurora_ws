import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String
import os

class StatusMonitorNode(Node):
    """
    UX Bridge: Converts AI logic states into robot feedback (LEDs/Sound).
    1: Listening (Blue)
    2: Processing (Yellow)
    3: Success (Green)
    4: Error (Red)
    """
    def __init__(self):
        super().__init__('status_monitor')
        
        self.led_sub = self.create_subscription(Int32, '/robot_led_mode', self.led_callback, 10)
        self.status_sub = self.create_subscription(String, '/ai_status', self.status_callback, 10)
        
        self.get_logger().info("Status Monitor (Feedback Layer) Initialized")

    def led_callback(self, msg):
        mode = msg.data
        # This would interface with GPIO or a specialized LED node
        # For now, we simulate with terminal logs or system beeps
        if mode == 1:
            self.get_logger().info("🔵 LED: Listening Mode (Wake word detected)")
            # os.system("beep -f 440 -l 100") # Sample beep
        elif mode == 2:
            self.get_logger().info("🟡 LED: Processing Mode (Thinking...)")
        elif mode == 3:
            self.get_logger().info("🟢 LED: Success (Ready)")
        elif mode == 4:
            self.get_logger().error("🔴 LED: Error Fault")

    def status_callback(self, msg):
        # Can be used to drive an OLED display or more complex patterns
        pass

def main(args=None):
    rclpy.init(args=args)
    node = StatusMonitorNode()
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
