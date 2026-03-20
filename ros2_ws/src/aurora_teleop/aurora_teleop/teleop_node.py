import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, select, termios, tty

msg = """
Control Your Aurora Robot!
---------------------------
Moving around:
   w
a  s  d

w/s : increase/decrease linear velocity (x)
a/d : increase/decrease angular velocity (z)

space key, s : force stop

CTRL-C to quit
"""

moveBindings = {
    'w': (1,0),
    'a': (0,1),
    'd': (0,-1),
    's': (0,0),
}

class TeleopNode(Node):

    def __init__(self):
        super().__init__('teleop_node')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.settings = termios.tcgetattr(sys.stdin)
        self.get_logger().info("Teleop node initialized")

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        select.select([sys.stdin], [], [], 0)
        key = sys.stdin.read(1)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def run(self):
        linear_vel = 0.0
        angular_vel = 0.0
        status = 0

        try:
            print(msg)
            while True:
                key = self.getKey()
                if key in moveBindings.keys():
                    if key == 'w':
                        linear_vel += 0.1
                    elif key == 's':
                        linear_vel = 0.0
                        angular_vel = 0.0
                    elif key == 'a':
                        angular_vel += 0.1
                    elif key == 'd':
                        angular_vel -= 0.1
                    
                    status = (status + 1) % 15
                elif key == '\x03':
                    break
                else:
                    if key == ' ':
                        linear_vel = 0.0
                        angular_vel = 0.0
                    
                twist = Twist()
                twist.linear.x = linear_vel
                twist.angular.z = angular_vel
                self.publisher.publish(twist)

                if status == 0:
                    print(f"Linear: {linear_vel:.2f}, Angular: {angular_vel:.2f}")

        except Exception as e:
            print(e)

        finally:
            twist = Twist()
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.publisher.publish(twist)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

def main(args=None):
    rclpy.init(args=args)
    node = TeleopNode()
    node.run()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
