#!/home/aurora/aurora_ws/aurora_env/bin/python3
"""
AURORA TELEOP V6 — Hold-to-Move
Publishes continuously while key is held. Stops when key released.
"""

from geometry_msgs.msg import Twist
import sys, select, termios, tty, time
import rclpy
from rclpy.node import Node

BANNER = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AURORA CUSTOM TELEOP 🎮 (Hold to Move)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  w / ↑  : Forward    v/b : Lx Speed +/-
  s / ↓  : Backward   y/h : Az Speed +/-
  a / ←  : Turn Left
  d / →  : Turn Right  SPACE/x : E-STOP
  q      : Quit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

class CustomTeleop(Node):

    KEY_BINDINGS = {
        'w': (1, 0),
        's': (-1, 0),
        'a': (0, 1),
        'd': (0, -1),
        '\x1b[A': (1, 0),   # Up arrow
        '\x1b[B': (-1, 0),  # Down arrow
        '\x1b[D': (0, 1),   # Left arrow
        '\x1b[C': (0, -1),  # Right arrow
    }

    def __init__(self):
        super().__init__('custom_teleop')
        self.pub = self.create_publisher(Twist, '/joy_vel', 10)
        self.lin = 1.0
        self.ang = 1.2
        self.settings = termios.tcgetattr(sys.stdin)

    def get_key(self, timeout=0.05):
        """Read one keypress (or escape sequence). Returns None on timeout."""
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if not rlist:
            return None
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            # Read the bracket and letter with a very short timeout
            rlist2, _, _ = select.select([sys.stdin], [], [], 0.02)
            if rlist2:
                ch += sys.stdin.read(2)
        return ch

    def publish(self, lx, az):
        t = Twist()
        t.linear.x = float(lx)
        t.angular.z = float(az)
        self.pub.publish(t)

    def run(self):
        print(BANNER)
        tty.setraw(sys.stdin.fileno())
        prev_lin_x = 0.0
        prev_ang_z = 0.0

        try:
            while rclpy.ok():
                key = self.get_key(timeout=0.05)

                if key is None:
                    # No key pressed — send stop ONLY if we were previously moving
                    if prev_lin_x != 0.0 or prev_ang_z != 0.0:
                        self.publish(0, 0)
                        prev_lin_x = 0.0
                        prev_ang_z = 0.0
                    continue  # Skip rest of loop

                if key == 'q':
                    break
                elif key in ('x', ' '):
                    self.publish(0, 0)
                    prev_lin_x = 0.0
                    prev_ang_z = 0.0
                elif key == 'v':
                    self.lin = min(2.0, self.lin + 0.1)
                    sys.stdout.write(f"\r[Linear: {self.lin:.1f} m/s]  ")
                    sys.stdout.flush()
                elif key == 'b':
                    self.lin = max(0.1, self.lin - 0.1)
                    sys.stdout.write(f"\r[Linear: {self.lin:.1f} m/s]  ")
                    sys.stdout.flush()
                elif key == 'y':
                    self.ang = min(3.0, self.ang + 0.1)
                    sys.stdout.write(f"\r[Angular: {self.ang:.1f} rad/s]  ")
                    sys.stdout.flush()
                elif key == 'h':
                    self.ang = max(0.1, self.ang - 0.1)
                    sys.stdout.write(f"\r[Angular: {self.ang:.1f} rad/s]  ")
                    sys.stdout.flush()
                elif key in self.KEY_BINDINGS:
                    ldir, adir = self.KEY_BINDINGS[key]
                    lx = ldir * self.lin
                    az = adir * self.ang
                    self.publish(lx, az)
                    prev_lin_x = lx
                    prev_ang_z = az

        except Exception as e:
            sys.stderr.write(f"\nTeleop error: {e}\n")
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
            try:
                self.publish(0, 0)
            except Exception:
                pass


def main():
    rclpy.init()
    node = CustomTeleop()
    node.run()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
