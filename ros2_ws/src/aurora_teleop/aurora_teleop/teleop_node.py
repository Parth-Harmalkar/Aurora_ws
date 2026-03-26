#!/usr/bin/env python3
"""
Aurora Teleop — Simple keyboard control (Hold-to-Move)
Hold w/a/s/d to move, release to stop.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, select, termios, tty, time

BANNER = """
---------------------------
Control Your Aurora Robot!
---------------------------
   w
a  s  d

w/s : forward / backward
a/d : turn left / right
space : force stop
CTRL-C : quit

** Hold key to move **
---------------------------
"""

MOVE_KEYS = {
    'w': ( 1.0,  0.0),
    's': (-1.0,  0.0),
    'a': ( 0.0,  1.0),
    'd': ( 0.0, -1.0),
}

LIN_SPEED = 0.3
ANG_SPEED = 1.0
KEY_TIMEOUT = 0.15  # Stop 150ms after key release


class TeleopNode(Node):
    def __init__(self):
        super().__init__('teleop_node')
        self.publisher = self.create_publisher(Twist, '/teleop_vel', 10)
        self.settings = termios.tcgetattr(sys.stdin)

        self.current_lin = 0.0
        self.current_ang = 0.0
        self.last_key_time = 0.0

        self.timer = self.create_timer(0.05, self.publish_cmd)
        self.get_logger().info("Teleop node initialized (hold-to-move)")

    def publish_cmd(self):
        now = time.monotonic()
        if (now - self.last_key_time) > KEY_TIMEOUT:
            self.current_lin = 0.0
            self.current_ang = 0.0

        twist = Twist()
        twist.linear.x = self.current_lin
        twist.angular.z = self.current_ang
        self.publisher.publish(twist)

    def get_key(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.02)
        key = None
        if rlist:
            key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        print(BANNER)
        try:
            while rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.005)

                key = self.get_key()
                if key is None:
                    continue

                if key == '\x03':  # Ctrl+C
                    break
                elif key in MOVE_KEYS:
                    lin_mult, ang_mult = MOVE_KEYS[key]
                    self.current_lin = lin_mult * LIN_SPEED
                    self.current_ang = ang_mult * ANG_SPEED
                    self.last_key_time = time.monotonic()
                    print(f"\rLinear: {self.current_lin:.2f}, Angular: {self.current_ang:.2f}   ", end='')
                elif key == ' ':
                    self.current_lin = 0.0
                    self.current_ang = 0.0
                    self.last_key_time = 0
                    print(f"\rSTOPPED                                        ", end='')

        except Exception as e:
            print(e)
        finally:
            # Make sure robot stops
            self.current_lin = 0.0
            self.current_ang = 0.0
            for _ in range(5):
                self.publish_cmd()
                time.sleep(0.02)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            print("\nTeleop exited.")


def main(args=None):
    rclpy.init(args=args)
    node = TeleopNode()
    node.run()
    node.destroy_node()
    try:
        rclpy.shutdown()
    except:
        pass


if __name__ == '__main__':
    main()
