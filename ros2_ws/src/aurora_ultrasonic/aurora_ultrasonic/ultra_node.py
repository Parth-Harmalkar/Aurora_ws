import smbus2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range

class UltrasonicNode(Node):

    def __init__(self):
        super().__init__('ultrasonic_node')
        
        # Publishers for two sensors
        self.pub_left = self.create_publisher(Range, '/ultrasonic/front_left', 10)
        self.pub_right = self.create_publisher(Range, '/ultrasonic/front_right', 10)
        
        self.bus_num = 1
        self.addr = 0x08
        try:
            self.bus = smbus2.SMBus(self.bus_num)
            self.get_logger().info(f"Ultrasonic node initialized at I2C {hex(self.addr)}")
        except Exception as e:
            self.get_logger().error(f"Failed to open I2C bus {self.bus_num}: {e}")
            self.bus = None

        self.timer = self.create_timer(0.1, self.read_sensor)

    def read_sensor(self):
        if self.bus is None:
            return

        try:
            # Reading from indices 0 and 1 for the 2 sensors (values in cm)
            d1 = self.bus.read_byte_data(self.addr, 0)
            d2 = self.bus.read_byte_data(self.addr, 1)
            
            # Publish Front Left
            range_msg_left = self.create_range_msg('ultrasonic_front_left', d1)
            self.pub_left.publish(range_msg_left)
            
            # Publish Front Right
            range_msg_right = self.create_range_msg('ultrasonic_front_right', d2)
            self.pub_right.publish(range_msg_right)

        except Exception as e:
            self.get_logger().warn(f"Ultrasonic read error: {e}")

    def create_range_msg(self, frame_id, distance_cm):
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        msg.radiation_type = Range.ULTRASOUND
        msg.field_of_view = 0.523 # Approx 30 degrees
        msg.min_range = 0.02
        msg.max_range = 2.0
        msg.range = float(distance_cm) / 100.0 # Convert to meters
        return msg

def main(args=None):
    rclpy.init(args=args)
    node = UltrasonicNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            if node.bus:
                node.bus.close()
            node.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()