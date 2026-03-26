#!/usr/bin/env python3
"""
AURORA CUSTOM TELEOP V8 — Responsive Hold-to-Move Control
- HOLD a key to move. Release to stop.
- 'i/k' and 'j/l' adjust speed scales (these are sticky).
- SPACE : emergency stop
- 'q'   : quit
"""

from geometry_msgs.msg import Twist
import sys, select, termios, tty, time
import rclpy
from rclpy.node import Node

BANNER = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AURORA TELEOP 🎮 (Hold-to-Move)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  w / ↑  : Forward    i / k : Lin Speed +/-
  s / ↓  : Backward   j / l : Ang Speed +/-
  a / ←  : Turn Left  
  d / →  : Turn Right  SPACE : STOP
  q      : Quit

  ** HOLD key to move, RELEASE to stop **
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

# Movement keys map to (linear, angular) multipliers
MOVE_KEYS = {
    'w':      ( 1.0,  0.0),
    's':      (-1.0,  0.0),
    'a':      ( 0.0,  1.0),
    'd':      ( 0.0, -1.0),
    '\x1b[A': ( 1.0,  0.0),  # Arrow Up
    '\x1b[B': (-1.0,  0.0),  # Arrow Down
    '\x1b[D': ( 0.0,  1.0),  # Arrow Left
    '\x1b[C': ( 0.0, -1.0),  # Arrow Right
}


class CustomTeleop(Node):
    def __init__(self):
        super().__init__('custom_teleop')
        self.pub = self.create_publisher(Twist, '/teleop_vel', 10)

        # Base speeds
        self.lin_speed = 0.3
        self.ang_speed = 1.0

        # Timeout: if no key for this long, stop
        self.key_timeout = 0.15  # 150ms — feels responsive

        self.last_key_time = time.monotonic()
        self.current_lin = 0.0
        self.current_ang = 0.0

        self.settings = termios.tcgetattr(sys.stdin)

        # Publish at 20Hz — fast enough for smooth control, light on CPU
        self.timer = self.create_timer(0.05, self.publish_cmd)

    def publish_cmd(self):
        """Timer callback: publish current velocity, auto-stop on timeout."""
        now = time.monotonic()
        if (now - self.last_key_time) > self.key_timeout:
            # No key held — stop
            self.current_lin = 0.0
            self.current_ang = 0.0

        t = Twist()
        t.linear.x = self.current_lin
        t.angular.z = self.current_ang
        self.pub.publish(t)

    def get_key(self):
        """Non-blocking key read with short timeout."""
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.02)
        key = None
        if rlist:
            key = sys.stdin.read(1)
            # Handle arrow key escape sequences
            if key == '\x1b':
                extra = sys.stdin.read(2)
                key += extra
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        print(BANNER)
        print(f"  Speed: lin={self.lin_speed:.2f}  ang={self.ang_speed:.2f}")
        try:
            while rclpy.ok():
                # Let ROS process the publish timer
                rclpy.spin_once(self, timeout_sec=0.005)

                key = self.get_key()
                if key is None:
                    continue

                # Quit
                if key in ('q', '\x03'):
                    break

                # Movement keys: set velocity while held
                if key in MOVE_KEYS:
                    lin_mult, ang_mult = MOVE_KEYS[key]
                    self.current_lin = lin_mult * self.lin_speed
                    self.current_ang = ang_mult * self.ang_speed
                    self.last_key_time = time.monotonic()

                # Speed adjustment (sticky — doesn't reset on release)
                elif key == 'i':
                    self.lin_speed = min(1.0, self.lin_speed + 0.05)
                    print(f"\r  Speed: lin={self.lin_speed:.2f}  ang={self.ang_speed:.2f}   ", end='')
                elif key == 'k':
                    self.lin_speed = max(0.05, self.lin_speed - 0.05)
                    print(f"\r  Speed: lin={self.lin_speed:.2f}  ang={self.ang_speed:.2f}   ", end='')
                elif key == 'j':
                    self.ang_speed = min(2.0, self.ang_speed + 0.1)
                    print(f"\r  Speed: lin={self.lin_speed:.2f}  ang={self.ang_speed:.2f}   ", end='')
                elif key == 'l':
                    self.ang_speed = max(0.1, self.ang_speed - 0.1)
                    print(f"\r  Speed: lin={self.lin_speed:.2f}  ang={self.ang_speed:.2f}   ", end='')

                # Emergency stop
                elif key == ' ':
                    self.current_lin = 0.0
                    self.current_ang = 0.0
                    self.last_key_time = 0  # Force timeout
                    print("\r  *** STOPPED ***                              ", end='')

        finally:
            # Ensure robot stops on exit
            self.current_lin = 0.0
            self.current_ang = 0.0
            for _ in range(5):
                self.publish_cmd()
                time.sleep(0.02)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            print("\n  Teleop exited. Robot stopped.")


def main():
    rclpy.init()
    node = CustomTeleop()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass


if __name__ == '__main__':
    main()
