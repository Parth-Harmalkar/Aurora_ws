#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading

class TextCommanderNode(Node):
    def __init__(self):
        super().__init__('text_commander')
        self.pub = self.create_publisher(String, '/voice_command', 10)
        self.get_logger().info('Text Commander Active: Type your command and press Enter.')

def main(args=None):
    rclpy.init(args=args)
    node = TextCommanderNode()
    
    # Run ROS spin in a background thread so `input()` doesn't block it
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()
    
    try:
        while rclpy.ok():
            # Get user input from the terminal
            command = input("\n[AI Commander] >> ")
            if command.strip():
                msg = String()
                msg.data = command.strip()
                node.pub.publish(msg)
                node.get_logger().info(f"Command Published: '{msg.data}' (Check AI Bridge logs for response)")
            
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
